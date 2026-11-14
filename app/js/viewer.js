// Canvas viewer for a single georeferenced raster grid (pixel coordinates).
// Layers are offscreen canvases at data resolution; vector overlays are drawn in screen space.

export const HH_RANGE = [-20, 0];   // fixed display stretch (dB) — identical for both dates
export const DELTA_MAX = 6;         // ΔdB colour saturation

const UP = [255, 138, 76], DOWN = [78, 163, 255];

export function grayImage(db, w, h) {
  const img = new ImageData(w, h);
  const [lo, hi] = HH_RANGE;
  for (let i = 0; i < db.length; i++) {
    const v = db[i];
    if (!Number.isFinite(v)) continue;           // alpha 0 = no data
    const t = Math.min(1, Math.max(0, (v - lo) / (hi - lo)));
    const g = Math.round(255 * t);
    const o = i * 4;
    img.data[o] = g; img.data[o + 1] = g; img.data[o + 2] = g; img.data[o + 3] = 255;
  }
  return img;
}

/** Change map: dimmed grayscale context, tinted by sign with opacity ∝ |Δ|. */
export function deltaImage(delta, baseDb, w, h, scaleW = 1) {
  const img = new ImageData(w, h);
  const [lo, hi] = HH_RANGE;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const d = delta[i];
      if (!Number.isFinite(d)) continue;
      const bi = scaleW === 1 ? i : (y * scaleW) * (w * scaleW) + x * scaleW;
      const b = baseDb ? baseDb[bi] : -10;
      const g = 0.38 * 255 * Math.min(1, Math.max(0, ((Number.isFinite(b) ? b : -10) - lo) / (hi - lo)));
      const a = Math.min(1, Math.abs(d) / DELTA_MAX) ** 0.75;
      const c = d >= 0 ? UP : DOWN;
      const o = i * 4;
      img.data[o] = g + (c[0] - g) * a;
      img.data[o + 1] = g + (c[1] - g) * a;
      img.data[o + 2] = g + (c[2] - g) * a;
      img.data[o + 3] = 255;
    }
  }
  return img;
}

export function deltaLegendGradient() {
  const stops = [];
  for (let k = 0; k <= 12; k++) {
    const d = -DELTA_MAX + k;
    const a = Math.min(1, Math.abs(d) / DELTA_MAX) ** 0.75;
    const g = 0.38 * 255 * 0.5;
    const c = d >= 0 ? UP : DOWN;
    const rgb = c.map((cc) => Math.round(g + (cc - g) * a));
    stops.push(`rgb(${rgb}) ${(k / 12) * 100}%`);
  }
  return `linear-gradient(90deg, ${stops.join(",")})`;
}

/** Boundary pixels of labelled regions (objects) and of a boolean mask (control). */
export function edgesImage(labels, signOf, w, h, selected, controlMask) {
  const img = new ImageData(w, h);
  const put = (i, r, g, b, a) => { const o = i * 4; img.data[o] = r; img.data[o + 1] = g; img.data[o + 2] = b; img.data[o + 3] = a; };
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const l = labels ? labels[i] : 0;
      if (l) {
        const edge = x === 0 || y === 0 || x === w - 1 || y === h - 1 ||
          labels[i - 1] !== l || labels[i + 1] !== l || labels[i - w] !== l || labels[i + w] !== l;
        if (edge) {
          if (l === selected) put(i, 255, 255, 255, 255);
          else if (signOf(l) > 0) put(i, 255, 196, 160, 235);
          else put(i, 170, 210, 255, 235);
        }
      }
      if (controlMask && controlMask[i]) {
        const edge = !controlMask[i - 1] || !controlMask[i + 1] || !controlMask[i - w] || !controlMask[i + w];
        if (edge) put(i, 232, 197, 71, 255);
      }
    }
  }
  return img;
}

export function toCanvas(img) {
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  c.getContext("2d").putImageData(img, 0, 0);
  return c;
}

export class Viewer {
  constructor(canvas, w, h) {
    this.canvas = canvas; this.ctx = canvas.getContext("2d");
    this.w = w; this.h = h;
    this.scale = 1; this.ox = 0; this.oy = 0;
    this.layers = { base: null, baseB: null, edges: null, scaleBase: 1 };
    this.mode = "delta"; this.swipe = 0.5;
    this.overlay = null;             // function(ctx, viewer)
    this.pointers = new Map();
    this.onHover = () => {}; this.onClick = () => {}; this.onChange = () => {};
    this.drawMode = false; this.poly = []; this.onPolygon = () => {};
    this._raf = 0;
    this._bind();
    new ResizeObserver(() => this.resize()).observe(canvas);
    this.resize();
  }

