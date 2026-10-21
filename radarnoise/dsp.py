"""Signal-processing primitives shared by preprocessing, the classical baseline and evaluation."""
import numpy as np
from scipy import signal


def bandpass(x, fs, lo, hi, order=3, axis=-1):
    sos = signal.butter(order, [lo, hi], btype="band", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, x, axis=axis)


def lowpass(x, fs, hi, order=4, axis=-1):
    sos = signal.butter(order, hi, btype="low", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, x, axis=axis)


def resample_to(x, fs_in, fs_out, n_out, axis=-1):
    """Anti-aliased linear-interpolation resampling onto a t=k/fs_out grid starting at 0."""
    x = np.moveaxis(np.asarray(x, dtype=np.float64), axis, -1)
    if fs_out < fs_in:
        x = lowpass(x, fs_in, 0.45 * fs_out)
    t_in = np.arange(x.shape[-1]) / fs_in
    t_out = np.arange(n_out) / fs_out
    flat = x.reshape(-1, x.shape[-1])
    out = np.stack([np.interp(t_out, t_in, row) for row in flat]).reshape(*x.shape[:-1], n_out)
    return np.moveaxis(out, -1, axis)


def estimate_if(M, nominal, tol=0.03):
    """Carrier position (cycles/sample) in real fast-time samples, searched near the nominal value."""
    p = M.mean(0) - M.mean()
    n = 8 * len(p)
    F = np.abs(np.fft.rfft(p * np.hanning(len(p)), n))
    f = np.fft.rfftfreq(n)
    m = (f > nominal - tol) & (f < nominal + tol)
    return float(f[m][np.argmax(F[m])])


def downconvert_fast_time(M, f_if, bw, numtaps=41):
    """Real UWB samples (slow, fast) -> complex baseband per range bin (mix to DC + zero-phase FIR)."""
    n = np.arange(M.shape[1])
    mixed = (M - M.mean(axis=1, keepdims=True)) * np.exp(-2j * np.pi * f_if * n)[None, :]
    h = signal.firwin(numtaps, bw, fs=1.0)
    return signal.filtfilt(h, [1.0], mixed, axis=1)


def circle_center(z):
    """Algebraic (Kasa) circle fit of an IQ trajectory; returns the complex centre (DC offset)."""
    x, y = z.real, z.imag
    A = np.stack([x, y, np.ones_like(x)], 1)
    b = x ** 2 + y ** 2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    return 0.5 * sol[0] + 0.5j * sol[1]


def phase_to_mm(z, wavelength_m, fs=20.0, gate=0.3, drift_hz=0.05):
    """Complex slow-time samples of one range bin -> chest displacement in millimetres.

    Arctangent demodulation around the arc centre (static clutter, from a circle fit on the
    low-passed trajectory). Phase is integrated from frame-to-frame increments, and increments are
    zeroed while the sample is close to the centre (|z-c| < gate * median radius): there the phase is
    dominated by noise and naive unwrapping produces the step artefacts seen in the raw data.
    Drift below `drift_hz` is removed.
    """
    z = np.asarray(z, np.complex128)
    zs = lowpass(z.real, fs, 3.0) + 1j * lowpass(z.imag, fs, 3.0) if len(z) > 30 else z
    spread = np.abs(zs - zs.mean()).std() + 1e-15
    c = circle_center(zs)
    if not np.isfinite(c) or np.abs(c - zs.mean()) > 50 * spread:
        c = zs.mean() - spread * np.exp(1j * np.angle(zs.mean() - zs.mean()))
    u = z - c
    r = np.abs(u)
    dph = np.angle(u[1:] * np.conj(u[:-1]))
    ok = np.minimum(r[1:], r[:-1]) >= gate * np.median(r)
    dph = np.where(ok, dph, 0.0)
    ph = np.concatenate([[0.0], np.cumsum(dph)])
    if len(ph) > 3 * fs / drift_hz / 10:
        ph = ph - lowpass(ph, fs, drift_hz, order=2)
    ph = ph - ph.mean()
    return ph * wavelength_m / (4 * np.pi) * 1e3


