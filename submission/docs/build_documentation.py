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
    ("Overview", "README.md"),
    ("Method", "docs/METHOD.md"),
    ("Global test — results", "research/global/RESULTS.md"),
    ("Next-pass prediction", "research/prediction/PREDICTION.md"),
    ("Prediction 2: two other orbits", "research/prediction/PREDICTION2.md"),
    ("Limitations", "docs/LIMITATIONS.md"),
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
    # links to repo files -> GitHub
    txt = re.sub(r"\]\((?!https?://)([^)#]+)\)", lambda m: f"](https://github.com/deniz2077/between-passes/blob/main/{m.group(1)})", txt)
    return markdown.markdown(txt, extensions=["tables", "fenced_code"])


def main():
    html = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Between Passes — Project Documentation</title>"
            f"<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap' rel='stylesheet'>"
            f"<style>{CSS}</style></head><body>"]
    html.append(f"""<section class='cover'><div class='k'>NASA Space Apps Challenge 2026 · Dancing with the SARs · Project Documentation</div>
      <h1>Between Passes</h1>
      <p>A radar evidence lab on NASA-ISRO NISAR data: what changed in the fields of Ceyhan (Adana, Türkiye) between two passes, why — tested worldwide on randomly drawn NISAR sites against NASA SMAP — and a falsifiable prediction for the next pass.</p>
      <img src='file://{ROOT}/app/img/ceyhan_change.jpg'>
      <div class='meta'>Team Dusk Orbit · Deniz Efe Bulut (solo) · Niğde Local Event, Türkiye<br>
      Live app: https://deniz2077.github.io/between-passes/<br>Code &amp; data: https://github.com/deniz2077/between-passes</div></section>""")
    for title, path in PARTS:
        html.append(f"<section class='part'><h1 class='ptitle'>{title}</h1>{md(path)}</section>")
    html.append("</body></html>")
    src = os.path.join(HERE, "documentation.html")
    open(src, "w", encoding="utf-8").write("".join(html))
    out = os.path.join(HERE, "Between_Passes_Documentation.pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={out}", f"file://{src}"], check=True, capture_output=True)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
