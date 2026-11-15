// Front page: hero demo, worldwide explorer, Ceyhan list, prediction board. All numbers come from shipped JSON.
const $ = (s) => document.querySelector(s);
const NS = "http://www.w3.org/2000/svg";
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const f = (v, d = 2, sign = false) => (v == null || !Number.isFinite(v)) ? "—" : (sign && v > 0 ? "+" : "") + v.toFixed(d);
const pct = (v, d = 0) => (v == null || !Number.isFinite(v)) ? "—" : (100 * v).toFixed(d) + "%";
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const day = (s) => `${+s.slice(6, 8)} ${MON[+s.slice(4, 6) - 1]}`;
const GH = "https://github.com/deniz2077/between-passes/blob/main/";

// ------------------------------------------------------------------ hero demo
const CAPTIONS = [
  "<b>22 October.</b> NISAR's radar view of farmland around Ceyhan, southern Türkiye. Brighter means more radar echo.",
  "<b>3 November, 12 days later.</b> The first autumn rain fell in between. A normal change map flags every patch that changed, in white. But how much of it really changed?",
  "<b>Filter on.</b> NASA's SMAP satellite says the soil got wetter, and wet soil only ever looks brighter. So fields that got brighter <span class='c-w'>could be just the rain (blue)</span>. Fields that got darker can't be explained by rain: <span class='c-b'>something really changed there (orange)</span>.",
];
const DATES = ["22 Oct 2026", "3 Nov 2026", "3 Nov 2026 · filtered"];
let timer = null;
function setStep(n, user = false) {
  $("#demo-stage").dataset.step = String(n);
  const sw = $("#sweep"); sw.style.animation = "none"; void sw.offsetWidth; sw.style.animation = "";
  $("#demo-caption").innerHTML = CAPTIONS[n];
  $("#demo-date").textContent = DATES[n];
  document.querySelectorAll(".steps button").forEach((b) => b.setAttribute("aria-selected", String(+b.dataset.step === n)));
  $("#legend").classList.toggle("on", n === 2);
  document.querySelectorAll("#rain-bars i.day").forEach((i) => i.classList.toggle("on", n >= 1));
  if (user) { clearTimeout(timer); timer = null; }
}
function heroDemo(C, hero) {
  if (hero) {
    const tot = hero.could_be_weather_px + hero.beyond_weather_px;
    $("#lg-w").textContent = Math.round((100 * hero.could_be_weather_px) / tot) + "%";
    $("#lg-b").textContent = Math.round((100 * hero.beyond_weather_px) / tot) + "%";
  }
  const rain = C ? C.weather.series.filter((d) => d.date >= "20261022" && d.date <= "20261103") : [];
  const max = Math.max(1, ...rain.map((d) => d.mm));
  $("#rain-bars").innerHTML = rain.map((d, i) => {
    const pass = d.date === "20261022" || d.date === "20261103";
    const bar = `<i class="day" title="${day(d.date)}: ${d.mm} mm" style="height:${Math.max(4, (100 * d.mm) / max)}%"></i>`;
    return pass ? (i === 0 ? bar + '<i class="pass" style="height:100%"></i>' : '<i class="pass" style="height:100%"></i>' + bar) : bar;
  }).join("");
  document.querySelectorAll(".steps button").forEach((b) => b.addEventListener("click", () => setStep(+b.dataset.step, true)));
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { setStep(2); return; }
  const seq = [[0, 2400], [1, 5200], [2, 0]];
  let k = 0;
  const go = () => { const [s, wait] = seq[k++]; setStep(s); if (wait) timer = setTimeout(go, wait); };
  go();
}

