# RadarNoiseBench survey report

Test windows: subject-disjoint folds pooled; best case = 0.5 m, facing, still. MAE in breaths/min (RR) and bpm (HR); `const` = training-subject mean. Quality = median rank of the true-rate spectral power in the chest bin (0 = strongest frequency, 0.5 = chance).


## FMCW (best-case test windows: 824)


### RR — clean accuracy

| estimator | MAE | within 2 |
|---|---|---|
| rr_fft_snr | 2.84 | 58% |
| rr_fft_chest | 3.13 | 53% |
| rr_fft_avg | 3.70 | 45% |
| rr_acf_snr | 4.04 | 45% |
| rr_acf_chest | 4.31 | 44% |
| constant (training mean) | 2.74 | 43% |

### RR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 2.74)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | rr_fft_snr | 2.84 | **20:3.24** **10:3.52** **5:4.07** **0:4.78** **-5:4.86** **-10:4.82** | 20 | 0.13 → 0.34 |
| quantization | bits | rr_fft_snr | 2.84 | **12:2.86** **10:2.90** **8:3.00** **6:2.92** **4:2.98** | 12 | 0.13 → 0.13 |
| impulsive | spikes/frame | rr_fft_snr | 2.84 | **0.001:2.94** **0.003:2.97** **0.01:2.95** **0.03:3.18** **0.1:4.05** | 0.001 | 0.13 → 0.19 |
| interference | SIR dB | rr_fft_snr | 2.84 | **20:3.23** **10:3.60** **0:4.17** **-10:5.51** | 20 | 0.13 → 0.38 |
| phase_noise | rad/sqrt(s) | rr_fft_snr | 2.84 | **0.01:2.87** **0.03:2.78** **0.1:2.93** **0.3:3.17** **1.0:3.50** | 0.01 | 0.13 → 0.14 |
| iq_imbalance | gain=phase(rad) | rr_fft_snr | 2.84 | **0.05:2.83** **0.1:2.89** **0.2:2.96** **0.3:3.07** **0.5:3.14** | 0.05 | 0.13 → 0.12 |
| gain_drift | relative std | rr_fft_snr | 2.84 | **0.05:2.99** **0.1:2.92** **0.2:3.01** **0.5:3.61** | 0.05 | 0.13 → 0.14 |
| frame_loss | fraction | rr_fft_snr | 2.84 | **0.01:2.94** **0.05:2.88** **0.1:3.10** **0.2:3.24** **0.4:3.61** | 0.01 | 0.13 → 0.15 |
| timing_jitter | ms | rr_fft_snr | 2.84 | **2:2.92** **5:2.91** **10:2.99** **20:2.86** | 2 | 0.13 → 0.14 |
| clock_drift | % | rr_fft_snr | 2.84 | **0.5:2.88** **1:3.00** **2:3.07** **5:3.15** | 0.5 | 0.13 → 0.19 |
| static_clutter | dB over chest motion | rr_fft_snr | 2.84 | **0:2.91** **10:3.14** **20:3.54** **30:3.69** **40:3.24** | 0 | 0.13 → 0.15 |
| moving_clutter | amplitude ratio | rr_fft_snr | 2.84 | **0.1:3.05** **0.3:3.24** **1:4.04** **3:4.93** | 0.1 | 0.13 → 0.43 |
| multipath | echo amplitude | rr_fft_snr | 2.84 | **0.1:2.97** **0.3:3.11** **0.5:3.09** **0.8:3.24** | 0.1 | 0.13 → 0.13 |
| range_offset | bins | rr_fft_snr | 2.84 | **1:2.85** **2:3.17** **4:4.07** **8:4.17** | 1 | 0.13 → 0.28 |
| body_motion | mm | rr_fft_snr | 2.84 | **0.2:3.25** **0.5:3.52** **1:3.58** **2:3.75** **5:3.70** | 0.2 | 0.13 → 0.23 |
| vibration_hr | mm (0.8-2.5 Hz) | rr_fft_snr | 2.84 | **0.01:2.82** **0.03:2.98** **0.1:2.91** **0.3:3.35** | 0.01 | 0.13 → 0.14 |
| vibration_rr | mm (0.15-0.5 Hz) | rr_fft_snr | 2.84 | **0.1:3.79** **0.3:5.74** **1:6.35** **3:6.35** | 0.1 | 0.13 → 0.26 |
| crop | window s | rr_fft_snr | 2.84 | **30:3.33** **20:4.17** **10:5.26** | 30 | 0.13 → 0.24 |

