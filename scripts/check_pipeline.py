"""CPU sanity check (no learned model required): torch demod vs reference disp, every noise type (17) and level (77)
runs and stays finite, classical estimators and spectral signal quality run on clean and noisy IQ windows.
Uses data/check/<radar>_w40_s2.npz if present, or built-in synthetic IQ windows out-of-the-box.
    python scripts/check_pipeline.py
"""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from radarnoise.constants import FS_OUT, RADARS          # noqa: E402
from radarnoise.data import synthetic_windows            # noqa: E402
from radarnoise.demod import demodulate                  # noqa: E402
from radarnoise.estimators import estimate, signal_quality  # noqa: E402
from radarnoise.noise import NOISES, apply               # noqa: E402

for radar in ["fmcw", "novelda", "umain"]:
    chk_path = f"data/check/{radar}_w40_s2.npz"
    if os.path.exists(chk_path):
        Z = np.load(chk_path, allow_pickle=True)
        tag = "data/check"
    else:
        Z = synthetic_windows(radar, n=32, seed=0)
        tag = "synthetic"
    z = torch.as_tensor(Z["iq"][:32])
    k0 = torch.as_tensor(Z["chest_k"][:32].astype(np.int64))
    hr, rr = torch.as_tensor(Z["hr"][:32]), torch.as_tensor(Z["rr"][:32])
    d = demodulate(radar, z).float()
    ref = torch.as_tensor(Z["disp"][:32].astype(np.float32))
    a = d - d.mean(-1, keepdim=True)
    b = ref - ref.mean(-1, keepdim=True)
    corr = ((a * b).sum(-1) / (a.norm(dim=-1) * b.norm(dim=-1) + 1e-9)).abs()
    print(f"== {radar} ({tag}): windows {len(z)}, demod |corr| median {corr.median():.3f} "
          f"p10 {corr.quantile(0.1):.3f}; disp std {d.std():.3f} mm vs {ref.std():.3f}")
    e = estimate(d, FS_OUT, k0)
    for k in sorted(e):
        y = rr if k.startswith("rr") else hr
        ok = torch.isfinite(y)
        print(f"   clean {k:14s} MAE {(e[k][ok] - y[ok]).abs().mean():6.2f}")
    q = signal_quality(d, FS_OUT, k0, hr, rr)
    print(f"   quality: hr rank {np.nanmedian(q['hr_rank']):.2f}, rr rank {np.nanmedian(q['rr_rank']):.2f}")
    ctx = dict(k0=k0, lam=RADARS[radar]["wavelength_m"], fs=FS_OUT)
    g = torch.Generator()
    g.manual_seed(0)
    for name, spec in NOISES.items():
        row = []
        for lv in spec["levels"]:
            zn = apply(name, z, lv, g, ctx)
            assert zn.shape == z.shape and torch.isfinite(zn.real).all() and torch.isfinite(zn.imag).all(), (name, lv)
            dn = torch.nan_to_num(demodulate(radar, zn).float(), 0.0)
            en = estimate(dn, FS_OUT, k0)
            ok = torch.isfinite(rr)
            row.append(f"{lv}:{(en['rr_fft_snr'][ok] - rr[ok]).abs().mean():.2f}/{(en['hr_fft_snr'] - hr).abs().nanmean():.1f}")
        print(f"   {name:15s} rr/hr MAE by level  " + "  ".join(row))
