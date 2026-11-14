"""Tests for the global test pipeline on synthetic inputs (no real data peeked)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from global_analyze import perm_p, sm_value  # noqa: E402
from global_scan import ease_rc  # noqa: E402


def _smap(entries):
    return {"days": entries}


def test_overpass_rule_prefers_same_day_nearest():
    s = _smap({"20261022": {"1,2,AM": [0.10, 0, 0, 0], "1,2,PM": [0.20, 0, 0, 0]}})
    v, used = sm_value(s, (1, 2), "20261022", 16.4)  # NISAR ~16:24 local -> PM (18 h) nearer
    assert v == 0.20 and used["overpass"] == "PM"
    v, used = sm_value(s, (1, 2), "20261022", 5.6)
    assert v == 0.10 and used["overpass"] == "AM"


def test_overpass_rule_falls_back_and_respects_quality():
    s = _smap({"20261022": {"1,2,AM": [0.10, 0, 0, 0], "1,2,PM": [0.20, 1, 0, 0]},
               "20261023": {"1,2,AM": [0.30, 0, 0, 0]}})
    v, used = sm_value(s, (1, 2), "20261022", 18.0)  # PM flagged -> same-day AM before other days
    assert v == 0.10 and used["day"] == "20261022"
    s2 = _smap({"20261022": {"1,2,AM": [-9999.0, 0, 0, 0]}, "20261023": {"1,2,AM": [0.30, 0, 0, 0]},
                "20261021": {"1,2,PM": [0.25, 0, 0, 0]}})
    v, used = sm_value(s2, (1, 2), "20261022", 6.0)  # nearest on +-1 day: 21 Oct PM is 12 h away, 23 Oct AM 24 h
    assert v == 0.25 and used["day"] == "20261021"
    v, why = sm_value(_smap({}), (1, 2), "20261022", 6.0)
    assert v is None


def test_permutation_p_detects_and_rejects():
    rng = np.random.default_rng(0)
    x = rng.normal(size=60)
    rho, p = perm_p(x, 2 * x + rng.normal(scale=0.3, size=60), n=500)
    assert rho > 0.8 and p < 0.01
    rho, p = perm_p(x, rng.normal(size=60), n=500)
    assert p > 0.01


def test_ease_grid_cell_for_known_points():
    # EASE-Grid 2.0 9 km: equator/prime meridian is the centre of the 3856 x 1624 grid
    r, c = ease_rc(0.0001, 0.0001)
    assert (r, c) == (811, 1928)
    r, c = ease_rc(-179.99, 0.0)
    assert c == 0


def test_recovery_scorer_on_synthetic_passes():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    from predict_next_pass import recovery
    obj = np.zeros((10, 10), np.uint16); obj[2:6, 2:6] = 1; obj[6:9, 6:9] = 2
    a = np.full((10, 10), 0.01); b = a.copy(); b[obj > 0] = 0.04          # +6 dB brightening
    valid = np.ones((10, 10), bool)
    c_dry = a.copy()                                                     # fully back -> R = 1
    c_stay = b.copy()                                                    # stayed bright -> R = 0
    r = recovery(a, b, c_dry, obj, valid, [1, 2])
    assert abs(r[1]["R"] - 1) < 1e-3 and abs(r[1]["dHH_AB"] - 6.021) < 1e-2
    r = recovery(a, b, c_stay, obj, valid, [1, 2])
    assert abs(r[2]["R"]) < 1e-3