  resize() {
    const r = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.dpr = dpr; this.cw = r.width; this.ch = r.height;
    this.canvas.width = Math.max(1, Math.round(r.width * dpr));
    this.canvas.height = Math.max(1, Math.round(r.height * dpr));
    if (!this._fitted && r.width > 0) { this.fit(); this._fitted = true; }
    this.request();
  }

  fit() {
    const s = Math.min(this.cw / this.w, this.ch / this.h) * 0.98;
    this.scale = s; this.ox = (this.cw - this.w * s) / 2; this.oy = (this.ch - this.h * s) / 2;
    this.request(); this.onChange();
  }

  focus(bbox, pad = 2.2) {  // bbox [x0,y0,x1,y1] in data px
    const bw = Math.max(20, bbox[2] - bbox[0]), bh = Math.max(20, bbox[3] - bbox[1]);
    const s = Math.min(24, Math.min(this.cw / (bw * pad), this.ch / (bh * pad)));
    const cx = (bbox[0] + bbox[2]) / 2, cy = (bbox[1] + bbox[3]) / 2;
    this.scale = s; this.ox = this.cw / 2 - cx * s; this.oy = this.ch / 2 - cy * s;
    this.request(); this.onChange();
  }

  toData(sx, sy) { return [(sx - this.ox) / this.scale, (sy - this.oy) / this.scale]; }
  toScreen(x, y) { return [x * this.scale + this.ox, y * this.scale + this.oy]; }

  zoomAt(sx, sy, f) {
    const ns = Math.min(40, Math.max(0.15, this.scale * f));
    const [dx, dy] = this.toData(sx, sy);
    this.scale = ns; this.ox = sx - dx * ns; this.oy = sy - dy * ns;
    this.request(); this.onChange();
  }

  request() { if (!this._raf) this._raf = requestAnimationFrame(() => { this._raf = 0; this.render(); }); }

  _drawLayer(ctx, cnv, factor = 1) {
    if (!cnv) return;
    ctx.imageSmoothingEnabled = this.scale * factor < 1.5;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(cnv, this.ox, this.oy, this.w * this.scale, this.h * this.scale);
  }

  render() {
    const ctx = this.ctx, dpr = this.dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#07090c"; ctx.fillRect(0, 0, this.cw, this.ch);
    const L = this.layers;
    if (this.mode === "swipe" && L.base && L.baseB) {
      const sx = this.cw * this.swipe;
      this._drawLayer(ctx, L.base);
      ctx.save(); ctx.beginPath(); ctx.rect(sx, 0, this.cw - sx, this.ch); ctx.clip();
      this._drawLayer(ctx, L.baseB); ctx.restore();
    } else {
      this._drawLayer(ctx, L.base, L.scaleBase);
    }
    if (L.edges) this._drawLayer(ctx, L.edges);
    if (this.overlay) this.overlay(ctx, this);
    if (this.mode === "swipe") this._drawSwipeHandle(ctx);
    if (this.poly.length) this._drawPoly(ctx);
  }

