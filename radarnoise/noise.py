"""Noise library: controlled impairments injected into complex slow-time radar windows before demodulation.

Every function takes z (B, K, L) complex (16 range bins x L frames at 20 Hz), a severity level in physical units,
a torch.Generator, and a context dict (chest index k0 (B,), wavelength lam in m, fs). Powers are relative to the
window's own dynamic chest signal P = mean_t |z_k0 - mean_t z_k0|^2, so levels mean the same thing for every radar.

17 noise types in 5 families (NOISES registry below; level lists go from mild to severe), plus the observation
length (crop), which the survey varies directly:
  receiver   thermal (AWGN, SNR dB), quantization (ADC bits), impulsive (EMI spikes, rate),
             interference (spurious tone, SIR dB)
  oscillator phase_noise (common random-walk phase, rad/sqrt(s)), iq_imbalance (gain/phase imbalance + DC),
             gain_drift (slow AGC/gain modulation)
  timing     frame_loss (burst packet loss, zero-order hold), timing_jitter (ms), clock_drift (% rate error)
  scene      static_clutter (strong static reflector, dB over chest motion), moving_clutter (second moving
             reflector, amplitude ratio), multipath (delayed echo of the bin's own signal, amplitude ratio),
             range_offset (target off the assumed chest bin, bins)
  subject    body_motion (random body movement: drift + jerks, mm), vibration_hr / vibration_rr (mechanical
             vibration of the radar mount inside the cardiac / breathing band, mm)
  observation  crop (window length in s) is applied by the survey, not here.
"""
import math

import torch


def _randn(shape, g, dev):
    return torch.randn(shape, generator=g, device=dev)


def _rand(shape, g, dev):
    return torch.rand(shape, generator=g, device=dev)


def _cn(shape, g, dev):
    """Unit-power circular complex Gaussian."""
    return torch.complex(_randn(shape, g, dev), _randn(shape, g, dev)) / math.sqrt(2)


def dyn_power(z, k0):
    zc = z[torch.arange(len(z), device=z.device), k0.long()]
    return (zc - zc.mean(-1, keepdim=True)).abs().pow(2).mean(-1)            # (B,)


def _smooth_noise(B, L, fs, hi, g, dev, lo=0.0):
    """Unit-std random process band-limited to [lo, hi] Hz, (B, L)."""
    x = _randn((B, L), g, dev)
    X = torch.fft.rfft(x, dim=-1)
    f = torch.fft.rfftfreq(L, 1 / fs).to(dev)
    x = torch.fft.irfft(X * ((f >= lo) & (f <= hi)), n=L, dim=-1)
    return x / (x.std(-1, keepdim=True) + 1e-12)


def _phase_motion(z, d_mm, lam):
    """Apply a displacement d (B, L) mm common to all bins as a phase rotation (round-trip)."""
    return z * torch.exp(1j * (4 * math.pi * d_mm / (lam * 1e3)))[:, None, :].to(z.dtype)


def _t(L, fs, dev):
    return torch.arange(L, device=dev) / fs


# ---------------------------------------------------------------------------------------------- receiver
def thermal(z, snr_db, g, c):
    P = dyn_power(z, c["k0"])
    s = torch.sqrt(P / 10 ** (snr_db / 10))[:, None, None]
    return z + s * _cn(z.shape, g, z.device)


def quantization(z, bits, g, c):
    fs_ = torch.maximum(z.real.abs().amax((-1, -2)), z.imag.abs().amax((-1, -2)))[:, None, None]
    step = 2 * fs_ / 2 ** bits
    q = lambda x: torch.round(x / step) * step
    return torch.complex(q(z.real), q(z.imag))


def impulsive(z, rate, g, c):
    B, K, L = z.shape
    A = torch.sqrt(dyn_power(z, c["k0"]))[:, None, None]
    hit = (_rand((B, 1, L), g, z.device) < rate)
    return z + hit * 10 * A * _cn((B, K, L), g, z.device)


def interference(z, sir_db, g, c):
    B, K, L = z.shape
    A = torch.sqrt(dyn_power(z, c["k0"]))[:, None, None] * 10 ** (-sir_db / 20)
    f = (_rand((B, 1, 1), g, z.device) * 6 - 3)                                 # -3..3 Hz Doppler
    tone = torch.exp(2j * math.pi * f * _t(L, c["fs"], z.device))
    return z + A * _cn((B, K, 1), g, z.device) * tone


# -------------------------------------------------------------------------------------------- oscillator
def phase_noise(z, sigma, g, c):
    B, K, L = z.shape
    ph = torch.cumsum(_randn((B, 1, L), g, z.device) * sigma / math.sqrt(c["fs"]), -1)
    return z * torch.exp(1j * ph)


def iq_imbalance(z, eps, g, c):
    I, Q = z.real, z.imag
    Q2 = (1 + eps) * (Q * math.cos(eps) + I * math.sin(eps))
    dc = eps * z.abs().mean((-1, -2), keepdim=True) * torch.exp(2j * math.pi * _rand((len(z), 1, 1), g, z.device))
    return torch.complex(I, Q2) + dc


