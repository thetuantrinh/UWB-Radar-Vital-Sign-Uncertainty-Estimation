"""Classical RR / HR estimators on displacement windows (B, K, L) in mm at fs Hz (torch, CPU or CUDA).

Bin selection:  chest  - the bin the radar's chest detector picked (rel_range = 0)
                snr    - the bin with the highest peak-to-band SNR for that vital
                avg    - spectra of all 16 bins (each normalised to unit band power) averaged
Methods:        fft    - spectral peak (Hann, x8 zero-padding, parabolic interpolation)
                acf    - first autocorrelation peak inside the band's lag range
Spectra are weighted by a forward-backward 3rd-order Butterworth band-pass (as in Vital-LM's evidence); HR spectra
also suppress +-0.04 Hz around harmonics 2..9 of the window's breathing estimate (same bin selection).
"""
import torch

RR_BAND, HR_BAND = (0.15, 0.6), (0.7, 3.0)           # RR band = the band the labels are defined in


def bp_weight(f, lo, hi, order=3):
    """Amplitude response of a zero-phase (forward-backward) Butterworth band-pass, as Vital-LM's DSP evidence
    applies before peak picking; damps the band edges, where drift and 1/f motion otherwise win."""
    x = (f ** 2 - lo * hi) / (f * (hi - lo) + 1e-12)
    return 1.0 / (1.0 + x ** (2 * order))


def bandpass(x, fs, lo, hi):
    X = torch.fft.rfft(x - x.mean(-1, keepdim=True), dim=-1)
    f = torch.fft.rfftfreq(x.shape[-1], 1 / fs).to(x.device)
    return torch.fft.irfft(X * ((f >= lo) & (f <= hi)), n=x.shape[-1], dim=-1)


def spectrum(x, fs, pad=8):
    L = x.shape[-1]
    w = torch.hann_window(L, periodic=False, device=x.device, dtype=x.dtype)
    S = torch.fft.rfft((x - x.mean(-1, keepdim=True)) * w, n=L * pad, dim=-1).abs()
    return S, torch.fft.rfftfreq(L * pad, 1 / fs).to(x.device)


def band_peak(S, f, lo, hi, mask=None):
    """S (..., F) -> (peak Hz, peak / mean band power) with parabolic interpolation."""
    m = (f >= lo) & (f <= hi)
    Sb = S[..., m]
    if mask is not None:
        Sb = Sb * mask
    i = Sb.argmax(-1)
    fb = f[m]
    df = fb[1] - fb[0]
    a = Sb.gather(-1, (i - 1).clamp(min=0)[..., None])[..., 0]
    b = Sb.gather(-1, i[..., None])[..., 0]
    c = Sb.gather(-1, (i + 1).clamp(max=Sb.shape[-1] - 1)[..., None])[..., 0]
    den = a - 2 * b + c
    delta = torch.where((den != 0) & (i > 0) & (i < Sb.shape[-1] - 1), 0.5 * (a - c) / den, torch.zeros_like(den))
    snr = b / (Sb.mean(-1) + 1e-12)
    return fb[i] + delta.clamp(-1, 1) * df, snr


def harmonic_mask(f, lo, hi, rr_hz, width=0.04, n=(2, 10)):
    fb = f[(f >= lo) & (f <= hi)]
    m = torch.ones(rr_hz.shape + fb.shape, device=f.device)
    for h in range(*n):
        m = m * ((fb - h * rr_hz[..., None]).abs() > width)
    return m


def acf_rate(x, fs, lo, hi):
    """x (..., L) band-passed -> rate (Hz) from the highest autocorrelation peak with lag in [1/hi, 1/lo]."""
    L = x.shape[-1]
    X = torch.fft.rfft(x, n=2 * L, dim=-1)
    r = torch.fft.irfft(X.abs() ** 2, n=2 * L, dim=-1)[..., :L]
    r = r / (r[..., :1] + 1e-12)
    a, b = int(fs / hi), min(int(fs / lo) + 1, L - 1)
    seg = r[..., a:b]
    i = seg.argmax(-1)
    y0 = seg.gather(-1, (i - 1).clamp(min=0)[..., None])[..., 0]
    y1 = seg.gather(-1, i[..., None])[..., 0]
    y2 = seg.gather(-1, (i + 1).clamp(max=seg.shape[-1] - 1)[..., None])[..., 0]
    den = y0 - 2 * y1 + y2
    d = torch.where(den != 0, 0.5 * (y0 - y2) / den, torch.zeros_like(den)).clamp(-1, 1)
    return fs / (a + i + d)


