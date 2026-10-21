"""Revision additions to the degradation library (radarnoise.noise is left unchanged for reproducibility).

body_motion_body   random body movement acting on the body return only: the chest return of each body bin is
                   rotated about that bin's static (clutter) centre, z_k = c_k + (z_k - c_k) e^{j4 pi d/lam}, and on
                   the UWB radars the dynamic part also migrates in range by d / bin spacing (fractional shift along
                   k). Body bins: all 16 on the UWB radars (their window spans 0.10 / 0.23 m), k0-1..k0+1 on FMCW
                   (0.18 m bins). Same displacement process d(t) as radarnoise.noise.body_motion, which applies d to
                   every bin (static reflectors included) and therefore models a common-mode (platform) motion.
cm_reference       common-mode phase correction from static reflectors: bins at least 3 bins from the chest bin are
                   weighted by their static power and the phase of sum_k w_k z_k(t) conj(mean z_k) is removed from
                   every bin. Meaningful only when the window contains static reflectors outside the body (FMCW,
                   2.9 m span); on the UWB windows every bin contains the chest.
"""
import math

import torch

from .demod import _centre
from .noise import NOISES, _rand, _smooth_noise


def _body_displacement(B, L, amp_mm, g, fs, dev):
    """Identical random process to radarnoise.noise.body_motion (drift + smoothed jerks), mm."""
    drift = 0.5 * amp_mm * _smooth_noise(B, L, fs, 0.3, g, dev, lo=0.02)
    ev = (_rand((B, L), g, dev) < 0.1 / fs).float()
    step = ev * (_rand((B, L), g, dev) + 0.5) * amp_mm * torch.where(_rand((B, L), g, dev) < 0.5, -1.0, 1.0)
    jerks = torch.cumsum(step, -1)
    k = int(0.5 * fs)
    jerks = torch.nn.functional.avg_pool1d(jerks[:, None], k, 1, k // 2, count_include_pad=False)[:, 0, :L]
    return drift + jerks


def body_motion_body(z, amp_mm, g, c):
    B, K, L = z.shape
    d = _body_displacement(B, L, amp_mm, g, c["fs"], z.device)                     # (B, L) mm
    _, m, _, cen, bad = _centre(z, c["fs"])
    cen = torch.where(bad, m, cen)                                                  # static centre per bin (B, K)
    u = z - cen[..., None]
    if c.get("bin_m") is not None and c.get("migrate", True):
        # fractional range shift of the dynamic part by d / bin spacing (linear interpolation along k)
        sh = (d * 1e-3 / c["bin_m"])[:, None, :]                                    # (B, 1, L) bins
        kk = torch.arange(K, device=z.device, dtype=sh.dtype)[None, :, None] - sh
        k0 = kk.floor().clamp(0, K - 1).long()
        k1 = (k0 + 1).clamp(max=K - 1)
        w = (kk - kk.floor()).clamp(0, 1).to(z.dtype)
        inside = ((kk >= 0) & (kk <= K - 1)).to(z.dtype)
        u = (torch.gather(u, 1, k0) * (1 - w) + torch.gather(u, 1, k1) * w) * inside
    rot = torch.exp(1j * (4 * math.pi * d / (c["lam"] * 1e3)))[:, None, :].to(z.dtype)
    out = cen[..., None] + u * rot
    if c.get("body_bins") is not None:                                              # FMCW: only bins near k0
        kidx = torch.arange(K, device=z.device)[None, :]
        body = ((kidx - c["k0"][:, None]).abs() <= c["body_bins"])[..., None]
        out = torch.where(body, out, z)
    return out


def cm_reference(z, k0, min_dist=3):
    B, K, L = z.shape
    kidx = torch.arange(K, device=z.device)[None, :]
    far = ((kidx - k0[:, None]).abs() >= min_dist).to(z.real.dtype)                # (B, K)
    zm = z.mean(-1)                                                                 # (B, K)
    w = far * zm.abs() ** 2
    ref = (w[..., None] * z * zm.conj()[..., None]).sum(1)                          # (B, L)
    ph = torch.angle(ref)
    ph = ph - ph[:, :1]
    return z * torch.exp(-1j * ph)[:, None, :].to(z.dtype)


NOISES_V2 = {"body_motion_body": dict(fn=body_motion_body, levels=NOISES["body_motion"]["levels"], unit="mm",
                                      family="subject")}
