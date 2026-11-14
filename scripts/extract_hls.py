"""Optical cross-check: NASA HLS (Harmonized Landsat Sentinel-2) NDVI on the radar grid.

For each date, mosaics the given HLS S30 granules (red B04, NIR-narrow B8A, Fmask),
reprojects them onto the exact NISAR 20 m UTM 37N window grid, and writes
data/raw/hls/<date>_{ndvi,clear,water}.tif plus a JSON sidecar.

Auth: the user's ~/.netrc Earthdata entry (GDAL /vsicurl/ with cookies).
Usage: python scripts/extract_hls.py
"""
import json
import os
import tempfile

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data/raw/hls")
GRID_REF = os.path.join(ROOT, "data/raw/win_A/20261022_A_HHHH.tif")
LP = "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/HLSS30.020"
SCENES = {
    # Tile 36SYF only: a consistent same-tile pair (23 Oct, 0% cloud -> 2 Nov).
    # Sensitivity run (14 Nov): adding northern tile 36SYG with a 21 Oct baseline raised coverage to 86%
    # but produced a visible NDVI seam (north 14.3% vs south 9.0% vegetation loss among brightened
    # objects), so it is excluded from published results. See DECISIONS.md.
    "20261023": ["HLS.S30.T36SYF.2026296T082011.v2.0"],
    "20261102": ["HLS.S30.T36SYF.2026306T082551.v2.0"],
}
# HLS v2 Fmask bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice, 5 water
BAD_BITS = (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)
WATER_BIT = 1 << 5


def main():
    os.makedirs(OUT, exist_ok=True)
    jar = os.path.join(tempfile.gettempdir(), "bp_hls_cookies.txt")
    env = dict(GDAL_HTTP_NETRC="YES", GDAL_HTTP_COOKIEFILE=jar, GDAL_HTTP_COOKIEJAR=jar,
               GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
               GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2")
    with rasterio.open(GRID_REF) as ref:
        dst_crs, dst_tr, H, W = ref.crs, ref.transform, ref.height, ref.width
    with rasterio.Env(**env):
        for date, grans in SCENES.items():
            red = np.full((H, W), np.nan, np.float32)
            nir = np.full((H, W), np.nan, np.float32)
            fm = np.full((H, W), 255, np.uint8)
            used = []
            for g in grans:
                url = lambda b: f"/vsicurl/{LP}/{g}/{g}.{b}.tif"
                bands = {}
                for b, rs, dtype, fill in (("B04", Resampling.average, np.float32, np.nan),
                                           ("B8A", Resampling.average, np.float32, np.nan),
                                           ("Fmask", Resampling.mode, np.uint8, 255)):
                    with rasterio.open(url(b)) as src:
                        arr = np.full((H, W), fill, dtype)
                        reproject(rasterio.band(src, 1), arr, dst_transform=dst_tr, dst_crs=dst_crs,
                                  dst_nodata=fill, resampling=rs,
                                  src_nodata=src.nodata if src.nodata is not None else (-9999 if b != "Fmask" else 255))
                        bands[b] = arr
                take = np.isfinite(bands["B04"]) & np.isfinite(bands["B8A"]) & (bands["Fmask"] != 255) & np.isnan(red)
                red[take] = bands["B04"][take] * 1e-4
                nir[take] = bands["B8A"][take] * 1e-4
                fm[take] = bands["Fmask"][take]
                used.append({"granule": g, "pixels_filled": int(take.sum())})
            clear = (fm != 255) & ((fm & BAD_BITS) == 0) & np.isfinite(red) & np.isfinite(nir) & \
                (red > 0) & (nir > 0)
            ndvi = np.full((H, W), np.nan, np.float32)
            ndvi[clear] = (nir[clear] - red[clear]) / (nir[clear] + red[clear])
            water = clear & ((fm & WATER_BIT) > 0)
            prof = dict(driver="GTiff", height=H, width=W, count=1, crs=dst_crs, transform=dst_tr, compress="deflate")
            with rasterio.open(os.path.join(OUT, f"{date}_ndvi.tif"), "w", dtype="float32", nodata=np.nan, **prof) as d:
                d.write(ndvi, 1)
            for name, arr in (("clear", clear), ("water", water)):
                with rasterio.open(os.path.join(OUT, f"{date}_{name}.tif"), "w", dtype="uint8", **prof) as d:
                    d.write(arr.astype(np.uint8), 1)
            meta = {"date": date, "granules": used, "collection": "HLSS30 v2.0 (DOI 10.5067/HLS/HLSS30.002)",
                    "bands": "NDVI=(B8A-B04)/(B8A+B04), surface reflectance scale 1e-4",
                    "resampling": "average (reflectance), mode (Fmask) onto NISAR 20 m UTM37N grid",
                    "fmask_excluded_bits": "cloud(1), adjacent(2), shadow(3), snow/ice(4)",
                    "clear_fraction": float(clear.mean()), "ndvi_median": float(np.nanmedian(ndvi)) if clear.any() else None}
            json.dump(meta, open(os.path.join(OUT, f"{date}_hls.json"), "w"), indent=1)
            print(json.dumps(meta))


if __name__ == "__main__":
    main()
