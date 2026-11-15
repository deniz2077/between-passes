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
  <p class="k"><b>N1</b>Technical infrastructure</p>
  <h2>No server, no login. It runs in any browser.</h2>
  <div class="row3" style="grid-template-columns:repeat(4,1fr);margin-top:34px">
    <div class="card"><div class="t">1 · Find</div><p>NASA's catalogue (CMR) gives two NISAR passes on the identical orbit and grid.</p></div>
    <div class="card"><div class="t">2 · Read</div><p>Only the needed window of each 1.9 GB file is downloaded: about 70 MB.</p></div>
    <div class="card"><div class="t">3 · Filter</div><p>Python compares the passes, reads SMAP and POWER, and sorts every change.</p></div>
    <div class="card"><div class="t">4 · Show</div><p>A static website that re-checks every published number when it opens.</p></div>
  </div>
  <p class="lead" style="margin-top:44px">Open source. Anyone with a free NASA Earthdata account can run <span class="mono" style="font-size:32px;color:var(--text)">bp_check.py</span> on any place NISAR has flown and get the same answer.</p>
  <p class="fn">Python (h5py, NumPy, SciPy, rasterio, Shapely) · HTTP byte-range reads · HTML/JS canvas app, no framework · GitHub Actions → Pages · 37 automated tests (pytest)</p>
  <div class="foot"><span>Between Passes · Dusk Orbit</span><span>N / T</span></div>
</section>

<!-- N2 HONEST -->
<section class="slide">
  <p class="k"><b>N2</b>How I know it's right · and what I don't claim</p>
  <h2>Rules first. Then the data.</h2>
  <div class="grid2" style="gap:28px;margin-top:34px;align-items:stretch">
    <div class="card"><div class="t" style="color:var(--weather)">What I did</div><p>Wrote the worldwide test, its repeat, the filter's rules and three predictions down <b>before</b> seeing the data, and published them on GitHub with timestamps. Reported every dropped site, deviation and failed run.</p></div>
    <div class="card"><div class="t" style="color:var(--beyond)">What I don't claim</div><p>The filter says <b>where to look</b>, not what happened. SMAP measures 9 km cells, so a local shower can look like real change. Radar alone can't prove the cause of one field's change.</p></div>
  </div>
  <p class="fn">research/global/PREREGISTRATION.md · research/filter/WEATHER_FILTER.md · research/prediction/ · docs/LIMITATIONS.md</p>
  <div class="foot"><span>Between Passes · Dusk Orbit</span><span>N / T</span></div>
</section>

<!-- N3 LOCAL IMPACT -->
<section class="slide grid2">
  <div>
    <p class="k"><b>N3</b>Local impact · Çukurova</p>
    <h2 style="font-size:66px">Built for the people who farm the plain. In Turkish, too.</h2>
    <ul style="margin-top:20px">
      <li>A plain-language Turkish page for farmers and agriculture technicians.</li>
      <li>"Where to look first": the fields the rain can't explain, with the nearest village.</li>
      <li>Radar sees through winter cloud every 12 days: a starting point for field checks, drainage and irrigation questions.</li>
    </ul>
    <p class="mono" style="margin-top:24px;font-size:22px;color:var(--muted)">deniz2077.github.io/between-passes/tr.html</p>
  </div>
  <div><img class="shot" src="../shots/n_tr.png" style="width:100%"></div>
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
    total = s.count('<section class="slide')

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