**RR noise ranking (rr_fft_snr, middle level):** vibration_rr @ 1: +3.51 (→ 6.35); thermal @ 0: +1.94 (→ 4.78); interference @ 0: +1.33 (→ 4.17); crop @ 20: +1.33 (→ 4.17); range_offset @ 4: +1.23 (→ 4.07); moving_clutter @ 1: +1.19 (→ 4.04); body_motion @ 1: +0.74 (→ 3.58); static_clutter @ 20: +0.69 (→ 3.54); frame_loss @ 0.1: +0.26 (→ 3.10); multipath @ 0.5: +0.25 (→ 3.09); clock_drift @ 2: +0.22 (→ 3.07); gain_drift @ 0.2: +0.17 (→ 3.01); quantization @ 8: +0.16 (→ 3.00); timing_jitter @ 10: +0.15 (→ 2.99); iq_imbalance @ 0.2: +0.12 (→ 2.96); impulsive @ 0.01: +0.11 (→ 2.95); phase_noise @ 0.1: +0.09 (→ 2.93); vibration_hr @ 0.1: +0.07 (→ 2.91)

### HR — clean accuracy

| estimator | MAE | within 5 |
|---|---|---|
| hr_fft_chest | 16.42 | 25% |
| hr_fft_snr | 17.18 | 21% |
| hr_fft_avg | 18.13 | 12% |
| hr_acf_snr | 18.26 | 15% |
| hr_acf_chest | 18.66 | 17% |
| constant (training mean) | 8.35 | 42% |

### HR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 8.35)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | hr_fft_chest | 16.42 | **20:15.91** **10:16.99** **5:17.44** **0:17.21** **-5:17.00** **-10:16.30** | 20 | 0.17 → 0.28 |
| quantization | bits | hr_fft_chest | 16.42 | **12:16.24** **10:16.39** **8:16.17** **6:15.91** **4:15.94** | 12 | 0.17 → 0.18 |
| impulsive | spikes/frame | hr_fft_chest | 16.42 | **0.001:16.11** **0.003:16.10** **0.01:16.49** **0.03:17.02** **0.1:17.81** | 0.001 | 0.17 → 0.26 |
| interference | SIR dB | hr_fft_chest | 16.42 | **20:16.49** **10:19.35** **0:19.49** **-10:32.18** | 20 | 0.17 → 0.34 |
| phase_noise | rad/sqrt(s) | hr_fft_chest | 16.42 | **0.01:16.24** **0.03:15.91** **0.1:15.96** **0.3:16.39** **1.0:16.24** | 0.01 | 0.17 → 0.22 |
| iq_imbalance | gain=phase(rad) | hr_fft_chest | 16.42 | **0.05:16.22** **0.1:15.89** **0.2:15.72** **0.3:15.64** **0.5:15.09** | 0.05 | 0.17 → 0.19 |
| gain_drift | relative std | hr_fft_chest | 16.42 | **0.05:16.04** **0.1:16.33** **0.2:16.53** **0.5:16.55** | 0.05 | 0.17 → 0.20 |
| frame_loss | fraction | hr_fft_chest | 16.42 | **0.01:16.31** **0.05:16.35** **0.1:16.27** **0.2:16.11** **0.4:15.81** | 0.01 | 0.17 → 0.22 |
| timing_jitter | ms | hr_fft_chest | 16.42 | **2:15.88** **5:15.91** **10:16.31** **20:16.21** | 2 | 0.17 → 0.17 |
| clock_drift | % | hr_fft_chest | 16.42 | **0.5:16.48** **1:15.77** **2:15.92** **5:16.30** | 0.5 | 0.17 → 0.24 |
| static_clutter | dB over chest motion | hr_fft_chest | 16.42 | **0:16.37** **10:16.59** **20:16.69** **30:16.66** **40:16.67** | 0 | 0.17 → 0.21 |
| moving_clutter | amplitude ratio | hr_fft_chest | 16.42 | **0.1:16.17** **0.3:17.61** **1:18.82** **3:19.68** | 0.1 | 0.17 → 0.24 |
| multipath | echo amplitude | hr_fft_chest | 16.42 | **0.1:16.01** **0.3:16.18** **0.5:17.05** **0.8:18.40** | 0.1 | 0.17 → 0.22 |
| range_offset | bins | hr_fft_chest | 16.42 | **1:17.61** **2:16.29** **4:16.17** **8:16.77** | 1 | 0.17 → 0.27 |
| body_motion | mm | hr_fft_chest | 16.42 | **0.2:16.31** **0.5:16.29** **1:16.70** **2:17.65** **5:18.74** | 0.2 | 0.17 → 0.21 |
| vibration_hr | mm (0.8-2.5 Hz) | hr_fft_chest | 16.42 | **0.01:16.40** **0.03:18.21** **0.1:29.98** **0.3:33.03** | 0.01 | 0.17 → 0.21 |
| vibration_rr | mm (0.15-0.5 Hz) | hr_fft_chest | 16.42 | **0.1:15.89** **0.3:15.88** **1:16.66** **3:17.31** | 0.1 | 0.17 → 0.19 |
| crop | window s | hr_fft_chest | 16.42 | **30:16.63** **20:16.97** **10:16.95** | 30 | 0.17 → 0.21 |

