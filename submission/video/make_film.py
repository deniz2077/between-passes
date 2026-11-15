"""Niğde demo film (≤60 s): AI-narrated motion graphics on real NISAR data + a live-app clip.

Needs: vo/timing.json (make_narration.py) and `python3 -m http.server 8765` serving app/.
Writes between_passes_film_60s.mp4.
"""
import io
import json
import math
import os
import subprocess
import sys
import wave

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from recorder import Recorder  # noqa: E402

FPS = 30
SR = 48000
FONT = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 44)
TAGF = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 24)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
LEAD = {"s1": 0.7}
GAP = 0.34
HOLD_END = 2.0


def timeline():
    vo = json.load(open(os.path.join(HERE, "vo", "timing.json")))
    tl, t = {}, 0.0
    for s in vo["scenes"]:
        lead = LEAD.get(s["key"], 0.22)
        end = s["words"][-1]["t"] + s["words"][-1]["d"]
        dur = lead + end + GAP
        if s["key"] == "s5":
            dur = max(dur, 6.9)
        if s["key"] == "s7":
            dur = lead + end + HOLD_END
        tl[s["key"]] = {"t0": round(t, 3), "dur": round(dur, 3), "lead": lead, "words": s["words"]}
        t += dur
    return tl, t


CURSOR_JS = """
(() => { const c=document.createElement('div');
c.style.cssText='position:fixed;z-index:99999;left:0;top:0;width:28px;height:28px;margin:-14px 0 0 -14px;border-radius:50%;background:rgba(255,255,255,.92);border:3px solid #0a0b0d;box-shadow:0 2px 10px rgba(0,0,0,.5);pointer-events:none;transition:transform .12s';
document.addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'},true);
document.addEventListener('mousedown',()=>c.style.transform='scale(.7)',true);
document.addEventListener('mouseup',()=>c.style.transform='scale(1)',true);
document.body.appendChild(c); })();
"""


def record_demo():
    r = Recorder("http://127.0.0.1:8765/index.html")
    p = r.page
    p.add_style_tag(content="html{scroll-behavior:auto}")
    p.wait_for_selector("#lg-w", timeout=20000)
    p.evaluate(CURSOR_JS)
    p.evaluate("window.scrollTo(0, document.querySelector('.chips').getBoundingClientRect().top + scrollY - 70)")
    p.wait_for_timeout(1200)
    p.mouse.move(1500, 520)
    r.start()
    r.wait(0.4)
    last = (1500, 520)
    dot = p.locator('#map circle.dot.beyond[aria-label^="India"]').first
    bb = dot.bounding_box()
    x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
    r.glide(last[0], last[1], x, y, 0.7)
    dot.click(force=True)
    r.wait(0.7)
    sw = p.locator("#swipe").bounding_box()
    cy = sw["y"] + sw["height"] * 0.5
    r.glide(x, y, sw["x"] + sw["width"] * 0.5, cy, 0.45)
    r.drag(sw["x"] + sw["width"] * 0.5, cy, sw["x"] + sw["width"] * 0.12, cy, 0.8)
    r.drag(sw["x"] + sw["width"] * 0.12, cy, sw["x"] + sw["width"] * 0.88, cy, 1.0)
    tb = p.locator("#t-filter").bounding_box()
    r.glide(sw["x"] + sw["width"] * 0.88, cy, tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 2, 0.45)
    p.locator("#t-filter").click(); r.wait(0.7)
    p.locator("#t-filter").click(); r.wait(0.5)
    p.evaluate("window.scrollTo({top: document.querySelector('#run').offsetTop - 20, behavior: 'smooth'})")
    r.wait(1.6)
    frames, _, t0 = r.stop()
    return [(t - t0, b) for t, b in frames if t >= t0]


def chunks(words, lead, text):
    """Caption lines: one clause of the script per line; clauses over 7 words split in balanced halves."""
    import re
    sizes = []
    for cl in re.split(r"[.?!:,]", text):
        n = len(cl.split())
        if not n:
            continue
        if n > 7:
            k = math.ceil(n / math.ceil(n / 6))
            while n > 0:
                sizes.append(min(k, n)); n -= k
        else:
            sizes.append(n)
    assert sum(sizes) == len(words), (sum(sizes), len(words), text)
    out, i = [], 0
    for n in sizes:
        out.append(words[i:i + n]); i += n
    res = []
    for i, c in enumerate(out):
        start = lead + c[0]["t"] - 0.08
        end = lead + (out[i + 1][0]["t"] - 0.08 if i + 1 < len(out) else c[-1]["t"] + c[-1]["d"] + 0.35)
        res.append((start, end, c))
    return res


