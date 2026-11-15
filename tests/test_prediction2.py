"""Prediction 2 scorer (two other NISAR orbits): synthetic inputs only."""
import os
import sys

import numpy as np
from rasterio.transform import Affine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from predict_two_orbits import map_labels, relative_change, verdict  # noqa: E402


def test_map_labels_identity_and_shift():
    T = Affine(20, 0, 1000, 0, -20, 5000)
    lab = np.arange(100, dtype=np.uint16).reshape(10, 10)
    (same,) = map_labels((10, 10), T, "EPSG:32637", T, "EPSG:32637", [lab])
    assert (same == lab).all()
    # own grid shifted one pixel east: own col 0 sits on case col 1; last col falls outside -> 0
    T2 = Affine(20, 0, 1020, 0, -20, 5000)
    (sh,) = map_labels((10, 10), T2, "EPSG:32637", T, "EPSG:32637", [lab])
    assert (sh[:, :9] == lab[:, 1:]).all() and (sh[:, 9] == 0).all()


def test_map_labels_across_utm_zones_keeps_geography():
    # a case grid in zone 37 mapped onto a zone-36 grid covering the same ground
    from rasterio.warp import transform as wt
    T37 = Affine(20, 0, 207680, 0, -20, 4111520)
    lab = np.zeros((1200, 1200), np.uint16); lab[400:420, 500:520] = 7
    xs, ys = wt("EPSG:32637", "EPSG:32636", [207680 + 510 * 20], [4111520 - 410 * 20])
    T36 = Affine(20, 0, xs[0] - 1000, 0, -20, ys[0] + 1000)   # own pixel (50, 50) on the patch
    (m,) = map_labels((100, 100), T36, "EPSG:32636", T37, "EPSG:32637", [lab])
    assert m[50, 50] == 7 and m[0, 0] == 0


def _scene(new_factor_bright):
    obj = np.zeros((30, 30), np.uint16)
    obj[2:8, 2:8] = 1; obj[10:16, 10:16] = 2; obj[20:26, 2:8] = 3
    ref = np.full((30, 30), 0.05); ref[obj > 0] = 0.2
    new = ref * 0.8                                   # all farmland -1 dB (drying)
    new[obj > 0] = 0.2 * new_factor_bright
    U = np.zeros((30, 30), bool); U[25:, 25:] = True
    ref[U] = 1.0; new[U] = 1.0
    B = obj > 0
    F = (obj == 0) & ~U
    return ref, new, obj, B, F, U


def test_relative_change_confirms_when_bright_fields_dry_back():
    ref, new, obj, B, F, U = _scene(0.25)              # bright fields -6 dB
    r, per = relative_change(ref, new, obj, [1, 2, 3], B, F, U)
    assert abs(r["dB_farmland"] + 0.969) < 0.01 and abs(r["relative"] - (-6.021 + 0.969)) < 0.01
    assert r["frac_fields_darker"] == 1.0 and r["dB_control"] == 0.0
    assert verdict(r).startswith("CONFIRMED")


def test_relative_change_refutes_when_bright_fields_stay_bright():
    ref, new, obj, B, F, U = _scene(1.0)               # bright fields unchanged, farmland -1 dB
    r, _ = relative_change(ref, new, obj, [1, 2, 3], B, F, U)
    assert r["relative"] > 0 and verdict(r).startswith("REFUTED")


def test_control_moving_makes_it_inconclusive():
    ref, new, obj, B, F, U = _scene(0.25)
    new[U] = 2.0                                       # +3 dB on the town
    r, _ = relative_change(ref, new, obj, [1, 2, 3], B, F, U)
    assert verdict(r).startswith("INCONCLUSIVE")


def test_small_fields_are_not_counted():
    ref, new, obj, B, F, U = _scene(0.25)
    r, per = relative_change(ref, new, obj, [1, 2, 3], B, F, U, min_px=37)
    assert r["n_fields"] == 0