// ------------------------------------------------------------------ problem + strip
function problem(sum) {
  $("#k-ratio").textContent = Math.round(sum.ratio) + "×";
  $("#k-share").textContent = pct(sum.pooled_weather_share_where_soil_moved);
  $("#b1v").textContent = pct(sum.median_changed_frac_soil_moved, 1);
  $("#b2v").textContent = pct(sum.median_changed_frac_soil_steady, 2);
  $("#b-n1").textContent = `${sum.soil_moved_n} places`;
  $("#b-n2").textContent = `${sum.soil_steady_n} places`;
  const io = new IntersectionObserver((es) => {
    if (!es.some((e) => e.isIntersecting)) return;
    const m = sum.median_changed_frac_soil_moved;
    $("#b1").style.width = "100%";
    $("#b2").style.width = Math.max(0.6, (100 * sum.median_changed_frac_soil_steady) / m) + "%";
    io.disconnect();
  }, { threshold: 0.4 });
  io.observe($(".bars"));
}

// ------------------------------------------------------------------ world explorer
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2;
function equalEarth(lon, lat) {
  const l = lon * Math.PI / 180, p = lat * Math.PI / 180;
  const t = Math.asin(M * Math.sin(p)), t2 = t * t, t6 = t2 * t2 * t2;
  return [(2 * Math.sqrt(3) * l * Math.cos(t)) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1)), t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))];
}
const MW = 1000, MH = 440, SC = MW / (2 * 2.7066 + 0.04);
const proj = (lon, lat) => { const [x, y] = equalEarth(lon, lat); return [MW / 2 + x * SC, MH / 2 + 22 - y * SC]; };
const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v); parent?.appendChild(e); return e; };
let SITES = [], cur = null, filt = "all";
const dots = new Map();
const VERDICT = { weather: "Mostly just the weather", beyond: "Something really changed", quiet: "Quiet: little changed" };

function drawMap(land) {
  const svg = $("#map");
  svg.setAttribute("viewBox", `0 0 ${MW} ${MH}`);
  const edge = [];
  for (let lat = -62; lat <= 84; lat += 2) edge.push(proj(180, lat));
  for (let lat = 84; lat >= -62; lat -= 2) edge.push(proj(-180, lat));
  el("path", { d: "M" + edge.map((p) => p.map((v) => v.toFixed(1)).join(",")).join("L") + "Z", class: "sphere" }, svg);
  for (let lon = -150; lon <= 150; lon += 30) {
    const g = []; for (let lat = -60; lat <= 84; lat += 4) g.push(proj(lon, lat));
    el("path", { d: "M" + g.map((p) => p.map((v) => v.toFixed(1)).join(",")).join("L"), class: "grat" }, svg);
  }
  let d = "";
  for (const poly of land.polygons) for (const ring of poly) {
    if (ring.every(([, la]) => la < -60)) continue;
    d += "M" + ring.map(([lo, la]) => proj(lo, Math.max(la, -62)).map((v) => v.toFixed(1)).join(",")).join("L") + "Z";
  }
  el("path", { d, class: "land", "fill-rule": "evenodd" }, svg);
  const order = [...SITES].sort((a, b) => (a.verdict === "quiet") - (b.verdict === "quiet") || a.changed_frac - b.changed_frac).reverse();
  for (const s of order) {
    const [x, y] = proj(s.lon, s.lat);
    const r = s.id === "ceyhan" ? 6.5 : 3.6 + Math.min(5, Math.sqrt(100 * s.changed_frac) * 1.6);
    const c = el("circle", { cx: x.toFixed(1), cy: y.toFixed(1), r: r.toFixed(1), class: `dot ${s.verdict}`, tabindex: 0, role: "button", "aria-label": `${s.name}: ${VERDICT[s.verdict]}` }, svg);
    el("title", {}, c).textContent = `${s.name} · ${VERDICT[s.verdict]}`;
    c.addEventListener("click", () => select(s));
    c.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(s); } });
    dots.set(s.id, c);
  }
  const cey = SITES.find((s) => s.id === "ceyhan");
  if (cey) { const [x, y] = proj(cey.lon, cey.lat); el("circle", { cx: x, cy: y, r: 11, class: "cey" }, svg); }
}

