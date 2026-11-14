// Small, dependency-free SVG charts. Every mark is data-driven.
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/** Overlaid normalized histograms: selection (filled) vs control (outline). */
export function histogramSvg(sel, ctrl, { lo = -8, hi = 8, color = "#ff8a4c", markers = [] } = {}) {
  const W = 360, H = 150, P = { l: 8, r: 8, t: 10, b: 24 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const dens = (h) => h.counts.map((c) => (h.n ? c / h.n : 0));
  const ds = dens(sel), dc = ctrl ? dens(ctrl) : [];
  const ymax = Math.max(1e-9, ...ds, ...dc);
  const bw = iw / ds.length;
  const x = (v) => P.l + ((v - lo) / (hi - lo)) * iw;
  const y = (d) => P.t + ih - (d / ymax) * ih;
  let bars = "";
  ds.forEach((d, i) => { if (d > 0) bars += `<rect x="${(P.l + i * bw).toFixed(2)}" y="${y(d).toFixed(2)}" width="${(bw - 0.4).toFixed(2)}" height="${(P.t + ih - y(d)).toFixed(2)}" fill="${color}" opacity=".78"/>`; });
  let line = "";
  if (ctrl) {
    line = `M${P.l},${P.t + ih}`;
    dc.forEach((d, i) => { line += `L${(P.l + i * bw).toFixed(2)},${y(d).toFixed(2)}L${(P.l + (i + 1) * bw).toFixed(2)},${y(d).toFixed(2)}`; });
    line += `L${P.l + iw},${P.t + ih}`;
  }
  let ticks = "";
  for (let v = lo; v <= hi; v += 2) ticks += `<line x1="${x(v)}" x2="${x(v)}" y1="${P.t + ih}" y2="${P.t + ih + 4}" stroke="#31405a"/><text class="axis" x="${x(v)}" y="${H - 6}" text-anchor="middle">${v > 0 ? "+" : ""}${v}</text>`;
  const mk = markers.map((m) => `<line x1="${x(m.v)}" x2="${x(m.v)}" y1="${P.t}" y2="${P.t + ih}" stroke="${m.color}" stroke-dasharray="${m.dash || "3 3"}"/><text class="axis" x="${x(m.v) + 3}" y="${P.t + 9}" fill="${m.color}">${esc(m.label)}</text>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Distribution of per-pixel ΔHH for the selection compared with the stable control">
    <line x1="${P.l}" x2="${P.l + iw}" y1="${P.t + ih}" y2="${P.t + ih}" stroke="#31405a"/>
    <line x1="${x(0)}" x2="${x(0)}" y1="${P.t}" y2="${P.t + ih}" stroke="#31405a"/>
    ${bars}${ctrl ? `<path d="${line}" fill="none" stroke="#e8c547" stroke-width="1.4"/>` : ""}${mk}${ticks}
    <text class="axis" x="${P.l + iw}" y="${H - 6}" text-anchor="end" dy="0"> </text>
  </svg>`;
}

/** Rain bars with acquisition markers. series: [{date:'YYYYMMDD', mm}] */
export function timelineSvg(series, passes, { start = "20261018", end = "20261108", width = 900 } = {}) {
  const days = series.filter((d) => d.date >= start && d.date <= end);
  const W = width, H = 150, P = { l: 30, r: 10, t: 34, b: 26 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const n = days.length, bw = iw / n;
  const ymax = Math.max(18, ...days.map((d) => d.mm));
  const xi = (i) => P.l + i * bw;
  const xd = (dstr, hourFrac = 0.5) => { const i = days.findIndex((d) => d.date === dstr); return i < 0 ? null : xi(i) + hourFrac * bw; };
  const y = (v) => P.t + ih - (v / ymax) * ih;
  const a = passes.find((p) => p.key === "a"), b = passes.find((p) => p.key === "b");
  const xa = xd(a.date, a.hourFrac), xb = xd(b.date, b.hourFrac);
  let s = `<rect x="${xa}" y="${P.t - 6}" width="${xb - xa}" height="${ih + 6}" fill="rgba(86,212,232,.07)"/>`;
  days.forEach((d, i) => {
    const inside = d.date > a.date && d.date <= b.date;
    const after = d.date > b.date;
    const fill = after ? "#3a4659" : inside ? "#56d4e8" : "#56708a";
    if (d.mm > 0) s += `<rect x="${(xi(i) + 1.5).toFixed(1)}" y="${y(d.mm).toFixed(1)}" width="${(bw - 3).toFixed(1)}" height="${(P.t + ih - y(d.mm)).toFixed(1)}" fill="${fill}" rx="1"><title>${d.date.slice(6)} ${monthName(d.date)}: ${d.mm.toFixed(2)} mm (NASA POWER estimate)</title></rect>`;
    if (d.mm >= 3) s += `<text class="tl-label" x="${xi(i) + bw / 2}" y="${y(d.mm) - 4}" text-anchor="middle">${d.mm.toFixed(1)}</text>`;
    const dd = +d.date.slice(6);
    if (dd === 1 || dd % 4 === 2 || i === 0) s += `<text class="tl-label" x="${xi(i) + bw / 2}" y="${H - 8}" text-anchor="middle">${dd}${dd === 1 || i === 0 ? " " + monthName(d.date) : ""}</text>`;
  });
  for (const p of passes) {
    const xp = xd(p.date, p.hourFrac);
    if (xp == null) continue;
    const dash = p.key === "c" ? "4 3" : "";
    const col = p.key === "c" ? "#8a93a3" : "#e8e3d8";
    s += `<line x1="${xp}" x2="${xp}" y1="${P.t - 18}" y2="${P.t + ih}" stroke="${col}" stroke-width="${p.key === "c" ? 1 : 1.6}" stroke-dasharray="${dash}"/>`;
    s += `<text class="tl-pass" x="${xp}" y="${P.t - 22}" text-anchor="middle" style="fill:${col}">${esc(p.label)}</text>`;
  }
  s += `<line x1="${P.l}" x2="${P.l + iw}" y1="${P.t + ih}" y2="${P.t + ih}" stroke="#31405a"/>`;
  s += `<text class="tl-label" x="${P.l - 6}" y="${y(ymax) + 4}" text-anchor="end">${ymax.toFixed(0)}</text><text class="tl-label" x="${P.l - 6}" y="${P.t + ih}" text-anchor="end">0</text>`;
  s += `<text class="tl-label" x="${(xb + P.l + iw) / 2}" y="${P.t - 6}" text-anchor="middle" style="fill:#8a93a3">after B · not in pair</text>`;
  s += `<text class="tl-label" x="${(xa + xb) / 2}" y="${P.t + ih + 13}" text-anchor="middle" style="fill:#56d4e8">${days.filter((d) => d.date > a.date && d.date <= b.date).reduce((t, d) => t + d.mm, 0).toFixed(1)} mm between passes</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Daily precipitation estimate from 18 October to 8 November 2026 with radar pass times">${s}</svg>`;
}

export function monthName(d) { return ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][+d.slice(4, 6)]; }

/** Area brightened vs darkened as a function of the object seed threshold. */
export function sensitivitySvg(sens, current) {
  const W = 380, H = 170, P = { l: 40, r: 10, t: 14, b: 32 };
  const iw = W - P.l - P.r, ih = H - P.t - P.b;
  const vmax = Math.max(...sens.map((s) => s.area_brightened_ha)) * 1.1;
  const gw = iw / sens.length, bw = gw * 0.32;
  const y = (v) => P.t + ih - (v / vmax) * ih;
  let s = "";
  sens.forEach((r, i) => {
    const x0 = P.l + i * gw + gw * 0.16;
    const cur = r.core_db === current;
    s += `<rect x="${x0}" y="${y(r.area_brightened_ha)}" width="${bw}" height="${P.t + ih - y(r.area_brightened_ha)}" fill="#ff8a4c" opacity="${cur ? 1 : .55}"><title>≥${r.core_db} dB: ${r.area_brightened_ha} ha brightened in ${r.objects_brightened} objects</title></rect>`;
    s += `<rect x="${x0 + bw + 2}" y="${y(r.area_darkened_ha)}" width="${bw}" height="${P.t + ih - y(r.area_darkened_ha)}" fill="#4ea3ff" opacity="${cur ? 1 : .55}"><title>≥${r.core_db} dB: ${r.area_darkened_ha} ha darkened in ${r.objects_darkened} objects</title></rect>`;
    s += `<text class="axis" x="${x0 + bw}" y="${H - 16}" text-anchor="middle" style="fill:${cur ? "#e8e3d8" : "#8a93a3"}">${r.core_db}</text>`;
    s += `<text class="axis" x="${x0 + bw}" y="${H - 4}" text-anchor="middle">${(r.area_brightened_ha / Math.max(1, r.area_darkened_ha)).toFixed(1)}×</text>`;
  });
  for (const v of [0, 1000, 2000, 3000]) if (v <= vmax) s += `<text class="axis" x="${P.l - 4}" y="${y(v) + 3}" text-anchor="end">${v ? v / 1000 + "k" : 0}</text><line x1="${P.l}" x2="${P.l + iw}" y1="${y(v)}" y2="${y(v)}" stroke="#18202b"/>`;
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Brightened versus darkened area for each detection threshold">${s}</svg></div>`;
}