**HR noise ranking (hr_fft_chest, middle level):** vibration_hr @ 0.1: +13.55 (→ 29.98); interference @ 0: +3.06 (→ 19.49); moving_clutter @ 1: +2.40 (→ 18.82); thermal @ 0: +0.79 (→ 17.21); multipath @ 0.5: +0.62 (→ 17.05); crop @ 20: +0.55 (→ 16.97); body_motion @ 1: +0.27 (→ 16.70); static_clutter @ 20: +0.26 (→ 16.69); vibration_rr @ 1: +0.24 (→ 16.66); gain_drift @ 0.2: +0.11 (→ 16.53); impulsive @ 0.01: +0.06 (→ 16.49); timing_jitter @ 10: +-0.11 (→ 16.31); frame_loss @ 0.1: +-0.15 (→ 16.27); range_offset @ 4: +-0.25 (→ 16.17); quantization @ 8: +-0.25 (→ 16.17); phase_noise @ 0.1: +-0.47 (→ 15.96); clock_drift @ 2: +-0.50 (→ 15.92); iq_imbalance @ 0.2: +-0.70 (→ 15.72)

### FMCW — real-world factors (clean, all conditions, n 10089)

| vital | estimator | 0.5 m | 1.5 m | facing | turned 45° | still | phone use |
|---|---|---|---|---|---|---|---|
| RR | rr_acf_chest | 4.61 | 5.68 | 4.82 | 5.21 | 5.37 | 4.72 |
| RR | rr_acf_snr | 4.26 | 5.07 | 4.35 | 4.74 | 4.92 | 4.22 |
| RR | rr_fft_avg | 3.87 | 4.56 | 3.91 | 4.30 | 4.43 | 3.84 |
| RR | rr_fft_chest | 3.51 | 4.61 | 3.84 | 4.08 | 4.14 | 3.83 |
| RR | rr_fft_snr | 3.37 | 3.99 | 3.24 | 3.83 | 3.79 | 3.46 |
| RR | constant | 3.06 | 3.40 | 3.22 | 3.20 | 3.05 | 3.41 |
| HR | hr_acf_chest | 18.57 | 20.12 | 19.23 | 19.41 | 19.77 | 18.94 |
| HR | hr_acf_snr | 18.29 | 19.33 | 18.70 | 18.87 | 19.02 | 18.61 |
| HR | hr_fft_avg | 17.32 | 18.45 | 17.56 | 18.05 | 18.15 | 17.63 |
| HR | hr_fft_chest | 15.64 | 17.62 | 16.29 | 16.81 | 17.20 | 16.08 |
| HR | hr_fft_snr | 16.85 | 17.43 | 16.84 | 17.29 | 17.48 | 16.80 |
| HR | constant | 8.36 | 8.22 | 7.98 | 8.44 | 8.77 | 7.82 |

## NOVELDA (best-case test windows: 824)


### RR — clean accuracy

| estimator | MAE | within 2 |
|---|---|---|
| rr_fft_snr | 0.84 | 92% |
| rr_fft_avg | 0.96 | 90% |
| rr_fft_chest | 0.96 | 90% |
| rr_acf_snr | 1.22 | 85% |
| rr_acf_chest | 1.35 | 85% |
| constant (training mean) | 2.74 | 43% |

