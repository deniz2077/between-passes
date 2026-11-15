"""Helper for demonstrations: inside a named region (bounding box), find the centre of a NISAR frame
that already has a repeat pass in CMR, so bp_check.py reads a window well inside the swath.
Usage: python scripts/find_check_points.py west south east north
"""
import re, sys, requests
from collections import defaultdict
RX = re.compile(r"NISAR_L2_PR_GCOV_(\d{3})_(\d{3})_([AD])_(\d{3})_\d{4}_(\w{4})_A_(\d{8})T")
w, s, e, n = map(float, sys.argv[1:5])
r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json", timeout=60,
                 params=dict(short_name="NISAR_L2_GCOV_V1", bounding_box=f"{w},{s},{e},{n}", page_size=2000)).json()["feed"]["entry"]
g = defaultdict(list)
for x in r:
    m = RX.match(x["title"])
    if not m or m.group(5) not in ("DHDH", "SHSH", "QPDH"):
        continue
    pts = list(map(float, x["polygons"][0][0].split()))
    lat, lon = sum(pts[0::2]) / (len(pts) // 2), sum(pts[1::2]) / (len(pts) // 2)
    g[(m.group(2), m.group(3), m.group(4))].append((m.group(6), lat, lon))
for k, v in sorted(g.items(), key=lambda kv: max(d for d, _, _ in kv[1]), reverse=True):
    if len({d for d, _, _ in v}) >= 2:
        _, lat, lon = v[0]
        if s - 1.5 <= lat <= n + 1.5 and w - 1.5 <= lon <= e + 1.5:
            print(f"{lat:.2f} {lon:.2f} track {k[0]}{k[1]} frame {k[2]} dates {sorted({d for d, _, _ in v})}")
