"""Niğde presentation = the 7 NASA slides + 3 slides the local brief asks for
(technical infrastructure, the locked next-pass prediction, local impact). Renders a PDF.
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

EXTRA = """
<!-- N1 HOW IT WORKS -->
<section class="slide">
  <p class="k">How it works</p>
  <h2>No server, no login. It runs in any browser.</h2>
  <div class="big3" style="grid-template-columns:repeat(4,1fr)">
    <div class="card"><div class="t">1 · Find</div><p>Search NASA's catalogue for NISAR passes over the same place.</p></div>
    <div class="card"><div class="t">2 · Read</div><p>Download only the needed part of each file: about 70 MB of 1.9 GB.</p></div>
    <div class="card"><div class="t">3 · Measure</div><p>Python code compares the passes against a town that should not change.</p></div>
    <div class="card"><div class="t">4 · Show</div><p>A website that re-checks every number when it opens.</p></div>
  </div>
  <p class="lead" style="margin-top:44px">Everything is open source. Anyone with a free NASA Earthdata account can run it again and get the same numbers.</p>
  <p class="fn">Python (h5py, numpy, scipy, rasterio) · HTTP byte-range reads · HTML/JS canvas app · GitHub Actions → Pages · 26 automated tests (pytest).</p>
  <div class="foot"><span>Between Passes · Dusk Orbit</span><span>N / T</span></div>
</section>

<!-- N2 HONEST -->
<section class="slide">
  <p class="k">How I know it's right · and what I don't claim</p>
  <h2>I checked my answer every way I could.</h2>
  <div class="two">
    <div class="out"><h3 class="acc">What I did</h3><p>Wrote the worldwide test down <strong>before</strong> seeing the data. Repeated it on new places. Published my mistakes, including a bug I caught in my own repeat run.</p></div>
    <div class="out"><h3 class="cau">What I don't claim</h3><p>That every single field was wet: some may have been ploughed. Radar alone can't prove the cause. This is a case study, not a warning system.</p></div>
  </div>
  <p class="fn">Pre-registration: research/global/PREREGISTRATION.md and REPLICATION_PREREGISTRATION.md · limits: docs/LIMITATIONS.md</p>
  <div class="foot"><span>Between Passes · Dusk Orbit</span><span>N / T</span></div>
</section>

<!-- N3 LOCAL IMPACT -->
<section class="slide" style="display:grid;grid-template-columns:1fr 1fr;gap:64px;align-items:center">
  <div>
    <p class="k">Local impact · Çukurova</p>
    <h2 style="font-size:66px">Built for the people who farm the plain. In Turkish, too.</h2>
    <ul style="margin-top:20px">
      <li>A plain-language Turkish page for farmers and agriculture technicians.</li>
      <li>Find your village, or draw your own field and measure it.</li>
      <li>Radar sees through winter cloud every 12 days: a starting point for field checks, drainage and irrigation questions.</li>
    </ul>
    <p class="note mono" style="margin-top:24px;font-size:22px">deniz2077.github.io/between-passes/tr.html</p>
  </div>
  <div><img class="shot" src="../shots/tr_page.png" style="width:100%"></div>
  <div class="foot"><span>Between Passes · Dusk Orbit</span><span>N / T</span></div>
</section>
"""


def main():
    s = open(os.path.join(HERE, "deck.html"), encoding="utf-8").read()
    i = s.index("<!-- 7 IMPACT -->")
    s = s[:i] + EXTRA + s[i:]
    s = s.replace("<title>Between Passes · NASA Space Apps 2026 demo deck</title>",
                  "<title>Between Passes · Niğde presentation</title>")
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
