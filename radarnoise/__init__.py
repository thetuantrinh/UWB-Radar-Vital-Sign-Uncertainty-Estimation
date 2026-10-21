"""RadarNoiseBench (Part 1): Controlled IQ-level physical degradations, demodulation, and classical vital-sign estimators."""

from .constants import CONDITIONS, DEPTH_FS, FS_OUT, HR_BAND, PPG_FS, RADAR_ORDER, RADARS, RESP_BAND
from .data import META, load, split, synthetic_windows
from .demod import demodulate, linear_mm, phase_mm
from .estimators import estimate, signal_quality
from .noise import NOISES, apply, dyn_power, random_noise

__version__ = "0.1.0"
__all__ = [
    "CONDITIONS",
    "DEPTH_FS",
    "FS_OUT",
    "HR_BAND",
    "META",
    "NOISES",
    "PPG_FS",
    "RADARS",
    "RADAR_ORDER",
    "RESP_BAND",
    "apply",
    "demodulate",
    "dyn_power",
    "estimate",
    "linear_mm",
    "load",
    "phase_mm",
    "random_noise",
    "signal_quality",
    "split",
    "synthetic_windows",
]
