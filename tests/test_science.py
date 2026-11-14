"""Unit tests for scripts/bp_science.py. All arrays here are SYNTHETIC test fixtures,
not NISAR observations."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import bp_science as bp  # noqa: E402


def test_to_db_known_values():
    assert bp.to_db([1.0, 10.0, 0.1, 2.0]).tolist() == pytest.approx([0, 10, -10, 3.0103], abs=1e-4)


def test_to_db_rejects_nonpositive_and_nonfinite():
    out = bp.to_db([0.0, -1.0, np.nan, np.inf])
    assert np.isnan(out).all()


def test_db_roundtrip():
    x = np.array([1e-4, 0.03, 1.0, 250.0])
    assert bp.from_db(bp.to_db(x)) == pytest.approx(x, rel=1e-12)


def test_int16_encoding_roundtrip_and_nodata():
    db = np.array([-35.123, -8.4, 0.0, 12.349, np.nan])
    enc = bp.encode_db_int16(db)
    assert enc[-1] == bp.INT16_NODATA
    dec = bp.decode_db_int16(enc)
    assert np.isnan(dec[-1])
    assert dec[:-1] == pytest.approx(db[:-1], abs=0.005 + 1e-9)


def test_joint_valid_requires_both_dates_and_flags():
    s = (2, 3)
    one = np.ones(s)
    m = np.ones(s, np.uint8)
    e = np.full(s, 768, np.uint16)
    m_b = m.copy(); m_b[0, 0] = 0          # partially focused on date B
    e_a = e.copy(); e_a[0, 1] = 768 + 2    # anomaly bit on date A
    hh_b = one.copy(); hh_b[1, 2] = 0.0    # non-positive power
    m_a = m.copy(); m_a[1, 0] = 255        # outside swath
    v = bp.joint_valid(one, hh_b, one, one, m_a, m_b, e_a, e)
    assert v.tolist() == [[False, False, True], [False, True, False]]


def test_edge_buffer_erodes_from_invalid_and_border():
    v = np.ones((11, 11), bool)
    v[:, 0] = False
    b = bp.edge_buffer(v, 2)
    assert not b[:, :3].any()       # within 2 px of invalid column 0
    assert b[5, 5]
    assert not b[0, 5] and not b[10, 5]   # array border counts as edge


def test_boxcar_ignores_invalid_pixels():
    lin = np.ones((5, 5))
    lin[2, 2] = 1000.0              # invalid outlier must not leak into neighbours
    valid = np.ones((5, 5), bool)
    valid[2, 2] = False
    out = bp.boxcar_linear(lin, valid, 3)
    assert np.isnan(out[2, 2])
    assert out[1, 1] == pytest.approx(1.0)


def test_region_change_uses_ratio_of_linear_means():
    a = np.array([1.0, 3.0])
    b = np.array([2.0, 2.0])
    r = np.array([True, True])
    # mean(b)/mean(a) = 1  -> 0 dB, whereas mean of per-pixel dB would be -0.88 dB
    assert bp.region_change_db(a, b, r) == pytest.approx(0.0, abs=1e-12)
    assert np.isnan(bp.region_change_db(a, b, np.array([False, False])))


def test_region_change_doubling_is_3db():
    a = np.full(10, 0.05)
    assert bp.region_change_db(a, 2 * a, np.ones(10, bool)) == pytest.approx(3.0103, abs=1e-4)


def test_quantiles_ignore_nan():
    assert bp.quantiles([np.nan, 1, 2, 3], (50,)) == [2.0]
    assert np.isnan(bp.quantiles([np.nan], (50,))[0])


def test_detect_change_objects_hysteresis_sign_and_size():
    d = np.zeros((40, 40))
    valid = np.ones_like(d, bool)
    d[5:15, 5:15] = 2.5            # brightening block grown from a single strong seed
    d[10, 10] = 4.0
    d[25:30, 25:30] = -3.5         # darkening block (25 px) -> kept
    d[2:4, 30:33] = 5.0            # strong but only 6 px -> rejected by min size
    d[30:38, 2:10] = 2.5           # no core seed -> rejected
    lab, info = bp.detect_change_objects(d, valid, core_db=3, grow_db=2, min_px=25)
    signs = sorted(s for _, s in info)
    assert signs == [-1, 1]
    bright = [l for l, s in info if s > 0][0]
    assert (lab == bright).sum() == 100
    assert lab[3, 31] == 0 and lab[33, 5] == 0


def test_detect_change_objects_respects_valid_mask():
    d = np.full((10, 10), 5.0)
    valid = np.zeros_like(d, bool)
    lab, info = bp.detect_change_objects(d, valid, min_px=1)
    assert info == [] and lab.max() == 0


def test_block_mean_linear_requires_half_valid():
    lin = np.arange(16, dtype=float).reshape(4, 4) + 1
    valid = np.ones((4, 4), bool)
    valid[0, 0] = valid[0, 1] = valid[1, 0] = False
    out = bp.block_mean_linear(lin, valid, 2)
    assert np.isnan(out[0, 0])                       # only 1 of 4 valid
    assert out[1, 1] == pytest.approx(np.mean([11, 12, 15, 16]))
