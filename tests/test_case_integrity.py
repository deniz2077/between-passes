"""Integrity: statistics in case.json must be reproducible from the shipped binary
layers (what the browser reads). Skips if the case has not been built."""
import hashlib
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import bp_science as bp  # noqa: E402

CASE = os.path.join(ROOT, "app", "data", "ceyhan")
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(CASE, "case.json")),
                                reason="case not built")


@pytest.fixture(scope="module")
def case():
    c = json.load(open(os.path.join(CASE, "case.json")))
    W, H = c["grid"]["width"], c["grid"]["height"]

    def load(name):
        meta = c["layers"][name]
        return np.fromfile(os.path.join(CASE, meta["file"]), dtype=meta["dtype"]).reshape(meta["shape"])
    lay = {k: load(k) for k in c["layers"]}
    assert lay["hh_a"].shape == (H, W)
    return c, lay


def test_hashes_match(case):
    c, _ = case
    for k, meta in c["layers"].items():
        h = hashlib.sha256(open(os.path.join(CASE, meta["file"]), "rb").read()).hexdigest()
        assert h == meta["sha256"], k


def test_urban_control_change_reproducible(case):
    c, lay = case
    urban = (lay["flags"] & 4) > 0
    a = bp.from_db(bp.decode_db_int16(lay["hh_a"]))
    b = bp.from_db(bp.decode_db_int16(lay["hh_b"]))
    assert urban.sum() == c["stats"]["urban_control"]["px"]
    assert bp.region_change_db(a, b, urban) == pytest.approx(c["stats"]["urban_control"]["dHH_db_region"], abs=0.01)


def test_object_changes_reproducible(case):
    c, lay = case
    a = bp.from_db(bp.decode_db_int16(lay["hh_a"]))
    b = bp.from_db(bp.decode_db_int16(lay["hh_b"]))
    objs = lay["objects"]
    for o in c["objects"][:25] + c["objects"][-5:]:
        reg = objs == o["id"]
        assert reg.sum() == o["pixels"]
        assert bp.region_change_db(a, b, reg) == pytest.approx(o["dHH_db"], abs=0.01)
        assert (o["dHH_db"] > 0) == (o["sign"] == "brightened")


def test_objects_inside_analysis_area(case):
    _, lay = case
    analysis = (lay["flags"] & 2) > 0
    assert not ((lay["objects"] > 0) & ~analysis).any()


def test_invalid_pixels_are_nodata(case):
    _, lay = case
    valid = (lay["flags"] & 1) > 0
    assert (lay["hh_a"][~valid] == bp.INT16_NODATA).all()
    assert (lay["hh_a"][valid] != bp.INT16_NODATA).all()


def test_optical_classes_follow_thresholds(case):
    c, _ = case
    if not c.get("optical"):
        pytest.skip("no optical cross-check in case")
    t, mn = c["params"]["ndvi_change"], c["params"]["optical_min_clear_frac"]
    for o in c["objects"]:
        if o["optical_class"] == "no clear optical view":
            assert o["optical_clear_frac"] < mn and "dNDVI" not in o
            continue
        assert o["optical_clear_frac"] >= mn
        d = o["dNDVI"]
        expect = "vegetation loss" if d <= -t else "greening" if d >= t else "little vegetation change"
        assert o["optical_class"] == expect
        assert -1 <= o["NDVI_before"] <= 1 and -1 <= o["NDVI_after"] <= 1
