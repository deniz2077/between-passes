"""Build the Niğde 'Project Documentation' PDF from the repository's own documents.

Sources (single source of truth): README.md, docs/METHOD.md, research/global/RESULTS.md,
research/prediction/PREDICTION.md, docs/LIMITATIONS.md, DATA_PROVENANCE.md, docs/AI_USE.md.
Output: submission/docs/Between_Passes_Documentation.pdf (rendered with headless Chrome).
"""
import os
import re
import subprocess

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PARTS = [
    ("The weather filter: rules fixed first", "research/filter/WEATHER_FILTER.md"),
    ("Method in detail", "docs/METHOD.md"),
    ("Worldwide test: results", "research/global/RESULTS.md"),
    ("Prediction 1: the next pass", "research/prediction/PREDICTION.md"),
    ("Prediction 2: two other orbits", "research/prediction/PREDICTION2.md"),
    ("Limitations: what I don't claim", "docs/LIMITATIONS.md"),
    ("Reproduce it yourself", "docs/REPRODUCE.md"),
    ("Data provenance", "DATA_PROVENANCE.md"),
    ("Use of AI", "docs/AI_USE.md"),
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font: 10.5pt/1.5 "IBM Plex Sans", -apple-system, sans-serif; color: #1b1f24; }
h1 { font-size: 22pt; margin: 0 0 6pt; letter-spacing: -.01em; }
h2 { font-size: 14pt; margin: 16pt 0 6pt; border-bottom: 1px solid #d8dde3; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
.part { page-break-before: always; }
.part:first-of-type { page-break-before: auto; }
.part > h1.ptitle { font-size: 9pt; letter-spacing: .12em; text-transform: uppercase; color: #0b7f95; margin-bottom: 10pt; }
code, pre { font-family: "IBM Plex Mono", Menlo, monospace; font-size: 8.6pt; }
pre { background: #f4f6f8; padding: 8pt; border-radius: 4pt; white-space: pre-wrap; word-break: break-all; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 6pt 0; }
td, th { border: 1px solid #d8dde3; padding: 3pt 5pt; text-align: left; vertical-align: top; }
a { color: #0b7f95; word-break: break-all; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; }
.cover .k { font: 500 9pt "IBM Plex Mono", monospace; letter-spacing: .12em; color: #0b7f95; text-transform: uppercase; }
.cover h1 { font-size: 40pt; margin: 8pt 0 12pt; }
.cover p { font-size: 12pt; max-width: 150mm; }
.cover img { width: 120mm; border-radius: 6pt; margin-top: 12pt; }
.meta { font: 9.5pt "IBM Plex Mono", monospace; color: #555; margin-top: 18pt; line-height: 1.7; }
"""


def md(path):
    txt = open(os.path.join(ROOT, path), encoding="utf-8").read()
    # images -> local files; links to repo files -> GitHub
    txt = re.sub(r"!\[([^\]]*)\]\((?!https?://)([^)]+)\)", lambda m: f"![{m.group(1)}](file://{ROOT}/{m.group(2)})", txt)
    txt = re.sub(r"\]\((?!https?://|file://)([^)#]+)\)", lambda m: f"](https://github.com/deniz2077/between-passes/blob/main/{m.group(1)})", txt)
    return markdown.markdown(txt, extensions=["tables", "fenced_code"])


FRONT_CSS = """
.cov { width: 210mm; height: 296.5mm; margin: 0; background: #0a0b0d; color: #eceae4; position: relative; overflow: hidden; page-break-after: always; }
.cov img.bg { position: absolute; right: 0; top: 0; height: 100%; width: 70%; object-fit: cover; opacity: .9; }
.cov .fade { position: absolute; inset: 0; background: linear-gradient(90deg,#0a0b0d 38%,rgba(10,11,13,.75) 58%,rgba(10,11,13,.05)); }
.cov .in { position: absolute; left: 16mm; top: 34mm; width: 125mm; }
.cov .k { font: 500 8pt "IBM Plex Mono", monospace; letter-spacing: .14em; text-transform: uppercase; color: #8d929b; }
.cov h1 { font-size: 46pt; line-height: .95; letter-spacing: -.03em; margin: 8mm 0 0; color: #eceae4; border: 0; }
.cov .sub { font-size: 17pt; color: #ffb020; font-weight: 500; margin: 5mm 0 0; line-height: 1.15; }
.cov p { color: #c4c6cb; font-size: 11pt; }
.cov .doc { position: absolute; left: 16mm; bottom: 20mm; font: 9pt/1.8 "IBM Plex Mono", monospace; color: #c4c6cb; }
.cov .doc b { color: #eceae4; }
.cov .qr { position: absolute; right: 16mm; bottom: 18mm; width: 30mm; border-radius: 3pt; }
.cov .brand { position: absolute; left: 16mm; top: 14mm; font: 600 9pt "IBM Plex Mono", monospace; letter-spacing: .16em; }
.cov .brand i { display: inline-block; width: 2.4mm; height: 5mm; background: #eceae4; margin-right: 1mm; border-radius: .5mm; vertical-align: -1mm; }
.cov .brand i.s { height: 3.4mm; opacity: .55; } .cov .brand em { display: inline-block; width: 2.2mm; height: 2.2mm; border-radius: 50%; background: #ffb020; margin: 0 3mm 0 .5mm; vertical-align: 2.5mm; }
.box { border: 1px solid #d8dde3; border-left: 4px solid #ffb020; border-radius: 4pt; padding: 8pt 12pt; margin: 8pt 0; background: #fbfaf7; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10pt; }
.toc { font-size: 11pt; } .toc div { display: flex; justify-content: space-between; border-bottom: 1px dotted #c9ced4; padding: 4pt 0; }
.toc span.n { font-family: "IBM Plex Mono", monospace; color: #b37a00; width: 9mm; display: inline-block; }
.fig { margin: 6pt 0 10pt; } .fig img { width: 100%; border-radius: 4pt; border: 1px solid #d8dde3; display: block; } .fig .c { font-size: 8.5pt; color: #5b636d; margin-top: 3pt; }
.step { display: grid; grid-template-columns: 9mm 1fr; gap: 6pt; margin: 6pt 0; } .step .n { font: 600 14pt "IBM Plex Mono", monospace; color: #b37a00; }
.pipe { display: grid; grid-template-columns: repeat(5, 1fr); gap: 5pt; margin: 8pt 0; }
.pipe div { border: 1px solid #d8dde3; border-radius: 4pt; padding: 6pt; font-size: 8.8pt; background: #fbfaf7; } .pipe b { display: block; color: #b37a00; font-family: "IBM Plex Mono", monospace; font-size: 8pt; }
.kv td:first-child { width: 42mm; font-weight: 600; }
"""

SHOTS = os.path.join(ROOT, "submission", "shots")


def img(path, cap, style=""):
    return f"<div class='fig'><img src='file://{path}' style='{style}'><div class='c'>{cap}</div></div>"


def front():
    h = []
    h.append(f"""<section class='cov'><img class='bg' src='file://{ROOT}/app/img/readme_filter.jpg'><div class='fade'></div>
    <div class='brand'><i></i><i class='s'></i><em></em>BETWEEN PASSES</div>
    <div class='in'><div class='k'>NASA Space Apps Challenge 2026 · Dancing with the SARs</div>
    <h1>Rain fools radar.</h1><div class='sub'>Between Passes shows what really changed.</div>
    <p style='margin-top:8mm'>A weather filter for satellite radar change maps, built on NASA–ISRO NISAR radar, NASA SMAP soil moisture and NASA POWER rain data.</p>
    <p style='margin-top:6mm;font:600 13pt "IBM Plex Sans";color:#eceae4'>Project Documentation</p></div>
    <div class='doc'><b>Team Dusk Orbit</b> · Deniz Efe Bulut · Niğde Local Event, Türkiye<br>
    App&nbsp;&nbsp;&nbsp;deniz2077.github.io/between-passes<br>Code&nbsp;&nbsp;github.com/deniz2077/between-passes<br>Video&nbsp;youtu.be/pUskV9Lm9Vk</div>
    <img class='qr' src='file://{ROOT}/submission/deck/n10/qr.png'></section>""")
    # summary + contents
    h.append("""<section><h1>Between Passes in two minutes</h1>
    <div class='box'><b>The problem.</b> Satellites find floods, harvests and cleared forest by comparing two radar pictures of the same place. But wet soil looks brighter to radar, so after rain whole regions look “changed” when nothing happened. At 147 random NISAR places, <b>28× more land</b> looked changed where NASA SMAP saw the soil get wetter or drier (5.0% vs 0.18%).</div>
    <div class='box'><b>The solution.</b> Wetter soil can only brighten radar, drier soil only darken it. Between Passes asks SMAP how the soil changed between the two passes and sorts every change: one that matches the weather <i>could be just the rain</i> (blue); one that goes against it <i>cannot be the weather</i>, so something really changed (orange).</div>
    <div class='box'><b>What it delivers.</b> A free web app with 148 places in 39 countries (41 really changed, 27 mostly weather, 80 quiet); a command, <code>bp_check.py</code>, that runs the filter on any place NISAR has flown; a Turkish “where to look first” list of 128 fields in Ceyhan, Adana; and three predictions locked before NASA released the data.</div>
    <div class='box'><b>Why trust it.</b> Every rule was committed to GitHub before it was run. The link between NISAR change and SMAP soil moisture held at 74 random places and again at 73 new ones (ρ = 0.58 and 0.55, p &lt; 0.001). 37 automated tests; the app re-checks its published numbers in the browser.</div>
    <h2>Contents</h2><div class='toc'>
    <div><span><span class='n'>1</span>User guide: how to use the app</span></div>
    <div><span><span class='n'>2</span>System architecture and technology</span></div>
    <div><span><span class='n'>3</span>NASA data sources</span></div>
        <div><span><span class='n'>4</span>Development process: 4 Scrum sprints</span></div>
    <div><span><span class='n'>5</span>The weather filter: rules fixed first</span></div>
    <div><span><span class='n'>6</span>Method in detail</span></div>
    <div><span><span class='n'>7</span>Worldwide test: results</span></div>
    <div><span><span class='n'>8</span>Prediction 1: the next pass</span></div>
    <div><span><span class='n'>9</span>Prediction 2: two other orbits</span></div>
    <div><span><span class='n'>10</span>Limitations: what I don't claim</span></div>
    <div><span><span class='n'>11</span>Reproduce it yourself</span></div>
    <div><span><span class='n'>12</span>Data provenance</span></div>
    <div><span><span class='n'>13</span>Use of AI</span></div></div></section>""")
    # 1 user guide
    h.append(f"""<section class='part'><h1 class='ptitle'>1 · User guide</h1><h1>How to use the app</h1>
    <p>Open <b>deniz2077.github.io/between-passes</b> on any computer or phone. No installation, no account, no login. A Turkish page is at <b>/tr.html</b>.</p>
    <div class='grid2'>{img(SHOTS+'/n_demo.png','The front page: real NISAR radar over Ceyhan, filter on. Blue: could be the rain. Orange: really changed.')}
    <div><div class='step'><div class='n'>1</div><div><b>Watch the filter work.</b> On the front page, press <i>Before</i>, <i>After the rain</i> and <i>Filter on</i>. The same radar map goes from “everything changed” (white) to blue and orange.</div></div>
    <div class='step'><div class='n'>2</div><div><b>Read the colours.</b> Blue: the change matches the soil moisture, so it could be just the weather. Orange: it goes against the weather, so something on the ground really changed.</div></div>
    <div class='step'><div class='n'>3</div><div><b>Explore the world.</b> Click any of 148 dots. Each card lets you drag between the two passes, switch the filter on and off, read the soil moisture and rain, and copy a share link.</div></div>
    <div class='step'><div class='n'>4</div><div><b>Look at Ceyhan.</b> “Where to look first” lists the 128 fields that got darker while the soil got wetter, largest first, with the nearest village.</div></div>
    <div class='step'><div class='n'>5</div><div><b>Check the predictions.</b> The prediction board shows three locked predictions and scores them automatically when NASA releases the passes.</div></div>
    <div class='step'><div class='n'>6</div><div><b>Go deeper.</b> The lab (lab.html) has a guided tour, field measurement, every layer and the method; world.html has the worldwide test.</div></div></div></div>
    <div class='grid2'>{img(SHOTS+'/n_map.png','World explorer: 148 places in 39 countries. Dot colour = the filter verdict.')}{img(SHOTS+'/n_look.png','Ceyhan: where to look first, with the nearest village.','height:62mm;object-fit:cover;object-position:top')}</div>
    <h2>Run it on a new place</h2><pre>python scripts/bp_check.py --lat 38.50 --lon -98.50 --name "Kansas, USA"</pre>
    <p>Finds two NISAR passes over the point in NASA's catalogue, reads only the needed part of each file, asks SMAP and POWER about the weather, and writes the filtered change map and a report. Needs a free NASA Earthdata account (section 11).</p></section>""")
    # 2 architecture
    h.append("""<section class='part'><h1 class='ptitle'>2 · Architecture</h1><h1>System architecture and technology</h1>
    <div class='pipe'><div><b>1 FIND</b>NASA CMR search: two NISAR passes on the identical orbit and grid, 12 days apart.</div><div><b>2 READ</b>HTTP byte-range reads: only the needed window, ~70 MB of a 1.9 GB HDF5 file.</div><div><b>3 WEATHER</b>SMAP soil moisture on both days, POWER rain in between.</div><div><b>4 FILTER</b>Python: speckle filter, ≥ 3 dB change, sort by soil-moisture direction.</div><div><b>5 SHOW</b>Static web app on GitHub Pages; re-checks its numbers on load.</div></div>
    <h2>Repository map</h2><table class='kv'>
    <tr><td>app/</td><td>The web app: index.html (product), lab.html (Ceyhan lab), world.html (worldwide test), tr.html (Turkish); plain HTML, CSS and JavaScript canvas, no framework; data packed as small binary files with SHA-256 checksums.</td></tr>
    <tr><td>scripts/</td><td>The pipeline: bp_check.py (filter any place), nisar_remote.py (byte-range reads), extract_window.py, extract_hls.py, build_case.py, global_scan.py / global_analyze.py / global_replication.py (worldwide test), predict_next_pass.py and predict_two_orbits.py (prediction scorers).</td></tr>
    <tr><td>research/</td><td>Pre-registered plans and results: filter rules, worldwide test and replication, the three predictions, per-site JSON.</td></tr>
    <tr><td>tests/</td><td>37 automated tests (pytest): science checks, filter rules, case integrity, global results, prediction scorer.</td></tr>
    <tr><td>docs/</td><td>Method, limitations, reproduction guide, AI use.</td></tr>
    <tr><td>sprint-reports/</td><td>Four Scrum sprint reports.</td></tr>
    <tr><td>submission/</td><td>Presentation, documentation and video sources.</td></tr></table>
    <h2>Technology</h2><table class='kv'>
    <tr><td>Data processing</td><td>Python 3 · h5py · NumPy · SciPy · rasterio · Shapely</td></tr>
    <tr><td>Data access</td><td>NASA CMR API · Earthdata Login (user's own .netrc, never stored in the repo) · HTTP range requests · NASA POWER API</td></tr>
    <tr><td>Web app</td><td>HTML · CSS · JavaScript canvas · SVG · no framework, no server, no tracking</td></tr>
    <tr><td>Hosting & CI</td><td>GitHub · GitHub Actions → GitHub Pages</td></tr>
    <tr><td>Quality</td><td>37 pytest tests · in-browser self-check of published numbers · every page tested at desktop and phone widths</td></tr>
    <tr><td>Licence</td><td>Code MIT; data under the providers' terms</td></tr></table>
    <div class='box'><b>Design choices.</b> No server and no login means anyone can open it anywhere and nothing can break after the event. Reading only byte ranges makes a 1.9 GB radar file usable on a home connection. Rules are committed before data are run so results cannot be tuned after the fact.</div></section>""")
    # 3 NASA data
    h.append("""<section class='part'><h1 class='ptitle'>3 · Data</h1><h1>NASA data sources</h1>
    <table><tr><th>Dataset</th><th>Product</th><th>Question it answers</th><th>How it is used</th></tr>
    <tr><td><b>NASA–ISRO NISAR</b></td><td>L2 GCOV v1 (VALIDATED), RTC γ⁰, 20 m · ASF DAAC · DOI 10.5067/NIL2GCOV-V1</td><td>What changed on the ground?</td><td>Two passes 12 days apart, same orbit and grid; change ≥ 3 dB flagged.</td></tr>
    <tr><td><b>NASA SMAP</b></td><td>SPL3SMP_E v006, daily, 9 km EASE-Grid 2.0 · NSIDC DAAC</td><td>Did the soil get wetter or drier?</td><td>The filter's key input: direction of soil-moisture change on the radar days.</td></tr>
    <tr><td><b>NASA POWER</b></td><td>PRECTOTCORR, daily point API · NASA LaRC</td><td>How much did it rain?</td><td>Rain between the passes, shown as context for every place.</td></tr>
    <tr><td><b>NASA HLS</b></td><td>HLSS30 v2.0, 30 m · LP DAAC · DOI 10.5067/HLS/HLSS30.002</td><td>Were plants removed?</td><td>Optical check in Ceyhan: only 9% of brightened fields lost their plants.</td></tr>
    <tr><td><b>NASA CMR</b></td><td>Common Metadata Repository API</td><td>Which passes exist?</td><td>Finds matching NISAR passes and SMAP files for any point.</td></tr></table>
    <p>Other: map context © OpenStreetMap contributors; land and country outlines from Natural Earth. ISRO is a 2026 Space Apps Space Agency Partner (NISAR is a NASA–ISRO mission). Exact files, versions and retrieval dates: section 12.</p></section>""")
    h.append("<section class='part'><h1 class='ptitle'>4 · Development process</h1><h1>How it was built: 4 Scrum sprints</h1>"
             "<p>Solo team: I was Product Owner, Developer and Scrum Master. Each sprint had a goal, a plan, a review and a public report on GitHub. "
             "The project changed direction because of what the data showed: it started as <b>“which fields changed in Ceyhan?”</b> (Sprints 1–2), "
             "the optical check showed it was mostly not harvest, so the question became <b>“was it the rain?”</b> (Sprint 3, tested worldwide with rules committed first), "
             "and the answer became a product: <b>a weather filter for radar change maps</b> (Sprint 4).</p>"
             "<table><tr><th>Sprint</th><th>Window (TRT)</th><th>Goal</th><th>Key result</th></tr>"
             "<tr><td>1</td><td>14 Nov 16:51–17:20</td><td>Problem and feasibility</td><td>NISAR passes found; 70 MB byte-range reads of 1.9 GB files; GO at 17:10</td></tr>"
             "<tr><td>2</td><td>14 Nov 17:20–18:10</td><td>Pipeline and first prototype</td><td>636 changed fields; HLS: only 9% lost plants; web app v1; 19 tests</td></tr>"
             "<tr><td>3</td><td>14 Nov 19:15–20:00</td><td>Scale the science</td><td>Rules committed first; 74 random sites, ρ = 0.58; repo and app public; 23 tests</td></tr>"
             "<tr><td>4</td><td>14 Nov 20:00–15 Nov 16:11</td><td>From study to product</td><td>Replicated (ρ = 0.55, 73 new sites); weather filter on 148 places; 3 locked predictions; 37 tests</td></tr></table>"
             "<p>The full sprint reports follow.</p>"
             + "".join(f"<div style='page-break-before:always'>{md(f'sprint-reports/sprint-{i}.md')}</div>" for i in range(1, 5))
             + "</section>")
    return h


def main():
    from playwright.sync_api import sync_playwright
    html = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Between Passes — Project Documentation</title>"
            f"<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap' rel='stylesheet'>"
            f"<style>{CSS}{FRONT_CSS}</style></head><body>"]
    parts = front()
    cover, rest = parts[0], parts[1:]
    html += rest
    for i, (title, path) in enumerate(PARTS, start=5):
        html.append(f"<section class='part'><h1 class='ptitle'>{i} · {title}</h1>{md(path)}</section>")
    html.append("</body></html>")
    src = os.path.join(HERE, "documentation.html")
    open(src, "w", encoding="utf-8").write("".join(html))
    csrc = os.path.join(HERE, "_cover.html")
    open(csrc, "w", encoding="utf-8").write(html[0].replace("<body>", "") .replace("@page { size: A4; margin: 18mm 16mm 18mm 16mm; }", "@page { size: A4; margin: 0; }") + "<body style='margin:0'>" + cover + "</body></html>")
    out = os.path.join(HERE, "Between_Passes_Documentation.pdf")
    tmp_c, tmp_b = os.path.join(HERE, "_c.pdf"), os.path.join(HERE, "_b.pdf")
    foot = ("<div style='width:100%;font:7pt Helvetica,Arial,sans-serif;color:#8d929b;padding:0 16mm;display:flex;justify-content:space-between'>"
            "<span>Between Passes · Project Documentation · Team Dusk Orbit</span><span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome")
        pg = b.new_page()
        pg.goto("file://" + csrc, wait_until="networkidle"); pg.evaluate("document.fonts.ready")
        pg.pdf(path=tmp_c, width="210mm", height="297mm", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        pg.goto("file://" + src, wait_until="networkidle"); pg.evaluate("document.fonts.ready")
        pg.pdf(path=tmp_b, format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=foot, prefer_css_page_size=True)
        b.close()
    import fitz
    d = fitz.open(tmp_c); d.insert_pdf(fitz.open(tmp_b)); d.save(out)
    for f in (tmp_c, tmp_b, csrc):
        os.remove(f)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
