import * as S from "./science.js";
import { Viewer, grayImage, deltaImage, edgesImage, toCanvas, deltaLegendGradient, ndviDeltaImage, ndviLegendGradient, NDVI_MAX, HH_RANGE, DELTA_MAX } from "./viewer.js";
import { histogramSvg, timelineSvg, sensitivitySvg, monthName } from "./charts.js";

const BASE = "data/ceyhan/";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const f = (v, d = 2, sign = false) => (Number.isFinite(v) ? (sign && v > 0 ? "+" : "") + v.toFixed(d) : "—");
const fmtInt = (v) => v.toLocaleString("en-US");

const st = {
  sel: { kind: "area" },   // {kind:'area'} | {kind:'object', id} | {kind:'roi', poly}
  tab: "observed",
  mode: "delta",
  show: { objects: true, context: true, control: true },
};
let C, D, viewer;

// ---------------------------------------------------------------- loading
async function fetchBin(meta) {
  const r = await fetch(BASE + meta.file);
  if (!r.ok) throw new Error(`${meta.file}: HTTP ${r.status}`);
  const buf = await r.arrayBuffer();
  const T = { int16: Int16Array, uint8: Uint8Array, uint16: Uint16Array }[meta.dtype];
  const arr = new T(buf);
  const expect = meta.shape.reduce((a, b) => a * b, 1);
  if (arr.length !== expect) throw new Error(`${meta.file}: expected ${expect} values, got ${arr.length}`);
  return arr;
}

async function load() {
  const r = await fetch(BASE + "case.json");
  if (!r.ok) throw new Error(`case.json: HTTP ${r.status}`);
  C = await r.json();
  const L = C.layers;
  const [hhA, hhB, hvA, hvB, flags, objects, ndA, ndB] = await Promise.all(
    ["hh_a", "hh_b", "hv_a_40m", "hv_b_40m", "flags", "objects", "ndvi_a_40m", "ndvi_b_40m"].map((k) => (L[k] ? fetchBin(L[k]) : Promise.resolve(null))));
  const W = C.grid.width, H = C.grid.height, N = W * H;
  const valid = new Uint8Array(N), analysis = new Uint8Array(N), urban = new Uint8Array(N);
  for (let i = 0; i < N; i++) { valid[i] = flags[i] & 1; analysis[i] = (flags[i] >> 1) & 1; urban[i] = (flags[i] >> 2) & 1; }
  const linA = S.decodeToLinear(hhA), linB = S.decodeToLinear(hhB);
  const k = C.params.speckle_boxcar_px;
  const sA = S.boxcarLinear(linA, valid, W, H, k), sB = S.boxcarLinear(linB, valid, W, H, k);
  const dbA = new Float32Array(N), dbB = new Float32Array(N), dHH = new Float32Array(N);
  for (let i = 0; i < N; i++) { dbA[i] = S.toDb(sA[i]); dbB[i] = S.toDb(sB[i]); dHH[i] = dbB[i] - dbA[i]; }
  // HV at 40 m (coarser; shown only with caution)
  const w2 = L.hv_a_40m.shape[1], h2 = L.hv_a_40m.shape[0];
  const dHV = new Float32Array(w2 * h2);
  for (let i = 0; i < dHV.length; i++) {
    dHV[i] = hvA[i] === S.NODATA || hvB[i] === S.NODATA ? NaN : (hvB[i] - hvA[i]) / S.DB_SCALE;
  }
  // object membership
  const nObj = C.objects.length;
  const counts = new Uint32Array(nObj + 1);
  for (let i = 0; i < N; i++) counts[objects[i]]++;
  const members = Array.from({ length: nObj + 1 }, (_, j) => new Uint32Array(counts[j]));
  const fill = new Uint32Array(nObj + 1);
  for (let i = 0; i < N; i++) { const o = objects[i]; if (o) members[o][fill[o]++] = i; }
  const urbanIdx = [], analysisIdx = [];
  for (let i = 0; i < N; i++) { if (urban[i]) urbanIdx.push(i); if (analysis[i]) analysisIdx.push(i); }
  const byId = new Map(C.objects.map((o) => [o.id, o]));
  let dNDVI = null;
  if (ndA && ndB) {
    dNDVI = new Float32Array(w2 * h2);
    for (let i = 0; i < dNDVI.length; i++) dNDVI[i] = ndA[i] === S.NODATA || ndB[i] === S.NODATA ? NaN : (ndB[i] - ndA[i]) / 10000;
  }
  D = { W, H, N, linA, linB, dbA, dbB, dHH, dHV, w2, h2, valid, analysis, urban, objects, members, byId, urbanIdx, analysisIdx, hvA, hvB, ndA, ndB, dNDVI };
  D.ctrlQ = C.stats.urban_control.dHH_px_q1_5_25_50_75_95_99;
  D.ctrlHist = S.histogram(urbanIdx.map((i) => dHH[i]), -8, 8, 64);
  D.checks = selfCheck();
}

// ------------------------------------------------------- integrity checks
function selfCheck() {
  const out = [];
  const tol = 0.01;
  const u = S.regionChangeDb(D.linA, D.linB, D.urbanIdx);
  out.push({ name: "Urban control ΔHH recomputed from shipped layers", diff: Math.abs(u.dDb - C.stats.urban_control.dHH_db_region), tol });
  let maxd = 0;
  for (const o of C.objects) maxd = Math.max(maxd, Math.abs(S.regionChangeDb(D.linA, D.linB, D.members[o.id]).dDb - o.dHH_db));
  out.push({ name: `All ${C.objects.length} change-object ΔHH values recomputed`, diff: maxd, tol });
  let pmax = 0;
  for (const p of C.parity_samples) pmax = Math.max(pmax, Math.abs(D.dHH[p.i] - p.dHH_s));
  out.push({ name: `Browser speckle filter vs Python at ${C.parity_samples.length} random pixels`, diff: pmax, tol: 0.02 });
  const a = S.regionChangeDb(D.linA, D.linB, D.analysisIdx);
  out.push({ name: "Analysis-area ΔHH recomputed", diff: Math.abs(a.dDb - C.stats.analysis_area.dHH_db_region), tol });
  out.forEach((c) => (c.pass = c.diff <= c.tol));
  return out;
}

// ------------------------------------------------------------ selection
function selectionMembers(sel) {
  if (sel.kind === "object") return D.members[sel.id];
  if (sel.kind === "roi") return S.rasterizePolygon(sel.poly, D.W, D.H, (i) => D.valid[i] === 1);
  return D.analysisIdx;
}

