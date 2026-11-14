"""Gate step: inspect structure + metadata of a remote NISAR GCOV granule.

Usage: python scripts/inspect_granule.py <GranuleUR> [out.json]
"""
import json
import sys

import h5py
import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from nisar_remote import RemoteFile, granule_url  # noqa: E402


def attrs(obj):
    out = {}
    for k, v in obj.attrs.items():
        if isinstance(v, bytes):
            v = v.decode(errors="replace")
        elif isinstance(v, np.ndarray):
            v = v.tolist()
        elif isinstance(v, np.generic):
            v = v.item()
        out[k] = v if isinstance(v, (str, int, float, list, bool)) or v is None else str(v)
    return out


def scalar(ds):
    v = ds[()]
    if isinstance(v, bytes):
        return v.decode(errors="replace")
    if isinstance(v, np.ndarray):
        if v.dtype.kind == "S":
            return [x.decode(errors="replace") for x in v.ravel()][:20]
        return v.ravel()[:20].tolist() if v.size <= 20 else f"array{v.shape} {v.dtype}"
    if isinstance(v, np.generic):
        return v.item()
    return str(v)


def main():
    gid = sys.argv[1]
    rf = RemoteFile(granule_url(gid))
    report = {"granule": gid, "file_size_bytes": rf.size}
    with h5py.File(rf, "r") as f:
        ident = f["/science/LSAR/identification"]
        report["identification"] = {k: scalar(ident[k]) for k in ident if isinstance(ident[k], h5py.Dataset)}
        grids = f["/science/LSAR/GCOV/grids"]
        report["grids"] = {}
        for freq in grids:
            g = grids[freq]
            entry = {}
            for k in g:
                obj = g[k]
                if isinstance(obj, h5py.Dataset):
                    d = {"shape": obj.shape, "dtype": str(obj.dtype), "chunks": obj.chunks,
                         "compression": obj.compression, "attrs": attrs(obj)}
                    if obj.size <= 20 or k in ("projection",):
                        d["value"] = scalar(obj)
                    if k in ("xCoordinates", "yCoordinates"):
                        d["first_last"] = [float(obj[0]), float(obj[-1])]
                    if k in ("xCoordinateSpacing", "yCoordinateSpacing", "listOfPolarizations",
                             "listOfCovarianceTerms"):
                        d["value"] = scalar(obj)
                    entry[k] = d
            report["grids"][freq] = entry
        # Calibration / processing metadata (names only + small scalars)
        meta = {}
        def visit(name, obj):
            if isinstance(obj, h5py.Dataset) and obj.size <= 8 and len(meta) < 400:
                try:
                    meta[name] = scalar(obj)
                except Exception as e:  # pragma: no cover
                    meta[name] = f"<err {e}>"
        f["/science/LSAR/GCOV/metadata"].visititems(visit)
        report["metadata_small_scalars"] = meta
    report["transfer"] = {"bytes": rf.bytes_fetched, "requests": rf.requests_made}
    out = sys.argv[2] if len(sys.argv) > 2 else None
    txt = json.dumps(report, indent=1, default=str)
    if out:
        open(out, "w").write(txt)
    print(txt[:20000])


if __name__ == "__main__":
    main()