def estimate(disp, fs, chest_k):
    """All classical estimators. Returns {name: (B,) rate in per-minute} for names '<vital>_<method>_<bins>'."""
    B, K, L = disp.shape
    S0, f = spectrum(disp, fs)
    S = S0 * bp_weight(f, *RR_BAND)
    ar = torch.arange(B, device=disp.device)
    out = {}
    # breathing
    pk, snr = band_peak(S, f, *RR_BAND)                                     # (B, K)
    best_rr = snr.argmax(-1)
    out["rr_fft_chest"] = 60 * pk[ar, chest_k]
    out["rr_fft_snr"] = 60 * pk[ar, best_rr]
    m = (f >= RR_BAND[0]) & (f <= RR_BAND[1])
    Sn = S / (S[..., m].pow(2).mean(-1, keepdim=True).sqrt() + 1e-12)
    out["rr_fft_avg"] = 60 * band_peak(Sn.mean(1), f, *RR_BAND)[0]
    xr = bandpass(disp, fs, *RR_BAND)
    out["rr_acf_snr"] = 60 * acf_rate(xr[ar, best_rr], fs, *RR_BAND)
    out["rr_acf_chest"] = 60 * acf_rate(xr[ar, chest_k], fs, *RR_BAND)
    # heart (breathing harmonics suppressed using the same bin-selection's breathing estimate)
    rr_hz = {"chest": out["rr_fft_chest"] / 60, "snr": out["rr_fft_snr"] / 60, "avg": out["rr_fft_avg"] / 60}
    S = S0 * bp_weight(f, *HR_BAND)
    hm = harmonic_mask(f, *HR_BAND, rr_hz["snr"][:, None].expand(B, K))
    pk, snr = band_peak(S, f, *HR_BAND, mask=hm)
    best_hr = snr.argmax(-1)
    out["hr_fft_snr"] = 60 * pk[ar, best_hr]
    hm_c = harmonic_mask(f, *HR_BAND, rr_hz["chest"])
    out["hr_fft_chest"] = 60 * band_peak(S[ar, chest_k], f, *HR_BAND, mask=hm_c)[0]
    mh = (f >= HR_BAND[0]) & (f <= HR_BAND[1])
    Sh = S / (S[..., mh].pow(2).mean(-1, keepdim=True).sqrt() + 1e-12)
    out["hr_fft_avg"] = 60 * band_peak(Sh.mean(1), f, *HR_BAND, mask=harmonic_mask(f, *HR_BAND, rr_hz["avg"]))[0]
    xh = bandpass(disp, fs, *HR_BAND)
    out["hr_acf_snr"] = 60 * acf_rate(xh[ar, best_hr], fs, *HR_BAND)
    out["hr_acf_chest"] = 60 * acf_rate(xh[ar, chest_k], fs, *HR_BAND)
    return out


def signal_quality(disp, fs, chest_k, hr, rr):
    """Label-based quality of the chest bin, to put all noise types on one axis: rank (0 = strongest, 0.5 = chance)
    of the spectral power at the true HR / RR among the band's frequencies."""
    B = len(disp)
    S, f = spectrum(disp[torch.arange(B, device=disp.device), chest_k], fs)
    out = {}
    for k, y, (lo, hi) in [("hr_rank", hr, HR_BAND), ("rr_rank", rr, RR_BAND)]:
        m = (f >= lo) & (f <= hi)
        Sb, fb = S[:, m], f[m]
        i = (fb[None] - (y / 60)[:, None]).abs().argmin(-1)
        p = Sb.gather(-1, i[:, None])
        r = (Sb >= p).float().mean(-1)
        out[k] = torch.where(torch.isfinite(y), r, torch.full_like(r, float("nan")))
    return out