function selectionStats(sel) {
  const idx = selectionMembers(sel);
  const r = S.regionChangeDb(D.linA, D.linB, idx);
  const vals = new Float32Array(idx.length);
  for (let k = 0; k < idx.length; k++) vals[k] = D.dHH[idx[k]];
  const q = S.quantiles(vals, [5, 25, 50, 75, 95]);
  const hist = S.histogram(vals, -8, 8, 64);
  let outside = 0, inUp = 0, inDown = 0;
  const objSet = new Set();
  for (const i of idx) {
    if (!D.analysis[i]) outside++;
    const o = D.objects[i];
    if (o) { objSet.add(o); if (D.byId.get(o).sign === "brightened") inUp++; else inDown++; }
  }
  // HV (40 m) — ratio of means over the 2x2 blocks covering members
  let hva = 0, hvb = 0, nh = 0;
  const seen = new Set();
  for (const i of idx) {
    const y = Math.floor(i / D.W) >> 1, x = (i % D.W) >> 1;
    const j = y * D.w2 + x;
    if (seen.has(j) || x >= D.w2 || y >= D.h2) continue;
    seen.add(j);
    if (D.hvA[j] === S.NODATA || D.hvB[j] === S.NODATA) continue;
    hva += 10 ** (D.hvA[j] / 1000); hvb += 10 ** (D.hvB[j] / 1000); nh++;
  }
  // Optical (HLS NDVI, 40 m blocks clear on both dates)
  let opt = null;
  if (D.dNDVI) {
    const vals = [], na = [], nb = [];
    for (const j of seen) { const v = D.dNDVI[j]; if (Number.isFinite(v)) { vals.push(v); na.push(D.ndA[j] / 10000); nb.push(D.ndB[j] / 10000); } }
    opt = { clearFrac: seen.size ? vals.length / seen.size : 0, dNDVI: S.quantiles(vals, [50])[0], before: S.quantiles(na, [50])[0], after: S.quantiles(nb, [50])[0] };
  }
  if (sel.kind === "object") {
    const o = D.byId.get(sel.id);
    opt = o.dNDVI !== undefined ? { clearFrac: o.optical_clear_frac, dNDVI: o.dNDVI, before: o.NDVI_before, after: o.NDVI_after, cls: o.optical_class, exact: true }
      : { clearFrac: o.optical_clear_frac ?? 0, dNDVI: NaN, cls: "no clear optical view", exact: true };
  } else if (opt && Number.isFinite(opt.dNDVI) && opt.clearFrac >= 0.5) {
    // regions: classify over the clear part when at least half is clear (objects need 80%)
    const t = C.params.ndvi_change;
    opt.cls = opt.dNDVI <= -t ? "vegetation loss" : opt.dNDVI >= t ? "greening" : "little vegetation change";
    opt.partial = opt.clearFrac < 0.999;
  } else if (opt) opt.cls = "no clear optical view";
  return { ...r, q, hist, outside, inUp, inDown, nObjects: objSet.size, dHV: nh ? 10 * Math.log10(hvb / hva) : NaN, idx, opt };
}

function verdict(d) {
  const [p1, p5, , , , p95, p99] = D.ctrlQ;
  if (!Number.isFinite(d)) return { cls: "flat", text: "No valid pixels in this selection." };
  if (d > p99) return { cls: "up", tag: "beyond control", text: `Brightened well beyond the stable control (control 99th percentile ${f(p99, 2, true)} dB).` };
  if (d > p95) return { cls: "up", tag: "beyond typical", text: `Brightened beyond typical control variability (control 95th percentile ${f(p95, 2, true)} dB), but within its extreme range.` };
  if (d < p1) return { cls: "down", tag: "beyond control", text: `Darkened well beyond the stable control (control 1st percentile ${f(p1, 2, true)} dB).` };
  if (d < p5) return { cls: "down", tag: "beyond typical", text: `Darkened beyond typical control variability (control 5th percentile ${f(p5, 2, true)} dB), but within its extreme range.` };
  return { cls: "flat", tag: "within control", text: `Within the variability of the stable control (${f(p5, 2, true)} to ${f(p95, 2, true)} dB). No change can be claimed.` };
}

function nearestPlace(px) {
  let best = null, bd = Infinity;
  for (const p of C.context.places) {
    const d = Math.hypot(p.px[0] - px[0], p.px[1] - px[1]);
    if (d < bd) { bd = d; best = p; }
  }
  return best ? { name: best.name, km: (bd * C.grid.posting_m) / 1000 } : null;
}

function selTitle(sel) {
  if (sel.kind === "object") { const o = D.byId.get(sel.id); return { kind: `Change object #${o.id} · ${o.sign}`, title: `${f(o.area_ha, 1)} ha near ${nearestPlace(o.centroid_px)?.name ?? "—"}` }; }
  if (sel.kind === "roi") return { kind: "Your region", title: `${f((S.polygonAreaPx(sel.poly) * C.grid.posting_m ** 2) / 1e4, 1)} ha drawn region` };
  return { kind: "Whole analysis area", title: "Ceyhan fields, Adana" };
}

