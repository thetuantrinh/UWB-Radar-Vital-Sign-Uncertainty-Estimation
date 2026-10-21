"""Noise survey: every noise type x level (radarnoise.noise.NOISES) and observation length, injected into the IQ of
the test windows, demodulated, and estimated by every classical estimator (radarnoise.estimators) and, when
checkpoints exist, by trained networks of that fold (Part 2/3 — Coming soon!).

Test windows: subject-disjoint folds pooled (each window scored by models that never saw its subject). Default test
set is the best case (0.5 m, facing, still), so measured degradation is caused by the injected noise; --test-cond
all adds the real-world factors (distance, orientation, phone use), which report.py breaks down by condition.
Noise is seeded per (noise, level, fold) so every estimator sees identical noisy windows.
    python -m radarnoise.survey --radar novelda --test-cond best --device cpu --models none
Output results/survey_<radar>_<cond>.npz: pred (configs, estimators, N), configs, estimators, index, rank_hr,
rank_rr (label-based signal quality of the chest bin per config, see estimators.signal_quality), constant (N, 2).
"""
import argparse
from contextlib import nullcontext
import glob
import os
import time
import zlib

import numpy as np
import torch

from .constants import FS_OUT, RADARS
from .data import load, split
from .demod import demodulate
from .estimators import estimate, signal_quality
from .noise import NOISES, apply

CROPS = [30, 20, 10]


def configs():
    c = [("clean", 0)]
    for name, spec in NOISES.items():
        c += [(name, lv) for lv in spec["levels"]]
    c += [("crop", s) for s in CROPS]
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", required=True, choices=list(RADARS))
    ap.add_argument("--test-cond", default="best", choices=["best", "all"])
    ap.add_argument("--data", default="data/{radar}_w40_s2.npz")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--models", default="none")
    ap.add_argument("--only-clean", action="store_true", help="real-world factors only (no injected noise)")
    ap.add_argument("--batch", type=int, default=256)
    a = ap.parse_args()
    dev = torch.device(a.device)
    if dev.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    W = load(a.radar, a.data)
    lam = RADARS[a.radar]["wavelength_m"]
    cfgs = [("clean", 0)] if a.only_clean else configs()
    folds = sorted(set(W["fold"].tolist()))
    test = {f: split(W, f)[2] for f in folds}
    if a.test_cond == "best":
        test = {f: t[W["best_case"][t]] for f, t in test.items()}
    index = np.concatenate([test[f] for f in folds])
    fold_of = np.concatenate([np.full(len(test[f]), f) for f in folds])
    # constant baseline: training-subject mean label of the fold
    const = np.zeros((len(index), 2), np.float32)
    for f in folds:
        tr = split(W, f)[0]
        const[fold_of == f] = [np.nanmean(W["rr"][tr]), np.nanmean(W["hr"][tr])]
    # learned models available for every fold (optional)
    nets = {}
    if a.models != "none":
        try:
            from .model import VitalNet
            from .train import amp
        except ImportError:
            VitalNet, amp = None, nullcontext
        if VitalNet is not None:
            tags = sorted({os.path.basename(os.path.dirname(p)).rsplit("_f", 1)[0]
                           for p in glob.glob(a.models.format(radar=a.radar, fold="*"))})
            for tag in tags:
                paths = {f: f"runs/{tag}_f{f}/model.pt" for f in folds}
                if all(os.path.exists(p) for p in paths.values()):
                    if dev.type != "cuda":
                        raise SystemExit("trained models found: run the survey on a GPU node with --device cuda")
                    nets[tag] = {}
                    for f, p in paths.items():
                        m = VitalNet().to(dev).eval()
                        m.load_state_dict(torch.load(p, map_location=dev)["model"])
                        nets[tag][f] = m
    else:
        amp = nullcontext
    est_names = None
    pred, rank = [], []
    t_start = time.time()
    for ci, (name, lv) in enumerate(cfgs):
        P, R = {}, {"hr_rank": [], "rr_rank": []}
        for f in folds:
            g = torch.Generator(device=dev)
            g.manual_seed(zlib.crc32(f"{name}|{lv}|{f}".encode()))
            idx = test[f]
            for s in range(0, len(idx), a.batch):
                j = idx[s:s + a.batch]
                z = torch.as_tensor(W["iq"][j], device=dev)
                k0 = torch.as_tensor(W["chest_k"][j].astype(np.int64), device=dev)
                if name == "crop":
                    z = z[..., :int(lv * FS_OUT)]
                elif name != "clean":
                    z = apply(name, z, lv, g, dict(k0=k0, lam=lam, fs=FS_OUT))
                d = torch.nan_to_num(demodulate(a.radar, z).float(), 0.0)
                e = estimate(d, FS_OUT, k0)
                for tag, ms in nets.items():
                    with torch.no_grad(), amp():
                        x = d if d.shape[-1] == W["iq"].shape[-1] else torch.nn.functional.pad(
                            d, (0, W["iq"].shape[-1] - d.shape[-1])
                        )
                        o = ms[f](x)
                    e[f"rr_net_{tag}"], e[f"hr_net_{tag}"] = o["rr_mu"].float(), o["hr_mu"].float()
                q = signal_quality(
                    d, FS_OUT, k0,
                    torch.as_tensor(W["hr"][j], device=dev),
                    torch.as_tensor(W["rr"][j], device=dev),
                )
                for k, v in e.items():
                    P.setdefault(k, []).append(v.float().cpu().numpy())
                for k in R:
                    R[k].append(q[k].cpu().numpy())
        if est_names is None:
            est_names = sorted(P)
        pred.append(np.stack([np.concatenate(P[k]) for k in est_names]).astype(np.float32))
        rank.append(np.stack([np.concatenate(R["hr_rank"]), np.concatenate(R["rr_rank"])]).astype(np.float16))
        print(f"{ci + 1}/{len(cfgs)} {name} {lv} ({time.time() - t_start:.0f}s)", flush=True)
    os.makedirs("results", exist_ok=True)
    out = f"results/survey_{a.radar}_{a.test_cond}{'_clean' if a.only_clean else ''}.npz"
    np.savez_compressed(
        out,
        pred=np.stack(pred),
        rank=np.stack(rank),
        configs=np.array([f"{n}|{l}" for n, l in cfgs]),
        estimators=np.array(est_names),
        index=index,
        fold=fold_of,
        constant=const,
        hr=W["hr"][index],
        rr=W["rr"][index],
        distance=W["distance"][index],
        angle=W["angle"][index],
        activity=W["activity"][index],
        subject=W["subject"][index],
    )
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()