def draw_caption(img, line, u, lead):
    if line is None:
        return img
    _, _, ws = line
    im = Image.fromarray(img).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    txt = [w["w"] for w in ws]
    space = d.textlength(" ", font=FONT)
    widths = [d.textlength(s, font=FONT) for s in txt]
    total = sum(widths) + space * (len(txt) - 1)
    x0, y0 = (1920 - total) / 2, 1080 - 128
    d.rounded_rectangle([x0 - 30, y0 - 18, x0 + total + 30, y0 + 66], 14, fill=(10, 11, 13, 215))
    im = Image.alpha_composite(im, ov)
    d = ImageDraw.Draw(im)
    x = x0
    for s, wd, w in zip(txt, widths, ws):
        spoken = u >= lead + w["t"] - 0.02
        active = spoken and u < lead + w["t"] + w["d"] + 0.05
        col = (255, 176, 32) if active else ((236, 234, 228) if spoken else (150, 154, 162))
        d.text((x, y0), s, font=FONT, fill=col)
        x += wd + space
    return np.asarray(im.convert("RGB"))


def draw_tag(img):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    s = "LIVE APP  ·  deniz2077.github.io/between-passes"
    w = d.textlength(s, font=TAGF)
    d.rounded_rectangle([1920 - 72 - w - 36, 40, 1920 - 72, 92], 8, fill=(255, 176, 32))
    d.text((1920 - 72 - w - 18, 52), s, font=TAGF, fill=(10, 11, 13))
    return np.asarray(im)


def music(total):
    """Quiet synthesized ambient pad (original, no samples): A minor add9, slow swell."""
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a in ((110, .5), (164.81, .35), (220, .3), (246.94, .18), (329.63, .14)):
        for det in (-0.6, 0.6):
            out += a * np.sin(2 * math.pi * (f + det) * t + det)
    lfo = 0.75 + 0.25 * np.sin(2 * math.pi * t / 9)
    env = np.minimum(1, t / 2.5) * np.minimum(1, (total - t) / 2.0)
    out = out * lfo * env
    return out / np.abs(out).max() * 0.07


def read_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return a


def main():
    tl, total = timeline()
    print("timeline", {k: (v["t0"], v["dur"]) for k, v in tl.items()}, "total", round(total, 2))
    demo = record_demo()
    print("demo frames", len(demo), "span", round(demo[-1][0], 2))
    texts = {x["key"]: x["text"] for x in json.load(open(os.path.join(HERE, "vo", "timing.json")))["scenes"]}
    caps = {k: chunks(v["words"], v["lead"], texts[k]) for k, v in tl.items()}

    # audio
    n = int(total * SR) + SR
    mix = music(n / SR)
    for k, v in tl.items():
        a = read_wav(os.path.join(HERE, "vo", k + ".wav"))
        i = int((v["t0"] + v["lead"]) * SR)
        mix[i:i + len(a)] += a[: len(mix) - i] * 0.95
    mix = np.clip(mix, -1, 1)
    wav = os.path.join(HERE, "film", "_mix.wav")
    with wave.open(wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[: int(total * SR)] * 32767).astype(np.int16).tobytes())

    silent = os.path.join(HERE, "film", "_video.mp4")
    wr = imageio.get_writer(silent, fps=FPS, codec="libx264", quality=9, macro_block_size=8,
                            ffmpeg_params=["-pix_fmt", "yuv420p"])
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=["--hide-scrollbars"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto("file://" + os.path.join(HERE, "film", "film.html"), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.evaluate(f"setTL({json.dumps(tl)})")
        s5 = tl["s5"]
        nf = int(total * FPS)
        j = 0
        for f in range(nf):
            t = f / FPS
            if s5["t0"] <= t < s5["t0"] + s5["dur"]:
                u = t - s5["t0"]
                while j + 1 < len(demo) and demo[j + 1][0] <= u:
                    j += 1
                img = np.asarray(Image.open(io.BytesIO(demo[j][1])).convert("RGB").crop((240, 36, 1680, 846)).resize((1920, 1080), Image.LANCZOS))
                # fade in/out of the clip
                a = min(1, u / 0.3, (s5["dur"] - u) / 0.3)
                img = draw_tag((img * a).astype(np.uint8))
            else:
                pg.evaluate(f"seek({t})")
                img = np.asarray(Image.open(io.BytesIO(pg.screenshot(type="jpeg", quality=94))).convert("RGB"))
            key = next(k for k, v in tl.items() if v["t0"] <= t < v["t0"] + v["dur"] + 1e-6) if t < total else "s7"
            u = t - tl[key]["t0"]
            line = next((c for c in caps[key] if c[0] <= u < c[1]), None)
            wr.append_data(draw_caption(img, line, u, tl[key]["lead"]))
            if f % 150 == 0:
                print("frame", f, "/", nf, flush=True)
        b.close()
    wr.close()
    out = os.path.join(HERE, "between_passes_film_60s.mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(out, round(total, 2), "s", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
