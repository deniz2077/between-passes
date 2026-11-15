"""Weather filter rules (research/filter/WEATHER_FILTER.md) on synthetic arrays."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build_sites import classify  # noqa: E402


def field(up=0, dn=0, n=10000):
    d = np.zeros(n)
    d[:up] = 4.0
    d[up:up + dn] = -4.0
    return d, np.ones(n, bool)


def test_wetter_soil_brightening_is_weather():
    d, an = field(up=500, dn=20)
    r, w, b = classify(d, an, +0.10)
    assert r["soil"] == "wetter" and r["verdict"] == "weather"
    assert w.sum() == 500 and b.sum() == 20


def test_drier_soil_darkening_is_weather_and_brightening_is_not():
    d, an = field(up=400, dn=100)
    r, w, b = classify(d, an, -0.10)
    assert r["soil"] == "drier" and w.sum() == 100 and b.sum() == 400 and r["verdict"] == "beyond"


def test_steady_soil_any_change_is_beyond():
    d, an = field(up=300, dn=0)
    r, w, b = classify(d, an, 0.01)
    assert r["soil"] == "steady" and w.sum() == 0 and r["verdict"] == "beyond"


def test_quiet_below_one_percent():
    d, an = field(up=50, dn=40)
    r, _, _ = classify(d, an, 0.2)
    assert r["verdict"] == "quiet"


def test_two_thirds_boundary_and_thresholds():
    d, an = field(up=200, dn=100)          # exactly 2/3 matches -> weather
    assert classify(d, an, 0.06)[0]["verdict"] == "weather"
    d, an = field(up=199, dn=101)
    assert classify(d, an, 0.06)[0]["verdict"] == "beyond"
    d = np.full(10000, 2.99); an = np.ones(10000, bool)   # below 3 dB never counts
    assert classify(d, an, 0.2)[0]["changed_frac"] == 0
    assert classify(*field(up=500), 0.0499)[0]["soil"] == "steady"
    assert classify(*field(up=500), 0.05)[0]["soil"] == "wetter"