def linear_displacement(z, wavelength_m, fs=20.0, drift_hz=0.05):
    """Complex slow-time samples of one range bin -> displacement in mm WITHOUT phase unwrapping.

    For chest motion << wavelength (IR-UWB: 41-65 mm vs a few mm of motion) the I/Q trajectory is a short arc,
    so its projection on the principal I/Q axis is linear in displacement. Arc length / arc radius = phase
    change, so d = proj / R * lambda / (4 pi). R is the circle-fit radius (fallback: |mean|). Compared with
    phase_to_mm this keeps weak cardiac modulation in low-SNR bins: on 72 recordings, the true-HR spectral
    rank gap rose from 12.5 to 24.2 points (Novelda) and from 1.5 to 13.3 (UMAIN) (results_repr_probe2.txt).
    Not suited to FMCW at 77 GHz, where breathing wraps the phase several times.
    """
    z = np.asarray(z, np.complex128)
    u = z - z.mean()
    X = np.stack([u.real, u.imag], 1)
    _, V = np.linalg.eigh(X.T @ X)
    proj = X @ V[:, -1]
    zs = lowpass(z.real, fs, 3.0) + 1j * lowpass(z.imag, fs, 3.0) if len(z) > 30 else z
    spread = np.abs(zs - zs.mean()).std() + 1e-15
    c = circle_center(zs)
    R = np.median(np.abs(zs - c)) if np.isfinite(c) and np.abs(c - zs.mean()) <= 50 * spread else np.abs(zs.mean())
    d = proj / (R + 1e-15) * wavelength_m / (4 * np.pi) * 1e3
    if len(d) > 3 * fs / drift_hz / 10:
        d = d - lowpass(d, fs, drift_hz, order=2)
    return d - d.mean()


def spectral_peak(x, fs, lo, hi, pad=8):
    """Peak frequency (Hz) in [lo, hi] with parabolic interpolation, plus a peak-to-band SNR."""
    x = np.asarray(x, float) - np.mean(x)
    n = len(x) * pad
    F = np.abs(np.fft.rfft(x * np.hanning(len(x)), n))
    f = np.fft.rfftfreq(n, 1 / fs)
    m = np.where((f >= lo) & (f <= hi))[0]
    if len(m) < 3:
        return np.nan, 0.0
    i = m[np.argmax(F[m])]
    if 0 < i < len(F) - 1:
        a, b, c = F[i - 1], F[i], F[i + 1]
        den = a - 2 * b + c
        delta = 0.5 * (a - c) / den if den != 0 else 0.0
    else:
        delta = 0.0
    snr = F[i] / (np.mean(F[m]) + 1e-12)
    return (i + delta) * fs / n, float(snr)


def resp_score(disp, fs):
    """How breathing-like a displacement series is: in-band peak power over broadband power."""
    x = disp - disp.mean()
    f, P = signal.welch(x, fs=fs, nperseg=min(len(x), int(fs * 20)))
    rb = (f >= 0.15) & (f <= 0.6)
    bb = (f >= 0.05) & (f <= min(5.0, fs / 2 - 0.1))
    return float(P[rb].max() / (P[bb].sum() + 1e-12))


def select_chest_bin(Z, wavelength_m, fs, exclude=()):
    """Pick the chest range bin: strongest clutter-removed motion, weighted by how breathing-like it is.

    Low-magnitude bins are skipped: their phase is noise and can look spuriously periodic.
    """
    dyn = np.abs(Z - Z.mean(0)).std(0)
    for k in exclude:
        dyn[k] = 0
    dyn = dyn / (dyn.max() + 1e-12)
    scores = np.full(Z.shape[1], -np.inf)
    for k in np.where(dyn >= 0.1)[0]:
        d = phase_to_mm(Z[:, k], wavelength_m, fs)
        scores[k] = np.sqrt(dyn[k]) * resp_score(d, fs)
    return int(np.argmax(scores)), scores


def resp_rate(x, fs, lo=0.15, hi=0.6):
    """Breathing rate (per min) from the spectral peak after removing drift below `lo`."""
    f, snr = spectral_peak(bandpass(x, fs, lo, hi), fs, lo, hi)
    return 60 * f, snr


def detect_beats(ppg, fs):
    """Systolic peak times (s) of a band-passed PPG."""
    x = bandpass(ppg, fs, 0.6, 4.0)
    x = (x - np.median(x)) / (np.std(x) + 1e-9)
    peaks, _ = signal.find_peaks(x, distance=int(0.33 * fs), prominence=0.3)
    return peaks / fs, x


def ppg_resp_from_beats(beats, n_out, fs):
    """Respiratory-induced frequency variation: inter-beat-interval series on a uniform grid (z-scored)."""
    t, ibi = beats[1:], np.diff(beats)
    ok = (ibi > 0.3) & (ibi < 1.6)
    if ok.sum() < 4:
        return np.zeros(n_out)
    s = np.interp(np.arange(n_out) / fs, t[ok], ibi[ok])
    return (s - s.mean()) / (s.std() + 1e-9)


def rate_from_events(times, t0, t1, lo_bpm, hi_bpm):
    """Rate (per min) from the median interval of events inside [t0, t1); nan if unreliable."""
    t = times[(times >= t0) & (times < t1)]
    if len(t) < 3:
        return np.nan
    iv = np.diff(t)
    iv = iv[(iv > 60 / hi_bpm) & (iv < 60 / lo_bpm)]
    if len(iv) < 2:
        return np.nan
    return 60.0 / np.median(iv)