function siteText(s) {
  const smap = `SMAP ${f(s.sm_a, 2)} → ${f(s.sm_b, 2)} m³/m³`;
  if (s.verdict === "quiet") return `Less than 1% of this patch changed by 3 dB or more (${pct(s.changed_frac, 1)}). Nothing to flag.`;
  if (s.verdict === "weather") return `The soil got <b>${s.soil}</b> (${smap}). ${pct(s.weather_share)} of the land that changed went the way wetter or drier soil would push it, so most of this change <span class="c-w">could be just the weather</span>.`;
  if (s.soil === "steady") return `The soil barely changed (${smap}), yet ${pct(s.changed_frac, 1)} of the patch changed. The weather can't explain that: <span class="c-b">something on the ground changed</span> (crops, water, building, or a local shower SMAP can't see).` +
    (s.rain_mm >= 10 ? ` <span class="small">Note: NASA POWER estimates ${f(s.rain_mm, 0)} mm of rain between the passes, so local wetting or drying that SMAP's 9 km cell missed is possible here.</span>` : "");
  return `The soil got <b>${s.soil}</b> (${smap}), but ${pct(1 - s.weather_share)} of the changed land went the other way. <span class="c-b">That part isn't the weather.</span>`;
}

function select(s, push = true) {
  cur = s;
  dots.forEach((c, id) => c.classList.toggle("sel", id === s.id));
  const base = s.base || `data/sites/${s.id}/`;
  const tot = s.weather_frac + s.beyond_frac;
  const wPct = tot ? (100 * s.weather_frac) / tot : 0;
  $("#card").innerHTML = `
    <div class="card-head">
      <div class="where">${esc(s.name)}</div>
      <div class="meta mono">${f(Math.abs(s.lat), 2)}°${s.lat >= 0 ? "N" : "S"} ${f(Math.abs(s.lon), 2)}°${s.lon >= 0 ? "E" : "W"} · ${day(s.date_a)} → ${day(s.date_b)} 2026 · ${s.id === "ceyhan" ? "17.6 × 13.6 km" : "10 × 10 km"}</div>
      <div class="verdict ${s.verdict}"><i class="sw ${s.verdict}"></i>${VERDICT[s.verdict]}</div>
    </div>
    <div class="swipe filt" id="swipe" aria-label="Drag to compare the two radar passes">
      <img class="s-before" src="${base}before.jpg" alt="NISAR radar, ${day(s.date_a)}" />
      <img class="s-after" src="${base}after.jpg" alt="NISAR radar, ${day(s.date_b)}" />
      <img class="s-filter" src="${base}filter.png" alt="Filtered change: blue could be the weather, amber beyond it" />
      <div class="handle" id="handle"></div>
      <span class="tag l">${day(s.date_a)}</span><span class="tag r">${day(s.date_b)}</span>
    </div>
    <div class="card-tools">
      <button class="btn small" id="t-filter" aria-pressed="true">Filter on</button>
      <span class="small" style="align-self:center">Drag across the picture to compare the two dates. Blue: could be just the rain. Orange: really changed.</span>
    </div>
    ${tot ? `<div class="split-bar" aria-hidden="true"><i style="width:${wPct}%;background:var(--weather)"></i><i style="width:${100 - wPct}%;background:var(--beyond)"></i></div>
    <div class="split-lab"><span class="c-w">${Math.round(wPct)}% could be just the rain</span><span class="c-b">${Math.round(100 - wPct)}% really changed</span></div>` : ""}
    <p class="card-text" style="margin-top:12px">${siteText(s)}</p>
    <dl class="kv">
      <dt>Land that changed strongly</dt><dd>${pct(s.changed_frac, 1)}</dd>
      <dt>Soil wetness (NASA SMAP, m³/m³)</dt><dd>${f(s.sm_a, 3)} → ${f(s.sm_b, 3)}${s.exploratory_smap ? "*" : ""}</dd>
      <dt>Rain between passes (NASA POWER)</dt><dd>${s.rain_mm == null ? "—" : f(s.rain_mm, 1) + " mm"}</dd>
      <dt>Radar brightness change, whole patch</dt><dd>${f(s.dHH_db, 2, true)} dB</dd>
      <dt>…expected from the soil wetness alone</dt><dd>${f(s.expected_dHH_db, 2, true)} dB</dd>
    </dl>
    ${s.exploratory_smap ? `<p class="card-text small">* Ceyhan's SMAP values use a ±2-day window (exploratory, labelled). <a href="lab.html#tour">Open the Ceyhan lab →</a></p>` : ""}
    <div class="card-foot">
      <button class="btn small" id="share">Copy link to this place</button>
      <span><button class="btn small" id="prev" aria-label="Previous place">←</button> <button class="btn small" id="next" aria-label="Next place">→</button></span>
    </div>`;
  const sw = $("#swipe"), after = sw.querySelector(".s-after"), h = $("#handle");
  const setX = (x) => { const r = sw.getBoundingClientRect(); const p = Math.min(100, Math.max(0, ((x - r.left) / r.width) * 100)); after.style.clipPath = `inset(0 0 0 ${p}%)`; h.style.left = p + "%"; };
  let drag = false;
  sw.addEventListener("pointerdown", (e) => { drag = true; sw.setPointerCapture(e.pointerId); setX(e.clientX); });
  sw.addEventListener("pointermove", (e) => drag && setX(e.clientX));
  sw.addEventListener("pointerup", () => { drag = false; });
  $("#t-filter").addEventListener("click", (e) => { const on = sw.classList.toggle("filt"); e.currentTarget.setAttribute("aria-pressed", String(on)); e.currentTarget.textContent = on ? "Filter on" : "Filter off"; });
  $("#share").addEventListener("click", async (e) => {
    const url = location.origin + location.pathname + "#site=" + s.id;
    try { await navigator.clipboard.writeText(url); e.target.textContent = "Link copied"; } catch { e.target.textContent = url; }
  });
  const list = visible();
  const i = list.indexOf(s);
  $("#prev").addEventListener("click", () => select(list[(i - 1 + list.length) % list.length]));
  $("#next").addEventListener("click", () => select(list[(i + 1) % list.length]));
  if (push) history.replaceState(null, "", "#site=" + s.id);
}
const visible = () => SITES.filter((s) => filt === "all" || s.verdict === filt).sort((a, b) => a.lon - b.lon);

function explorer(data, land) {
  SITES = data.sites;
  const n = (v) => SITES.filter((s) => s.verdict === v).length;
  $("#c-all").textContent = SITES.length;
  for (const v of ["beyond", "weather", "quiet"]) $(`#c-${v}`).textContent = n(v);
  drawMap(land);
  document.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
    filt = b.dataset.v;
    document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c === b));
    dots.forEach((c, id) => c.classList.toggle("off", filt !== "all" && SITES.find((s) => s.id === id).verdict !== filt));
    if (cur && filt !== "all" && cur.verdict !== filt) select(visible()[0]);
  }));
  const m = location.hash.match(/^#site=([\w-]+)/);
  const first = (m && SITES.find((s) => s.id === m[1])) || SITES.find((s) => s.id === "ceyhan");
  select(first, false);
  if (m) setTimeout(() => $("#world").scrollIntoView(), 50);
}