### RR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 2.74)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | rr_fft_snr | 0.84 | 20:0.84 10:0.89 5:0.88 0:0.93 -5:0.99 -10:1.16 | none | 0.02 → 0.03 |
| quantization | bits | rr_fft_snr | 0.84 | 12:0.84 10:0.84 8:0.84 6:0.86 4:0.99 | none | 0.02 → 0.02 |
| impulsive | spikes/frame | rr_fft_snr | 0.84 | 0.001:0.88 0.003:0.89 0.01:0.90 0.03:0.96 0.1:1.33 | none | 0.02 → 0.04 |
| interference | SIR dB | rr_fft_snr | 0.84 | 20:0.84 10:1.00 0:1.76 -10:2.44 | none | 0.02 → 0.03 |
| phase_noise | rad/sqrt(s) | rr_fft_snr | 0.84 | 0.01:0.88 0.03:0.87 0.1:0.89 0.3:1.63 **1.0:4.00** | 1.0 | 0.02 → 0.30 |
| iq_imbalance | gain=phase(rad) | rr_fft_snr | 0.84 | 0.05:0.84 0.1:0.86 0.2:0.87 0.3:0.88 0.5:0.93 | none | 0.02 → 0.02 |
| gain_drift | relative std | rr_fft_snr | 0.84 | 0.05:0.84 0.1:0.98 0.2:1.83 0.5:2.70 | none | 0.02 → 0.11 |
| frame_loss | fraction | rr_fft_snr | 0.84 | 0.01:0.84 0.05:0.85 0.1:0.86 0.2:0.87 0.4:0.87 | none | 0.02 → 0.02 |
| timing_jitter | ms | rr_fft_snr | 0.84 | 2:0.84 5:0.84 10:0.83 20:0.85 | none | 0.02 → 0.02 |
| clock_drift | % | rr_fft_snr | 0.84 | 0.5:0.85 1:0.88 2:1.00 5:1.32 | none | 0.02 → 0.07 |
| static_clutter | dB over chest motion | rr_fft_snr | 0.84 | 0:0.84 10:0.84 20:0.84 30:0.84 40:0.84 | none | 0.02 → 0.02 |
| moving_clutter | amplitude ratio | rr_fft_snr | 0.84 | 0.1:0.94 0.3:0.89 1:0.92 3:1.25 | none | 0.02 → 0.09 |
| multipath | echo amplitude | rr_fft_snr | 0.84 | 0.1:0.84 0.3:0.90 0.5:0.90 0.8:0.94 | none | 0.02 → 0.02 |
| range_offset | bins | rr_fft_snr | 0.84 | 1:0.94 2:1.06 4:1.19 8:1.39 | none | 0.02 → 0.15 |
| body_motion | mm | rr_fft_snr | 0.84 | 0.2:0.88 0.5:1.01 1:1.39 2:1.84 **5:3.37** | 5 | 0.02 → 0.21 |
| vibration_hr | mm (0.8-2.5 Hz) | rr_fft_snr | 0.84 | 0.01:0.84 0.03:0.84 0.1:0.84 0.3:0.85 | none | 0.02 → 0.02 |
| vibration_rr | mm (0.15-0.5 Hz) | rr_fft_snr | 0.84 | 0.1:0.89 0.3:1.24 **1:3.93** **3:5.74** | 1 | 0.02 → 0.17 |
| crop | window s | rr_fft_snr | 0.84 | 30:1.09 20:1.54 10:2.05 | none | 0.02 → 0.14 |

**RR noise ranking (rr_fft_snr, middle level):** vibration_rr @ 1: +3.09 (→ 3.93); gain_drift @ 0.2: +0.99 (→ 1.83); interference @ 0: +0.93 (→ 1.76); crop @ 20: +0.70 (→ 1.54); body_motion @ 1: +0.55 (→ 1.39); range_offset @ 4: +0.36 (→ 1.19); clock_drift @ 2: +0.16 (→ 1.00); thermal @ 0: +0.10 (→ 0.93); moving_clutter @ 1: +0.08 (→ 0.92); multipath @ 0.5: +0.07 (→ 0.90); impulsive @ 0.01: +0.06 (→ 0.90); phase_noise @ 0.1: +0.06 (→ 0.89); iq_imbalance @ 0.2: +0.03 (→ 0.87); frame_loss @ 0.1: +0.03 (→ 0.86); vibration_hr @ 0.1: +0.01 (→ 0.84); quantization @ 8: +0.00 (→ 0.84); static_clutter @ 20: +0.00 (→ 0.84); timing_jitter @ 10: +-0.00 (→ 0.83)

### HR — clean accuracy

| estimator | MAE | within 5 |
|---|---|---|
| hr_fft_snr | 14.60 | 45% |
| hr_fft_avg | 14.86 | 43% |
| hr_fft_chest | 15.18 | 41% |
| hr_acf_snr | 19.53 | 27% |
| hr_acf_chest | 20.78 | 23% |
| constant (training mean) | 8.35 | 42% |

