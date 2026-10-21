# RadarNoiseBench Dataset Directory

> 🚧 **Status: Coming Soon!**
> The full anonymized slow-time IQ window files (`{radar}_w40_s2.npz` and `{radar}_w40_s2_best.npz`) and pre-computed cardiac spectral features (`hr_best_w40_s2.npz`) will be released upon publication of the manuscript.
>
> In the meantime, [`radarnoise.data.synthetic_windows()`](../radarnoise/data.py) and [`examples/quickstart.py`](../examples/quickstart.py) provide built-in synthetic complex slow-time IQ windows so you can test the 17 physical degradation models, demodulation routines, and classical estimators out of the box.

---

## Expected File Layout

When released, place the `.npz` files in this `data/` directory:

```text
data/
├── splits.json              # Subject-disjoint 5-fold definitions (anonymized S01–S17, included)
├── fmcw_w40_s2.npz          # 79 GHz FMCW full dataset (10,089 windows, 1.33 GB) — Coming soon!
├── novelda_w40_s2.npz       # 7.25 GHz Novelda IR-UWB full dataset (10,089 windows, 1.33 GB) — Coming soon!
├── umain_w40_s2.npz         # 4.60 GHz UMAIN IR-UWB full dataset (10,089 windows, 1.33 GB) — Coming soon!
├── *_w40_s2_best.npz        # Best-case subset (0.5 m, facing, still; 824 windows, ~110 MB each) — Coming soon!
└── hr_best_w40_s2.npz       # Part 2 multi-radar cardiac spectra (p6/p4h, 99 MB) — Coming soon!
```

## Window Schema (`<radar>_w40_s2.npz`)

Each radar file contains **10,089 windows of 40 s** (stride 2 s, 20 frames/s → `L = 800` slow-time frames) cut from **1,013 synchronized recordings** across **17 subjects** (`S01`–`S17`) in **12 conditions** (`0.5 / 1.5 m` × `0° / ±45°` × `still / phone use`):

| Array | Shape & Dtype | Description |
|---|---|---|
| `iq` | `(N, 16, 800)` `complex64` | Complex slow-time matrix of 16 range bins centered around the chest at 20 Hz. **Physical degradations are injected here before demodulation.** |
| `disp` | `(N, 16, 800)` `float16` | Demodulated chest displacement in mm (FMCW: Kåsa circle-fit gated arctangent; IR-UWB: principal I/Q axis projection). |
| `rel_range` | `(N, 16)` `float32` | Range of each bin relative to the detected chest bin (m). |
| `chest_k` | `(N,)` `int64` | Index `k0 ∈ {0..15}` of the detected chest bin. |
| `hr` | `(N,)` `float32` | Reference heart rate (bpm): `60 / median(IBI)` from synchronized finger PPG (`255 Hz`). |
| `rr` | `(N,)` `float32` | Reference respiration rate (breaths/min): mean of depth-camera and PPG-derived rates when they agree within `3 br/min` (`NaN` otherwise; 53% concordant). |
| `beat_t` | `(N, 96)` `float32` | Reference PPG heartbeat times in the window (s from window start, `NaN`-padded). |
| `subject` | `(N,)` `str` | Anonymized subject identifier (`S01`–`S17`). |
| `distance`, `angle`, `activity`, `condition`, `repeat` | `(N,)` | Recording condition metadata. |
| `best_case` | `(N,)` `bool` | `True` for `0.5 m`, `facing (0°)`, `still` (824 windows across 84 recordings). |
| `fold` | `(N,)` `int64` | Subject-disjoint test fold index `0..4`. |