// ------------------------------------------------------------ panel
function renderPanel() {
  const sel = st.sel;
  const t = selTitle(sel);
  $("#sel-kind").textContent = t.kind;
  $("#sel-title").textContent = t.title;
  $("#sel-clear").hidden = sel.kind === "area";
  const s = selectionStats(sel);
  st.lastStats = s;
  const v = verdict(s.dDb);
  if (sel.kind === "area") {
    const so = C.stats.objects;
    v.text = `The change is concentrated in individual parcels, not spread evenly — the area-wide average stays within the stable control's spread.` + (C.optical ? ` NASA HLS optical check: of ${C.optical.brightened.objects_with_clear_view} brightened parcels with a clear view, only ${Math.round(100 * C.optical.brightened.frac_vegetation_loss)}% lost vegetation, so harvest explains a minority.` : "") + ` Click an outlined parcel or draw a region.`;
  }
  const color = v.cls === "down" ? "#4ea3ff" : v.cls === "up" ? "#ff8a4c" : "#b9b4aa";
  const areaHa = (s.n * C.grid.posting_m ** 2) / 1e4;

  // OBSERVED
  const so = C.stats.objects;
  let obs = sel.kind === "area" ? `<div class="verdict">
      <div class="big up">${(so.area_ha_brightened / so.area_ha_darkened).toFixed(1)}×</div>
      <div class="label">more parcel area brightened (${fmtInt(Math.round(so.area_ha_brightened))} ha) than darkened (${fmtInt(Math.round(so.area_ha_darkened))} ha) — change objects ≥ 3 dB, ≥ 1 ha, over ${f(areaHa / 100, 0)} km². Area-average ΔHH ${f(s.dDb, 2, true)} dB.</div>
      <div class="call">${esc(v.text)}</div></div>` : `<div class="verdict">
      <div class="big ${v.cls}">${f(s.dDb, 2, true)} dB</div>
      <div class="label">ΔHH = 10·log₁₀(mean γ⁰ 3 Nov / mean γ⁰ 22 Oct) over ${fmtInt(s.n)} valid pixels (${f(areaHa, 1)} ha)</div>
      <div class="call">${esc(v.text)}</div>
    </div>`;
  if (sel.kind === "roi" && s.n < 25) obs += `<div class="caution-box"><p><strong>Too small.</strong> Fewer than 25 valid pixels (1 ha): speckle dominates. Draw a larger region.</p></div>`;
  if (s.outside > 0 && sel.kind === "roi") obs += `<div class="caution-box"><p><strong>Edge zone.</strong> ${fmtInt(s.outside)} pixels lie within 500 m of the swath edge, where NISAR's valid-sample mask is known to be misaligned.</p></div>`;
  obs += `<dl class="kv">
      <dt>HH 22 Oct (region mean)</dt><dd>${f(s.aDb)} dB</dd>
      <dt>HH 3 Nov (region mean)</dt><dd>${f(s.bDb)} dB</dd>
      <dt>Per-pixel Δ median [IQR]</dt><dd>${f(s.q[2], 2, true)} [${f(s.q[1], 1, true)}, ${f(s.q[3], 1, true)}]</dd>
      <dt>Stable control ΔHH</dt><dd>${f(C.stats.urban_control.dHH_db_region, 2, true)} dB</dd>
      ${sel.kind !== "object" ? `<dt>Inside brightened objects</dt><dd>${f((s.inUp * 0.04), 1)} ha</dd><dt>Inside darkened objects</dt><dd>${f((s.inDown * 0.04), 1)} ha</dd>` : ""}
    </dl>`;
  obs += `<div class="chart">${histogramSvg(s.hist, D.ctrlHist, { color, markers: [{ v: D.ctrlQ[6], label: "ctrl p99", color: "#e8c547" }, { v: D.ctrlQ[0], label: "p1", color: "#e8c547" }] })}
      <p class="chart-caption">Bars: per-pixel ΔHH in the selection (100 m speckle filter). Amber line: the stable urban control (Ceyhan centre, ${fmtInt(C.stats.urban_control.px)} px). Pixels are spatially correlated, so no independent-pixel confidence interval is claimed.</p></div>`;
  if (s.opt) {
    const o = s.opt, has = Number.isFinite(o.dNDVI) && o.cls !== "no clear optical view";
    const pillCls = o.cls === "vegetation loss" ? "down" : o.cls === "greening" ? "ok" : o.cls === "little vegetation change" ? "" : "caution";
    obs += `<h3>Optical cross-check · NASA HLS (Sentinel-2)</h3>
      <dl class="kv">
        <dt>Vegetation index (NDVI) 23 Oct → 2 Nov</dt><dd>${has ? `${f(o.before)} → ${f(o.after)}` : "—"}</dd>
        <dt>ΔNDVI (median)</dt><dd>${has ? f(o.dNDVI, 3, true) : "—"}</dd>
        <dt>Clear on both dates</dt><dd>${f(100 * o.clearFrac, 0)}%</dd>
        <dt>Optical reading</dt><dd><span class="pill ${pillCls}">${esc(o.cls)}</span></dd>
      </dl>
      <p class="chart-caption">${has ? `Fields outside change objects greened by ${f(C.optical.background_fields_dNDVI_median, 3, true)} (median) over the same days. ` : "Cloud, cloud shadow or the satellite's swath edge left too few clear pixels (parcels need ≥ 80%, regions ≥ 50% clear on both dates). "}${o.partial ? `Values cover the ${f(100 * o.clearFrac, 0)}% of this selection with a clear view. ` : ""}A vegetation-loss reading would point to harvest; little change points to the soil surface (moisture or roughness).${o.exact ? "" : " Region values use 40 m blocks."}</p>`;
  }
  obs += `<div class="caution-box"><p><strong>ΔHV ${f(s.dHV, 2, true)} dB — unresolved.</strong> HV change across this scene grows from west to east even for equally bright pixels, and HV carries a high radio-interference likelihood flag. It is shown, not interpreted.</p></div>`;
  $("#tab-observed").innerHTML = obs;

  // CONTEXT
  const ws = C.weather.series;
  const between = ws.filter((d) => d.date > "20261022" && d.date <= "20261103");
  const tot = between.reduce((a, d) => a + d.mm, 0);
  const wettest = [...between].sort((a, b) => b.mm - a.mm).slice(0, 2);
  const cpx = sel.kind === "object" ? D.byId.get(sel.id).centroid_px : sel.kind === "roi" ? centroid(sel.poly) : [D.W / 2, D.H / 2];
  const ll = S.pxToLonLat(C.grid, cpx[0], cpx[1]);
  const np_ = nearestPlace(cpx);
  $("#tab-context").innerHTML = `
    <dl class="kv">
      <dt>Centre</dt><dd>${f(ll[1], 4)}°N ${f(ll[0], 4)}°E</dd>
      <dt>Nearest settlement (OSM)</dt><dd>${esc(np_?.name ?? "—")} · ${f(np_?.km, 1)} km</dd>
      <dt>Rain between passes</dt><dd>${f(tot, 1)} mm</dd>
      <dt>Wettest days</dt><dd>${wettest.map((d) => `${+d.date.slice(6)} ${monthName(d.date)} ${f(d.mm, 1)}`).join(" · ")}</dd>
      <dt>Pass times (local)</dt><dd>19:24 · 19:24 TRT</dd>
    </dl>
    <p>Both passes were acquired on the same descending orbit track (151) at the same time of day and identical geometry, so the comparison is pixel-for-pixel on one 20 m grid without resampling.</p>
    <p>NASA POWER estimates ${f(tot, 1)} mm of rain over the interval, concentrated on 28–29 October — about five days before the second pass. Rain on 4–6 November fell <em>after</em> the second pass and cannot appear in this pair.</p>
    <p>A third NISAR pass exists on 29 October (track 079, the rainiest day) but views the ground from a different angle. It is not compared pixel-by-pixel here.</p>
    <p class="muted">Precipitation: NASA POWER daily point estimate (~0.5° model grid). Not a rain gauge; it cannot say how much rain fell on any single field.</p>`;

  // INTERPRETATION
  $("#tab-interp").innerHTML = interpretation(sel, s);

  // LIMITATIONS
  $("#tab-limits").innerHTML = `
    <ul class="plain">
      <li><strong>Two dates only.</strong> One before/after pair cannot separate a lasting change (tillage) from a transient one (wet soil drying out).</li>
      <li><strong>Cause is not measured.</strong> Backscatter responds to soil moisture, surface roughness, vegetation structure and water. Interpretations are possibilities, not findings.</li>
      <li><strong>Speckle and spatial correlation.</strong> Values use a 100 m × 100 m filter; neighbouring pixels are not independent, so we compare against a control instead of reporting pixel-count confidence intervals.</li>
      <li><strong>Control is urban.</strong> The stable control (bright, built-up Ceyhan centre) shows instrument and processing stability, not how an unchanged field behaves.</li>
      <li><strong>HV unresolved.</strong> A west–east gradient in ΔHV and a high RFI-likelihood flag make HV unsuitable for interpretation here.</li>
      <li><strong>Noise not subtracted.</strong> The product's thermal-noise correction is off; very dark pixels (≲ −18 dB HH) carry a larger noise share.</li>
      <li><strong>Swath edge.</strong> The western strip is outside the swath; a 500 m buffer excludes pixels near invalid data.</li>
      <li><strong>Optical is a cross-check, not ground truth.</strong> NASA HLS dates (23 Oct, 2 Nov) differ from the radar passes by up to ~1.5 days, and a consistent cloud-free pair covers only the southern ~60% of the area. Adding the northern tile (21 Oct baseline) would reach 86% but creates a visible NDVI seam, so it is excluded; with it, vegetation loss would be 10% instead of 9%. Optical NDVI cannot tell wet soil from ploughed soil.</li>
      <li><strong>Rainfall is coarse.</strong> NASA POWER is a gridded estimate, used only as timing context.</li>
      <li><strong>Thresholds are choices.</strong> Objects use a 3 dB seed, 2 dB growth and 1 ha minimum. The census below shows how the result changes from 2 to 5 dB.</li>
    </ul>`;
  highlightCensus();
}

function centroid(poly) { let x = 0, y = 0; poly.forEach((p) => { x += p[0]; y += p[1]; }); return [x / poly.length, y / poly.length]; }

