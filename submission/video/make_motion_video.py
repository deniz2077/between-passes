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
    p.wait_for_selector("#open-case:not([disabled])", timeout=20000)
    p.wait_for_timeout(800)
    r.start()
    # 1 — cover
    r.mark("Real NASA-ISRO NISAR radar data. Two passes, 12 days apart, over farmland in Ceyhan, Türkiye.")
    r.wait(1.2)
    b = p.locator("#open-case").bounding_box()
    r.glide(1400, 800, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, 1.2)
    p.locator("#open-case").click()
    p.wait_for_timeout(300)
    if p.locator("#story").is_visible():
        p.locator('#story [data-story="close"]').click()
    p.locator('#mode-seg [data-mode="delta"]').click()
    p.wait_for_timeout(900)
    # 2 — change map, zoom
    r.mark("636 fields changed sharply — 7× more farmland lit up on radar than went dark.")
    v = p.locator("#viewer").bounding_box()
    cx, cy = v["x"] + v["width"] * 0.55, v["y"] + v["height"] * 0.45
    r.glide(b["x"], b["y"], cx, cy, 0.8)
    r.wheel(cx, cy, -100, 14, 2.2)
    r.drag(cx, cy, cx - 160, cy + 60, 1.2)
    r.wait(0.6)
    # 3 — swipe between passes
    r.mark("Swipe between the two passes, taken 12 days apart from the same orbit.")
    p.locator('#mode-seg [data-mode="swipe"]').click()
    r.wait(0.4)
    mx = v["x"] + v["width"] / 2
    r.drag(mx, cy + 40, v["x"] + v["width"] * 0.2, cy + 40, 1.0)
    r.drag(v["x"] + v["width"] * 0.2, cy + 40, v["x"] + v["width"] * 0.8, cy + 40, 1.2)
    r.wait(0.4)
    p.locator('#mode-seg [data-mode="delta"]').click()
    # 4 — a parcel's evidence
    r.mark("Tap any field for its evidence: compared with the town, which shouldn't change, and a NASA optical satellite.")
    p.evaluate("location.hash='#object-2'")
    r.wait(1.6)
    t = p.locator("#tb-interp").bounding_box()
    r.glide(cx, cy, t["x"] + t["width"] / 2, t["y"] + t["height"] / 2, 0.9)
    p.locator("#tb-interp").click()
    r.wait(2.0)
    # 4b — the locked prediction
    r.mark("Then I published what NISAR's next three passes will show, before NASA released the data.")
    p.evaluate("document.querySelector('#nextpass').scrollIntoView({behavior:'smooth', block:'center'})")
    r.wait(4.2)
    # 5 — global test
    r.mark("Does it work everywhere? I tested it on random NISAR sites worldwide.")
    p.goto(BASE + "world.html", wait_until="networkidle")
    p.wait_for_timeout(700)
    r.wait(1.8)
    dots = p.locator("#w-map .site-dot")
    n = dots.count()
    last = (960, 540)
    for i in (int(n * 0.15), int(n * 0.55), int(n * 0.85)):
        bb = dots.nth(i).bounding_box()
        if not bb:
            continue
        x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        r.glide(last[0], last[1], x, y, 0.7)
        dots.nth(i).click()
        last = (x, y)
        r.wait(0.9)
    r.mark(os.environ.get("BP_RESULT_CAPTION", "Twice, on new random sites: where NASA's soil-moisture satellite saw ground get wetter or drier, NISAR's radar changed with it."))
    p.evaluate("document.querySelector('.w-scattercard').scrollIntoView({behavior:'smooth', block:'center'})")
    r.wait(2.4)
    cm = p.locator("#w-scatter .cey-mark")
    if cm.count():
        bb = cm.first.bounding_box()
        x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        r.glide(last[0], last[1], x, y, 1.0)
        r.wait(0.2)
        p.mouse.click(x, y)
    r.wait(0.4)
    r.mark(os.environ.get("BP_CEYHAN_CAPTION", "Ceyhan: the leading explanation is rain-soaked soil, backed by NASA SMAP."))
    r.wait(2.0)
    p.evaluate("document.querySelector('#w-site').scrollIntoView({behavior:'smooth', block:'start'})")
    r.wait(4.0)
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
    d.rectangle([0, 1080 - 120, 1920, 1080], fill=(28, 27, 23, 236))
    d.rectangle([0, 1080 - 120, 8, 1080], fill=(217, 83, 30, 255))
    im = Image.alpha_composite(im, ov).convert("RGB")
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=FONT)
    d.text(((1920 - w) / 2, 1080 - 120 + 38), text, font=FONT, fill=(243, 239, 230))
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
