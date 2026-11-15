// Intro background: a faint, slowly drifting star field (white/grey only, so it never
// competes with the blue/amber data colours) and one NISAR ground track with the
// satellite passing along it. Drawn in code, no images. Pauses when off-screen.
const cv = document.getElementById("sky");
if (cv) {
  const ctx = cv.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let W = 0, H = 0, dpr = 1, stars = [], visible = true, t0 = performance.now();
  const rnd = (a, b) => a + Math.random() * (b - a);

  function resize() {
    dpr = Math.min(2, devicePixelRatio || 1);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round((W * H) / (W < 600 ? 5200 : 3600));
    stars = Array.from({ length: n }, () => ({
      x: rnd(0, W), y: rnd(0, H), r: Math.random() < 0.06 ? rnd(1.1, 1.6) : rnd(0.35, 0.95),
      a: rnd(0.22, 0.8), tw: Math.random() < 0.25 ? rnd(0.4, 1.2) : 0, ph: rnd(0, 6.28),
      g: Math.random() < 0.3 ? 170 : 235,
    }));
  }

  // ground track: from upper right to lower left, like a descending NISAR pass
  const track = () => W < 980 ? [[W * 0.95, -H * 0.05], [W * 0.55, H * 0.55]] : [[W * 0.585, -H * 0.05], [W * 0.43, H * 1.05]];

  function draw(now) {
    const s = (now - t0) / 1000;
    ctx.clearRect(0, 0, W, H);
    for (const p of stars) {
      const x = still ? p.x : (p.x - s * 2.2 + W * 10) % W;
      const a = p.tw ? p.a * (0.6 + 0.4 * Math.sin(s * p.tw + p.ph)) : p.a;
      ctx.fillStyle = `rgba(${p.g},${p.g},${p.g + 8},${a})`;
      ctx.beginPath(); ctx.arc(x, p.y, p.r, 0, 6.283); ctx.fill();
    }
    const [[x0, y0], [x1, y1]] = track();
    ctx.strokeStyle = "rgba(236,234,228,.09)"; ctx.lineWidth = 1; ctx.setLineDash([2, 6]);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.setLineDash([]);
    const k = still ? 0.3 : (s / 16) % 1;            // one pass every 16 s
    const x = x0 + (x1 - x0) * k, y = y0 + (y1 - y0) * k;
    const tail = 0.06;
    const g = ctx.createLinearGradient(x0 + (x1 - x0) * (k - tail), y0 + (y1 - y0) * (k - tail), x, y);
    g.addColorStop(0, "rgba(236,234,228,0)"); g.addColorStop(1, "rgba(236,234,228,.35)");
    ctx.strokeStyle = g; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(x0 + (x1 - x0) * Math.max(0, k - tail), y0 + (y1 - y0) * Math.max(0, k - tail)); ctx.lineTo(x, y); ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,.95)";
    ctx.shadowColor = "rgba(255,255,255,.8)"; ctx.shadowBlur = 8;
    ctx.beginPath(); ctx.arc(x, y, 2.2, 0, 6.283); ctx.fill(); ctx.shadowBlur = 0;
  }

  function loop(now) { if (visible && !document.hidden) draw(now); requestAnimationFrame(loop); }
  resize(); draw(performance.now());
  addEventListener("resize", () => { resize(); draw(performance.now()); });
  new IntersectionObserver((e) => { visible = e[0].isIntersecting; }).observe(cv);
  if (!still) requestAnimationFrame(loop);
}