// ------------------------------------------------------------------ Ceyhan
let lookAll = false;
function ceyhan(C, cey) {
  const so = C.stats.objects, op = C.optical;
  const rain = C.weather.series.filter((d) => d.date > "20261022" && d.date <= "20261103").reduce((a, d) => a + d.mm, 0);
  $("#c-facts").innerHTML = [
    [`${f(rain, 0)} mm`, "of rain between the passes, mostly on 28–29 October (NASA POWER)."],
    [`${f(cey.sm_a, 2)}→${f(cey.sm_b, 2)}`, "soil moisture measured by NASA SMAP: the soil more than doubled in water."],
    [`${so.brightened}`, `fields got <span class="c-w">brighter</span>: what wetter soil does. An optical satellite (NASA HLS) shows only ${Math.round(100 * op.brightened.frac_vegetation_loss)}% of them lost their plants.`],
    [`${so.darkened}`, `fields got <span class="c-b">darker</span>: wetter soil can't do that, so something else changed them.`],
    [`${f(C.stats.urban_control.dHH_db_region, 2, true)}`, "dB: the town centre, which shouldn't change, barely moved. The measurement is stable."],
  ].map(([k, v]) => `<li><b>${k}</b><span>${v}</span></li>`).join("");
  const places = C.context.places;
  const near = (px) => { let b = null, bd = Infinity; for (const p of places) { const d = Math.hypot(p.px[0] - px[0], p.px[1] - px[1]); if (d < bd) { bd = d; b = p; } } return { name: b?.name ?? "—", km: (bd * 20) / 1000 }; };
  const dark = C.objects.filter((o) => o.sign === "darkened").sort((a, b) => b.area_ha - a.area_ha);
  const render = () => {
    const rows = lookAll ? dark : dark.slice(0, 8);
    $("#look-list").innerHTML = rows.map((o, i) => {
      const n = near(o.centroid_px);
      const opt = o.optical_class && o.optical_class !== "no clear optical view" ? o.optical_class.replace("little vegetation change", "plants unchanged") : "no clear optical view";
      return `<li><a href="lab.html#object-${o.id}"><span class="r">${i + 1}</span><span>${esc(n.name)} <small>${f(n.km, 1)} km away · ${esc(opt)}</small></span><span class="a">${f(o.area_ha, 1)} ha</span><span class="v">${f(o.dHH_db, 1, true)} dB</span></a></li>`;
    }).join("");
    $("#look-more").textContent = lookAll ? "Show top 8" : `Show all ${dark.length}`;
  };
  $("#look-more").addEventListener("click", () => { lookAll = !lookAll; render(); });
  render();
}