### HR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 8.35)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | hr_fft_snr | 14.60 | **20:14.31** **10:14.62** **5:18.41** **0:23.64** **-5:28.81** **-10:30.79** | 20 | 0.09 → 0.49 |
| quantization | bits | hr_fft_snr | 14.60 | **12:14.58** **10:14.56** **8:14.52** **6:14.83** **4:14.58** | 12 | 0.09 → 0.12 |
| impulsive | spikes/frame | hr_fft_snr | 14.60 | **0.001:14.92** **0.003:14.19** **0.01:15.49** **0.03:26.23** **0.1:29.56** | 0.001 | 0.09 → 0.51 |
| interference | SIR dB | hr_fft_snr | 14.60 | **20:36.48** **10:39.72** **0:39.98** **-10:41.31** | 20 | 0.09 → 0.12 |
| phase_noise | rad/sqrt(s) | hr_fft_snr | 14.60 | **0.01:14.69** **0.03:15.10** **0.1:15.82** **0.3:16.80** **1.0:17.54** | 0.01 | 0.09 → 0.27 |
| iq_imbalance | gain=phase(rad) | hr_fft_snr | 14.60 | **0.05:14.77** **0.1:15.09** **0.2:14.93** **0.3:15.05** **0.5:15.18** | 0.05 | 0.09 → 0.09 |
| gain_drift | relative std | hr_fft_snr | 14.60 | **0.05:14.85** **0.1:15.19** **0.2:14.70** **0.5:17.21** | 0.05 | 0.09 → 0.12 |
| frame_loss | fraction | hr_fft_snr | 14.60 | **0.01:14.77** **0.05:14.99** **0.1:14.63** **0.2:15.12** **0.4:15.46** | 0.01 | 0.09 → 0.17 |
| timing_jitter | ms | hr_fft_snr | 14.60 | **2:14.55** **5:14.56** **10:14.63** **20:14.48** | 2 | 0.09 → 0.09 |
| clock_drift | % | hr_fft_snr | 14.60 | **0.5:14.63** **1:14.60** **2:15.05** **5:15.80** | 0.5 | 0.09 → 0.20 |
| static_clutter | dB over chest motion | hr_fft_snr | 14.60 | **0:14.60** **10:14.60** **20:14.60** **30:14.60** **40:14.60** | 0 | 0.09 → 0.09 |
| moving_clutter | amplitude ratio | hr_fft_snr | 14.60 | **0.1:16.13** **0.3:18.11** **1:19.52** **3:19.81** | 0.1 | 0.09 → 0.21 |
| multipath | echo amplitude | hr_fft_snr | 14.60 | **0.1:14.91** **0.3:15.03** **0.5:15.99** **0.8:16.88** | 0.1 | 0.09 → 0.10 |
| range_offset | bins | hr_fft_snr | 14.60 | **1:14.89** **2:14.57** **4:15.13** **8:15.71** | 1 | 0.09 → 0.26 |
| body_motion | mm | hr_fft_snr | 14.60 | **0.2:14.86** **0.5:15.45** **1:15.62** **2:17.81** **5:21.67** | 0.2 | 0.09 → 0.18 |
| vibration_hr | mm (0.8-2.5 Hz) | hr_fft_snr | 14.60 | **0.01:14.83** **0.03:15.95** **0.1:25.94** **0.3:31.24** | 0.01 | 0.09 → 0.11 |
| vibration_rr | mm (0.15-0.5 Hz) | hr_fft_snr | 14.60 | **0.1:14.64** **0.3:15.28** **1:16.86** **3:19.91** | 0.1 | 0.09 → 0.15 |
| crop | window s | hr_fft_snr | 14.60 | **30:15.02** **20:15.64** **10:18.58** | 30 | 0.09 → 0.13 |

**HR noise ranking (hr_fft_snr, middle level):** interference @ 0: +25.38 (→ 39.98); vibration_hr @ 0.1: +11.34 (→ 25.94); thermal @ 0: +9.04 (→ 23.64); moving_clutter @ 1: +4.93 (→ 19.52); vibration_rr @ 1: +2.26 (→ 16.86); multipath @ 0.5: +1.40 (→ 15.99); phase_noise @ 0.1: +1.23 (→ 15.82); crop @ 20: +1.04 (→ 15.64); body_motion @ 1: +1.02 (→ 15.62); impulsive @ 0.01: +0.89 (→ 15.49); range_offset @ 4: +0.53 (→ 15.13); clock_drift @ 2: +0.46 (→ 15.05); iq_imbalance @ 0.2: +0.34 (→ 14.93); gain_drift @ 0.2: +0.10 (→ 14.70); timing_jitter @ 10: +0.04 (→ 14.63); frame_loss @ 0.1: +0.03 (→ 14.63); static_clutter @ 20: +0.00 (→ 14.60); quantization @ 8: +-0.08 (→ 14.52)

### NOVELDA — real-world factors (clean, all conditions, n 10089)

