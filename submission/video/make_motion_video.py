"""≤60 s real-motion demo for the Niğde package (YouTube). No narration, no person on screen.

1. Records the working app (served at http://127.0.0.1:8765/) with recorder.Recorder:
   real cursor moves, zoom, swipe, parcel evidence, the World test page.
2. Resamples the screencast to a constant 30 fps, burns in captions, adds a short
   title and end card rendered from cards.html, writes between_passes_demo_60s.mp4.

Usage: python submission/video/make_motion_video.py
"""
import io
import os
import subprocess
import sys

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recorder import Recorder  # noqa: E402

BASE = "http://127.0.0.1:8765/"
FPS = 30
FONT = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 38)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def record():
    r = Recorder(BASE + "index.html")
    p = r.page
    p.add_style_tag(content="html{scroll-behavior:auto}")
    p.wait_for_selector("#lg-w", timeout=20000)
    p.wait_for_timeout(1500)
    p.locator('.steps button[data-step="0"]').click()
    p.wait_for_timeout(400)
    r.start()
    # 1 - the problem, live on real data
    r.mark("NASA-ISRO's NISAR radar over farmland in Ceyhan, Türkiye. 22 October.")
    r.wait(2.2)
    b1 = p.locator('.steps button[data-step="1"]').bounding_box()
    r.glide(1300, 700, b1["x"] + 60, b1["y"] + 15, 0.6)
    p.locator('.steps button[data-step="1"]').click()
    r.mark("12 days later, after the first autumn rain, a normal change map flags all of this.")
    r.wait(4.2)
    b2 = p.locator('.steps button[data-step="2"]').bounding_box()
    r.glide(b1["x"] + 60, b1["y"] + 15, b2["x"] + 60, b2["y"] + 15, 0.5)
    p.locator('.steps button[data-step="2"]').click()
    r.mark("The filter: wet soil can only brighten radar. Blue could be the weather. Amber can't: it really changed.")
    r.wait(4.2)
    # 2 - the problem, measured
    p.evaluate("window.scrollTo({top: document.querySelector('#problem').offsetTop - 40, behavior: 'smooth'})")
    r.mark("At 147 random places, 28× more land looked 'changed' where NASA's SMAP saw the soil get wetter or drier.")
    r.wait(4.0)
    # 3 - worldwide explorer
    p.evaluate("window.scrollTo({top: document.querySelector('.chips').getBoundingClientRect().top + scrollY - 80, behavior: 'smooth'})")
    r.mark("The filter on 148 places in 39 countries. Click any of them.")
    r.wait(1.2)
    last = (960, 540)
    for sel in ('#map circle.dot.weather[aria-label^="India"]', '#map circle.dot.beyond[aria-label^="India"]'):
        dot = p.locator(sel).first
        bb = dot.bounding_box()
        if not bb:
            continue
        x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        r.glide(last[0], last[1], x, y, 0.6)
        dot.click(force=True)
        last = (x, y)
        r.wait(1.0)
    sw = p.locator("#swipe").bounding_box()
    if sw:
        r.mark("Drag between the two passes, then switch the filter on and off.")
        cy = sw["y"] + sw["height"] * 0.5
        r.glide(last[0], last[1], sw["x"] + sw["width"] * 0.5, cy, 0.5)
        r.drag(sw["x"] + sw["width"] * 0.5, cy, sw["x"] + sw["width"] * 0.15, cy, 0.9)
        r.drag(sw["x"] + sw["width"] * 0.15, cy, sw["x"] + sw["width"] * 0.85, cy, 1.1)
        t = p.locator("#t-filter").bounding_box()
        r.glide(sw["x"] + sw["width"] * 0.85, cy, t["x"] + t["width"] / 2, t["y"] + t["height"] / 2, 0.5)
        p.locator("#t-filter").click(); r.wait(1.0)
        p.locator("#t-filter").click(); r.wait(0.8)
    # 4 - any place: Kansas
    p.evaluate("window.scrollTo({top: document.querySelector('#run').offsetTop - 20, behavior: 'smooth'})")
    r.mark("One command runs it on any place NISAR has flown. Six new farming regions, run today.")
    r.wait(2.4)
    k = p.locator('.nc[data-id="check-kansas"]')
    kb = k.bounding_box()
    r.glide(900, 600, kb["x"] + kb["width"] / 2, kb["y"] + kb["height"] / 2, 0.7)
    k.click()
    r.wait(1.6)
    r.mark("Kansas: 50 mm of rain made a third of the land look 'changed'. All of it could be the weather.")
    r.wait(3.6)
    # 5 - Ceyhan: where to look first
    p.evaluate("window.scrollTo({top: document.querySelector('#ceyhan').offsetTop - 20, behavior: 'smooth'})")
    r.mark("In my home region, the fields the rain can't explain, listed with their villages.")
    r.wait(3.6)
    # 6 - predictions
    p.evaluate("window.scrollTo({top: document.querySelector('#predictions').offsetTop - 20, behavior: 'smooth'})")
    r.mark("And predictions for the next three passes, locked before NASA released the data. They score themselves.")
    r.wait(4.2)
    return r.stop()


def card(hash_, path):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080",
                    "--virtual-time-budget=4000", f"--screenshot={path}",
                    f"file://{os.path.join(HERE, 'cards.html')}#{hash_}"], check=True, capture_output=True)
    return np.asarray(Image.open(path).convert("RGB").resize((1920, 1080)))


def caption(img, text):
    if not text:
        return img
    im = Image.fromarray(img).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 1080 - 120, 1920, 1080], fill=(10, 11, 13, 236))
    d.rectangle([0, 1080 - 120, 8, 1080], fill=(255, 176, 32, 255))
    im = Image.alpha_composite(im, ov).convert("RGB")
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=FONT)
    d.text(((1920 - w) / 2, 1080 - 120 + 38), text, font=FONT, fill=(236, 234, 228))
    return np.asarray(im)


def main():
    frames, marks, t0 = record()
    frames = [(t, b) for t, b in frames if t >= t0]
    t_end = frames[-1][0]
    out = os.path.join(HERE, "between_passes_demo_60s.mp4")
    w = imageio.get_writer(out, fps=FPS, codec="libx264", quality=8, macro_block_size=8,
                           ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    intro = card("intro", os.path.join(HERE, "frames", "_intro.png"))
    outro = card("outro", os.path.join(HERE, "frames", "_outro.png"))
    n = 0
    for _ in range(int(2.5 * FPS)):
        w.append_data(intro); n += 1
    j, cache = 0, {}
    t = frames[0][0]
    prev = None
    while t <= t_end:
        while j + 1 < len(frames) and frames[j + 1][0] <= t:
            j += 1
        cap = ""
        for mt, label in marks:
            if mt <= t + 0.15:
                cap = label
        key = (j, cap)
        if key not in cache:
            cache.clear()
            img = np.asarray(Image.open(io.BytesIO(frames[j][1])).convert("RGB").resize((1920, 1080)))
            cache[key] = caption(img, cap)
        cur = cache[key]
        if prev is None and n:
            for i in range(10):  # fade from intro
                a = (i + 1) / 11
                w.append_data((intro * (1 - a) + cur * a).astype(np.uint8)); n += 1
        w.append_data(cur); n += 1
        prev = cur
        t += 1 / FPS
    for i in range(10):
        a = (i + 1) / 11
        w.append_data((prev * (1 - a) + outro * a).astype(np.uint8)); n += 1
    for _ in range(int(4.5 * FPS)):
        w.append_data(outro); n += 1
    w.close()
    print(out, f"{n / FPS:.1f} s", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