// ------------------------------------------------------------------ predictions board
const okV = (v) => /^(CONFIRMED|WETTING)/.test(v || "") ? "ok" : /^(REFUTED|PERSISTENT)/.test(v || "") ? "no" : "mid";
async function board() {
  const get = (n) => fetch("data/ceyhan/" + n).then((r) => r.ok ? r.json() : null).catch(() => null);
  const [P, P2] = await Promise.all([get("prediction.json"), get("prediction2.json")]);
  const R2 = P2?.scored ? await get("prediction2_result.json") : null;
  const R = P?.scored ? await get("prediction_result.json") : null;
  const st = (r, txt) => r ? `<span class="st ${okV(r.verdict)}">${esc(r.verdict)}</span><span class="num">${txt(r)}</span>` : `<span class="st wait">Waiting for NASA to release the data</span>`;
  const rel = (r) => `fields vs farmland ${f(r.relative, 2, true)} dB · ${Math.round(100 * r.frac_fields_darker)}% of fields darker · town ${f(r.dB_control, 2, true)} dB`;
  const cards = [
    { h: "Dusk orbit", m: "track 079 · 29 Oct → 10 Nov", p: "The bright fields get at least 1 dB darker than the farmland around them, and two thirds of them darken.", s: st(R2?.["079"], rel), lock: "PREDICTION2.md" },
    { h: "Dawn orbit", m: "track 071 · 29 Oct → 10 Nov", p: "The same test, seen from the other side of the sky, at sunrise.", s: st(R2?.["071"], rel), lock: "PREDICTION2.md" },
    { h: "My study's orbit", m: "track 151 · 3 Nov → 15 Nov", p: `The bright fields lose at least half of their brightening (${f(P?.P1_threshold_dHH_BC_db, 2)} dB overall).`,
      s: st(R, (r) => `overall ${f(r.aggregate_dHH_BC_db, 2, true)} dB · typical field reversed ${f(100 * r.median_R, 0)}% · town ${f(r.control_dHH_BC_db, 2, true)} dB`), lock: "PREDICTION.md" },
  ];
  $("#board").innerHTML = cards.map((c) => `<div class="chk"><div class="chk-h"><b>${c.h}</b><span>${c.m}</span></div><p>${c.p}</p>${c.s}<span class="num"><a href="${GH}research/prediction/${c.lock}">locked prediction</a></span></div>`).join("")
    + `<p class="small">If the fields stay bright, my explanation is wrong. A check doesn't count if it rains again or the town centre moves by more than 0.5 dB.</p>`;
  const scored = [R2?.["079"], R2?.["071"], R].filter(Boolean);
  $("#pr-count").textContent = scored.length ? `${scored.length} of 3 scored so far: ${scored.filter((r) => okV(r.verdict) === "ok").length} confirmed.` : "None scored yet: NASA usually releases NISAR data a few days to three weeks after a pass.";
}

