// Between Passes — browser-side science. Mirrors scripts/bp_science.py.
// Input layers are int16 dB*100 (NODATA -32768) decoded to linear gamma-0 power.

export const NODATA = -32768;
export const DB_SCALE = 100;

export function decodeToLinear(i16) {
  const out = new Float32Array(i16.length);
  for (let i = 0; i < i16.length; i++) {
    const v = i16[i];
    out[i] = v === NODATA ? NaN : Math.pow(10, v / DB_SCALE / 10);
  }
  return out;
}

export const toDb = (lin) => (lin > 0 && Number.isFinite(lin) ? 10 * Math.log10(lin) : NaN);

/** Valid-weighted k×k boxcar mean of linear power using summed-area tables.
 *  Same definition as bp_science.boxcar_linear (zero padding outside the array). */
export function boxcarLinear(lin, valid, w, h, k) {
  const r = (k - 1) >> 1;
  const W1 = w + 1;
  const S = new Float64Array(W1 * (h + 1));
  const N = new Float64Array(W1 * (h + 1));
  for (let y = 0; y < h; y++) {
    let rs = 0, rn = 0;
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      if (valid[i]) { rs += lin[i]; rn += 1; }
      const j = (y + 1) * W1 + (x + 1);
      S[j] = S[j - W1] + rs;
      N[j] = N[j - W1] + rn;
    }
  }
  const out = new Float32Array(w * h).fill(NaN);
  for (let y = 0; y < h; y++) {
    const y0 = Math.max(0, y - r), y1 = Math.min(h, y + r + 1);
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      if (!valid[i]) continue;
      const x0 = Math.max(0, x - r), x1 = Math.min(w, x + r + 1);
      const s = S[y1 * W1 + x1] - S[y0 * W1 + x1] - S[y1 * W1 + x0] + S[y0 * W1 + x0];
      const n = N[y1 * W1 + x1] - N[y0 * W1 + x1] - N[y1 * W1 + x0] + N[y0 * W1 + x0];
      if (n > 0) out[i] = s / n;
    }
  }
  return out;
}

/** ΔdB of a region = 10 log10(mean(B)/mean(A)) over member pixels (linear power). */
export function regionChangeDb(linA, linB, members) {
  let sa = 0, sb = 0, n = 0;
  for (const i of members) { sa += linA[i]; sb += linB[i]; n++; }
  if (!n) return { n: 0, dDb: NaN, aDb: NaN, bDb: NaN };
  return { n, dDb: 10 * Math.log10(sb / sa), aDb: 10 * Math.log10(sa / n), bDb: 10 * Math.log10(sb / n) };
}

/** Pixel indices whose centres fall inside a polygon (pixel coords, x right, y down). */
export function rasterizePolygon(poly, w, h, accept) {
  const ys = poly.map((p) => p[1]);
  const yMin = Math.max(0, Math.floor(Math.min(...ys))), yMax = Math.min(h - 1, Math.ceil(Math.max(...ys)));
  const out = [];
  for (let y = yMin; y <= yMax; y++) {
    const cy = y + 0.5;
    const xs = [];
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [x1, y1] = poly[i], [x2, y2] = poly[j];
      if ((y1 > cy) !== (y2 > cy)) xs.push(x1 + ((cy - y1) * (x2 - x1)) / (y2 - y1));
    }
    xs.sort((a, b) => a - b);
    for (let k = 0; k + 1 < xs.length; k += 2) {
      const x0 = Math.max(0, Math.ceil(xs[k] - 0.5)), x1 = Math.min(w - 1, Math.floor(xs[k + 1] - 0.5));
      for (let x = x0; x <= x1; x++) { const i = y * w + x; if (!accept || accept(i)) out.push(i); }
    }
  }
  return out;
}

export function polygonAreaPx(poly) {
  let a = 0;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) a += (poly[j][0] + poly[i][0]) * (poly[j][1] - poly[i][1]);
  return Math.abs(a / 2);
}

export function quantiles(values, qs) {
  const v = Float64Array.from(values).filter(Number.isFinite).sort();
  if (!v.length) return qs.map(() => NaN);
  // numpy 'linear' interpolation
  return qs.map((q) => {
    const pos = (q / 100) * (v.length - 1);
    const lo = Math.floor(pos), hi = Math.ceil(pos);
    return v[lo] + (v[hi] - v[lo]) * (pos - lo);
  });
}

export function histogram(values, lo, hi, bins) {
  const c = new Array(bins).fill(0);
  let n = 0;
  for (const v of values) {
    if (!Number.isFinite(v)) continue;
    const b = Math.floor(((v - lo) / (hi - lo)) * bins);
    c[Math.min(bins - 1, Math.max(0, b))]++;
    n++;
  }
  return { counts: c, n, lo, hi };
}

/** Bilinear lon/lat from the shipped node grid (pixel-edge coordinates). */
export function pxToLonLat(grid, x, y) {
  const g = grid.lonlat_grid, s = g.step_px;
  const fx = Math.min(Math.max(x / s, 0), g.nx - 1.000001), fy = Math.min(Math.max(y / s, 0), g.ny - 1.000001);
  const i = Math.floor(fx), j = Math.floor(fy), tx = fx - i, ty = fy - j;
  const at = (arr, ii, jj) => arr[jj * g.nx + ii];
  const lerp = (arr) => (1 - ty) * ((1 - tx) * at(arr, i, j) + tx * at(arr, i + 1, j)) +
    ty * ((1 - tx) * at(arr, i, j + 1) + tx * at(arr, i + 1, j + 1));
  return [lerp(g.lon), lerp(g.lat)];
}
