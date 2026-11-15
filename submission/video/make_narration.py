"""AI voiceover for the Niğde demo film (neural text-to-speech, not a real person's voice).

Writes vo/<scene>.mp3 and vo/timing.json (word timings for the burned-in captions).
Usage: .venv/bin/python submission/video/make_narration.py [voice]
"""
import asyncio
import json
import os
import subprocess
import sys

import edge_tts
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, "vo")
VOICE = sys.argv[1] if len(sys.argv) > 1 else "en-US-BrianMultilingualNeural"

# Every claim below is in README.md / research/: hero crop 88% vs 12%, 147 sites 28x,
# 148 places / 39 countries, rules committed first, predictions locked before release.
SCENES = [
    ("s1", "Every twelve days, the NASA-ISRO NISAR satellite maps the Earth by radar. Through cloud, day and night."),
    ("s2", "Compare two passes to spot floods, harvests and cleared forest. But rain fools radar. "
           "Wet soil shines brighter, so after one rainy week, hundreds of fields look changed."),
    ("s3", "At 147 random places, twenty-eight times more land looked changed where the soil got wetter or drier."),
    ("s4", "Between Passes asks NASA's SMAP satellite: did the soil get wetter? Wet soil can only brighten radar. "
           "So brighter fields could be the rain. Darker ones can't. Something really changed there."),
    ("s5", "It's a live app. 148 places, 39 countries, and one command checks anywhere NISAR flies."),
    ("s6", "The rules were written before the data. Predictions were locked before NASA released it."),
    ("s7", "Fewer false alarms, so flood teams and farmers check the real changes first. "
           "Rain fools radar. Between Passes shows what really changed."),
]


async def one(key, text):
    c = edge_tts.Communicate(text, VOICE, rate="+12%", boundary="WordBoundary")
    words, audio = [], bytearray()
    async for ch in c.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            words.append({"t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7, "w": ch["text"]})
    mp3 = os.path.join(VO, key + ".mp3")
    open(mp3, "wb").write(audio)
    wav = os.path.join(VO, key + ".wav")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", mp3, "-ar", "48000", "-ac", "1", wav], check=True)
    import wave
    with wave.open(wav) as w:
        dur = w.getnframes() / w.getframerate()
    return {"key": key, "text": text, "words": words, "dur": dur}


async def main():
    os.makedirs(VO, exist_ok=True)
    out = [await one(k, t) for k, t in SCENES]
    json.dump({"voice": VOICE, "scenes": out}, open(os.path.join(VO, "timing.json"), "w"), indent=1)
    for s in out:
        print(s["key"], f"{s['dur']:.2f}s", len(s["words"]), "words")
    print("total speech", round(sum(s["dur"] for s in out), 2))


if __name__ == "__main__":
    asyncio.run(main())
