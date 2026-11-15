"""Niğde presentation: 10 standalone slides in deck_nigde.html (problem, idea, solution,
NASA data, technical infrastructure, product, local impact and proof, expected impact). Renders a PDF.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main():
    src = os.path.join(HERE, "deck_nigde.html")
    out = os.path.join(HERE, "Between_Passes_Nigde_Presentation.pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={out}", f"file://{src}"], check=True, capture_output=True)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
