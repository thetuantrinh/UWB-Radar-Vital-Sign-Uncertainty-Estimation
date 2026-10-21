"""Survey results -> results/REPORT.md + results/figs/*.png.
    python -m radarnoise.report
For each radar and vital sign:
  * clean accuracy of every estimator (and the constant baseline)
  * degradation table: MAE per noise type and level for the best clean classical estimator and each trained net
  * breakdown level: the mildest level at which that estimator is no better than the constant baseline
  * ranking of noise types by the MAE increase at their middle level
  * chest-bin signal quality (rank of the true-rate spectral power) per configuration: one axis for every noise
  * real-world factors (test-cond all, clean): MAE by distance, orientation, activity
"""
import glob
import os

import numpy as np

from .noise import NOISES

RADARS = ["fmcw", "novelda", "umain"]
TOL = {"rr": 2.0, "hr": 5.0}


def mae(p, y):
    ok = np.isfinite(p) & np.isfinite(y)
    return float(np.abs(p[ok] - y[ok]).mean()) if ok.any() else np.nan


def within(p, y, k):
    ok = np.isfinite(p) & np.isfinite(y)
    return float((np.abs(p[ok] - y[ok]) <= TOL[k]).mean() * 100) if ok.any() else np.nan


def load(radar, cond="best"):
    p = f"results/survey_{radar}_{cond}.npz"
    return dict(np.load(p, allow_pickle=True)) if os.path.exists(p) else None