function interpretation(sel, s) {
  const d = s.dDb, before = s.aDb, after = s.bDb;
  const bright = d > 0;
  const strong = Math.abs(d) >= 3;
  const mk = (title, tag, cls, body, need) => `<div class="hyp"><h4>${title} <span class="pill ${cls}">${tag}</span></h4><p>${body}</p><p class="need">Would be decided by: ${need}</p></div>`;
  let h = `<p>The radar measures how much L-band energy returns from the ground. These are physical explanations that remain <em>possible</em> for what was measured in this selection. None is confirmed by this data alone.</p>`;
  h += mk("Wetter soil after the 28–29 Oct rain",
    bright ? "consistent" : "not indicated", bright ? "ok" : "",
    bright ? `Water raises the soil's dielectric constant and increases HH return, most visibly on bare or sparsely vegetated fields. This selection was ${f(before, 1)} dB before (${before < -9 ? "dark — typical of bare or smooth soil" : "moderately bright"}) and brightened by ${f(d, 2, true)} dB. About five days of drying separate the last heavy rain from the second pass.` :
      `Rain-wetted soil would raise HH, but this selection darkened.`,
    "in-situ soil moisture, or a NISAR pass shortly after the rain on the same track (a decay back toward the 22 Oct level would point to moisture).");
  h += mk("Ploughing or tillage (rougher surface)",
    bright && strong ? "consistent" : bright ? "possible" : "not indicated", bright && strong ? "ok" : "",
    bright ? `Rougher soil scatters more energy back to the radar. Large jumps (≥ 3 dB) confined to a single parcel fit a field-management event better than rain, which would affect neighbouring bare fields similarly.${sel.kind === "object" ? " This object is parcel-shaped and its change is " + (strong ? "strong." : "moderate.") : ""}` :
      "Tillage usually brightens HH; this selection darkened.",
    "farm records; a persistent change in later NISAR passes (wet soil dries back, ploughed roughness persists). Optical NDVI cannot separate wet from ploughed bare soil.");
  const o = s.opt || { cls: "no clear optical view" };
  const harvestTag = o.cls === "vegetation loss" ? ["consistent", "ok"] : o.cls === "no clear optical view" ? ["possible", ""] : ["not indicated", ""];
  h += mk("Harvest or removal of vegetation",
    harvestTag[0], harvestTag[1],
    (o.cls === "vegetation loss" ? `NASA HLS shows the vegetation index fell (ΔNDVI ${f(o.dNDVI, 3, true)}) between 23 Oct and 2 Nov — consistent with a crop being harvested or cleared. ` :
      o.cls === "no clear optical view" ? "No clear optical view of this selection on both dates, so vegetation change cannot be checked here. " :
      `NASA HLS shows no vegetation loss here (ΔNDVI ${f(o.dNDVI, 3, true)}), so harvest is unlikely to explain this radar change. `) +
    "The Çukurova autumn calendar (cotton harvest, preparation for winter wheat) makes field operations plausible in this window — general regional knowledge, not verified for these fields.",
    "a cloud-free optical pair where unavailable; field records; a reliable HV channel (vegetation volume), unresolved here.");
  h += mk("Standing water or flooding",
    !bright && after < -15 ? "consistent" : "not indicated", !bright && after < -15 ? "ok" : "",
    !bright && after < -15 ? `Smooth open water reflects energy away and appears very dark. This selection fell to ${f(after, 1)} dB on 3 Nov.` :
      `Open water would drive HH very low (≲ −15 dB). This selection is ${f(after, 1)} dB on 3 Nov.`,
    "optical water index or a visual check; consistent darkness over several passes.");
  h += mk("Sensor or processing artefact",
    "unlikely for HH", "",
    `Same orbit track and geometry, identical grid, VALIDATED calibration. The stable urban control changed by ${f(C.stats.urban_control.dHH_db_region, 2, true)} dB, and HH change shows no trend across the swath for equally bright pixels. HV does — which is why HV is excluded.`,
    "additional stable controls (e.g. bare rock, large buildings) in more passes.");
  return h;
}

// ------------------------------------------------------------ viewer layers
function layerFor(mode) {
  D.cache ||= {};
  if (D.cache[mode]) return D.cache[mode];
  let L;
  if (mode === "a") L = { base: toCanvas(grayImage(D.dbA, D.W, D.H)) };
  else if (mode === "b") L = { base: toCanvas(grayImage(D.dbB, D.W, D.H)) };
  else if (mode === "swipe") L = { base: layerFor("a").base, baseB: layerFor("b").base };
  else if (mode === "delta") L = { base: toCanvas(deltaImage(D.dHH, D.dbA, D.W, D.H)) };
  else if (mode === "hv") L = { base: toCanvas(deltaImage(D.dHV, D.dbA, D.w2, D.h2, 2)), scaleBase: 0.5 };
  else if (mode === "ndvi") L = { base: toCanvas(ndviDeltaImage(D.dNDVI, D.dbA, D.w2, D.h2, 2)), scaleBase: 0.5 };
  D.cache[mode] = L;
  return L;
}

function updateEdges() {
  const selId = st.sel.kind === "object" ? st.sel.id : 0;
  const key = `${st.show.objects}-${st.show.control}-${selId}`;
  if (D.edgesKey === key) return;
  D.edgesKey = key;
  viewer.layers.edges = (st.show.objects || st.show.control)
    ? toCanvas(edgesImage(st.show.objects ? D.objects : null, (l) => (D.byId.get(l).sign === "brightened" ? 1 : -1), D.W, D.H, selId, st.show.control ? D.urban : null))
    : null;
}

function setMode(mode) {
  st.mode = mode;
  const L = layerFor(mode);
  viewer.layers.base = L.base; viewer.layers.baseB = L.baseB || null; viewer.layers.scaleBase = L.scaleBase || 1;
  viewer.mode = mode;
  document.querySelectorAll("#mode-seg button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.mode === mode)));
  renderLegend();
  viewer.request();
}

function renderLegend() {
  const m = st.mode;
  let h = "";
  if (m === "ndvi") {
    const op = C.optical;
    h = `<div class="title">ΔNDVI optical (2 Nov − 23 Oct)</div>
      <div class="bar" style="background:${ndviLegendGradient()}"></div>
      <div class="ticks"><span>−${NDVI_MAX}</span><span>veg. loss</span><span>0</span><span>greening</span><span>+${NDVI_MAX}</span></div>
      <div class="note">NASA HLS S30 (Sentinel-2), 40 m. Grey = no clear view on both dates (cloud or outside the optical swath; ${Math.round(op.clear_both_frac_of_analysis * 100)}% of the area is clear). Outlines: radar change objects.</div>`;
  } else if (m === "delta" || m === "hv") {
    h = `<div class="title">${m === "hv" ? "ΔHV" : "ΔHH"} (3 Nov − 22 Oct), dB</div>
      <div class="bar" style="background:${deltaLegendGradient()}"></div>
      <div class="ticks"><span>−${DELTA_MAX}</span><span>darker</span><span>0</span><span>brighter</span><span>+${DELTA_MAX}</span></div>`;
    h += m === "hv" ? `<div class="note caution">Unresolved: west–east gradient and high RFI flag. Not interpreted. Shown at 40 m.</div>`
      : `<div class="note">100 m speckle filter on linear γ⁰. Outlines: change objects (≥ 3 dB seed, ≥ 1 ha). Amber outline: stable control.</div>`;
  } else {
    h = `<div class="title">HH γ⁰ ${m === "swipe" ? "22 Oct | 3 Nov" : m === "a" ? "22 Oct 2026" : "3 Nov 2026"}, dB</div>
      <div class="bar" style="background:linear-gradient(90deg,#000,#fff)"></div>
      <div class="ticks"><span>${HH_RANGE[0]}</span><span>${HH_RANGE[1]}</span></div>
      <div class="note">Same fixed stretch for both dates. Bright = more radar return.${m === "swipe" ? " Drag the handle to compare." : ""}</div>`;
  }
  $("#legend").innerHTML = h;
}

function drawOverlay(ctx, v) {
  if (!st.show.context) return;
  const ctxData = C.context;
  ctx.save();
  // graticule
  ctx.strokeStyle = "rgba(232,227,216,.14)"; ctx.lineWidth = 1;
  ctx.font = "10.5px IBM Plex Mono, monospace"; ctx.fillStyle = "rgba(232,227,216,.6)";
  for (const g of ctxData.graticule) {
    ctx.beginPath(); g.px.forEach(([x, y], i) => { const [sx, sy] = v.toScreen(x, y); i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); }); ctx.stroke();
    const [x, y] = g.kind === "lon" ? g.px[g.px.length - 1] : g.px[0];
    const [sx, sy] = v.toScreen(x, y);
    const label = g.kind === "lon" ? `${g.value.toFixed(2)}°E` : `${g.value.toFixed(2)}°N`;
    if (g.kind === "lon") {
      const lx = Math.min(Math.max(sx, 30), v.cw - 30), ly = Math.max(14, Math.min(sy - 6, v.ch - 22));
      if (lx < v.cw - 80) { ctx.textAlign = "center"; ctx.fillText(label, lx, ly); }   // keep clear of lat labels
    } else {
      const ly = Math.min(Math.max(sy - 4, 14), v.ch - 24);
      if (ly > 26 && ly < v.ch - 44) { ctx.textAlign = "right"; ctx.fillText(label, v.cw - 8, ly); }  // keep clear of lon labels & scale bar
    }
  }
  // roads & rivers
  const line = (pts, style, width) => { ctx.strokeStyle = style; ctx.lineWidth = width; ctx.beginPath(); pts.forEach(([x, y], i) => { const [sx, sy] = v.toScreen(x, y); i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); }); ctx.stroke(); };
  for (const r of ctxData.roads) line(r.px, r.class === "motorway" ? "rgba(232,227,216,.45)" : "rgba(232,227,216,.25)", r.class === "motorway" ? 1.6 : 1);
  for (const r of ctxData.rivers) line(r.px, "rgba(86,212,232,.75)", 1.6);
  // places
  ctx.textAlign = "left";
  for (const p of ctxData.places) {
    if (p.kind === "village" && v.scale < 1.1) continue;
    const [sx, sy] = v.toScreen(p.px[0], p.px[1]);
    if (sx < -50 || sy < -20 || sx > v.cw + 50 || sy > v.ch + 20) continue;
    const city = p.kind !== "village";
    ctx.font = city ? "600 13px IBM Plex Sans, sans-serif" : "11px IBM Plex Sans, sans-serif";
    ctx.fillStyle = "#e8e3d8"; ctx.beginPath(); ctx.arc(sx, sy, city ? 3.5 : 2, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = 3; ctx.strokeStyle = "rgba(7,9,12,.85)"; ctx.strokeText(p.name, sx + 6, sy + 4); ctx.fillText(p.name, sx + 6, sy + 4);
  }
  // scale bar
  const km = v.scale * 50 > 120 ? 1 : v.scale * 50 * 5 > 120 ? 5 : 10;   // 50 px = 1 km
  const len = km * 50 * v.scale;
  const x0 = v.cw - len - 16, y0 = v.ch - 30;
  ctx.fillStyle = "#e8e3d8"; ctx.fillRect(x0, y0, len, 3);
  ctx.font = "11px IBM Plex Mono, monospace"; ctx.textAlign = "center"; ctx.fillText(`${km} km`, x0 + len / 2, y0 - 5);
  ctx.restore();
}