| vital | estimator | 0.5 m | 1.5 m | facing | turned 45° | still | phone use |
|---|---|---|---|---|---|---|---|
| RR | rr_acf_chest | 2.34 | 3.02 | 2.32 | 2.79 | 2.33 | 3.05 |
| RR | rr_acf_snr | 2.10 | 2.86 | 2.19 | 2.55 | 2.15 | 2.81 |
| RR | rr_fft_avg | 1.54 | 2.23 | 1.81 | 1.87 | 1.48 | 2.33 |
| RR | rr_fft_chest | 1.57 | 2.31 | 1.84 | 1.93 | 1.49 | 2.44 |
| RR | rr_fft_snr | 1.45 | 2.19 | 1.72 | 1.81 | 1.42 | 2.25 |
| RR | constant | 3.06 | 3.40 | 3.22 | 3.20 | 3.05 | 3.41 |
| HR | hr_acf_chest | 19.40 | 20.15 | 19.79 | 19.77 | 20.75 | 18.81 |
| HR | hr_acf_snr | 18.95 | 19.85 | 19.29 | 19.46 | 20.22 | 18.60 |
| HR | hr_fft_avg | 16.11 | 15.93 | 14.82 | 16.62 | 16.30 | 15.75 |
| HR | hr_fft_chest | 16.33 | 16.07 | 15.06 | 16.78 | 16.35 | 16.06 |
| HR | hr_fft_snr | 15.62 | 15.96 | 14.68 | 16.34 | 15.77 | 15.80 |
| HR | constant | 8.36 | 8.22 | 7.98 | 8.44 | 8.77 | 7.82 |

## UMAIN (best-case test windows: 824)


### RR — clean accuracy

| estimator | MAE | within 2 |
|---|---|---|
| rr_fft_snr | 1.14 | 87% |
| rr_fft_avg | 1.33 | 83% |
| rr_fft_chest | 1.37 | 82% |
| rr_acf_snr | 1.97 | 73% |
| rr_acf_chest | 2.52 | 67% |
| constant (training mean) | 2.74 | 43% |

### RR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 2.74)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | rr_fft_snr | 1.14 | 20:1.18 10:1.20 5:1.24 0:1.33 -5:1.56 -10:1.85 | none | 0.04 → 0.08 |
| quantization | bits | rr_fft_snr | 1.14 | 12:1.14 10:1.14 8:1.16 6:1.09 4:1.19 | none | 0.04 → 0.04 |
| impulsive | spikes/frame | rr_fft_snr | 1.14 | 0.001:1.11 0.003:1.08 0.01:1.27 0.03:1.53 0.1:2.07 | none | 0.04 → 0.11 |
| interference | SIR dB | rr_fft_snr | 1.14 | 20:1.24 10:1.57 0:2.31 -10:2.59 | none | 0.04 → 0.06 |
| phase_noise | rad/sqrt(s) | rr_fft_snr | 1.14 | 0.01:1.22 0.03:1.40 0.1:2.06 **0.3:3.54** **1.0:4.63** | 0.3 | 0.04 → 0.32 |
| iq_imbalance | gain=phase(rad) | rr_fft_snr | 1.14 | 0.05:1.18 0.1:1.18 0.2:1.17 0.3:1.18 0.5:1.33 | none | 0.04 → 0.03 |
| gain_drift | relative std | rr_fft_snr | 1.14 | 0.05:1.50 0.1:2.58 **0.2:3.21** **0.5:3.59** | 0.2 | 0.04 → 0.22 |
| frame_loss | fraction | rr_fft_snr | 1.14 | 0.01:1.15 0.05:1.16 0.1:1.18 0.2:1.27 0.4:1.31 | none | 0.04 → 0.04 |
| timing_jitter | ms | rr_fft_snr | 1.14 | 2:1.14 5:1.14 10:1.13 20:1.15 | none | 0.04 → 0.04 |
| clock_drift | % | rr_fft_snr | 1.14 | 0.5:1.15 1:1.18 2:1.23 5:1.50 | none | 0.04 → 0.08 |
| static_clutter | dB over chest motion | rr_fft_snr | 1.14 | 0:1.14 10:1.14 20:1.14 30:1.14 40:1.14 | none | 0.04 → 0.04 |
| moving_clutter | amplitude ratio | rr_fft_snr | 1.14 | 0.1:1.12 0.3:1.20 1:1.31 3:1.65 | none | 0.04 → 0.10 |
| multipath | echo amplitude | rr_fft_snr | 1.14 | 0.1:1.15 0.3:1.15 0.5:1.14 0.8:1.20 | none | 0.04 → 0.04 |
| range_offset | bins | rr_fft_snr | 1.14 | 1:1.25 2:1.50 4:1.71 8:2.05 | none | 0.04 → 0.20 |
| body_motion | mm | rr_fft_snr | 1.14 | 0.2:1.31 0.5:1.67 1:2.67 **2:3.22** **5:3.52** | 2 | 0.04 → 0.23 |
| vibration_hr | mm (0.8-2.5 Hz) | rr_fft_snr | 1.14 | 0.01:1.14 0.03:1.14 0.1:1.14 0.3:1.16 | none | 0.04 → 0.04 |
| vibration_rr | mm (0.15-0.5 Hz) | rr_fft_snr | 1.14 | 0.1:1.65 **0.3:3.10** **1:5.11** **3:6.34** | 0.3 | 0.04 → 0.20 |
| crop | window s | rr_fft_snr | 1.14 | 30:1.29 20:1.96 **10:2.77** | 10 | 0.04 → 0.16 |

