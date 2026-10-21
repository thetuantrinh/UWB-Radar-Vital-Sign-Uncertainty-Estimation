"""Quick start: load one radar's windows (or generate synthetic IQ windows if the full .npz dataset is not yet
downloaded), take fold 0, run the classical estimators on the best-case test windows, add one noise type, and compare.
CPU is fine.
    python examples/quickstart.py --radar novelda
"""
import argparse
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from radarnoise.constants import FS_OUT, RADARS          # noqa: E402
from radarnoise.data import load, split, synthetic_windows  # noqa: E402
from radarnoise.demod import demodulate                  # noqa: E402
from radarnoise.estimators import estimate               # noqa: E402
from radarnoise.noise import NOISES, apply               # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--radar", default="novelda", choices=list(RADARS))
ap.add_argument("--data", default="data/{radar}_w40_s2.npz", help="full file or the *_best.npz subset")
ap.add_argument("--noise", default="body_motion", choices=list(NOISES))
ap.add_argument("--level", type=float, default=2.0)
a = ap.parse_args()

data_path = a.data.format(radar=a.radar)
if os.path.exists(data_path):
    W = load(a.radar, a.data)
    mode = "real dataset"
else:
    print(f"[Info] '{data_path}' not found locally (Full Dataset — Coming soon!).")
    print(f"[Info] Running quickstart with built-in synthetic IQ windows for {a.radar.upper()}...\n")
    W = synthetic_windows(a.radar, n=85, seed=0)
    mode = "synthetic demo"

tr, va, te = split(W, fold=0)
te = te[W["best_case"][te]]
print(f"{a.radar} ({mode}): {len(W['hr'])} windows; fold 0 -> train {len(tr)}, val {len(va)}, best-case test {len(te)}")
z = torch.as_tensor(W["iq"][te])
k0 = torch.as_tensor(W["chest_k"][te].astype(np.int64))
ctx = dict(k0=k0, lam=RADARS[a.radar]["wavelength_m"], fs=FS_OUT)
g = torch.Generator().manual_seed(0)
for name, zz in [("clean", z), (f"{a.noise} @ {a.level}", apply(a.noise, z, a.level, g, ctx))]:
    e = estimate(torch.nan_to_num(demodulate(a.radar, zz).float()), FS_OUT, k0)
    rr, hr = W["rr"][te], W["hr"][te]
    ok = np.isfinite(rr)
    print(f"{name:22s} RR MAE {np.abs(e['rr_fft_snr'].numpy()[ok] - rr[ok]).mean():5.2f} br/min | "
          f"HR MAE {np.abs(e['hr_fft_snr'].numpy() - hr).mean():5.2f} bpm  (constant HR baseline "
          f"{np.abs(np.nanmean(W['hr'][tr]) - hr).mean():.2f})")
