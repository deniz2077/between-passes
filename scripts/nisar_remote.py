"""Read small windows of remote NISAR HDF5 granules without downloading full files.

Uses HTTP byte-range requests (authenticated via the user's ~/.netrc Earthdata
Login entry) wrapped in a seekable, block-cached file-like object that h5py can
open directly. Only the HDF5 metadata and the chunks that intersect the
requested window are transferred.
"""
from __future__ import annotations

import io
import time
from collections import OrderedDict

import requests

ASF_BASE = "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_V1"


def granule_url(granule_ur: str) -> str:
    return f"{ASF_BASE}/{granule_ur}/{granule_ur}.h5"


class RemoteFile(io.RawIOBase):
    """Seekable read-only file over HTTP Range requests with an LRU block cache."""

    def __init__(self, url: str, block_size: int = 2 * 1024 * 1024, max_blocks: int = 256,
                 session: requests.Session | None = None, timeout: float = 120):
        super().__init__()
        self.session = session or requests.Session()  # trust_env -> ~/.netrc
        self.timeout = timeout
        self.block_size = block_size
        self.max_blocks = max_blocks
        self._cache: "OrderedDict[int, bytes]" = OrderedDict()
        self.bytes_fetched = 0
        self.requests_made = 0
        # Resolve the auth redirect chain once to a signed direct URL.
        r = self.session.get(url, headers={"Range": "bytes=0-0"}, timeout=timeout,
                             allow_redirects=True)
        if r.status_code != 206:
            raise PermissionError(f"Range request failed: HTTP {r.status_code} for {url} "
                                  f"(is ~/.netrc configured for urs.earthdata.nasa.gov?)")
        self.url = r.url
        self.size = int(r.headers["Content-Range"].split("/")[-1])
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        else:
            self.pos = self.size + offset
        return self.pos

    def _block(self, i: int) -> bytes:
        if i in self._cache:
            self._cache.move_to_end(i)
            return self._cache[i]
        start = i * self.block_size
        end = min(start + self.block_size, self.size) - 1
        for attempt in range(4):
            try:
                r = self.session.get(self.url, headers={"Range": f"bytes={start}-{end}"},
                                     timeout=self.timeout)
                if r.status_code == 206:
                    break
                raise IOError(f"HTTP {r.status_code}")
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        data = r.content
        self.bytes_fetched += len(data)
        self.requests_made += 1
        self._cache[i] = data
        if len(self._cache) > self.max_blocks:
            self._cache.popitem(last=False)
        return data

    def readinto(self, b):
        n = len(b)
        if self.pos >= self.size or n == 0:
            return 0
        n = min(n, self.size - self.pos)
        out = memoryview(b)
        got = 0
        while got < n:
            i, off = divmod(self.pos + got, self.block_size)
            blk = self._block(i)
            take = min(len(blk) - off, n - got)
            out[got:got + take] = blk[off:off + take]
            got += take
        self.pos += n
        return n