**RR noise ranking (rr_fft_snr, middle level):** vibration_rr @ 1: +3.97 (→ 5.11); gain_drift @ 0.2: +2.07 (→ 3.21); body_motion @ 1: +1.53 (→ 2.67); interference @ 0: +1.17 (→ 2.31); phase_noise @ 0.1: +0.92 (→ 2.06); crop @ 20: +0.82 (→ 1.96); range_offset @ 4: +0.57 (→ 1.71); thermal @ 0: +0.19 (→ 1.33); moving_clutter @ 1: +0.17 (→ 1.31); impulsive @ 0.01: +0.13 (→ 1.27); clock_drift @ 2: +0.09 (→ 1.23); frame_loss @ 0.1: +0.04 (→ 1.18); iq_imbalance @ 0.2: +0.03 (→ 1.17); quantization @ 8: +0.02 (→ 1.16); vibration_hr @ 0.1: +0.00 (→ 1.14); static_clutter @ 20: +0.00 (→ 1.14); multipath @ 0.5: +-0.00 (→ 1.14); timing_jitter @ 10: +-0.01 (→ 1.13)

### HR — clean accuracy

| estimator | MAE | within 5 |
|---|---|---|
| hr_acf_chest | 18.95 | 20% |
| hr_acf_snr | 19.68 | 20% |
| hr_fft_avg | 20.82 | 31% |
| hr_fft_snr | 20.86 | 30% |
| hr_fft_chest | 22.08 | 29% |
| constant (training mean) | 8.35 | 42% |

### HR — degradation (MAE; columns = levels mild → severe; **bold** = no better than constant 8.35)

| noise | unit | estimator | clean | levels... | breakdown level | quality (clean → worst) |
|---|---|---|---|---|---|---|
| thermal | SNR dB | hr_acf_chest | 18.95 | **20:19.14** **10:18.61** **5:18.63** **0:18.40** **-5:19.70** **-10:17.99** | 20 | 0.22 → 0.49 |
| quantization | bits | hr_acf_chest | 18.95 | **12:18.95** **10:18.94** **8:19.04** **6:18.73** **4:17.80** | 12 | 0.22 → 0.27 |
| impulsive | spikes/frame | hr_acf_chest | 18.95 | **0.001:18.81** **0.003:18.37** **0.01:18.29** **0.03:18.70** **0.1:18.30** | 0.001 | 0.22 → 0.51 |
| interference | SIR dB | hr_acf_chest | 18.95 | **20:19.22** **10:20.38** **0:24.50** **-10:31.82** | 20 | 0.22 → 0.24 |
| phase_noise | rad/sqrt(s) | hr_acf_chest | 18.95 | **0.01:19.03** **0.03:19.41** **0.1:19.42** **0.3:19.62** **1.0:20.07** | 0.01 | 0.22 → 0.28 |
| iq_imbalance | gain=phase(rad) | hr_acf_chest | 18.95 | **0.05:18.80** **0.1:18.63** **0.2:18.28** **0.3:18.30** **0.5:18.24** | 0.05 | 0.22 → 0.19 |
| gain_drift | relative std | hr_acf_chest | 18.95 | **0.05:18.78** **0.1:18.37** **0.2:17.50** **0.5:18.11** | 0.05 | 0.22 → 0.23 |
| frame_loss | fraction | hr_acf_chest | 18.95 | **0.01:19.12** **0.05:19.34** **0.1:18.85** **0.2:19.41** **0.4:19.15** | 0.01 | 0.22 → 0.22 |
| timing_jitter | ms | hr_acf_chest | 18.95 | **2:18.98** **5:19.04** **10:19.05** **20:19.08** | 2 | 0.22 → 0.21 |
| clock_drift | % | hr_acf_chest | 18.95 | **0.5:19.20** **1:19.30** **2:19.17** **5:19.63** | 0.5 | 0.22 → 0.30 |
| static_clutter | dB over chest motion | hr_acf_chest | 18.95 | **0:18.95** **10:18.95** **20:18.95** **30:18.95** **40:18.95** | 0 | 0.22 → 0.22 |
| moving_clutter | amplitude ratio | hr_acf_chest | 18.95 | **0.1:19.20** **0.3:19.32** **1:20.12** **3:21.00** | 0.1 | 0.22 → 0.25 |
| multipath | echo amplitude | hr_acf_chest | 18.95 | **0.1:19.00** **0.3:20.85** **0.5:21.09** **0.8:24.25** | 0.1 | 0.22 → 0.24 |
| range_offset | bins | hr_acf_chest | 18.95 | **1:19.21** **2:19.26** **4:19.14** **8:19.67** | 1 | 0.22 → 0.42 |
| body_motion | mm | hr_acf_chest | 18.95 | **0.2:19.17** **0.5:19.67** **1:19.92** **2:20.52** **5:20.74** | 0.2 | 0.22 → 0.21 |
| vibration_hr | mm (0.8-2.5 Hz) | hr_acf_chest | 18.95 | **0.01:18.95** **0.03:18.77** **0.1:18.72** **0.3:19.38** | 0.01 | 0.22 → 0.22 |
| vibration_rr | mm (0.15-0.5 Hz) | hr_acf_chest | 18.95 | **0.1:18.99** **0.3:19.19** **1:19.92** **3:21.34** | 0.1 | 0.22 → 0.22 |
| crop | window s | hr_acf_chest | 18.95 | **30:19.29** **20:20.49** **10:21.32** | 30 | 0.22 → 0.25 |

