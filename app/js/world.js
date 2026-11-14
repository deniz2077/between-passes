// Global rain test page: renders the pre-registered NISAR x SMAP result and re-verifies it in the browser.
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const UP = [217, 83, 30], DOWN = [42, 93, 176];
const fmt = (v, d = 2, sign = false) => (v == null || !Number.isFinite(v)) ? "—" : (sign && v > 0 ? "+" : "") + v.toFixed(d);
const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
};

// ---------- statistics (mirror scripts/global_analyze.py) ----------
function ranks(a) {
  const idx = a.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]);
  const r = new Array(a.length);
  for (let i = 0; i < idx.length;) {
    let j = i;
    while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    const avg = (i + j) / 2 + 1;
    for (let k = i; k <= j; k++) r[idx[k][1]] = avg;
    i = j + 1;
  }
  return r;
}
function pearson(x, y) {
  const n = x.length, mx = x.reduce((s, v) => s + v, 0) / n, my = y.reduce((s, v) => s + v, 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { const a = x[i] - mx, b = y[i] - my; sxy += a * b; sxx += a * a; syy += b * b; }
  return sxy / Math.sqrt(sxx * syy);
}
const spearman = (x, y) => pearson(ranks(x), ranks(y));
const median = (a) => { const s = [...a].sort((p, q) => p - q), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; };
function theilSen(x, y) {
  const sl = [];
  for (let i = 0; i < x.length; i++) for (let j = i + 1; j < x.length; j++) if (x[j] !== x[i]) sl.push((y[j] - y[i]) / (x[j] - x[i]));
  const m = median(sl);
  return [m, median(y) - m * median(x)];
}

// ---------- projection: Equal Earth ----------
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2;
function equalEarth(lon, lat) {
  const l = lon * Math.PI / 180, p = lat * Math.PI / 180;
  const t = Math.asin(M * Math.sin(p)), t2 = t * t, t6 = t2 * t2 * t2;
  const x = (2 * Math.sqrt(3) * l * Math.cos(t)) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1));
  const y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [x, y];
}
const MAP_W = 1000, MAP_H = 487, SC = MAP_W / (2 * 2.7066 + 0.04);
const proj = (lon, lat) => { const [x, y] = equalEarth(lon, lat); return [MAP_W / 2 + x * SC, MAP_H / 2 - y * SC]; };

function colorFor(d) {
  const a = Math.min(1, Math.abs(d) / 3) ** 0.8, c = d >= 0 ? UP : DOWN, g = 120;
  return `rgb(${Math.round(g + (c[0] - g) * a)},${Math.round(g + (c[1] - g) * a)},${Math.round(g + (c[2] - g) * a)})`;
}

let G, thumbs, sel = null;
const cDSM = () => G.ceyhan.dSM ?? G.ceyhan.exploratory?.dSM ?? null;
const dots = new Map(), pts = new Map();

function drawMap(land) {
  const svg = $("#w-map");
  svg.setAttribute("viewBox", `0 0 ${MAP_W} ${MAP_H}`);
  // sphere outline
  const edge = [];
  for (let lat = -90; lat <= 90; lat += 2) edge.push(proj(180, lat));
  for (let lat = 90; lat >= -90; lat -= 2) edge.push(proj(-180, lat));
  el("path", { d: "M" + edge.map((p) => p.map((v) => v.toFixed(1)).join(",")).join("L") + "Z", class: "sphere" }, svg);
  for (let lon = -150; lon <= 150; lon += 30) {
    const g = []; for (let lat = -88; lat <= 88; lat += 4) g.push(proj(lon, lat));
    el("path", { d: "M" + g.map((p) => p.map((v) => v.toFixed(1)).join(",")).join("L"), class: "grat" }, svg);
  }
  for (let lat = -60; lat <= 60; lat += 30) {
    const g = []; for (let lon = -180; lon <= 180; lon += 5) g.push(proj(lon, lat));
    el("path", { d: "M" + g.map((p) => p.map((v) => v.toFixed(1)).join(",")).join("L"), class: "grat" }, svg);
  }
  let d = "";
  for (const poly of land.polygons) for (const ring of poly) {
    d += "M" + ring.map(([lo, la]) => proj(lo, la).map((v) => v.toFixed(1)).join(",")).join("L") + "Z";
  }
  el("path", { d, class: "land", "fill-rule": "evenodd" }, svg);
  const sorted = [...G.sites].sort((a, b) => Math.abs(a.dHH_site_db) - Math.abs(b.dHH_site_db));
  for (const s of sorted) {
    const [x, y] = proj(s.lon, s.lat);
    const c = el("circle", { cx: x.toFixed(1), cy: y.toFixed(1), r: 5.2, fill: colorFor(s.dHH_site_db), class: "site-dot", tabindex: 0,
      role: "button", "aria-label": `Site ${s.k}: ${fmt(s.dHH_site_db, 2, true)} dB` }, svg);
    c.addEventListener("click", () => select(s));
    c.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(s); } });
    el("title", {}, c).textContent = `${fmt(s.lat, 2)}, ${fmt(s.lon, 2)} · ΔHH ${fmt(s.dHH_site_db, 2, true)} dB · ΔSM ${fmt(s.dSM, 3, true)}`;
    dots.set(s.k, c);
  }
  const c = G.ceyhan, [cx, cy] = proj(c.lon, c.lat);
  const m = el("g", { class: "cey-g", style: "cursor:pointer" }, svg);
  el("circle", { cx, cy, r: 9, class: "cey-mark" }, m);
  el("circle", { cx, cy, r: 4, fill: colorFor(c.dHH_site_db), stroke: "#fbf9f4" }, m);
  m.addEventListener("click", () => select(c));
}

