"""Between Passes — core scientific functions (pure, tested in tests/).

Conventions
- Input backscatter is NISAR GCOV RTC gamma-0 *linear power* (dimensionless).
- dB = 10*log10(linear). Change = dB(after) - dB(before) = 10*log10(after/before).
- Region statistics use the ratio of region-mean *linear* power (not the mean of
  per-pixel dB), the standard multilook estimator for SAR intensity.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

DB_SCALE = 100            # int16 storage: dB * 100  (0.01 dB quantisation)
INT16_NODATA = -32768


def to_db(lin):
    """Linear power -> dB. Non-positive or non-finite -> NaN (never log of <=0)."""
    lin = np.asarray(lin, dtype="float64")
    out = np.full(lin.shape, np.nan)
    ok = np.isfinite(lin) & (lin > 0)
    out[ok] = 10.0 * np.log10(lin[ok])
    return out


def from_db(db):
    return np.power(10.0, np.asarray(db, dtype="float64") / 10.0)


def joint_valid(hh_a, hh_b, hv_a, hv_b, mask_a, mask_b, exc_a, exc_b, ok_exception=768):
    """Pixels valid in BOTH acquisitions.

    mask: GCOV subswath mask; 0 = partially focused/invalid, 255 = outside swath,
          1..n = valid subswath number.
    exc:  inputDataExceptionMask; 768 = HH(256)+HV(512) fully focused, no anomaly.
    """
    v = np.ones(np.shape(hh_a), bool)
    for m, e in ((mask_a, exc_a), (mask_b, exc_b)):
        m = np.asarray(m)
        v &= (m > 0) & (m < 255) & (np.asarray(e) == ok_exception)
    for x in (hh_a, hh_b, hv_a, hv_b):
        x = np.asarray(x)
        v &= np.isfinite(x) & (x > 0)
    return v


def edge_buffer(valid, pixels):
    """Erode the valid area by `pixels` from any invalid pixel or the array border
    (NISAR L2 valid-sample masks are known to be misaligned near swath edges)."""
    if pixels <= 0:
        return valid.copy()
    padded = np.pad(valid, 1, constant_values=False)
    dist = ndimage.distance_transform_edt(padded)[1:-1, 1:-1]
    return valid & (dist > pixels)


def boxcar_linear(lin, valid, k):
    """Valid-weighted k×k mean of linear power; NaN where no valid neighbours or
    the centre pixel itself is invalid."""
    x = np.where(valid, lin, 0.0).astype("float64")
    w = valid.astype("float64")
    s = ndimage.uniform_filter(x, k, mode="constant")
    n = ndimage.uniform_filter(w, k, mode="constant")
    out = np.full(x.shape, np.nan)
    ok = valid & (n > 1e-12)
    out[ok] = s[ok] / n[ok]
    return out


def region_change_db(lin_a, lin_b, region):
    """ΔdB of a region = 10 log10( mean(B) / mean(A) ) over region pixels."""
    a = np.asarray(lin_a)[region]
    b = np.asarray(lin_b)[region]
    if a.size == 0:
        return float("nan")
    return float(10.0 * np.log10(b.mean() / a.mean()))


def quantiles(x, qs=(5, 25, 50, 75, 95)):
    x = np.asarray(x, dtype="float64")
    x = x[np.isfinite(x)]
    if x.size == 0:
        return [float("nan")] * len(qs)
    return [float(v) for v in np.percentile(x, qs)]


def detect_change_objects(delta_db, valid, core_db=3.0, grow_db=2.0, min_px=25):
    """Hysteresis change objects on a (speckle-filtered) ΔdB map.

    Seeds: |Δ| >= core_db. Objects grow through same-sign pixels with |Δ| >= grow_db
    (8-connectivity). Brightening and darkening are segmented separately.
    Objects smaller than `min_px` are discarded. Returns int32 label array
    (0 = none) and a list of (label, sign).
    """
    labels = np.zeros(delta_db.shape, np.int32)
    info = []
    nxt = 1
    d = np.where(valid, delta_db, 0.0)
    struct = np.ones((3, 3), bool)
    for sign in (+1, -1):
        grow = valid & (sign * d >= grow_db)
        core = valid & (sign * d >= core_db)
        lab, n = ndimage.label(grow, structure=struct)
        if n == 0:
            continue
        has_core = ndimage.maximum(core, lab, index=np.arange(1, n + 1)).astype(bool)
        sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
        keep = np.where(has_core & (sizes >= min_px))[0] + 1
        for k in keep:
            labels[lab == k] = nxt
            info.append((nxt, sign))
            nxt += 1
    return labels, info


def encode_db_int16(db):
    out = np.full(np.shape(db), INT16_NODATA, np.int16)
    ok = np.isfinite(db)
    out[ok] = np.clip(np.round(np.asarray(db)[ok] * DB_SCALE), -32767, 32767).astype(np.int16)
    return out


def decode_db_int16(arr):
    arr = np.asarray(arr)
    out = np.full(arr.shape, np.nan)
    ok = arr != INT16_NODATA
    out[ok] = arr[ok] / DB_SCALE
    return out


def block_mean_linear(lin, valid, f):
    """f×f block average of linear power (requires >= half valid), for coarse layers."""
    h, w = lin.shape
    H, W = h // f, w // f
    x = np.where(valid, lin, 0.0)[:H * f, :W * f].reshape(H, f, W, f)
    n = valid[:H * f, :W * f].reshape(H, f, W, f).sum(axis=(1, 3))
    s = x.sum(axis=(1, 3))
    out = np.full((H, W), np.nan)
    ok = n >= (f * f) / 2
    out[ok] = s[ok] / n[ok]
    return out
