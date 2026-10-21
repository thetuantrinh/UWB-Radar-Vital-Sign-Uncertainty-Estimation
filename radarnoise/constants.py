"""Sensor constants. Values from TIM 2026 Tables I-II and the raw-data checks in README.md."""
C0 = 299_792_458.0

# fc: carrier used for phase->displacement (FMCW uses the sweep centre 77 GHz + 3.995/2 GHz).
# fs: slow-time frame rate. bin_m: fast-time range-bin spacing in metres.
# f_if: carrier position in the UWB fast-time samples (cycles/sample), measured from the static range
#   profile spectrum (Novelda 7.25/23.33 GHz = 0.31; UMAIN 0.443 -> ~10.4 GS/s sampling).
# bin_m for FMCW and UMAIN is empirical: the chest bin moves ~5.5 FMCW bins and ~70 UMAIN bins between
#   the 0.5 m and 1.5 m recordings (README "Raw-data checks"); the TIM Table I/II values do not match the data.
RADARS = {
    "fmcw":    dict(fc=78.9975e9, fs=20.0, bin_m=0.18),
    "novelda": dict(fc=7.25e9,   fs=20.0, bin_m=0.00643, f_if=0.301, if_bw=0.05),
    "umain":   dict(fc=4.60e9,   fs=44.9, bin_m=0.0144,  f_if=0.443, if_bw=0.04),
}
for _r in RADARS.values():
    _r["wavelength_m"] = C0 / _r["fc"]

RADAR_ORDER = ["fmcw", "novelda", "umain"]

PPG_FS = 255.0          # ubpulse H3; 15.2-15.3k samples per ~60 s recording
DEPTH_FS = 30.0         # RealSense D435i
FS_OUT = 20.0           # common slow-time rate (as in TIM 2026)

# FMCW raw frame: 65536 int16 = 128 chirps x 64 samples x (I,Q) x 4 RX (xWR12xx 4-lane LVDS order).
FMCW_CHIRPS, FMCW_SAMPLES, FMCW_RX = 128, 64, 4

HR_BAND = (0.7, 3.0)     # Hz
RESP_BAND = (0.1, 0.6)   # Hz

# condition name -> (activity, angle_deg). "phonecam*" recordings are the phone-use activity.
CONDITIONS = {
    "ideal":           ("still", 0),
    "cam45left":       ("still", -45),
    "cam45right":      ("still", 45),
    "phonecam0":       ("phone", 0),
    "phonecam45left":  ("phone", -45),
    "phonecam45right": ("phone", 45),
}