function drawScatter(fit) {
  const svg = $("#w-scatter"), W = 820, H = 420, L = 58, R = 18, T = 16, B = 46;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.innerHTML = "";
  const cdsm = cDSM();
  const all = [...G.sites, ...(REP ? REP.rep_sites : []), ...(cdsm != null ? [{ dSM: cdsm, dHH_site_db: G.ceyhan.dHH_site_db }] : [])];
  const xs = all.map((s) => s.dSM), ys = all.map((s) => s.dHH_site_db);
  const pad = (lo, hi, f) => { const r = hi - lo || 1; return [lo - r * f, hi + r * f]; };
  const [x0, x1] = pad(Math.min(...xs, 0), Math.max(...xs, 0), 0.06), [y0, y1] = pad(Math.min(...ys, 0), Math.max(...ys, 0), 0.08);
  const X = (v) => L + (v - x0) / (x1 - x0) * (W - L - R), Y = (v) => T + (y1 - v) / (y1 - y0) * (H - T - B);
  const nice = (lo, hi, n) => { const st = Math.pow(10, Math.floor(Math.log10((hi - lo) / n))); const m = [1, 2, 5, 10].find((k) => (hi - lo) / (st * k) <= n) * st; const out = []; for (let v = Math.ceil(lo / m) * m; v <= hi + 1e-9; v += m) out.push(+v.toFixed(6)); return out; };
  for (const v of nice(x0, x1, 7)) { el("line", { x1: X(v), x2: X(v), y1: T, y2: H - B, class: v === 0 ? "ax" : "gl" }, svg); el("text", { x: X(v), y: H - B + 16, "text-anchor": "middle" }, svg).textContent = fmt(v, 2, true); }
  for (const v of nice(y0, y1, 6)) { el("line", { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: v === 0 ? "ax" : "gl" }, svg); el("text", { x: L - 8, y: Y(v) + 4, "text-anchor": "end" }, svg).textContent = fmt(v, 1, true); }
  el("text", { x: (L + W - R) / 2, y: H - 8, "text-anchor": "middle", class: "lab" }, svg).textContent = "SMAP soil-moisture change (m³/m³)  →  wetter";
  el("text", { x: 14, y: (T + H - B) / 2, "text-anchor": "middle", class: "lab", transform: `rotate(-90 14 ${(T + H - B) / 2})` }, svg).textContent = "NISAR ΔHH (dB)  →  brighter";
  const [m, b] = fit;
  el("line", { x1: X(x0), y1: Y(b + m * x0), x2: X(x1), y2: Y(b + m * x1), class: "fit" }, svg);
  if (REP) for (const s of REP.rep_sites) {
    const c = el("circle", { cx: X(s.dSM), cy: Y(s.dHH_site_db), r: 3.6, class: "rep-dot", stroke: colorFor(s.dHH_site_db) }, svg);
    el("title", {}, c).textContent = `replication site: ΔSM ${fmt(s.dSM, 3, true)}, ΔHH ${fmt(s.dHH_site_db, 2, true)} dB`;
  }
  for (const s of G.sites) {
    const c = el("circle", { cx: X(s.dSM), cy: Y(s.dHH_site_db), r: 4.2, fill: colorFor(s.dHH_site_db), class: "site-dot", "fill-opacity": .9 }, svg);
    c.addEventListener("click", () => select(s));
    el("title", {}, c).textContent = `site ${s.k}: ΔSM ${fmt(s.dSM, 3, true)}, ΔHH ${fmt(s.dHH_site_db, 2, true)} dB`;
    pts.set(s.k, c);
  }
  const c = G.ceyhan;
  if (cdsm != null) {
    const ex = c.dSM == null;
    el("circle", { cx: X(cdsm), cy: Y(c.dHH_site_db), r: 9, class: "cey-mark", "stroke-dasharray": ex ? "3 3" : "" }, svg);
    const t = el("text", { x: X(cdsm) - 12, y: Y(c.dHH_site_db) - 14, class: "lab", "text-anchor": "end" }, svg); t.textContent = ex ? "Ceyhan (exploratory)" : "Ceyhan";
    pts.set("ceyhan", el("circle", { cx: X(cdsm), cy: Y(c.dHH_site_db), r: 4, fill: colorFor(c.dHH_site_db), class: "site-dot" }, svg));
    pts.get("ceyhan").addEventListener("click", () => select(c));
  }
}

