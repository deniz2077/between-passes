"""Niğde presentation = the 7 NASA slides + 3 slides the local brief asks for
(technical infrastructure, the locked next-pass prediction, local impact). Renders a PDF.
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

EXTRA = """
<!-- N1 ARCHITECTURE -->
<section class="slide">
  <p class="k">Technical infrastructure</p>
  <h2 style="font-size:56px">Light, reproducible, verifiable — no server, no login.</h2>
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:18px;margin-top:40px">
    <div class="rung" style="min-height:380px"><div class="q">1 · Find</div><p style="font-size:26px;margin-top:14px">NASA <strong>CMR</strong> search: 15,122 VALIDATED NISAR granules → repeat pairs; SMAP, HLS granules.</p><span class="arrow"></span></div>
    <div class="rung" style="min-height:380px"><div class="q">2 · Read</div><p style="font-size:26px;margin-top:14px"><strong>HTTP byte-range</strong> reads into h5py with the user's own Earthdata Login: ~70 MB of a 1.9 GB file.</p><span class="arrow"></span></div>
    <div class="rung" style="min-height:380px"><div class="q">3 · Measure</div><p style="font-size:26px;margin-top:14px">Python <strong>science module</strong> (numpy, scipy, rasterio): masks, speckle filter, control, objects, statistics.</p><span class="arrow"></span></div>
    <div class="rung" style="min-height:380px"><div class="q">4 · Freeze</div><p style="font-size:26px;margin-top:14px">Compact binary layers + JSON with <strong>SHA-256</strong> per file and provenance for every number.</p><span class="arrow"></span></div>
    <div class="rung" style="min-height:380px"><div class="q">5 · Show</div><p style="font-size:26px;margin-top:14px">Static <strong>HTML/JS app</strong> (canvas + SVG), deployed by <strong>GitHub Actions → Pages</strong>.</p></div>
  </div>
  <div style="margin-top:40px;display:grid;grid-template-columns:1fr 1fr;gap:48px">
    <p style="font-size:28px"><strong class="acc">Verification at three levels:</strong> 26 automated tests (pytest) · data-integrity tests on the shipped files · the browser recomputes the published statistics on every load.</p>
    <p style="font-size:28px"><strong class="acc">Science hygiene:</strong> pre-registered global test and replication, deviations listed, a falsifiable prediction locked in public git history before the satellite pass.</p>
  </div>
  <div class="foot"><span>Between Passes · Signal Foundry</span><span>N / T</span></div>
</section>

<!-- N2 PREDICTION -->
<section class="slide">
  <p class="k">A falsifiable prediction · locked before the satellite flies over</p>
  <h2 style="font-size:58px">NISAR passes over Ceyhan again on 15 Nov. I wrote down what it must show.</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:60px;margin-top:34px;align-items:start">
    <div>
      <ul>
        <li><strong>If the brightening was wet soil</strong>, the 508 parcels must <strong class="down">dim back</strong> as the soil dries — SMAP already shows Ceyhan drying from 0.36 to 0.10 m³/m³.</li>
        <li><strong>If it was ploughing</strong>, roughness doesn't dry: they <strong class="up">stay bright</strong>.</li>
        <li><strong>Locked criteria:</strong> wetting dominant if the parcels dim by ≤ −2.07 dB overall and the typical parcel reverses ≥ 50 %; ploughing dominant if &lt; 25 %; void if the town control moves or it rains again.</li>
      </ul>
    </div>
    <div style="background:var(--ink2);border:1px solid var(--line);border-radius:16px;padding:40px 44px">
      <p class="k" style="font-size:20px">Why it matters</p>
      <p style="font-size:32px;color:var(--bone);line-height:1.35">Most projects explain the past. This one <strong class="acc">commits to the future</strong> — and can be proven wrong. The scorer is in the repository; the verdict appears in the app when NASA releases the pass.</p>
      <p class="note" style="margin-top:22px">research/prediction/PREDICTION.md · scripts/predict_next_pass.py</p>
    </div>
  </div>
  <div class="foot"><span>Between Passes · Signal Foundry</span><span>N / T</span></div>
</section>

<!-- N3 LOCAL IMPACT -->
<section class="slide" style="display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center">
  <div>
    <p class="k">Local impact · Çukurova</p>
    <h2 style="font-size:54px">Built for the people who farm the plain — in Turkish, too.</h2>
    <ul style="margin-top:20px">
      <li>A <strong>plain-language Turkish page</strong> for farmers and agriculture technicians: what changed, why, and what is not claimed.</li>
      <li><strong>Find your village</strong> in the parcel census, or draw your own field and measure it.</li>
      <li>Radar sees through Çukurova's winter cloud <strong>every 12 days</strong> — a starting point for field checks, drainage and irrigation questions.</li>
    </ul>
    <p class="note mono" style="margin-top:24px;font-size:22px">deniz2077.github.io/between-passes/tr.html</p>
  </div>
  <div><img class="shot" src="../shots/tr_page.png" style="width:100%"></div>
  <div class="foot"><span>Between Passes · Signal Foundry</span><span>N / T</span></div>
</section>
"""


def main():
    s = open(os.path.join(HERE, "deck.html"), encoding="utf-8").read()
    i = s.index("<!-- 7 IMPACT -->")
    s = s[:i] + EXTRA + s[i:]
    s = s.replace("<title>Between Passes — NASA Space Apps 2026 demo deck</title>",
                  "<title>Between Passes — Niğde presentation</title>")
    # renumber every slide footer "k / T"
    n = [0]
    total = s.count('class="slide"')

    def num(m):
        n[0] += 1
        return f"<span>{n[0]} / {total}</span></div>"
    s = re.sub(r"<span>(?:\d+|N) / (?:7|T)</span></div>", num, s)
    src = os.path.join(HERE, "deck_nigde.html")
    open(src, "w", encoding="utf-8").write(s)
    out = os.path.join(HERE, "Between_Passes_Nigde_Presentation.pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={out}", f"file://{src}"], check=True, capture_output=True)
    print(out, total, "slides", os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
