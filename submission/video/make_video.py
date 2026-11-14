"""Assemble the captioned, narration-free walkthrough video from real app screenshots.

Frames: submission/video/frames/*.png (1920x1080, captured from the working app with headless Chrome)
Output: submission/video/between_passes_walkthrough.mp4
"""
import os

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "frames")
FPS = 24
FADE = 0.5
FONT = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", 40)

SCENES = [
    ("00_intro.png", 6, None),
    ("01_cover.png", 6, "Real NISAR VALIDATED radar data over the fields of Ceyhan, Adana (Türkiye)."),
    ("02_story1.png", 8, "Two passes — 22 Oct and 3 Nov 2026 — from the identical orbit, compared on one 20 m grid."),
    ("03_story2.png", 8, "636 field parcels changed by ≥ 3 dB: 7.0× more area brightened than darkened."),
    ("04_story3.png", 8, "Is it real? Ceyhan's town centre, a stable control, changed by only +0.12 dB."),
    ("05_story4.png", 8, "Is it harvest? NASA HLS optical data: only 9% of brightened parcels lost vegetation."),
    ("06_story5.png", 9, "What remains is the soil surface — wetted by ~23 mm of rain, or ploughed. One pair can't tell; the app says so."),
    ("07_object.png", 8, "Every parcel opens its evidence: change vs. control, optical check, and an HV caution."),
    ("08_roi.png", 8, "Draw any region: statistics are computed live in the browser from the real data."),
    ("09_census.png", 7, "The full census, with a threshold-sensitivity check from 2 to 5 dB."),
    ("10_method.png", 8, "On every load, the browser re-verifies the published numbers from the shipped data."),
    ("11_export.png", 6, "Export a case file — JSON, CSV or a printable report."),
    ("12_outro.png", 8, None),
]


def captioned(path, text):
    im = Image.open(os.path.join(FR, path)).convert("RGB").resize((1920, 1080))
    if text:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        d.rectangle([0, 1080 - 132, 1920, 1080], fill=(7, 9, 12, 228))
        d.rectangle([0, 1080 - 132, 8, 1080], fill=(86, 212, 232, 255))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        d = ImageDraw.Draw(im)
        w = d.textlength(text, font=FONT)
        d.text(((1920 - w) / 2, 1080 - 132 + 44), text, font=FONT, fill=(232, 227, 216))
    return np.asarray(im)


def main():
    frames = [(captioned(p, t), s) for p, t, s in [(p, t, s) for p, s, t in SCENES]]
    out = os.path.join(HERE, "between_passes_walkthrough.mp4")
    w = imageio.get_writer(out, fps=FPS, codec="libx264", quality=8, macro_block_size=8,
                           ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    nf = int(FADE * FPS)
    total = 0
    for k, (img, secs) in enumerate(frames):
        hold = int(secs * FPS) - (nf if k < len(frames) - 1 else 0)
        for _ in range(hold):
            w.append_data(img)
        total += hold
        if k < len(frames) - 1:
            nxt = frames[k + 1][0]
            for i in range(nf):
                a = (i + 1) / (nf + 1)
                w.append_data((img * (1 - a) + nxt * a).astype(np.uint8))
            total += nf
    w.close()
    print(out, f"{total / FPS:.1f} s", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