function thumbCanvas(s) {
  const n = G.thumbs.size, off = s.thumb * n * n, cv = document.createElement("canvas");
  cv.width = n; cv.height = n;
  const ctx = cv.getContext("2d"), img = ctx.createImageData(n, n);
  for (let i = 0; i < n * n; i++) {
    const q = thumbs[off + i], o = i * 4;
    if (!q) { img.data[o + 3] = 0; continue; }
    const d = (q - 128) * G.thumbs.step_db, a = Math.min(1, Math.abs(d) / 6) ** 0.75, c = d >= 0 ? [255, 138, 76] : [90, 169, 255], g = 40;
    img.data[o] = g + (c[0] - g) * a; img.data[o + 1] = g + (c[1] - g) * a; img.data[o + 2] = g + (c[2] - g) * a; img.data[o + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return cv;
}

const fmtDate = (d) => d ? `${+d.slice(6)} ${["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+d.slice(4, 6) - 1]}` : "—";

function select(s, push = true) {
  sel = s;
  for (const [, c] of dots) c.classList.remove("sel");
  for (const [, c] of pts) c.classList.remove("sel");
  dots.get(s.k)?.classList.add("sel"); pts.get(s.k)?.classList.add("sel");
  const box = $("#w-site"), isC = s.k === "ceyhan";
  const r = s.rain || {};
  const ns = (v) => `${fmt(Math.abs(v), 2)}° ${v >= 0 ? "N" : "S"}`, ew = (v) => `${fmt(Math.abs(v), 2)}° ${v >= 0 ? "E" : "W"}`;
  box.innerHTML = `
    <p class="eyebrow">${isC ? "My case study (not in the sample)" : `Site ${s.k} of ${G.sites.length}`}</p>
    <h2>${isC ? "Ceyhan, Adana" : `${ns(s.lat)}, ${ew(s.lon)}`}</h2>
    <p class="sub mono">${fmtDate(s.date_a)} → ${fmtDate(s.date_b)} 2026 · ${s.spacing_m} m grid · local ${fmt(s.local_solar_hour, 1)} h</p>
    <div id="w-thumb"></div>
    <p class="cap">ΔHH at 100 m over the 10 × 10 km window · <span class="up-t">brighter</span> / <span class="dn-t">darker</span></p>
    <dl>
      <dt>NISAR ΔHH (site)</dt><dd class="${s.dHH_site_db >= 0 ? "up-t" : "dn-t"}">${fmt(s.dHH_site_db, 2, true)} dB</dd>
      <dt>Area ≥ +3 dB / ≤ −3 dB</dt><dd>${fmt(100 * s.frac_up3, 1)} % / ${fmt(100 * s.frac_dn3, 1)} %</dd>
      <dt>SMAP soil moisture${isC && s.exploratory ? "*" : ""}</dt><dd>${fmt(s.sm_a ?? s.exploratory?.sm_a, 3)} → ${fmt(s.sm_b ?? s.exploratory?.sm_b, 3)}</dd>
      <dt>SMAP change${isC && s.exploratory ? "*" : ""}</dt><dd>${fmt(s.dSM ?? s.exploratory?.dSM, 3, true)} m³/m³</dd>
      <dt>Rain between passes</dt><dd>${r.between == null ? "—" : fmt(r.between, 1) + " mm"}</dd>
      <dt>Rain 3 d before each</dt><dd>${r.pre3_a == null ? "—" : `${fmt(r.pre3_a, 1)} / ${fmt(r.pre3_b, 1)} mm`}</dd>
      <dt>Valid pixels</dt><dd>${fmt(100 * s.valid_frac, 0)} %</dd>
    </dl>
    ${isC ? smapSeries(s) + (s.exploratory ? `<p class="cap">* exploratory: ${s.exploratory.rule}.</p>` : "") : ""}
    <p class="ids">${s.a}<br>${s.b}${(() => { const u = s.dSM != null ? s : s.exploratory; return u ? `<br>SMAP ${u.smap_a.day} ${u.smap_a.overpass} / ${u.smap_b.day} ${u.smap_b.overpass}` : ""; })()}</p>
    ${isC ? `<div class="navrow"><a class="btn small primary" href="index.html#case">Open the full Ceyhan case</a></div>` : `<div class="navrow"><button class="btn small ghost" id="w-prev">← Previous</button><button class="btn small ghost" id="w-next">Next →</button></div>`}`;
  $("#w-thumb").appendChild(thumbCanvas(s));
  if (!isC) {
    const i = G.sites.indexOf(s), n = G.sites.length;
    $("#w-prev").onclick = () => select(G.sites[(i - 1 + n) % n]);
    $("#w-next").onclick = () => select(G.sites[(i + 1) % n]);
  }
  if (push) history.replaceState(null, "", `#site-${s.k}`);
}

function selfCheck(fit) {
  const x = G.sites.map((s) => s.dSM), y = G.sites.map((s) => s.dHH_site_db), P = G.results.primary;
  const rho = spearman(x, y), dr = Math.abs(rho - P.spearman_rho), ds = Math.abs(fit[0] * 0.1 - P.theil_sen_db_per_0p1);
  const ok = dr < 1e-3 && ds < 2e-3 && G.sites.length === P.n;
  $("#w-check").innerHTML = `<span class="${ok ? "ok-t" : "bad-t"}">${ok ? "✓ PASS" : "✗ MISMATCH"}</span> — recomputed from the ${G.sites.length} shipped sites: Spearman ρ ${fmt(rho, 4)} (published ${fmt(P.spearman_rho, 4)}), Theil–Sen ${fmt(fit[0] * 0.1, 3)} dB per 0.1 m³/m³ (published ${fmt(P.theil_sen_db_per_0p1, 3)}).`;
}

function signAgreement() {
  const clear = G.sites.filter((s) => Math.abs(s.dSM) > 0.05);
  return [clear.filter((s) => Math.sign(s.dSM) === Math.sign(s.dHH_site_db)).length, clear.length];
}

function hero(fit) {
  const P = G.results.primary, n = P.n, sig = P.perm_p < 0.05 && P.spearman_rho > 0, c = G.ceyhan;
  const [agree, clear] = signAgreement();
  const R = REP, rep = R && R.replicates;
  $("#w-n-sites").textContent = rep ? `${G.results.n_sampled + R.replication.n_sampled}` : G.results.n_sampled;
  $("#w-pop").textContent = G.results.n_population_pairs;
  $("#w-headline").innerHTML = !sig ? `Across ${n} sites worldwide, NISAR's site-wide change did not track soil wetting.`
    : rep ? `From orbit, NISAR's radar tracks whether the ground got <em>wetter or drier</em>. I tested it at random places worldwide, twice.`
          : `Where NASA's SMAP saw soil get wetter, NISAR's radar got brighter. Where it dried, NISAR got darker.`;
  $("#w-lede").innerHTML = !sig ? `The pre-registered test did not find the expected relationship.`
    : `I wrote the rules down before looking, picked ${G.results.n_sampled} NISAR sites at random from ${G.results.n_population_pairs} worldwide, and compared each with NASA's soil-moisture satellite, SMAP. ${rep ? `Then I repeated it on ${R.replication.n_sampled} <i>new</i> random sites. Both times, when the soil got wetter or drier, the radar changed with it. Drying shows most clearly: soil that dried got about 1 dB darker.` : `Radar change tracks soil-moisture change (ρ = ${fmt(P.spearman_rho, 2)}); ${agree} of the ${clear} sites with a clear moisture change moved in the same direction.`} <a href="#site-ceyhan">At Ceyhan, SMAP confirms the soil was wetted between the two passes.</a>`;
  const stats = rep ? [
    ["Sites with soil data", `${P.n + R.replication.n}<small> of ${G.results.n_sampled + R.replication.n_sampled} picked</small>`],
    ["First test", `ρ ${fmt(P.spearman_rho, 2)}<small> ${P.n} sites</small>`],
    ["Repeat test", `ρ ${fmt(R.replication.rho, 2)}<small> ${R.replication.n} sites</small>`],
    ["Chance result", "&lt; 0.1%<small> both</small>"],
    ["Moved the same way", `${R.pooled.same_direction[0]}/${R.pooled.same_direction[1]}<small> clear cases</small>`],
  ] : [
    ["Sites tested", `${n}<small> of ${G.results.n_sampled} drawn</small>`],
    ["Spearman ρ", fmt(P.spearman_rho, 2)],
    ["p (permutation)", P.perm_p <= 0.00011 ? "< 0.001" : fmt(P.perm_p, 4)],
    ["Slope", `${fmt(P.theil_sen_db_per_0p1, 1, true)}<small> dB per +0.1 m³/m³</small>`],
    ["Same direction", `${agree}/${clear}<small> clear cases</small>`],
  ];
  $("#w-stats").innerHTML = stats.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");
  const e = c.exploratory, cd = cDSM(), pred = cd != null ? fit[1] + fit[0] * cd : null;
  $("#w-scatter-note").innerHTML = `Line: Theil–Sen fit across the ${n} sampled sites (95 % CI of the slope ${fmt(P.boot95_db_per_0p1[0], 2, true)} … ${fmt(P.boot95_db_per_0p1[1], 2, true)} dB per +0.1 m³/m³). ` + (cd == null
    ? `SMAP had no quality-approved value at Ceyhan on these dates.`
    : `<b>Ceyhan</b> (dashed, not in the sample${e ? "; <i>exploratory</i>: the pre-registered ±1-day SMAP window found no approved reading near 22 Oct, so a ±2-day window was used" : ""}): SMAP ${fmt(cd, 2, true)} m³/m³, NISAR ${fmt(c.dHH_site_db, 2, true)} dB over its 10 km window. Its wetting is larger than at any sampled site (so the line is extrapolated), and its site-wide brightening is smaller than the fitted line (${fmt(pred, 1, true)} dB) — only ${fmt(100 * c.frac_up3, 1)} % of the window brightened by ≥ 3 dB: the change sits in individual fields (see the case's parcel map).`);
  const reasons = {};
  for (const d of G.drops) { const k = (d.reason || "").split(":")[0].replace(/\s*\[.*$/, ""); reasons[k] = (reasons[k] || 0) + 1; }
  const why = { "SMAP unavailable": "SMAP had no quality-approved reading within a day of a pass (orbit gaps, dense vegetation, water or flags)", "valid fraction < 0.5": "NISAR window less than half valid" };
  $("#w-drops").innerHTML = Object.entries(reasons).map(([k, v]) => `<li>${v} × ${why[k] || k}</li>`).join("") || "<li>None</li>";
}

function smapSeries(c) {
  const e = c.exploratory; if (!e) return "";
  const pts = e.recommended_series.map(([d, ov, v]) => ({ t: Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6)) + (ov === "PM" ? 18 : 6) * 3600e3, v }));
  const t0 = Date.UTC(2026, 9, 19), t1 = Date.UTC(2026, 10, 12), W = 300, H = 110, L = 28, B = 18;
  const X = (t) => L + (t - t0) / (t1 - t0) * (W - L - 6), Y = (v) => 6 + (0.4 - v) / 0.4 * (H - B - 6);
  const pass = [Date.UTC(2026, 9, 22, 18, 47), Date.UTC(2026, 10, 3, 18, 47)];
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;margin:6px 0 2px" aria-label="SMAP soil moisture at Ceyhan">
    ${[0, 0.2, 0.4].map((v) => `<line x1="${L}" x2="${W - 6}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e6dfd2"/><text x="${L - 4}" y="${Y(v) + 3}" text-anchor="end" fill="#948a7a" font-size="9" font-family="DM Mono">${v}</text>`).join("")}
    ${pass.map((t, i) => `<line x1="${X(t)}" x2="${X(t)}" y1="4" y2="${H - B}" stroke="#1f6f5c" stroke-dasharray="3 2"/><text x="${X(t) + 3}" y="12" fill="#1f6f5c" font-size="9" font-family="DM Mono">NISAR ${i ? "B" : "A"}</text>`).join("")}
    <polyline fill="none" stroke="#1c1b17" stroke-width="1.5" points="${pts.map((p) => `${X(p.t).toFixed(1)},${Y(p.v).toFixed(1)}`).join(" ")}"/>
    ${pts.map((p) => `<circle cx="${X(p.t).toFixed(1)}" cy="${Y(p.v).toFixed(1)}" r="2.6" fill="#1c1b17"/>`).join("")}
    <text x="${L}" y="${H - 4}" fill="#948a7a" font-size="9" font-family="DM Mono">19 Oct</text><text x="${W - 6}" y="${H - 4}" text-anchor="end" fill="#948a7a" font-size="9" font-family="DM Mono">12 Nov</text>
  </svg><p class="cap">NASA SMAP soil moisture at Ceyhan (m³/m³), every quality-approved reading. The rain on 28–29 Oct is visible as a jump.</p>`;
}

let REP = null; // replication summary (optional)
function renderReplication(R) {
  const o = R.original, r = R.replication, P = R.pooled, box = $("#w-rep");
  box.hidden = false;
  box.innerHTML = `<p class="eyebrow">Independent replication · pre-registered before extraction</p>
    <h2>${R.replicates ? "The result replicated on 200 fresh random sites." : "The result did not replicate on 200 fresh random sites."}</h2>
    <p>Same plan, new random draw (seed 2027) from the 563 pairs not used before. At the <b>${r.n}</b> new sites with quality SMAP data: Spearman ρ <b>${fmt(r.rho, 2)}</b>, p ${r.p <= 0.00011 ? "&lt; 0.001" : "= " + fmt(r.p, 4)}, slope ${fmt(r.slope, 2, true)} dB per +0.1 m³/m³ (95 % CI ${fmt(r.ci[0], 2, true)} … ${fmt(r.ci[1], 2, true)}; original ${fmt(o.ci[0], 2, true)} … ${fmt(o.ci[1], 2, true)}, ${R.slope_ci_overlap ? "overlapping" : "not overlapping"}).</p>
    <p class="verdict ${R.replicates ? "ok-t" : "bad-t"}">${R.replicates ? "✓ Replication criterion met (ρ > 0, p < 0.05)" : "✗ Replication criterion not met"}</p>
    <p class="muted">${esc(R.pooled_label)}: n ${P.n}, ρ ${fmt(P.rho, 2)}, slope ${fmt(P.slope, 2, true)} dB per +0.1 m³/m³; ${P.same_direction[0]} of ${P.same_direction[1]} sites with a clear moisture change moved in the same direction. Hollow points on the plot are the replication sites.</p>`;
}
const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function boot() {
  const [g, land, tb] = await Promise.all([
    fetch("data/global/global.json").then((r) => r.json()),
    fetch("data/global/land.json").then((r) => r.json()),
    fetch("data/global/thumbs.u8").then((r) => r.arrayBuffer()),
  ]);
  G = g; thumbs = new Uint8Array(tb);
  const fit = theilSen(G.sites.map((s) => s.dSM), G.sites.map((s) => s.dHH_site_db));
  REP = await fetch("data/global/replication.json").then((r) => r.ok ? r.json() : null).catch(() => null);
  hero(fit); drawMap(land); drawScatter(fit); selfCheck(fit);
  if (REP) renderReplication(REP);
  const m = location.hash.match(/^#site-(\w+)/);
  const s = m ? (m[1] === "ceyhan" ? G.ceyhan : G.sites.find((x) => String(x.k) === m[1])) : null;
  select(s || G.ceyhan, !!s);
}
boot().catch((e) => { $("#w-headline").textContent = "Could not load the global data."; console.error(e); });