  _drawSwipeHandle(ctx) {
    const x = this.cw * this.swipe;
    ctx.fillStyle = "#e8e3d8"; ctx.fillRect(x - 1, 0, 2, this.ch);
    ctx.beginPath(); ctx.arc(x, this.ch / 2, 15, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#0b0e13"; ctx.font = "600 12px IBM Plex Sans, sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("⇆", x, this.ch / 2 + 1);
    ctx.font = "600 12px IBM Plex Mono, monospace";
    const tag = (t, tx, align) => { ctx.textAlign = align; ctx.fillStyle = "rgba(11,14,19,.85)"; const m = ctx.measureText(t).width; const bx = align === "right" ? tx - m - 8 : tx - 4; ctx.fillRect(bx, this.ch - 64, m + 12, 22); ctx.fillStyle = "#e8e3d8"; ctx.fillText(t, tx + (align === "right" ? -2 : 2), this.ch - 53); };
    tag("22 Oct", x - 10, "right"); tag("3 Nov", x + 10, "left");
  }

  _drawPoly(ctx) {
    const pts = this.poly.map(([x, y]) => this.toScreen(x, y));
    ctx.save();
    ctx.lineWidth = 2; ctx.strokeStyle = "#56d4e8"; ctx.fillStyle = "rgba(86,212,232,.12)";
    ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    if (this.polyClosed) { ctx.closePath(); ctx.fill(); }
    else if (this._hoverPt) ctx.lineTo(...this._hoverPt);
    ctx.stroke();
    ctx.fillStyle = "#56d4e8";
    pts.forEach(([x, y], i) => { ctx.beginPath(); ctx.arc(x, y, i === 0 && !this.polyClosed ? 6 : 3, 0, Math.PI * 2); ctx.fill(); });
    ctx.restore();
  }

  _bind() {
    const c = this.canvas;
    const pos = (e) => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    let drag = null, moved = 0, pinch = null;
    c.addEventListener("pointerdown", (e) => {
      c.setPointerCapture(e.pointerId);
      this.pointers.set(e.pointerId, pos(e));
      moved = 0;
      if (this.pointers.size === 2) {
        const [a, b] = [...this.pointers.values()];
        pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s: this.scale };
        drag = null; return;
      }
      const [x, y] = pos(e);
      const nearSwipe = this.mode === "swipe" && Math.abs(x - this.cw * this.swipe) < 22;
      drag = { x, y, ox: this.ox, oy: this.oy, swipe: nearSwipe };
    });
    c.addEventListener("pointermove", (e) => {
      const p = pos(e);
      if (this.pointers.has(e.pointerId)) this.pointers.set(e.pointerId, p);
      if (pinch && this.pointers.size === 2) {
        const [a, b] = [...this.pointers.values()];
        const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
        this.zoomAt(mx, my, (pinch.s * d / pinch.d) / this.scale);
        moved = 99; return;
      }
      if (drag) {
        const dx = p[0] - drag.x, dy = p[1] - drag.y;
        moved = Math.max(moved, Math.hypot(dx, dy));
        if (drag.swipe) { this.swipe = Math.min(1, Math.max(0, p[0] / this.cw)); this.request(); }
        else if (moved > 3) { c.classList.add("dragging"); this.ox = drag.ox + dx; this.oy = drag.oy + dy; this.request(); this.onChange(); }
      }
      if (this.drawMode && !this.polyClosed) { this._hoverPt = p; this.request(); }
      this.onHover(...this.toData(...p), p);
    });
    const up = (e) => {
      this.pointers.delete(e.pointerId);
      c.classList.remove("dragging");
      if (pinch) { if (this.pointers.size < 2) pinch = null; drag = null; return; }
      if (drag && moved <= 3 && !drag.swipe) {
        const p = pos(e);
        const [dx, dy] = this.toData(...p);
        if (this.drawMode) this._addVertex(dx, dy, p);
        else this.onClick(dx, dy);
      }
      drag = null;
    };
    c.addEventListener("pointerup", up);
    c.addEventListener("pointercancel", up);
    c.addEventListener("pointerleave", () => { this._hoverPt = null; this.onHover(NaN, NaN); });
    c.addEventListener("wheel", (e) => { e.preventDefault(); const [x, y] = pos(e); this.zoomAt(x, y, Math.exp(-e.deltaY * 0.0015)); }, { passive: false });
    c.addEventListener("dblclick", (e) => {
      e.preventDefault();
      if (this.drawMode) { this._closePoly(); return; }
      const [x, y] = pos(e); this.zoomAt(x, y, 2);
    });
    c.addEventListener("keydown", (e) => {
      const k = e.key, st = 60;
      if (k === "+" || k === "=") this.zoomAt(this.cw / 2, this.ch / 2, 1.4);
      else if (k === "-" || k === "_") this.zoomAt(this.cw / 2, this.ch / 2, 1 / 1.4);
      else if (k === "ArrowLeft") { this.ox += st; this.request(); }
      else if (k === "ArrowRight") { this.ox -= st; this.request(); }
      else if (k === "ArrowUp") { this.oy += st; this.request(); }
      else if (k === "ArrowDown") { this.oy -= st; this.request(); }
      else if (k === "0") this.fit();
      else if (k === "Escape" && this.drawMode) { this.cancelDraw(); this.onPolygon(null); }
      else return;
      e.preventDefault();
    });
  }

  startDraw() { this.drawMode = true; this.poly = []; this.polyClosed = false; this.canvas.classList.add("drawing"); this.request(); }
  cancelDraw() { this.drawMode = false; this.poly = []; this.polyClosed = false; this._hoverPt = null; this.canvas.classList.remove("drawing"); this.request(); }
  _addVertex(x, y, sp) {
    if (this.poly.length >= 3) {
      const [fx, fy] = this.toScreen(...this.poly[0]);
      if (Math.hypot(sp[0] - fx, sp[1] - fy) < 12) { this._closePoly(); return; }
    }
    this.poly.push([Math.min(this.w, Math.max(0, x)), Math.min(this.h, Math.max(0, y))]);
    this.request();
  }
  _closePoly() {
    // dblclick also fires two clicks; drop duplicate trailing vertices
    const p = this.poly.filter((v, i, a) => i === 0 || Math.hypot(v[0] - a[i - 1][0], v[1] - a[i - 1][1]) > 0.5);
    if (p.length < 3) return;
    this.poly = p; this.polyClosed = true; this.drawMode = false; this._hoverPt = null;
    this.canvas.classList.remove("drawing"); this.request();
    this.onPolygon(p);
  }
}