def gain_drift(z, depth, g, c):
    B, K, L = z.shape
    s = _smooth_noise(B, L, c["fs"], 0.3, g, z.device, lo=0.01)
    return z * (1 + depth * s)[:, None, :]


# ------------------------------------------------------------------------------------------------ timing
def frame_loss(z, p, g, c, burst=5):
    B, K, L = z.shape
    start = _rand((B, L), g, z.device) < p / burst
    lost = torch.zeros((B, L), dtype=torch.bool, device=z.device)
    for k in range(burst):                                                     # bursts of `burst` frames
        lost |= torch.roll(start, k, -1) & (torch.arange(L, device=z.device) >= k)
    lost[:, 0] = False
    idx = torch.arange(L, device=z.device).expand(B, L) * (~lost)
    idx = torch.cummax(idx, -1).values                                        # zero-order hold
    return torch.gather(z, -1, idx[:, None, :].expand(B, K, L))


def _resample(z, t_new, fs):
    """Linear interpolation of z (B,K,L) at times t_new (B,L) s (clamped to the window)."""
    B, K, L = z.shape
    x = (t_new * fs).clamp(0, L - 1)
    i0 = x.floor().long().clamp(max=L - 2)
    w = (x - i0)[:, None, :]
    g0 = torch.gather(z, -1, i0[:, None, :].expand(B, K, L))
    g1 = torch.gather(z, -1, (i0 + 1)[:, None, :].expand(B, K, L))
    return g0 * (1 - w) + g1 * w


def timing_jitter(z, sigma_ms, g, c):
    B, K, L = z.shape
    t = _t(L, c["fs"], z.device).expand(B, L) + _randn((B, L), g, z.device) * sigma_ms * 1e-3
    return _resample(z, t, c["fs"])


def clock_drift(z, pct, g, c):
    """The radar's frame clock runs pct % fast: frames labelled k/fs were taken at k/fs * (1 + pct/100), so every
    rate is read pct % low. Sign is random per window."""
    B, K, L = z.shape
    sgn = torch.where(_rand((B, 1), g, z.device) < 0.5, -1.0, 1.0)
    t = _t(L, c["fs"], z.device).expand(B, L) * (1 + sgn * pct / 100)
    return _resample(z, t, c["fs"])


# ------------------------------------------------------------------------------------------------- scene
def static_clutter(z, ratio_db, g, c):
    B, K, L = z.shape
    A = torch.sqrt(dyn_power(z, c["k0"]))[:, None, None] * 10 ** (ratio_db / 20)
    return z + A * _cn((B, K, 1), g, z.device)


def moving_clutter(z, ratio, g, c):
    """A second reflector (fan, curtain, another person's sway) with its own band-limited motion (std 2 mm,
    0.05-1 Hz), present in every bin with a random complex gain."""
    B, K, L = z.shape
    A = torch.sqrt(dyn_power(z, c["k0"]))[:, None, None] * ratio
    d = 2.0 * _smooth_noise(B, L, c["fs"], 1.0, g, z.device, lo=0.05)
    s = torch.exp(1j * (4 * math.pi * d / (c["lam"] * 1e3)))[:, None, :]
    return z + A * _cn((B, K, 1), g, z.device) * s


def multipath(z, a, g, c):
    """Delayed echo (0.1-0.5 s, random phase) of each bin's own dynamic signal with relative amplitude a."""
    B, K, L = z.shape
    lag = (2 + (_rand((B,), g, z.device) * 8).long())                           # 2..9 frames
    u = z - z.mean(-1, keepdim=True)
    idx = (torch.arange(L, device=z.device)[None] - lag[:, None]).clamp(min=0)
    echo = torch.gather(u, -1, idx[:, None, :].expand(B, K, L))
    ph = torch.exp(2j * math.pi * _rand((B, 1, 1), g, z.device))
    return z + a * ph * echo


def range_offset(z, bins, g, c):
    """The target sits `bins` range bins away from where it is assumed (random direction): shift the bins and fill
    the vacated ones with noise at the window's quietest bin's dynamic level."""
    B, K, L = z.shape
    sgn = 1 if _rand((1,), g, z.device).item() < 0.5 else -1
    s = sgn * int(bins)
    out = torch.roll(z, s, 1)
    u = z - z.mean(-1, keepdim=True)
    floor = u.abs().pow(2).mean(-1).amin(-1).sqrt()[:, None, None]
    fill = z.mean(-1, keepdim=True) * 0 + floor * _cn((B, K, L), g, z.device)
    if s > 0:
        out[:, :s] = fill[:, :s]
    else:
        out[:, s:] = fill[:, s:]
    return out


