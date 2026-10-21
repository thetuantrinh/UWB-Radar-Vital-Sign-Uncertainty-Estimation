"""Loading the per-radar window files, subject-disjoint splits, and synthetic IQ generator for quick testing."""
import math
import numpy as np

from .constants import FS_OUT, RADARS

META = ["hr", "rr", "rr_depth", "rr_ppg", "hr_device", "subject", "distance", "angle", "activity", "condition",
        "repeat", "key", "t0", "best_case", "fold", "chest_k", "rel_range", "beat_t"]


def load(radar, path="data/{radar}_w40_s2.npz", arrays=("iq",)):
    Z = np.load(path.format(radar=radar), allow_pickle=True)
    return {k: Z[k] for k in list(META) + list(arrays)}


def split(W, fold, train_cond="all", seed=0):
    """(train, val, test) indices. Test = the fold's subjects, every condition (filter with W['best_case'] for the
    best-case test set). Validation = 2 other subjects. train_cond 'best' keeps only best-case windows in train/val."""
    idx = np.arange(len(W["hr"]))
    test_s = sorted(set(W["subject"][W["fold"] == fold]))
    rest = [s for s in sorted(set(W["subject"])) if s not in test_s]
    val_s = set(np.random.RandomState(seed + 100 + fold).choice(rest, 2, replace=False))
    te = np.isin(W["subject"], test_s)
    va = np.isin(W["subject"], list(val_s))
    tr = ~te & ~va
    if train_cond == "best":
        tr &= W["best_case"]
        va &= W["best_case"]
    return idx[tr], idx[va], idx[te]


def synthetic_windows(radar="novelda", n=64, k_bins=16, length=800, seed=0):
    """Generate realistic synthetic slow-time IQ windows (n, 16, 800) with physiological RR/HR chest displacement
    and static clutter for standalone testing when the full .npz dataset is not yet downloaded."""
    rng = np.random.RandomState(seed)
    lam = RADARS[radar]["wavelength_m"]
    t = np.arange(length, dtype=np.float64) / FS_OUT

    subjects = [f"S{i:02d}" for i in range(1, 18)]
    subj = np.array([subjects[i % len(subjects)] for i in range(n)])
    fold = np.array([(i % len(subjects)) % 5 for i in range(n)], dtype=np.int64)
    best_case = np.ones(n, dtype=bool)
    chest_k = rng.randint(5, 11, size=n, dtype=np.int64)

    rr = rng.uniform(11.0, 22.0, size=n).astype(np.float32)
    hr = rng.uniform(55.0, 90.0, size=n).astype(np.float32)

    iq = np.zeros((n, k_bins, length), dtype=np.complex64)
    disp = np.zeros((n, k_bins, length), dtype=np.float16)

    for i in range(n):
        f_rr = rr[i] / 60.0
        f_hr = hr[i] / 60.0
        ph_rr = rng.uniform(0, 2 * math.pi)
        ph_hr = rng.uniform(0, 2 * math.pi)
        # Chest motion (mm): ~1.5 mm respiration + 0.15 mm fundamental cardiac + harmonic
        d_chest = (
            1.5 * np.sin(2 * math.pi * f_rr * t + ph_rr)
            + 0.25 * np.sin(4 * math.pi * f_rr * t + 2 * ph_rr)
            + 0.18 * np.sin(2 * math.pi * f_hr * t + ph_hr)
        )
        for k in range(k_bins):
            dist_bins = abs(k - chest_k[i])
            w = math.exp(-0.5 * (dist_bins / 1.8) ** 2)
            d_k = w * d_chest + rng.normal(0, 0.02, size=length)
            disp[i, k] = d_k.astype(np.float16)
            # Static clutter center + round-trip phase modulation + slight receiver noise
            clutter = (2.5 + 0.5 * w) * np.exp(1j * rng.uniform(0, 2 * math.pi))
            dyn_amp = 0.25 + 0.75 * w
            z_k = clutter + dyn_amp * np.exp(1j * (4 * math.pi * (d_k * 1e-3) / lam))
            z_k += 0.015 * (rng.normal(size=length) + 1j * rng.normal(size=length))
            iq[i, k] = z_k.astype(np.complex64)

    rel_range = (np.arange(k_bins)[None, :] - chest_k[:, None]) * RADARS[radar]["bin_m"]
    return {
        "iq": iq,
        "disp": disp,
        "hr": hr,
        "rr": rr,
        "rr_depth": rr,
        "rr_ppg": rr,
        "hr_device": hr,
        "subject": subj,
        "distance": np.full(n, 0.5, dtype=np.float32),
        "angle": np.zeros(n, dtype=np.int64),
        "activity": np.full(n, "still"),
        "condition": np.full(n, "ideal"),
        "repeat": np.ones(n, dtype=np.int64),
        "key": np.array([f"{subj[i]}_synthetic_{i:03d}" for i in range(n)]),
        "t0": np.zeros(n, dtype=np.float32),
        "best_case": best_case,
        "fold": fold,
        "chest_k": chest_k,
        "rel_range": rel_range.astype(np.float32),
        "beat_t": np.full((n, 96), np.nan, dtype=np.float32),
    }