def main():
    os.makedirs("results/figs", exist_ok=True)
    L = ["# RadarNoiseBench survey report\n",
         "Test windows: subject-disjoint folds pooled; best case = 0.5 m, facing, still. MAE in breaths/min (RR) and "
         "bpm (HR); `const` = training-subject mean. Quality = median rank of the true-rate spectral power in the chest "
         "bin (0 = strongest frequency, 0.5 = chance).\n"]
    curves = {}
    for radar in RADARS:
        S = load(radar)
        if S is None:
            continue
        cfg = [str(c) for c in S["configs"]]
        est = [str(e) for e in S["estimators"]]
        ci = {c: i for i, c in enumerate(cfg)}
        L.append(f"\n## {radar.upper()} (best-case test windows: {S['pred'].shape[2]})\n")
        for k, col in [("rr", 0), ("hr", 1)]:
            y = S[k]
            const = S["constant"][:, col]
            cm = mae(const + 1e-9, y)
            mine = [e for e in est if e.startswith(f"{k}_")]
            clean = {e: mae(S["pred"][ci["clean|0"], est.index(e)], y) for e in mine}
            classical = [e for e in mine if "_net_" not in e]
            best = min(classical, key=clean.get)
            nets = [e for e in mine if "_net_" in e]
            L.append(f"\n### {k.upper()} — clean accuracy\n\n| estimator | MAE | within {TOL[k]:.0f} |\n|---|---|---|")
            for e in sorted(mine, key=clean.get):
                L.append(f"| {e} | {clean[e]:.2f} | {within(S['pred'][ci['clean|0'], est.index(e)], y, k):.0f}% |")
            L.append(f"| constant (training mean) | {cm:.2f} | {within(const, y, k):.0f}% |")
            show = [best] + nets
            L.append(f"\n### {k.upper()} — degradation (MAE; columns = levels mild → severe; **bold** = no better "
                     f"than constant {cm:.2f})\n")
            L.append("| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |")
            L.append("|---|---|---|---|---|---|---|")
            rank_rows = []
            names = list(NOISES) + ["crop"]
            for name in names:
                lv = [c for c in cfg if c.startswith(name + "|")]
                if not lv:
                    continue
                unit = NOISES[name]["unit"] if name in NOISES else "window s"
                for e in show:
                    vals = [mae(S["pred"][ci[c], est.index(e)], y) for c in lv]
                    brk = next((c.split("|")[1] for c, v in zip(lv, vals) if v >= cm), "none")
                    cells = " ".join(f"**{c.split('|')[1]}:{v:.2f}**" if v >= cm else f"{c.split('|')[1]}:{v:.2f}"
                                     for c, v in zip(lv, vals))
                    qr = [float(np.nanmedian(S["rank"][ci[c], 1 - col].astype(float))) for c in ["clean|0"] + lv]  # rank = [hr, rr]
                    L.append(f"| {name} | {unit} | {e} | {clean[e]:.2f} | {cells} | {brk} | {qr[0]:.2f} → {qr[-1]:.2f} |")
                    if e == best:
                        mid = vals[len(vals) // 2]
                        rank_rows.append((mid - clean[e], name, lv[len(vals) // 2].split("|")[1], mid))
                        curves.setdefault((k, name), {})[radar] = ([c.split("|")[1] for c in lv], vals, clean[e], cm)
            L.append(f"\n**{k.upper()} noise ranking ({best}, middle level):** " + "; ".join(
                f"{n} @ {l}: +{d:.2f} (→ {m:.2f})" for d, n, l, m in sorted(rank_rows, reverse=True)))
        A = load(radar, "all")
        if A is None:
            A = load(radar, "all_clean")
        if A is not None:
            est_a = [str(e) for e in A["estimators"]]
            L.append(f"\n### {radar.upper()} — real-world factors (clean, all conditions, n {A['pred'].shape[2]})\n")
            groups = {"0.5 m": A["distance"] == 0.5, "1.5 m": A["distance"] == 1.5, "facing": A["angle"] == 0,
                      "turned 45°": A["angle"] != 0, "still": A["activity"] == "still", "phone use": A["activity"] == "phone"}
            L.append("| vital | estimator | " + " | ".join(groups) + " |\n|---|---|" + "---|" * len(groups))
            for k, col in [("rr", 0), ("hr", 1)]:
                for e in [x for x in est_a if x.startswith(k + "_")] + ["constant"]:
                    p = A["constant"][:, col] if e == "constant" else A["pred"][0, est_a.index(e)]
                    L.append(f"| {k.upper()} | {e} | " + " | ".join(f"{mae(p[m], A[k][m]):.2f}" for m in groups.values()) + " |")
    open("results/REPORT.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        colors = {"fmcw": "#1f77b4", "novelda": "#d62728", "umain": "#2ca02c"}
        for k in ["rr", "hr"]:
            names = [n for n in list(NOISES) + ["crop"] if (k, n) in curves]
            if not names:
                continue
            nc = 6
            nr = -(-len(names) // nc)
            fig, axs = plt.subplots(nr, nc, figsize=(3 * nc, 2.4 * nr), squeeze=False)
            for ax, n in zip(axs.flat, names):
                for radar, (lv, vals, c0, cm) in curves[(k, n)].items():
                    ax.plot(range(len(lv) + 1), [c0] + vals, "o-", ms=3, lw=1.5, color=colors[radar], label=radar)
                    ax.axhline(cm, color=colors[radar], lw=0.8, ls=":")
                ax.set_xticks(range(len(lv) + 1)); ax.set_xticklabels(["clean"] + lv, fontsize=7, rotation=30)
                unit = NOISES[n]["unit"] if n in NOISES else "window s"
                ax.set_title(f"{n} ({unit})", fontsize=8); ax.tick_params(labelsize=7)
            for ax in list(axs.flat)[len(names):]:
                ax.axis("off")
            axs.flat[0].legend(fontsize=7)
            fig.supylabel(f"{k.upper()} MAE ({'breaths/min' if k == 'rr' else 'bpm'}); dotted = constant", fontsize=9)
            fig.tight_layout()
            fig.savefig(f"results/figs/degradation_{k}.png", dpi=150)
            print("saved", f"results/figs/degradation_{k}.png")
    except ImportError:
        print("matplotlib not available: figures skipped")


if __name__ == "__main__":
    main()
