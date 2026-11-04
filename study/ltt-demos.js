// Interactive demonstrations for the left-turning tendencies page: torque reaction,
// the spiraling slipstream, P-factor, and gyroscopic precession. Each one is a toy model
// tuned to behave the way the handbook describes, not a flight simulation.
(function () {
  const css = getComputedStyle(document.documentElement);
  const col = (v, d) => css.getPropertyValue(v).trim() || d;
  const TEXT = col('--text', '#E5E8EA'), MUTED = col('--muted', '#9BA5AC'), ACCENT = col('--accent', '#CF6B7B'), SURF2 = col('--surface-2', '#272C31'), LINE = col('--line', '#353B41');
  const BLUE = '#7fb6f0';
  const TAU = Math.PI * 2, deg = Math.PI / 180;
  const $ = id => document.getElementById(id);
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Shared helpers ----------
  const demos = [];
  function demo(id) {
    const c = $(id); if (!c) return null;
    const ctx = c.getContext('2d'), d = { c, ctx, W: 0, H: 0, draw: null, on: true };
    const resize = () => { const dpr = Math.min(devicePixelRatio || 1, 2); d.W = c.clientWidth; d.H = c.clientHeight; c.width = d.W * dpr; c.height = d.H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
    new ResizeObserver(resize).observe(c); resize();
    if ('IntersectionObserver' in window) new IntersectionObserver(e => { d.on = e[0].isIntersecting; }, { rootMargin: '80px' }).observe(c);
    demos.push(d); return d;
  }
  function range(id, fmt) {
    const el = $(id), out = el.previousElementSibling;
    const upd = () => { out.textContent = fmt(+el.value); };
    el.addEventListener('input', upd); upd();
    return () => +el.value;
  }
  function text(ctx, s, x, y, color, align, size, weight) {
    ctx.fillStyle = color || TEXT; ctx.font = `${weight || 600} ${size || 13}px "Barlow Semi Condensed", sans-serif`; ctx.textAlign = align || 'left'; ctx.fillText(s, x, y);
  }
  function arrow(ctx, x1, y1, x2, y2, color, w) {
    const a = Math.atan2(y2 - y1, x2 - x1), h = 8 + w;
    ctx.strokeStyle = ctx.fillStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * h * .6, y2 - Math.sin(a) * h * .6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - h * Math.cos(a - .42), y2 - h * Math.sin(a - .42)); ctx.lineTo(x2 - h * Math.cos(a + .42), y2 - h * Math.sin(a + .42)); ctx.closePath(); ctx.fill();
  }
  // Curved arrow around (cx, cy) from angle a0 to a1; canvas angles run clockwise
  function curve(ctx, cx, cy, r, a0, a1, color, w) {
    const ccw = a1 < a0;
    ctx.strokeStyle = ctx.fillStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1, ccw); ctx.stroke();
    const t = a1 + (ccw ? -1 : 1) * Math.PI / 2, ex = cx + r * Math.cos(a1), ey = cy + r * Math.sin(a1), h = 8 + w;
    ctx.beginPath(); ctx.moveTo(ex + Math.cos(t) * h * .6, ey + Math.sin(t) * h * .6);
    ctx.lineTo(ex + Math.cos(t + 2.6) * h, ey + Math.sin(t + 2.6) * h); ctx.lineTo(ex + Math.cos(t - 2.6) * h, ey + Math.sin(t - 2.6) * h); ctx.closePath(); ctx.fill();
  }
  function rr(ctx, x, y, w, h, r) { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); }
  const pct = v => Math.round(v) + '%', kt = v => Math.round(v) + ' kt';
  const powerFmt = v => v < 8 ? 'Idle' : v > 95 ? 'Full' : pct(v);

  // ---------- Torque reaction: seen from behind ----------
  (function () {
    const d = demo('d-torque'); if (!d) return;
    const power = range('tq-power', powerFmt), speed = range('tq-speed', kt), ail = range('tq-ail', pct);
    let roll = 0, rate = 0, blade = 0;
    $('tq-reset').onclick = () => { roll = 0; rate = 0; };
    d.draw = dt => {
      const { ctx, W, H } = d, P = power() / 100, V = speed(), q = (V / 80) ** 2;
      const need = clamp(45 * P / q, 0, 100);                                  // right aileron that holds the wings level
      rate += (.5 * (.45 * P - ail() / 100 * q) - 1.2 * rate * (V / 80)) * dt;
      roll = clamp(roll + rate * dt, -70 * deg, 70 * deg);
      if (Math.abs(roll) >= 70 * deg - 1e-6) rate = 0;
      if (!reduce) blade += (6 + 30 * P) * dt;
      ctx.clearRect(0, 0, W, H);
      const cx = W / 2, cy = H * .52, s = Math.min(W * .27, H * .34);
      ctx.strokeStyle = LINE; ctx.setLineDash([6, 6]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(cx - s * 2.2, cy + s * .1); ctx.lineTo(cx + s * 2.2, cy + s * .1); ctx.stroke(); ctx.setLineDash([]);
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(-roll);                   // roll left puts the left wing down on screen
      ctx.fillStyle = SURF2; ctx.strokeStyle = MUTED; ctx.lineWidth = 1.5;
      rr(ctx, -1.75 * s, .04 * s, 3.5 * s, .12 * s, .05 * s); ctx.fill(); ctx.stroke();            // wings
      rr(ctx, -.62 * s, -.5 * s, 1.24 * s, .08 * s, .03 * s); ctx.fill(); ctx.stroke();           // stabilizer
      ctx.beginPath(); ctx.ellipse(0, 0, .3 * s, .34 * s, 0, 0, TAU); ctx.fill(); ctx.stroke();  // fuselage
      ctx.fillStyle = TEXT; ctx.beginPath(); ctx.moveTo(-.05 * s, -.3 * s); ctx.lineTo(-.03 * s, -.98 * s); ctx.lineTo(.03 * s, -.98 * s); ctx.lineTo(.05 * s, -.3 * s); ctx.closePath(); ctx.fill();   // fin
      ctx.fillStyle = 'rgba(127,182,240,.08)'; ctx.strokeStyle = 'rgba(127,182,240,.3)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, .8 * s, 0, TAU); ctx.fill(); ctx.stroke();                   // propeller disc
      ctx.strokeStyle = TEXT; ctx.lineWidth = 3; ctx.lineCap = 'round';
      for (const k of [0, Math.PI]) { ctx.beginPath(); ctx.moveTo(Math.cos(blade + k) * .1 * s, Math.sin(blade + k) * .1 * s); ctx.lineTo(Math.cos(blade + k) * .78 * s, Math.sin(blade + k) * .78 * s); ctx.stroke(); }
      ctx.fillStyle = TEXT; ctx.beginPath(); ctx.arc(0, 0, .09 * s, 0, TAU); ctx.fill();
      curve(ctx, 0, 0, .96 * s, -.5 * Math.PI, -.5 * Math.PI + (.35 + .6 * P) * Math.PI, BLUE, 3);           // propeller: clockwise
      if (P > .05) curve(ctx, 0, 0, 1.18 * s, .5 * Math.PI - .25, .5 * Math.PI - .25 - (.3 + .55 * P), ACCENT, 3 + 3 * P);   // reaction: the other way
      ctx.restore();
      const narrow = W < 560;
      text(ctx, 'Propeller turns clockwise', narrow ? W - 14 : cx + s * .6, narrow ? 22 : cy - s * 1.12, BLUE, narrow ? 'right' : 'left', 13);
      text(ctx, 'Reaction rolls the airplane left', narrow ? 14 : cx + s * 1.32, narrow ? H - 32 : cy + s * .62, ACCENT, 'left', 13);
      text(ctx, 'Seen from behind', 14, H - 12, MUTED, 'left', 12, 500);
      const bank = Math.round(Math.abs(roll) / deg);
      text(ctx, bank ? `Bank ${bank}° ${roll > 0 ? 'left' : 'right'}` : 'Wings level', W - 14, H - 12, TEXT, 'right', 13);
      const r = Math.round(rate / deg);
      $('tq-read').textContent = `Right aileron to hold the wings level here: about ${Math.round(need)}%. ` + (Math.abs(roll) >= 70 * deg - 1e-6 ? 'Stopped at the limit of this demo.' : Math.abs(r) < 1 ? 'Holding.' : `Rolling ${r > 0 ? 'left' : 'right'} at ${Math.abs(r)}° per second.`);
    };
  })();

  // ---------- Spiraling slipstream: top view, nose to the left ----------
  (function () {
    const d = demo('d-slip'); if (!d) return;
    const power = range('sl-power', powerFmt), speed = range('sl-speed', kt), rud = range('sl-rud', pct);
    const parts = []; let yaw = 0, yrate = 0, emit = 0;
    d.draw = dt => {
      const { ctx, W, H } = d, P = power() / 100, V = speed();
      const va = (V / 60) * (.55 + .35 * P), om = 3.6 * Math.pow(P, .7);         // axial speed (fuselage lengths per second) and swirl rate
      const hit = Math.atan(om * .2 / va) / deg;                                   // angle the spiral meets the fin
      const need = clamp(85 * P / Math.pow(V / 60, 1.6) * (.2 + .8 * Math.min(1, hit / 25)), 0, 100);
      yrate += (.5 * (need - rud()) / 100 - 1.6 * yrate) * dt;
      yaw = clamp(yaw + yrate * dt, -14 * deg, 14 * deg);
      const L = Math.min(W * .64, H * 2.4), x0 = W / 2 - L * .5, cy = H / 2, R = L * .16;
      emit += dt * (40 + 170 * P);
      while (emit > 1) { emit -= 1; parts.push({ x: 0, r: .35 + .65 * Math.random(), ph: Math.random() * TAU }); }
      for (let i = parts.length - 1; i >= 0; i--) { const p = parts[i]; p.x += va * dt * (1 + .15 * (1 - p.r)); p.ph += om * dt / Math.sqrt(p.r); if (p.x > 1.5) parts.splice(i, 1); }
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = LINE; ctx.setLineDash([6, 6]); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x0 - L * .15, cy); ctx.lineTo(x0 + L * 1.2, cy); ctx.stroke(); ctx.setLineDash([]);   // original heading
      ctx.save(); ctx.translate(W / 2, cy); ctx.rotate(yaw); ctx.translate(-W / 2, -cy);
      // Clockwise seen from behind: over the top toward the right wing, which is up on this screen
      const dot = (p, up) => { const z = Math.cos(p.ph), y = -Math.sin(p.ph); ctx.fillStyle = up ? `rgba(127,182,240,${.5 + .5 * z})` : 'rgba(127,182,240,.25)'; const sz = up ? 2.4 + 1.4 * z : 1.8; ctx.fillRect(x0 + p.x * L - sz / 2, cy + y * p.r * R - sz / 2, sz, sz); };
      parts.forEach(p => { if (Math.cos(p.ph) < 0) dot(p, false); });
      ctx.fillStyle = SURF2; ctx.strokeStyle = MUTED; ctx.lineWidth = 1.5;
      rr(ctx, x0 + L * .38, cy - L * .34, L * .07, L * .68, L * .02); ctx.fill(); ctx.stroke();    // wings
      rr(ctx, x0 + L * .9, cy - L * .14, L * .06, L * .28, L * .012); ctx.fill(); ctx.stroke();    // stabilizer
      ctx.beginPath(); ctx.moveTo(x0 + L * .02, cy); ctx.quadraticCurveTo(x0 + L * .05, cy - L * .07, x0 + L * .3, cy - L * .06); ctx.lineTo(x0 + L * .98, cy - L * .018); ctx.lineTo(x0 + L * .98, cy + L * .018); ctx.lineTo(x0 + L * .3, cy + L * .06); ctx.quadraticCurveTo(x0 + L * .05, cy + L * .07, x0 + L * .02, cy); ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = TEXT; ctx.fillRect(x0 + L * .84, cy - L * .007, L * .15, L * .014);          // fin, seen edge-on
      ctx.strokeStyle = TEXT; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, cy - R); ctx.lineTo(x0, cy + R); ctx.stroke();   // propeller
      parts.forEach(p => { if (Math.cos(p.ph) >= 0) dot(p, true); });
      if (P > .05) {
        const f = clamp(hit / 25, 0, 1);
        arrow(ctx, x0 + L * .92, cy + R + 10 + 28 * f, x0 + L * .92, cy + 10, ACCENT, 2.5 + 2 * f);      // tail pushed right
        arrow(ctx, x0 + L * .1, cy - 10, x0 + L * .1, cy + 18 + 26 * f, ACCENT, 2.5 + 2 * f);            // nose swings left
      }
      ctx.restore();
      text(ctx, W < 560 ? 'Top view, nose to the left' : 'Top view, nose to the left. Bright dots pass over the fuselage, dim ones under it.', 14, H - 12, MUTED, 'left', 12, 500);
      text(ctx, 'Slipstream hits the left side of the fin', W - 14, 22, ACCENT, 'right', 13);
      text(ctx, 'Nose yaws left', x0 + L * .14, cy + R + 36, ACCENT, 'left', 13);
      $('sl-read').textContent = `The spiral meets the fin at about ${Math.round(hit)}° from the left. Right rudder to hold the heading here: about ${Math.round(need)}%.`;
    };
  })();

  // ---------- P-factor: the blade's angle of attack on each side of the disc ----------
  (function () {
    const d = demo('d-pfactor'); if (!d) return;
    const aoa = range('pf-aoa', v => v + '°'), speed = range('pf-speed', kt), rpm = range('pf-rpm', v => v + ' RPM');
    const BETA = 21, R75 = .71;                     // blade angle (degrees) and radius (m) at 75% of a 75 in propeller
    let th = 0;
    // Blade angle of attack = blade angle minus the angle of the relative wind. The wind's
    // component across the tilted disc adds to the descending blade's speed and subtracts from the ascending blade's.
    const bladeAoA = (V, a, om, c) => BETA - Math.atan2(V * Math.cos(a), om * R75 + V * Math.sin(a) * c) / deg;
    d.draw = dt => {
      const { ctx, W, H } = d, a = aoa() * deg, V = speed() * .5144, om = rpm() * TAU / 60;
      const aD = bladeAoA(V, a, om, 1), aA = bladeAoA(V, a, om, -1), asym = (aD - aA) / (aD + aA);
      if (!reduce) th += (3 + rpm() / 700) * dt;
      $('pf-read').textContent = `Descending blade ${aD.toFixed(1)}°, ascending blade ${aA.toFixed(1)}°. The right side makes about ${Math.max(0, Math.round(asym * 200))}% more thrust than the left, so the nose yaws left.`;
      ctx.clearRect(0, 0, W, H);
      const narrow = W < 560, split = narrow ? W : W * .56, cx = split / 2, cy = H * .5, Rp = Math.min(split * .3, H * .3);
      // Seen from behind: the blade glows brighter where its angle of attack is higher
      ctx.fillStyle = 'rgba(127,182,240,.06)'; ctx.strokeStyle = 'rgba(127,182,240,.3)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(cx, cy, Rp, 0, TAU); ctx.fill(); ctx.stroke();
      for (const k of [0, Math.PI]) {
        const ang = th + k, c = Math.cos(ang), g = clamp((bladeAoA(V, a, om, c) - aA) / Math.max(.25, aD - aA), 0, 1);
        ctx.strokeStyle = `hsl(208,72%,${52 + 40 * g}%)`; ctx.lineWidth = 5 + 4 * g; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(cx + c * Rp * .12, cy + Math.sin(ang) * Rp * .12); ctx.lineTo(cx + c * Rp * .95, cy + Math.sin(ang) * Rp * .95); ctx.stroke();
      }
      ctx.fillStyle = TEXT; ctx.beginPath(); ctx.arc(cx, cy, Rp * .1, 0, TAU); ctx.fill();
      curve(ctx, cx, cy, Rp * 1.1, -.5 * Math.PI, -.08 * Math.PI, MUTED, 2);
      const tl = Rp * .85, m = Math.max(aD, aA);
      arrow(ctx, cx + Rp * .72, cy, cx + Rp * .72, cy - tl * aD / m, BLUE, 4);
      arrow(ctx, cx - Rp * .72, cy, cx - Rp * .72, cy - tl * aA / m, BLUE, 4);
      text(ctx, 'Descending blade', cx + Rp * .72, cy + Rp * 1.22, TEXT, 'center', 13);
      text(ctx, `${aD.toFixed(1)}° angle of attack`, cx + Rp * .72, cy + Rp * 1.22 + 16, MUTED, 'center', 12, 500);
      text(ctx, 'Ascending blade', cx - Rp * .72, cy + Rp * 1.22, TEXT, 'center', 13);
      text(ctx, `${aA.toFixed(1)}° angle of attack`, cx - Rp * .72, cy + Rp * 1.22 + 16, MUTED, 'center', 12, 500);
      const shift = asym * Rp * 2.5;                 // center of thrust, exaggerated so the shift can be seen
      ctx.fillStyle = ACCENT; ctx.beginPath(); ctx.arc(cx + shift, cy - tl * .45, 5, 0, TAU); ctx.fill();
      text(ctx, 'Center of thrust', cx + shift + 9, cy - tl * .45 + 4, ACCENT, 'left', 12);
      if (asym > .003) { arrow(ctx, cx + Rp * 1.25, cy - Rp * 1.25, cx + Rp * 1.25 - 36 - 400 * asym, cy - Rp * 1.25, ACCENT, 3); text(ctx, 'Nose yaws left', cx + Rp * 1.25, cy - Rp * 1.25 - 10, ACCENT, 'right', 13); }
      text(ctx, 'Seen from behind', 14, 20, MUTED, 'left', 12, 500);
      if (narrow) return;
      // Velocity triangles: why the descending blade meets the air at a bigger angle
      const tx = split + (W - split) * .55, sc = (W - split) * .4 / 200;
      [[aD, 1, H * .3, 'Descending blade'], [aA, -1, H * .76, 'Ascending blade']].forEach(([ab, c, by, name]) => {
        const ut = (om * R75 + V * Math.sin(a) * c) * sc, ua = V * Math.cos(a) * sc;
        ctx.strokeStyle = LINE; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(tx - ut - 10, by); ctx.lineTo(tx + 30, by); ctx.stroke();   // plane of rotation
        ctx.save(); ctx.translate(tx, by); ctx.rotate(-BETA * deg); ctx.fillStyle = SURF2; ctx.strokeStyle = TEXT; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.ellipse(-14, 0, 30, 5, 0, 0, TAU); ctx.fill(); ctx.stroke(); ctx.restore();                                     // blade section, leading edge up and to the left
        arrow(ctx, tx - ut, by - ua, tx, by, BLUE, 2.5);                                                                                   // relative wind
        text(ctx, name, tx - ut - 10, by - ua - 14, TEXT, 'left', 13);
        text(ctx, `${ab.toFixed(1)}° between the wind and the blade`, tx - ut - 10, by + 22, MUTED, 'left', 12, 500);
      });
      text(ctx, 'Relative wind at the blade, to scale', W - 14, H - 12, MUTED, 'right', 12, 500);
    };
  })();

  // ---------- Gyroscopic precession: a three-dimensional airplane you can pitch and yaw ----------
  (function () {
    const d = demo('d-gyro'); if (!d) return;
    // Body axes: x forward, y left, z up. R turns body coordinates into world coordinates.
    // The propeller turns clockwise seen from the cockpit, so its angular momentum points forward.
    let R = [1, 0, 0, 0, 1, 0, 0, 0, 1], spin = 0, held = null;
    const stopped = $('gy-stop');
    d.c.parentElement.querySelectorAll('button[data-g]').forEach(b => {
      const on = e => { e.preventDefault(); held = b.dataset.g; b.classList.add('on'); };
      const off = () => { if (held === b.dataset.g) held = null; b.classList.remove('on'); };
      b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointerleave', off); b.addEventListener('pointercancel', off);
      b.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') on(e); }); b.addEventListener('keyup', off);
    });
    if (location.search.includes('debug')) { d.hold = g => { held = g; }; d.att = () => { const f = ap(R, [1, 0, 0]); return [Math.asin(f[2]) / deg, Math.atan2(f[1], f[0]) / deg]; }; }
    const mul = (A, B) => { const C = []; for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C.push(A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j]); return C; };
    const rot = ([x, y, z], ang) => { const c = Math.cos(ang), s = Math.sin(ang), t = 1 - c; return [t * x * x + c, t * x * y - s * z, t * x * z + s * y, t * x * y + s * z, t * y * y + c, t * y * z - s * x, t * x * z - s * y, t * y * z + s * x, t * z * z + c]; };
    const ap = (M, p) => [M[0] * p[0] + M[1] * p[1] + M[2] * p[2], M[3] * p[0] + M[4] * p[1] + M[5] * p[2], M[6] * p[0] + M[7] * p[1] + M[8] * p[2]];
    const norm = v => { const m = Math.hypot(v[0], v[1], v[2]) || 1; return v.map(x => x / m); };
    const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const dotp = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    // Camera behind, to the right of, and above the airplane
    const F = norm([3, 1.3, -1.5]), RT = norm(cross(F, [0, 0, 1])), UP = cross(RT, F);
    let cx = 0, cy = 0, S = 1;
    const projW = w => { const k = S / (1 + .13 * dotp(w, F)); return [cx + dotp(w, RT) * k, cy - dotp(w, UP) * k]; };
    const proj = p => projW(ap(R, p));
    const poly = (ctx, pts, color, w, fill, world) => {
      ctx.beginPath(); pts.forEach((p, i) => { const q = world ? projW(p) : proj(p); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); });
      if (fill) { ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); }
      ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineJoin = 'round'; ctx.stroke();
    };
    const arrow3 = (ctx, p0, p1, color, w) => { const a = proj(p0), b = proj(p1); arrow(ctx, a[0], a[1], b[0], b[1], color, w); };
    const wing = s => [[.45, s * .24, -.1], [.35, s * 1.25, -.04], [-.22, s * 1.25, -.04], [-.3, s * .24, -.1]];
    const stab = s => [[-.95, s * .1, .06], [-1.02, s * .52, .06], [-1.35, s * .52, .06], [-1.35, s * .1, .06]];
    const FUS = [[[1.3, 0, .03], [.95, 0, .22], [.2, 0, .3], [-.6, 0, .2], [-1.35, 0, .12]], [[1.3, 0, -.03], [.6, 0, -.22], [-.2, 0, -.2], [-1.35, 0, -.04]], [[1.3, .03, 0], [.6, .24, 0], [-.4, .2, 0], [-1.35, .06, 0]], [[1.3, -.03, 0], [.6, -.24, 0], [-.4, -.2, 0], [-1.35, -.06, 0]]];
    const DISC = []; for (let i = 0; i <= 40; i++) DISC.push([1.3, -.5 * Math.sin(i / 40 * TAU), .5 * Math.cos(i / 40 * TAU)]);
    const ARC = []; for (let i = 0; i <= 12; i++) { const s = -.9 + 1.8 * i / 12; ARC.push([1.3, -.62 * Math.sin(s), .62 * Math.cos(s)]); }
    const PTS = { top: [1.3, 0, .5], bottom: [1.3, 0, -.5], right: [1.3, -.5, 0], left: [1.3, .5, 0] };
    const APPLIED = { pd: ['top', 1], pu: ['top', -1], yl: ['right', 1], yr: ['left', 1] };
    const FELT = { pd: ['right', 1], pu: ['right', -1], yl: ['bottom', 1], yr: ['top', 1] };
    const WORDS = { pd: ['Pitching the nose down', 'yaws the nose left'], pu: ['Pitching the nose up', 'yaws the nose right'], yl: ['Yawing the nose left', 'pitches the nose up'], yr: ['Yawing the nose right', 'pitches the nose down'] };
    d.draw = dt => {
      const { ctx, W, H } = d, spinning = !stopped.checked, rate = .3;
      let wa = [0, 0, 0];
      if (held === 'pd') wa = [0, rate, 0]; else if (held === 'pu') wa = [0, -rate, 0]; else if (held === 'yl') wa = [0, 0, rate]; else if (held === 'yr') wa = [0, 0, -rate];
      // Precession: forcing the spin axis to turn produces a turn 90° later in the direction of rotation
      const wp = spinning ? [0, -.85 * wa[2], .85 * wa[1]] : [0, 0, 0];
      const w = [wa[0] + wp[0], wa[1] + wp[1], wa[2] + wp[2]], mag = Math.hypot(w[0], w[1], w[2]);
      if (mag > 1e-6) {
        const R2 = mul(R, rot(w.map(x => x / mag), mag * dt)), f2 = ap(R2, [1, 0, 0]);
        if (Math.abs(f2[2]) < .6 && f2[0] > .75) R = R2;                   // stop at about 35° of pitch or heading
      }
      if (!held) {                                                             // ease back to level between inputs
        const k = Math.min(1, 1.1 * dt), I = [1, 0, 0, 0, 1, 0, 0, 0, 1];
        R = R.map((v, i) => v + (I[i] - v) * k);
        const a = norm(R.slice(0, 3)); let b = R.slice(3, 6); const ab = dotp(a, b); b = norm(b.map((v, i) => v - ab * a[i]));
        R = [...a, ...b, ...cross(a, b)];
      }
      if (spinning && !reduce) spin += 9 * dt;
      ctx.clearRect(0, 0, W, H);
      cx = W * .5; cy = H * .5; S = Math.min(W * .28, H * .34);
      ctx.setLineDash([5, 7]); poly(ctx, [[-2.2, 1.9, -.7], [2.4, 1.9, -.7], [2.4, -1.9, -.7], [-2.2, -1.9, -.7], [-2.2, 1.9, -.7]], LINE, 1, null, true); ctx.setLineDash([]);   // level reference
      poly(ctx, [[-2.2, 0, -.7], [2.4, 0, -.7]], LINE, 1, null, true);
      poly(ctx, wing(1), MUTED, 1.3, 'rgba(155,165,172,.14)'); poly(ctx, wing(-1), MUTED, 1.3, 'rgba(155,165,172,.14)');
      FUS.forEach(l => poly(ctx, l, TEXT, 1.6));
      poly(ctx, stab(1), MUTED, 1.3, 'rgba(155,165,172,.14)'); poly(ctx, stab(-1), MUTED, 1.3, 'rgba(155,165,172,.14)');
      poly(ctx, [[-1, 0, .12], [-1.22, 0, .58], [-1.35, 0, .58], [-1.35, 0, .12]], TEXT, 1.5, 'rgba(229,232,234,.25)');
      poly(ctx, DISC, 'rgba(127,182,240,.45)', 1.5, spinning ? 'rgba(127,182,240,.08)' : null);
      for (const k of [0, Math.PI]) poly(ctx, [[1.3, -.05 * Math.sin(spin + k), .05 * Math.cos(spin + k)], [1.3, -.47 * Math.sin(spin + k), .47 * Math.cos(spin + k)]], TEXT, 3);
      if (spinning) { poly(ctx, ARC, BLUE, 2.5); arrow3(ctx, ARC[11], ARC[12], BLUE, 2.5); }
      if (held) {
        const [p0, s0] = APPLIED[held], P0 = PTS[p0];
        arrow3(ctx, P0, [P0[0] + .6 * s0, P0[1], P0[2]], ACCENT, 3.5);
        const q0 = proj(P0); text(ctx, 'Force applied here', q0[0] - 10, q0[1] - 12, ACCENT, 'right', 13);
        if (spinning) {
          const [p1, s1] = FELT[held], P1 = PTS[p1];
          arrow3(ctx, P1, [P1[0] + .6 * s1, P1[1], P1[2]], BLUE, 3.5);
          const q1 = proj(P1); text(ctx, 'Felt here, 90° later', q1[0] + 10, q1[1] + 18, BLUE, 'left', 13);
        }
      }
      const fx = ap(R, [1, 0, 0]), hd = Math.atan2(fx[1], fx[0]) / deg, pt = Math.asin(clamp(fx[2], -1, 1)) / deg;
      text(ctx, `Nose ${Math.abs(Math.round(pt))}° ${pt >= 0 ? 'up' : 'down'}, heading ${Math.abs(Math.round(hd))}° ${hd >= 0 ? 'left' : 'right'}`, W - 14, H - 12, TEXT, 'right', 13);
      text(ctx, 'Seen from behind and to the right', 14, H - 12, MUTED, 'left', 12, 500);
      $('gy-read').textContent = held ? `${WORDS[held][0]} ${spinning ? 'also ' + WORDS[held][1] + ': that’s precession.' : 'does nothing else: with the propeller stopped there is no precession.'}` : 'Hold a button to pitch or yaw the airplane.';
    };
  })();

  // ---------- Animation loop: only demos on screen are drawn ----------
  let last = performance.now();
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    for (const d of demos) if (d.on && d.draw) d.draw(dt);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  if (location.search.includes('debug')) window.__ltt = { demos, step: (dt, n) => { for (let k = 0; k < (n || 1); k++) for (const d of demos) if (d.draw) d.draw(dt); }, hold: g => demos.forEach(x => x.hold && x.hold(g)) };
})();