**HR noise ranking (hr_acf_chest, middle level):** interference @ 0: +5.56 (→ 24.50); multipath @ 0.5: +2.15 (→ 21.09); crop @ 20: +1.54 (→ 20.49); moving_clutter @ 1: +1.17 (→ 20.12); body_motion @ 1: +0.98 (→ 19.92); vibration_rr @ 1: +0.97 (→ 19.92); phase_noise @ 0.1: +0.47 (→ 19.42); clock_drift @ 2: +0.22 (→ 19.17); range_offset @ 4: +0.19 (→ 19.14); timing_jitter @ 10: +0.11 (→ 19.05); quantization @ 8: +0.09 (→ 19.04); static_clutter @ 20: +0.00 (→ 18.95); frame_loss @ 0.1: +-0.10 (→ 18.85); vibration_hr @ 0.1: +-0.23 (→ 18.72); thermal @ 0: +-0.55 (→ 18.40); impulsive @ 0.01: +-0.66 (→ 18.29); iq_imbalance @ 0.2: +-0.67 (→ 18.28); gain_drift @ 0.2: +-1.45 (→ 17.50)

### UMAIN — real-world factors (clean, all conditions, n 10089)

| vital | estimator | 0.5 m | 1.5 m | facing | turned 45° | still | phone use |
|---|---|---|---|---|---|---|---|
| RR | rr_acf_chest | 4.15 | 4.77 | 3.73 | 4.74 | 4.22 | 4.69 |
| RR | rr_acf_snr | 3.62 | 4.50 | 3.32 | 4.33 | 3.81 | 4.28 |
| RR | rr_fft_avg | 2.49 | 3.06 | 2.73 | 2.75 | 2.31 | 3.31 |
| RR | rr_fft_chest | 2.60 | 3.22 | 2.82 | 2.90 | 2.41 | 3.48 |
| RR | rr_fft_snr | 2.35 | 2.83 | 2.48 | 2.61 | 2.15 | 3.10 |
| RR | constant | 3.06 | 3.40 | 3.22 | 3.20 | 3.05 | 3.41 |
| HR | hr_acf_chest | 17.97 | 19.10 | 18.99 | 18.31 | 18.91 | 18.17 |
| HR | hr_acf_snr | 17.86 | 18.51 | 18.78 | 17.89 | 18.71 | 17.67 |
| HR | hr_fft_avg | 20.54 | 24.05 | 20.77 | 23.07 | 23.54 | 21.09 |
| HR | hr_fft_chest | 21.07 | 25.00 | 21.57 | 23.78 | 24.24 | 21.87 |
| HR | hr_fft_snr | 20.08 | 23.20 | 20.19 | 22.38 | 22.44 | 20.88 |
| HR | constant | 8.36 | 8.22 | 7.98 | 8.44 | 8.77 | 7.82 |
