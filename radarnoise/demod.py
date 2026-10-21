"""Batched torch demodulation of complex slow-time windows to chest displacement (mm), mirroring radarnoise.dsp:
  FMCW (79 GHz, motion wraps the phase): arctangent demodulation around a circle-fit centre with gated phase
          increments (phase_to_mm)
  UWB  (Novelda, UMAIN; motion << wavelength): projection on the principal I/Q axis divided by the arc radius
          (linear_displacement)
Works on CPU or CUDA; z: (..., L) complex.
"""
import math

import torch

from .constants import FS_OUT, RADARS


def fft_band(x, fs, lo=None, hi=None):
    """Zero-phase FFT-mask filter along the last axis (real input)."""
    X = torch.fft.rfft(x, dim=-1)
    f = torch.fft.rfftfreq(x.shape[-1], 1 / fs).to(x.device)
    m = torch.ones_like(f, dtype=torch.bool)
    if lo is not None:
        m &= f >= lo
    if hi is not None:
        m &= f <= hi
    return torch.fft.irfft(X * m, n=x.shape[-1], dim=-1)


def butter_lowpass(x, fs, fc, order):
    """Zero-phase Butterworth low-pass as in scipy filtfilt (|H|^2 response), applied by FFT on a reflect-padded
    signal so window edges do not ring."""
    L = x.shape[-1]
    p = min(L - 1, int(3 * fs / fc) if fc > 0 else L - 1)
    xp = torch.cat([2 * x[..., :1] - x[..., 1:p + 1].flip(-1), x, 2 * x[..., -1:] - x[..., -p - 1:-1].flip(-1)], -1)
    n = xp.shape[-1]
    f = torch.fft.rfftfreq(n, 1 / fs).to(x.device)
    H = 1.0 / (1.0 + (f / fc) ** (2 * order))
    return torch.fft.irfft(torch.fft.rfft(xp, dim=-1) * H, n=n, dim=-1)[..., p:p + L]


def lowpass_c(z, fs, hi):
    return torch.complex(butter_lowpass(z.real, fs, hi, 4), butter_lowpass(z.imag, fs, hi, 4))


def circle_center(z, ridge=1e-9):
    """Kasa circle fit per trajectory: (..., L) complex -> (...,) complex centre."""
    x, y = z.real.double(), z.imag.double()
    A = torch.stack([x, y, torch.ones_like(x)], -1)                          # (..., L, 3)
    b = (x ** 2 + y ** 2)[..., None]
    AtA = A.transpose(-1, -2) @ A
    AtA = AtA + ridge * AtA.diagonal(dim1=-2, dim2=-1).mean(-1)[..., None, None] * torch.eye(3, device=z.device, dtype=x.dtype)
    sol = torch.linalg.solve(AtA, A.transpose(-1, -2) @ b)[..., 0]
    return torch.complex(0.5 * sol[..., 0], 0.5 * sol[..., 1])


def _centre(z, fs):
    zs = lowpass_c(z, fs, 3.0)
    m = zs.mean(-1)
    spread = (zs - m[..., None]).abs().std(-1) + 1e-15
    c = circle_center(zs).to(z.dtype)
    bad = ~torch.isfinite(c.real) | ~torch.isfinite(c.imag) | ((c - m).abs() > 50 * spread)
    return zs, m, spread, c, bad


def _detrend(d, fs, drift_hz=0.05):
    if d.shape[-1] > 3 * fs / drift_hz / 10:
        d = d - butter_lowpass(d, fs, drift_hz, 2)
    return d - d.mean(-1, keepdim=True)


def phase_mm(z, lam, fs=FS_OUT, gate=0.3):
    zs, m, spread, c, bad = _centre(z, fs)
    c = torch.where(bad, m - spread.to(z.dtype), c)
    u = z - c[..., None]
    r = u.abs()
    dph = torch.angle(u[..., 1:] * u[..., :-1].conj())
    ok = torch.minimum(r[..., 1:], r[..., :-1]) >= gate * r.median(-1, keepdim=True).values
    ph = torch.cat([torch.zeros_like(dph[..., :1]), torch.cumsum(dph * ok, -1)], -1)
    return _detrend(ph, fs) * lam / (4 * math.pi) * 1e3


def linear_mm(z, lam, fs=FS_OUT):
    u = z - z.mean(-1, keepdim=True)
    X = torch.stack([u.real, u.imag], -1).double()                            # (..., L, 2)
    C = X.transpose(-1, -2) @ X
    _, V = torch.linalg.eigh(C)
    proj = (X @ V[..., :, -1:])[..., 0].to(z.real.dtype)
    zs, m, spread, c, bad = _centre(z, fs)
    R = torch.where(bad, m.abs(), (zs - c[..., None]).abs().median(-1).values)
    return _detrend(proj / (R[..., None] + 1e-15) * lam / (4 * math.pi) * 1e3, fs)


def demodulate(radar, z, fs=FS_OUT):
    lam = RADARS[radar]["wavelength_m"]
    return phase_mm(z, lam, fs) if radar == "fmcw" else linear_mm(z, lam, fs)
