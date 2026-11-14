"""Extract a georeferenced window of NISAR GCOV layers from a remote granule.

Usage:
  python scripts/extract_window.py <GranuleUR> <lon> <lat> <half_km> <out_dir> [freq]

Writes <out_dir>/<short>_<freq>_<layer>.tif (native UTM grid, no resampling)
and a JSON sidecar with exact provenance. Only intersecting HDF5 chunks are
transferred (HTTP Range).
"""
import json
import os
import sys
from datetime import datetime, timezone

import h5py
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform as warp_transform

sys.path.insert(0, os.path.dirname(__file__))
from nisar_remote import RemoteFile, granule_url  # noqa: E402

LAYERS = ["HHHH", "HVHV", "mask", "numberOfLooks", "rtcGammaToSigmaFactor",
          "inputDataExceptionMask"]


def main():
    gid, lon, lat, half_km, out_dir = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), \
        float(sys.argv[4]), sys.argv[5]
    freq = sys.argv[6] if len(sys.argv) > 6 else "A"
    os.makedirs(out_dir, exist_ok=True)
    short = gid.split("_")[-6][:8]  # acquisition date YYYYMMDD
    rf = RemoteFile(granule_url(gid))
    with h5py.File(rf, "r") as f:
        g = f[f"/science/LSAR/GCOV/grids/frequency{freq}"]
        epsg = int(g["projection"][()])
        x = g["xCoordinates"][:]
        y = g["yCoordinates"][:]
        dx = float(g["xCoordinateSpacing"][()])
        dy = float(g["yCoordinateSpacing"][()])
        xs, ys = warp_transform("EPSG:4326", f"EPSG:{epsg}", [lon], [lat])
        cx, cy = xs[0], ys[0]
        h = half_km * 1000.0
        c0 = int(np.searchsorted(x, cx - h))
        c1 = int(np.searchsorted(x, cx + h))
        # y decreasing
        r0 = int(np.searchsorted(-y, -(cy + h)))
        r1 = int(np.searchsorted(-y, -(cy - h)))
        sub_x, sub_y = x[c0:c1], y[r0:r1]
        # x/y are pixel centres: freq A (20 m) first x 151930 and freq B (80 m) first x 151960
        # share the same outer edge 151920 only under the centre convention.
        transform = from_origin(sub_x[0] - dx / 2, sub_y[0] - dy / 2, dx, -dy)
        side = {
            "granule": gid, "frequency": freq, "epsg": epsg, "center_lonlat": [lon, lat],
            "center_utm": [cx, cy], "half_km": half_km, "rows": [r0, r1], "cols": [c0, c1],
            "x_first_last": [float(sub_x[0]), float(sub_x[-1])],
            "y_first_last": [float(sub_y[0]), float(sub_y[-1])], "spacing": [dx, dy],
            "transform": list(transform)[:6], "source_url": granule_url(gid),
            "extracted_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "layers": {},
        }
        for name in LAYERS:
            if name not in g:
                continue
            ds = g[name]
            arr = ds[r0:r1, c0:c1]
            fill = ds.attrs.get("_FillValue")
            path = os.path.join(out_dir, f"{short}_{freq}_{name}.tif")
            with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1],
                               count=1, dtype=arr.dtype, crs=f"EPSG:{epsg}", transform=transform,
                               compress="deflate",
                               nodata=None if fill is None else float(fill)) as dst:
                dst.write(arr, 1)
            fin = np.isfinite(arr) if arr.dtype.kind == "f" else np.ones(arr.shape, bool)
            side["layers"][name] = {
                "file": os.path.basename(path), "dtype": str(arr.dtype), "shape": list(arr.shape),
                "units": (ds.attrs.get("units", b"").decode() if isinstance(ds.attrs.get("units"), bytes)
                          else ds.attrs.get("units")),
                "fill": None if fill is None else (None if np.isnan(fill) else float(fill)),
                "finite_fraction": float(fin.mean()),
                "min": float(np.nanmin(arr)) if fin.any() else None,
                "max": float(np.nanmax(arr)) if fin.any() else None,
                "unique_first20": (np.unique(arr)[:20].tolist() if arr.dtype.kind in "ui" else None),
            }
    side["transfer"] = {"bytes": rf.bytes_fetched, "requests": rf.requests_made}
    with open(os.path.join(out_dir, f"{short}_{freq}_window.json"), "w") as fh:
        json.dump(side, fh, indent=1)
    print(json.dumps({k: v for k, v in side.items() if k != "layers"}, indent=1))
    for k, v in side["layers"].items():
        print(k, v)


if __name__ == "__main__":
    main()
