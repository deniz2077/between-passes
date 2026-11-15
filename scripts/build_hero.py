"""Hero images for the front page, from the shipped Ceyhan layers (real NISAR data).

before.jpg / after.jpg : HH gamma0 22 Oct / 3 Nov, same fixed stretch, 20 m.
filter.png             : the weather filter applied to Ceyhan (research/filter/WEATHER_FILTER.md):
                         soil got wetter (SMAP, exploratory +0.195), so pixels >= +3 dB brighter
                         "could be the weather" (blue), pixels <= -3 dB darker are "beyond the weather" (amber).
Writes app/img/hero/ and app/img/hero/hero.json (crop, counts).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from bp_science import boxcar_linear  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CE = os.path.join(ROOT, "app", "data", "ceyhan")
OUT = os.path.join(ROOT, "app", "img", "hero")
R0, R1, C0, C1 = 500, 1180, 310, 1190      # fully inside the valid swath
WEATHER = (111, 168, 220)
BEYOND = (255, 176, 32)


def main():
    os.makedirs(OUT, exist_ok=True)
    W = H = 1200
    a = np.fromfile(os.path.join(CE, "hh_a.i16"), np.int16).reshape(H, W)
    b = np.fromfile(os.path.join(CE, "hh_b.i16"), np.int16).reshape(H, W)
    flags = np.fromfile(os.path.join(CE, "flags.u8"), np.uint8).reshape(H, W)
    valid = (flags & 1).astype(bool)
    la = np.where(valid, 10 ** (a / 1000.0), 0)
    lb = np.where(valid, 10 ** (b / 1000.0), 0)
    sa, sb = boxcar_linear(la, valid, 5), boxcar_linear(lb, valid, 5)
    s3a, s3b = boxcar_linear(la, valid, 3), boxcar_linear(lb, valid, 3)
    d = 10 * np.log10(sb / sa)
    sl = (slice(R0, R1), slice(C0, C1))

    def gray(lin):
        db = 10 * np.log10(np.maximum(lin, 1e-6))
        g = np.clip((db + 22) / 22, 0, 1) ** 0.9
        return (g * 255).astype(np.uint8)

    Image.fromarray(gray(s3a[sl])).save(os.path.join(OUT, "before.jpg"), quality=86)
    Image.fromarray(gray(s3b[sl])).save(os.path.join(OUT, "after.jpg"), quality=86)
    an = (flags & 2).astype(bool)
    up = (d >= 3) & an
    dn = (d <= -3) & an
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[up] = (*WEATHER, 235)
    rgba[dn] = (*BEYOND, 255)
    Image.fromarray(rgba[sl]).save(os.path.join(OUT, "filter.png"), optimize=True)
    allc = np.zeros((H, W, 4), np.uint8)
    allc[up | dn] = (245, 243, 236, 255)
    Image.fromarray(allc[sl]).save(os.path.join(OUT, "changes.png"), optimize=True)
    nv = int(an.sum())
    meta = dict(crop=[R0, R1, C0, C1], posting_m=20, analysis_px=nv,
                could_be_weather_px=int(up.sum()), beyond_weather_px=int(dn.sum()),
                could_be_weather_frac=round(up.sum() / nv, 4), beyond_weather_frac=round(dn.sum() / nv, 4),
                source="app/data/ceyhan hh_a/hh_b/flags; 5x5 linear boxcar; +/-3 dB; soil wetter (SMAP exploratory)")
    json.dump(meta, open(os.path.join(OUT, "hero.json"), "w"), indent=1)
    print(meta)


if __name__ == "__main__":
    main()
