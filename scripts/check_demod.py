"""Torch demod vs numpy dsp demod on the SAME 40 s window (implementation check), plus estimator accuracy."""
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from radarnoise import dsp                               # noqa: E402
from radarnoise.constants import FS_OUT, RADARS          # noqa: E402
from radarnoise.data import synthetic_windows            # noqa: E402
from radarnoise.demod import demodulate                  # noqa: E402
from radarnoise.estimators import estimate               # noqa: E402


def corr(a, b):
    a = a - a.mean(-1, keepdims=True)
    b = b - b.mean(-1, keepdims=True)
    return np.abs((a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1) + 1e-9))


for radar in ["fmcw", "novelda", "umain"]:
    chk_path = f"data/check/{radar}_w40_s2.npz"
    if os.path.exists(chk_path):
        Z = np.load(chk_path, allow_pickle=True)
        n = min(60, len(Z["hr"]))
    else:
        Z = synthetic_windows(radar, n=16, seed=0)
        n = 16
    iq = Z["iq"][:n]
    k0 = Z["chest_k"][:n].astype(np.int64)
    lam = RADARS[radar]["wavelength_m"]
    f = dsp.phase_to_mm if radar == "fmcw" else dsp.linear_displacement
    npw = np.stack([[f(b, lam, FS_OUT) for b in w] for w in iq])               # numpy, per window
    tw = demodulate(radar, torch.as_tensor(iq)).numpy()                          # torch, per window
    rec = Z["disp"][:n].astype(np.float32)                                       # reference displacement
    ar = np.arange(n)
    print(f"{radar}: chest-bin |corr| torch-vs-numpy (same window) median {np.median(corr(tw[ar, k0], npw[ar, k0])):.3f}; "
          f"numpy window-vs-ref {np.median(corr(npw[ar, k0], rec[ar, k0])):.3f}")
    for name, d in [("torch window", tw), ("numpy window", npw), ("reference disp", rec)]:
        e = estimate(torch.as_tensor(d, dtype=torch.float32), FS_OUT, torch.as_tensor(k0))
        rr, hr = Z["rr"][:n], Z["hr"][:n]
        ok = np.isfinite(rr)
        print(f"   {name:16s} rr_fft_chest {np.abs(e['rr_fft_chest'].numpy()[ok] - rr[ok]).mean():.2f}  "
              f"rr_fft_snr {np.abs(e['rr_fft_snr'].numpy()[ok] - rr[ok]).mean():.2f}  "
              f"hr_fft_snr {np.abs(e['hr_fft_snr'].numpy() - hr).mean():.1f}")