// ------------------------------------------------------------------ new places run today with bp_check.py
async function checks() {
  const d = await fetch("data/checks/checks.json").then((r) => r.ok ? r.json() : null).catch(() => null);
  if (!d) return;
  const ok = d.checks.filter((c) => c.verdict), no = d.checks.filter((c) => !c.verdict);
  $("#new-sites").innerHTML = `<h3 style="margin-top:28px">New places, run today with that command</h3>
    <p class="small">${ok.length} of ${d.checks.length} farming regions worked. Chosen by name, not part of the statistical test. Click one to open its card.</p>
    <div class="nc-grid">${ok.map((c) => `<button class="nc" data-id="${c.id}">
      <span class="nc-img"><img src="${c.base}after.jpg" alt="" loading="lazy"><img src="${c.base}filter.png" alt="" loading="lazy"></span>
      <span class="nc-t"><b>${esc(c.name)}</b><span class="verdict ${c.verdict}" style="margin:2px 0 0;font-size:13px"><i class="sw ${c.verdict}"></i>${VERDICT[c.verdict]}</span>
      <small class="mono">${pct(c.changed_frac, 1)} changed · ${c.soil} soil · ${f(c.rain_mm, 0)} mm rain</small></span></button>`).join("")}</div>
    ${no.length ? `<p class="small" style="margin-top:12px"><b>Didn't run, and why:</b> ${no.map((c) => `${esc(c.name)}: ${esc(c.reason.replace(/ \(.*\)\.?$/, "").replace(/\.$/, ""))}`).join(" · ")}.</p>` : ""}`;
  document.querySelectorAll(".nc").forEach((b) => b.addEventListener("click", () => {
    const c = ok.find((x) => x.id === b.dataset.id);
    select(c); $("#world").scrollIntoView({ behavior: "smooth" });
  }));
}

// ------------------------------------------------------------------ misc
function themes() {
  const cur = document.documentElement.dataset.theme || "ink";
  document.querySelectorAll(".themes button").forEach((b) => {
    b.classList.toggle("on", b.dataset.theme === cur);
    b.addEventListener("click", () => {
      document.documentElement.dataset.theme = b.dataset.theme === "ink" ? "" : b.dataset.theme;
      try { localStorage.setItem("bp-theme", b.dataset.theme); } catch (e) {}
      document.querySelectorAll(".themes button").forEach((x) => x.classList.toggle("on", x === b));
    });
  });
}

function scrollspy() {
  const links = [...document.querySelectorAll('.nav nav a[href^="#"]')];
  const secs = links.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
  const upd = () => {
    const y = scrollY + 140;
    let cur = secs[0];
    for (const s of secs) if (s.id !== "top" && s.getBoundingClientRect().top + scrollY <= y) cur = s;
    links.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + cur.id));
  };
  addEventListener("scroll", upd, { passive: true }); upd();
}

async function init() {
  themes();
  scrollspy();
  $("#copy").addEventListener("click", async (e) => { try { await navigator.clipboard.writeText($("#cmd").textContent); e.target.textContent = "Copied"; } catch { e.target.textContent = "Select and copy"; } });
  const j = (u) => fetch(u).then((r) => r.ok ? r.json() : null).catch(() => null);
  const [C, hero, S, land] = await Promise.all([j("data/ceyhan/case.json"), j("img/hero/hero.json"), j("data/sites/sites.json"), j("data/global/land.json")]);
  heroDemo(C, hero);
  if (S) { problem(S.summary); if (land) explorer(S, land); }
  if (C && S) ceyhan(C, S.sites.find((s) => s.id === "ceyhan"));
  board();
  await checks();
  // content above may have changed height while loading: land on the requested section again
  const h = location.hash;
  if (/^#(problem|world|ceyhan|predictions|run|lab)$/.test(h)) requestAnimationFrame(() => document.querySelector(h)?.scrollIntoView());
}
init();