# ----------------------------------------------------------------------------------------------- subject
def body_motion(z, amp_mm, g, c):
    """Random body movement: slow postural drift (< 0.3 Hz, std amp/2) plus jerks (Poisson, 1 per 10 s, steps of
    about amp mm smoothed over 0.5 s), applied as a displacement common to all bins."""
    B, K, L = z.shape
    fs = c["fs"]
    drift = 0.5 * amp_mm * _smooth_noise(B, L, fs, 0.3, g, z.device, lo=0.02)
    ev = (_rand((B, L), g, z.device) < 0.1 / fs).float()
    step = ev * (_rand((B, L), g, z.device) + 0.5) * amp_mm * torch.where(_rand((B, L), g, z.device) < 0.5, -1.0, 1.0)
    jerks = torch.cumsum(step, -1)
    k = int(0.5 * fs)
    jerks = torch.nn.functional.avg_pool1d(jerks[:, None], k, 1, k // 2, count_include_pad=False)[:, 0, :L]
    return _phase_motion(z, drift + jerks, c["lam"])


def _vibration(z, amp_mm, lo, hi, g, c):
    B, K, L = z.shape
    f = lo + (hi - lo) * _rand((B, 1), g, z.device)
    ph = 2 * math.pi * _rand((B, 1), g, z.device)
    d = amp_mm * torch.sin(2 * math.pi * f * _t(L, c["fs"], z.device) + ph)
    return _phase_motion(z, d, c["lam"])


def vibration_hr(z, amp_mm, g, c):
    return _vibration(z, amp_mm, 0.8, 2.5, g, c)


def vibration_rr(z, amp_mm, g, c):
    return _vibration(z, amp_mm, 0.15, 0.5, g, c)


NOISES = {
    "thermal":        dict(fn=thermal, levels=[20, 10, 5, 0, -5, -10], unit="SNR dB", family="receiver"),
    "quantization":   dict(fn=quantization, levels=[12, 10, 8, 6, 4], unit="bits", family="receiver"),
    "impulsive":      dict(fn=impulsive, levels=[0.001, 0.003, 0.01, 0.03, 0.1], unit="spikes/frame", family="receiver"),
    "interference":   dict(fn=interference, levels=[20, 10, 0, -10], unit="SIR dB", family="receiver"),
    "phase_noise":    dict(fn=phase_noise, levels=[0.01, 0.03, 0.1, 0.3, 1.0], unit="rad/sqrt(s)", family="oscillator"),
    "iq_imbalance":   dict(fn=iq_imbalance, levels=[0.05, 0.1, 0.2, 0.3, 0.5], unit="gain=phase(rad)", family="oscillator"),
    "gain_drift":     dict(fn=gain_drift, levels=[0.05, 0.1, 0.2, 0.5], unit="relative std", family="oscillator"),
    "frame_loss":     dict(fn=frame_loss, levels=[0.01, 0.05, 0.1, 0.2, 0.4], unit="fraction", family="timing"),
    "timing_jitter":  dict(fn=timing_jitter, levels=[2, 5, 10, 20], unit="ms", family="timing"),
    "clock_drift":    dict(fn=clock_drift, levels=[0.5, 1, 2, 5], unit="%", family="timing"),
    "static_clutter": dict(fn=static_clutter, levels=[0, 10, 20, 30, 40], unit="dB over chest motion", family="scene"),
    "moving_clutter": dict(fn=moving_clutter, levels=[0.1, 0.3, 1, 3], unit="amplitude ratio", family="scene"),
    "multipath":      dict(fn=multipath, levels=[0.1, 0.3, 0.5, 0.8], unit="echo amplitude", family="scene"),
    "range_offset":   dict(fn=range_offset, levels=[1, 2, 4, 8], unit="bins", family="scene"),
    "body_motion":    dict(fn=body_motion, levels=[0.2, 0.5, 1, 2, 5], unit="mm", family="subject"),
    "vibration_hr":   dict(fn=vibration_hr, levels=[0.01, 0.03, 0.1, 0.3], unit="mm (0.8-2.5 Hz)", family="subject"),
    "vibration_rr":   dict(fn=vibration_rr, levels=[0.1, 0.3, 1, 3], unit="mm (0.15-0.5 Hz)", family="subject"),
}


def apply(name, z, level, g, ctx):
    return NOISES[name]["fn"](z, level, g, ctx)


def random_noise(z, g, ctx, p=0.4, max_n=2):
    """Training augmentation: max_n rounds; in each, one random noise type at a random level is applied to a random
    fraction p of the windows (so ~1 - (1-p)^max_n of the windows are impaired, some by two noises)."""
    B = len(z)
    names = list(NOISES)
    out = z.clone()
    for _ in range(max_n):
        sel = _rand((B,), g, z.device) < p
        if not sel.any():
            continue
        name = names[int(_rand((1,), g, z.device).item() * len(names))]
        lv = NOISES[name]["levels"]
        level = lv[int(_rand((1,), g, z.device).item() * len(lv))]
        if name == "range_offset":
            continue                                    # changes which bin is the chest; not a training augmentation
        c = dict(ctx, k0=ctx["k0"][sel])
        out[sel] = apply(name, out[sel], level, g, c)
    return out