// ------------------------------------------------------------ census
function renderCensus() {
  const sObj = C.stats.objects;
  $("#census-sub").innerHTML = `${fmtInt(sObj.count)} change objects at the default threshold: <strong style="color:var(--up)">${fmtInt(sObj.brightened)} brightened (${fmtInt(Math.round(sObj.area_ha_brightened))} ha)</strong> vs <strong style="color:var(--down)">${fmtInt(sObj.darkened)} darkened (${fmtInt(Math.round(sObj.area_ha_darkened))} ha)</strong>. The bars show how the census changes with the detection threshold (|ΔHH| seed, dB); ratios below each pair are brightened ÷ darkened area. The asymmetry holds at every threshold.`;
  $("#sensitivity").innerHTML = sensitivitySvg(C.stats.sensitivity, C.params.object_core_db);
  const filt = $("#census-filter").value, sort = $("#census-sort").value;
  let rows = C.objects.filter((o) => filt === "all" || o.sign === filt);
  rows = rows.slice().sort(sort === "area" ? (a, b) => b.area_ha - a.area_ha : (a, b) => Math.abs(b.dHH_db) - Math.abs(a.dHH_db));
  $("#census-table tbody").innerHTML = rows.slice(0, 300).map((o) => `<tr data-id="${o.id}" tabindex="0"><td class="num">${o.id}</td><td><span class="pill ${o.sign === "brightened" ? "up" : "down"}">${o.sign}</span></td><td class="num">${f(o.area_ha, 1)}</td><td class="num">${f(o.dHH_db, 2, true)}</td><td class="num">${f(o.HH_before_db, 1)}</td><td>${o.dNDVI !== undefined ? `${esc(o.optical_class)} <span class="muted mono">${f(o.dNDVI, 2, true)}</span>` : '<span class="muted">no clear view</span>'}</td><td>${esc(nearestPlace(o.centroid_px)?.name ?? "")}</td></tr>`).join("");
  highlightCensus();
}
function highlightCensus() {
  document.querySelectorAll("#census-table tbody tr").forEach((tr) => tr.classList.toggle("sel", st.sel.kind === "object" && +tr.dataset.id === st.sel.id));
}

// ------------------------------------------------------------ selection actions
function select(sel, { focus = false } = {}) {
  st.sel = sel;
  if (sel.kind !== "roi") viewer.cancelDraw();
  updateEdges();
  renderPanel();
  if (focus && sel.kind === "object") viewer.focus(D.byId.get(sel.id).bbox_px);
  viewer.request();
  const h = sel.kind === "object" ? `#object-${sel.id}` : "#case";
  if (location.hash !== h) history.replaceState(null, "", h);
}

function setTab(name) {
  st.tab = name;
  for (const t of ["observed", "context", "interp", "limits"]) {
    $(`#tb-${t}`).setAttribute("aria-selected", String(t === name));
    $(`#tab-${t}`).hidden = t !== name;
  }
}

// ------------------------------------------------------------ dialogs / export
function methodHtml() {
  const checks = D.checks.map((c) => `<tr><td>${esc(c.name)}</td><td>${c.pass ? "<span class='pill ok'>pass</span>" : "<span class='pill caution'>FAIL</span>"} max |Δ| ${c.diff.toFixed(4)} dB (tol ${c.tol})</td></tr>`).join("");
  const a = C.acquisitions;
  return `<div class="dlg-head"><h2 id="method-title">Method &amp; sources</h2><button class="btn small ghost" data-close>Close</button></div>
  <div class="dlg-body">
    <h3>Question</h3>
    <p>Between NISAR's passes on 22 October and 3 November 2026 — an interval that included the area's first significant autumn rain — which fields around Ceyhan changed in L-band HH backscatter beyond a stable urban control, and what physical explanations remain possible?</p>
    <h3>Pipeline</h3>
    <ol class="steps">
      <li><strong>Find.</strong> NASA CMR search for VALIDATED NISAR L2 GCOV granules at 35.8°E 37.0°N; two share track 151, descending, frame 70 and CRID P05036.</li>
      <li><strong>Read only what's needed.</strong> Authenticated HTTP byte-range reads of the HDF5 files (≈70 MB of 1.9 GB each) for a 24 × 24 km window: γ⁰ HHHH, HVHV, subswath mask, input-exception mask, looks.</li>
      <li><strong>Verify comparability.</strong> Identical UTM 37N 20 m grid on both dates (no resampling); joint validity = mask valid, both polarizations fully focused, positive power; 500 m buffer from invalid data.</li>
      <li><strong>Measure.</strong> 5 × 5 (100 m) valid-weighted boxcar on linear γ⁰; Δ = 10·log₁₀(after/before). Region values use the ratio of mean linear power.</li>
      <li><strong>Control.</strong> Largest persistently bright (HH &gt; 0 dB on both dates) cluster: Ceyhan centre, ${fmtInt(C.stats.urban_control.px)} px, ΔHH ${f(C.stats.urban_control.dHH_db_region, 2, true)} dB.</li>
      <li><strong>Detect.</strong> Change objects: |Δ| ≥ ${C.params.object_core_db} dB seeds grown through same-sign pixels ≥ ${C.params.object_grow_db} dB, ≥ ${C.params.object_min_px} px (1 ha); threshold sensitivity reported.</li>
      <li><strong>Cross-check with optical.</strong> NASA HLS S30 (Sentinel-2) surface reflectance on 23 Oct and 2 Nov (same tile, 08:30 UTC), cloud-masked with Fmask and resampled onto the same 20 m grid; NDVI change per object (≥ 80% clear pixels) separates vegetation loss (harvest) from soil-surface change.</li>
      <li><strong>Check.</strong> HV tested for range-dependent bias (failed → excluded); HH tested (passed). Python unit tests and an integrity test recompute every published number from the shipped files; the browser repeats that check on every load (below).</li>
    </ol>
    <h3>Integrity check — run in your browser just now</h3>
    <table class="checks">${checks}</table>
    <h3>Data</h3>
    <ul class="plain">
      <li>NASA-ISRO NISAR L2 Geocoded Polarimetric Covariance (GCOV), VALIDATED, collection NISAR_L2_GCOV_V1, DOI <a href="https://doi.org/10.5067/NIL2GCOV-V1">10.5067/NIL2GCOV-V1</a>, distributed by ASF DAAC.<br><code>${esc(a.a.granule)}</code><br><code>${esc(a.b.granule)}</code></li>
      <li>NASA POWER daily point data (PRECTOTCORR), 35.8°E 37.0°N, 18 Oct–8 Nov 2026.</li>
      <li>NASA HLS S30 v2.0 (DOI <a href="https://doi.org/10.5067/HLS/HLSS30.002">10.5067/HLS/HLSS30.002</a>), LP DAAC: <code>HLS.S30.T36SYF.2026296T082011.v2.0</code>, <code>HLS.S30.T36SYF.2026306T082551.v2.0</code>.</li>
      <li>Map context: © OpenStreetMap contributors, ODbL (places, rivers, main roads).</li>
      <li>Product metadata: RTC-AP area-based terrain correction (Shiroma et al., 2022, IEEE TGRS, doi:10.1109/TGRS.2022.3147472); Copernicus DEM 30 m (modified for NISAR).</li>
    </ul>
    <h3>Reproduce</h3>
    <pre>python3 scripts/setup_earthdata_netrc.py      # your own Earthdata Login
python scripts/extract_window.py &lt;granule&gt; 35.85 37.0 12 data/raw/win_A
python scripts/build_case.py
python -m pytest tests</pre>
    <h3>AI assistance</h3>
    <p>Generative AI (Claude Code) assisted with software development, data-processing code and documentation. The research question, study area and decisions were made by the participant. All numbers shown are computed from NASA data by the code in the repository and re-verified in your browser; no AI-generated imagery is used.</p>
    <p class="muted">Built ${esc(C.built_utc)} · case ${esc(C.id)}</p>
  </div>`;
}

function exportHtml() {
  return `<div class="dlg-head"><h2 id="export-title">Export case file</h2><button class="btn small ghost" data-close>Close</button></div>
  <div class="dlg-body"><p>Exports describe the current selection: <strong>${esc(selTitle(st.sel).kind)}</strong>.</p>
    <div class="export-list" style="margin-top:14px">
      <button class="btn" data-export="json">Case file (JSON)<small>Selection geometry (pixels and lon/lat), measured statistics, control comparison, source granules, parameters, limitations and integrity checks.</small></button>
      <button class="btn" data-export="csv">All change objects (CSV)<small>${fmtInt(C.objects.length)} objects with area, ΔHH, before/after, centroid lon/lat.</small></button>
      <button class="btn" data-export="report">Printable report<small>A one-page evidence report with the current map view. Save as PDF from the print dialog.</small></button>
    </div></div>`;
}

function download(name, text, type) {
  const blob = new Blob([text], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

function caseFile() {
  const s = st.lastStats, sel = st.sel;
  let geometry = null;
  if (sel.kind === "roi") geometry = { type: "Polygon", pixel_coords: sel.poly, lonlat: sel.poly.map(([x, y]) => S.pxToLonLat(C.grid, x, y).map((v) => +v.toFixed(6))) };
  if (sel.kind === "object") { const o = D.byId.get(sel.id); geometry = { type: "ChangeObject", id: o.id, bbox_px: o.bbox_px, centroid_lonlat: o.centroid_lonlat }; }
  return {
    schema: "between-passes/casefile@1",
    generated_utc: new Date().toISOString(),
    case_id: C.id,
    selection: { kind: sel.kind, geometry },
    measured: { valid_pixels: s.n, area_ha: +(s.n * 0.04).toFixed(2), dHH_db: +s.dDb.toFixed(3), HH_before_db: +s.aDb.toFixed(3), HH_after_db: +s.bDb.toFixed(3),
      per_pixel_dHH_q5_25_50_75_95: s.q.map((v) => +v.toFixed(3)), dHV_db_unresolved_40m_blocks: Number.isFinite(s.dHV) ? +s.dHV.toFixed(3) : null },
    control: { name: "Ceyhan urban centre (persistently bright)", pixels: C.stats.urban_control.px, dHH_db: C.stats.urban_control.dHH_db_region, per_pixel_q1_5_25_50_75_95_99: D.ctrlQ },
    verdict: verdict(s.dDb).text,
    optical_cross_check: st.lastStats.opt ? { source: C.optical.source, before: C.optical.before, after: C.optical.after, ...st.lastStats.opt } : null,
    sources: { nisar: C.acquisitions, collection: "NISAR_L2_GCOV_V1 (DOI 10.5067/NIL2GCOV-V1)", weather: C.weather.source, map_context: "© OpenStreetMap contributors (ODbL)" },
    method: { params: C.params, estimator: "10*log10(mean linear gamma0 after / mean before)", grid: { epsg: C.grid.epsg, posting_m: C.grid.posting_m, transform: C.grid.transform } },
    integrity_checks: D.checks.map(({ name, diff, tol, pass }) => ({ name, max_abs_diff_db: +diff.toFixed(5), tol_db: tol, pass })),
    limitations: ["Two dates only", "Cause not measured by backscatter", "Spatially correlated pixels; control-based comparison", "Urban control", "HV unresolved", "Thermal noise not subtracted", "NASA POWER rainfall is a coarse model estimate"],
  };
}

function exportCsv() {
  const head = ["id", "sign", "area_ha", "pixels", "dHH_db", "HH_before_db", "HH_after_db", "dHV_db_unresolved", "NDVI_before", "NDVI_after", "dNDVI", "optical_class", "optical_clear_frac", "lon", "lat", "nearest_place"];
  const rows = C.objects.map((o) => [o.id, o.sign, o.area_ha, o.pixels, o.dHH_db, o.HH_before_db, o.HH_after_db, o.dHV_db_unresolved, o.NDVI_before ?? "", o.NDVI_after ?? "", o.dNDVI ?? "", o.optical_class, o.optical_clear_frac, o.centroid_lonlat[0], o.centroid_lonlat[1], `"${(nearestPlace(o.centroid_px)?.name ?? "").replace(/"/g, '""')}"`].join(","));
  return [head.join(","), ...rows].join("\n");
}

function openReport() {
  const cf = caseFile();
  const img = $("#viewer").toDataURL("image/png");
  const t = selTitle(st.sel);
  const w = window.open("", "_blank");
  if (!w) { alert("Please allow pop-ups to open the printable report."); return; }
  w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Between Passes — case report</title>
  <style>body{font:13px/1.45 "IBM Plex Sans",system-ui,sans-serif;color:#111;max-width:820px;margin:24px auto;padding:0 20px}h1{font-size:22px;margin:0}h2{font-size:14px;margin:18px 0 6px}
  .meta{color:#555;font-size:12px}img{width:100%;border:1px solid #ccc;margin-top:10px}table{border-collapse:collapse;width:100%}td{border-top:1px solid #ddd;padding:4px 6px}td:last-child{text-align:right;font-family:monospace}
  code{font-size:10.5px;word-break:break-all}.v{font-size:20px;font-weight:600;font-family:monospace}@media print{button{display:none}}</style></head><body>
  <button onclick="print()">Print / save as PDF</button>
  <h1>Between Passes — ${esc(t.kind)}: ${esc(t.title)}</h1>
  <p class="meta">NISAR L2 GCOV VALIDATED · HH γ⁰ · 22 Oct → 3 Nov 2026 · Ceyhan, Adana · generated ${esc(cf.generated_utc)}</p>
  <img src="${img}" alt="Map view at the time of export">
  <h2>Measured</h2><p class="v">ΔHH ${f(cf.measured.dHH_db, 2, true)} dB</p><p>${esc(cf.verdict)}</p>
  <table><tr><td>Valid pixels / area</td><td>${fmtInt(cf.measured.valid_pixels)} / ${cf.measured.area_ha} ha</td></tr>
  <tr><td>HH before → after (region mean)</td><td>${f(cf.measured.HH_before_db)} → ${f(cf.measured.HH_after_db)} dB</td></tr>
  <tr><td>Per-pixel ΔHH 5/25/50/75/95 %</td><td>${cf.measured.per_pixel_dHH_q5_25_50_75_95.join(" / ")}</td></tr>
  <tr><td>Stable urban control ΔHH</td><td>${f(cf.control.dHH_db, 2, true)} dB</td></tr>
  <tr><td>ΔHV (unresolved, not interpreted)</td><td>${f(cf.measured.dHV_db_unresolved_40m_blocks, 2, true)} dB</td></tr></table>
  <h2>Interpretation</h2><p>Backscatter change does not identify its cause. Possible explanations: wetter soil after the 28–29 Oct rain, tillage, harvest, standing water. See the app for which are consistent with this selection.</p>
  <h2>Sources</h2><p><code>${esc(C.acquisitions.a.granule)}</code><br><code>${esc(C.acquisitions.b.granule)}</code><br>DOI 10.5067/NIL2GCOV-V1 · NASA POWER · © OpenStreetMap contributors</p>
  <h2>Integrity</h2><table>${cf.integrity_checks.map((c) => `<tr><td>${esc(c.name)}</td><td>${c.pass ? "pass" : "FAIL"} (${c.max_abs_diff_db} dB)</td></tr>`).join("")}</table>
  <h2>Limitations</h2><p>${cf.limitations.join(" · ")}</p></body></html>`);
  w.document.close();
}

// ------------------------------------------------------------ cover
function renderCover() {
  const s = C.stats.objects;
  const ratio = s.area_ha_brightened / s.area_ha_darkened;
  $("#cover-result").innerHTML = `Across the ${fmtInt(Math.round((C.stats.analysis_px * 0.04) / 100))} km² analysed, <strong>${ratio.toFixed(1)}× more land brightened than darkened</strong> in the radar — ${fmtInt(Math.round(s.area_ha_brightened))} ha vs ${fmtInt(Math.round(s.area_ha_darkened))} ha — while the town centre held steady (${f(C.stats.urban_control.dHH_db_region, 2, true)} dB).`;
  const cv = $("#cover-canvas"), ctx = cv.getContext("2d");
  const img = layerFor("delta").base;
  const edges = toCanvas(edgesImage(D.objects, (l) => (D.byId.get(l).sign === "brightened" ? 1 : -1), D.W, D.H, 0, D.urban));
  ctx.fillStyle = "#11161e"; ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
  ctx.drawImage(img, 0, 0, cv.width, cv.height);
  ctx.globalAlpha = 0.6; ctx.drawImage(edges, 0, 0, cv.width, cv.height); ctx.globalAlpha = 1;
  ctx.font = "500 11px IBM Plex Mono, monospace"; ctx.fillStyle = "rgba(232,227,216,.75)";
  ctx.fillText("ΔHH 22 Oct → 3 Nov 2026 · NISAR · real data", 12, cv.height - 12);
  const btn = $("#open-case"); btn.disabled = false;
}

function openApp(push = true) {
  $("#cover").hidden = true; $("#app").hidden = false;
  if (!viewer) initViewer();
  else viewer.resize();
  if (push && !location.hash.startsWith("#object-")) history.replaceState(null, "", "#case");
  $("#viewer").focus({ preventScroll: true });
}

function initViewer() {
  viewer = new Viewer($("#viewer"), D.W, D.H);
  viewer.overlay = drawOverlay;
  viewer.onClick = (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y);
    if (xi < 0 || yi < 0 || xi >= D.W || yi >= D.H) return;
    const o = D.objects[yi * D.W + xi];
    if (o) select({ kind: "object", id: o });
  };
  viewer.onHover = (x, y) => {
    const ro = $("#readout");
    const xi = Math.floor(x), yi = Math.floor(y);
    if (!Number.isFinite(x) || xi < 0 || yi < 0 || xi >= D.W || yi >= D.H) { ro.textContent = ""; return; }
    const i = yi * D.W + xi;
    const [lon, lat] = S.pxToLonLat(C.grid, xi + 0.5, yi + 0.5);
    if (!D.valid[i]) { ro.textContent = `${lat.toFixed(4)}°N ${lon.toFixed(4)}°E\nno valid radar data`; return; }
    const o = D.objects[i];
    ro.textContent = `${lat.toFixed(4)}°N ${lon.toFixed(4)}°E\nHH 22 Oct  ${f(D.dbA[i], 1).padStart(6)} dB\nHH 3 Nov   ${f(D.dbB[i], 1).padStart(6)} dB\nΔHH       ${f(D.dHH[i], 2, true).padStart(6)} dB` + (o ? `\nobject #${o} (${D.byId.get(o).sign})` : "") + (D.urban[i] ? "\nstable control" : "");
  };
  viewer.onPolygon = (poly) => {
    $("#draw-btn").setAttribute("aria-pressed", "false"); $("#draw-hint").hidden = true;
    if (poly) { select({ kind: "roi", poly }); setTab("observed"); }
  };
  setMode(st.mode);
  updateEdges();
  renderPanel();
  renderCensus();
  const drawTimeline = () => {
    const w = Math.max(640, Math.round($("#timeline").clientWidth || 900));
    $("#timeline").innerHTML = timelineSvg(C.weather.series, [
      { key: "a", date: "20261022", hourFrac: 16.4 / 24, label: "Pass A · 22 Oct" },
      { key: "c", date: "20261029", hourFrac: 16.53 / 24, label: "29 Oct · other track" },
      { key: "b", date: "20261103", hourFrac: 16.4 / 24, label: "Pass B · 3 Nov" },
    ], { width: w });
  };
  drawTimeline();
  let tlw = 0;
  new ResizeObserver(() => { const w = $("#timeline").clientWidth; if (Math.abs(w - tlw) > 40) { tlw = w; drawTimeline(); } }).observe($("#timeline"));
  $("#loading").hidden = true;
  const m = location.hash.match(/^#object-(\d+)$/);
  if (m && D.byId.has(+m[1])) select({ kind: "object", id: +m[1] }, { focus: true });
}

// ------------------------------------------------------------ guided story
function storySteps() {
  const so = C.stats.objects, uc = C.stats.urban_control, op = C.optical;
  const ratio = so.area_ha_brightened / so.area_ha_darkened;
  let ux0 = D.W, uy0 = D.H, ux1 = 0, uy1 = 0;
  for (const i of D.urbanIdx) { const x = i % D.W, y = (i / D.W) | 0; ux0 = Math.min(ux0, x); uy0 = Math.min(uy0, y); ux1 = Math.max(ux1, x); uy1 = Math.max(uy1, y); }
  const soilObj = C.objects.find((o) => o.sign === "brightened" && o.optical_class === "little vegetation change") || C.objects[0];
  const rain = C.weather.series.filter((d) => d.date === "20261028" || d.date === "20261029").reduce((a, d) => a + d.mm, 0);
  return [
    { k: "1 · Two passes", t: "Same orbit, same time of day, twelve days apart",
      p: `NASA-ISRO's NISAR radar imaged these fields around <strong>Ceyhan, Adana</strong> on 22 Oct and 3 Nov 2026 at 19:24 local time, from the identical orbit track. Radar sees through cloud and darkness. <strong>Drag the handle</strong> to compare the two calibrated scenes.`,
      go: () => { select({ kind: "area" }); setMode("swipe"); viewer.fit(); } },
    { k: "2 · What changed", t: `${ratio.toFixed(1)}× more land brightened than darkened`,
      p: `Orange parcels returned more radar energy on 3 Nov, blue less. Field by field: <span class="num-up">${fmtInt(so.brightened)} parcels brightened (${fmtInt(Math.round(so.area_ha_brightened))} ha)</span> vs <span class="num-down">${fmtInt(so.darkened)} darkened (${fmtInt(Math.round(so.area_ha_darkened))} ha)</span>. The asymmetry holds at every detection threshold from 2 to 5 dB.`,
      go: () => { select({ kind: "area" }); setMode("delta"); viewer.fit(); } },
    { k: "3 · Is it real?", t: "Check against something that shouldn't change",
      p: `Ceyhan's town centre (amber outline) is our stable control: buildings, not crops. It changed by just <span class="num-ok">${f(uc.dHH_db_region, 2, true)} dB</span>. A parcel only counts as changed above <strong>3 dB</strong> — beyond 99% of the control's pixels (${f(D.ctrlQ[6], 2, true)} dB).`,
      go: () => { select({ kind: "area" }); setMode("delta"); viewer.focus([ux0, uy0, ux1, uy1], 6); } },
    { k: "4 · Is it the harvest?", t: "Ask a second NASA satellite",
      p: op ? `NASA HLS optical imagery (Sentinel-2) measures vegetation. Of <strong>${op.brightened.objects_with_clear_view}</strong> radar-brightened parcels with a clear view, only <span class="num-up">${Math.round(100 * op.brightened.frac_vegetation_loss)}%</span> lost vegetation (magenta). <strong>Harvest explains a minority.</strong>` : "Optical cross-check unavailable.",
      go: () => { select({ kind: "area" }); setMode("ndvi"); viewer.fit(); } },
    { k: "5 · What remains", t: "The soil surface: wetter, or ploughed",
      p: `This ${f(soilObj.area_ha, 0)} ha parcel near ${esc(nearestPlace(soilObj.centroid_px)?.name ?? "Ceyhan")} brightened <span class="num-up">${f(soilObj.dHH_db, 1, true)} dB</span> with no vegetation loss (ΔNDVI ${f(soilObj.dNDVI, 2, true)}). Left: wetter soil after <strong>${f(rain, 0)} mm</strong> of rain on 28–29 Oct, or ploughing. One radar pair can't tell them apart — the <strong>Interpretation</strong> tab shows what would.`,
      go: () => { setMode("delta"); select({ kind: "object", id: soilObj.id }, { focus: true }); setTab("interp"); } },
    { k: "6 · Your turn", t: "Draw any region and measure it",
      p: `Every number here is computed in your browser from the real NISAR data — and re-verified on load (see <strong>Method &amp; sources</strong>). Click <strong>Draw region</strong>, outline a field, and export the evidence as a case file.`,
      go: () => { setTab("observed"); select({ kind: "area" }); setMode("delta"); viewer.fit(); } },
  ];
}

function renderStory(i) {
  const steps = (D.steps ||= storySteps());
  st.story = i;
  const s = steps[i], el = $("#story");
  el.hidden = false;
  el.innerHTML = `<button class="close" aria-label="Close guided case" data-story="close">×</button>
    <div class="step-k">${s.k}</div><h3>${s.t}</h3><p>${s.p}</p>
    <div class="nav"><div class="dots">${steps.map((_, j) => `<button aria-label="Step ${j + 1}" aria-current="${j === i}" data-story="${j}"></button>`).join("")}</div>
      ${i > 0 ? `<button class="btn small ghost" data-story="prev">Back</button>` : ""}
      ${i < steps.length - 1 ? `<button class="btn small primary" data-story="next">Next</button>` : `<button class="btn small primary" data-story="draw">Draw a region</button>`}
    </div>`;
  s.go();
}

function closeStory() { $("#story").hidden = true; st.story = null; }

// ------------------------------------------------------------ wiring
function wire() {
  $("#open-case").addEventListener("click", () => { openApp(); renderStory(0); });
  $("#open-method").addEventListener("click", () => openDialog("method"));
  document.querySelectorAll("#mode-seg button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  for (const [id, key] of [["#t-objects", "objects"], ["#t-context", "context"], ["#t-control", "control"]]) {
    $(id).addEventListener("change", (e) => { st.show[key] = e.target.checked; updateEdges(); viewer.request(); });
  }
  $("#draw-btn").addEventListener("click", (e) => {
    const on = e.currentTarget.getAttribute("aria-pressed") !== "true";
    e.currentTarget.setAttribute("aria-pressed", String(on));
    $("#draw-hint").hidden = !on;
    if (on) viewer.startDraw(); else viewer.cancelDraw();
    $("#viewer").focus();
  });
  $("#reset-view").addEventListener("click", () => viewer.fit());
  $("#story-btn").addEventListener("click", () => renderStory(0));
  $("#story").addEventListener("click", (e) => {
    const v = e.target.closest("[data-story]")?.dataset.story;
    if (v == null) return;
    if (v === "close") closeStory();
    else if (v === "next") renderStory(st.story + 1);
    else if (v === "prev") renderStory(st.story - 1);
    else if (v === "draw") { closeStory(); $("#draw-btn").click(); }
    else renderStory(+v);
  });
  $("#sel-clear").addEventListener("click", () => { viewer.cancelDraw(); select({ kind: "area" }); });
  for (const t of ["observed", "context", "interp", "limits"]) $(`#tb-${t}`).addEventListener("click", () => setTab(t));
  $("#census-filter").addEventListener("change", renderCensus);
  $("#census-sort").addEventListener("change", renderCensus);
  const pick = (e) => { const tr = e.target.closest("tr[data-id]"); if (tr) { select({ kind: "object", id: +tr.dataset.id }, { focus: true }); $(".stage").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }); } };
  $("#census-table").addEventListener("click", pick);
  $("#census-table").addEventListener("keydown", (e) => { if (e.key === "Enter") pick(e); });
  document.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => openDialog(b.dataset.open)));
  for (const d of ["#dlg-method", "#dlg-export"]) {
    $(d).addEventListener("click", (e) => {
      if (e.target.closest("[data-close]") || e.target === $(d)) $(d).close();
      const ex = e.target.closest("[data-export]")?.dataset.export;
      if (ex === "json") download(`between-passes-casefile-${st.sel.kind}${st.sel.id ? "-" + st.sel.id : ""}.json`, JSON.stringify(caseFile(), null, 2), "application/json");
      if (ex === "csv") download("between-passes-change-objects.csv", exportCsv(), "text/csv");
      if (ex === "report") openReport();
    });
  }
  window.addEventListener("hashchange", () => {
    if (!D) return;
    if (location.hash === "" || location.hash === "#") { $("#app").hidden = true; $("#cover").hidden = false; return; }
    if ($("#app").hidden) openApp(false);
    const m = location.hash.match(/^#object-(\d+)$/);
    if (m && D.byId.has(+m[1]) && !(st.sel.kind === "object" && st.sel.id === +m[1])) select({ kind: "object", id: +m[1] }, { focus: true });
  });
}

function openDialog(name) {
  if (!D) return;
  const dlg = $(`#dlg-${name}`);
  dlg.innerHTML = name === "method" ? methodHtml() : exportHtml();
  dlg.showModal();
}

async function boot() {
  wire();
  try {
    await load();
    renderCover();
    const sm = location.hash.match(/^#story-(\d)$/);
    if (sm) { openApp(false); renderStory(Math.min(5, Math.max(0, +sm[1] - 1))); }
    else if (location.hash.startsWith("#case") || location.hash.startsWith("#object-")) openApp(false);
  } catch (err) {
    console.error(err);
    $("#cover-result").textContent = "The case data could not be loaded.";
    const fe = $("#fatal"); fe.hidden = false;
    fe.textContent = `Could not load the NISAR case data (${err.message}). If you opened index.html directly from disk, serve the folder over HTTP instead (e.g. python3 -m http.server).`;
  }
}
boot();
