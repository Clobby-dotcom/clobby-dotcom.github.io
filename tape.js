// Airspeed tape: draws an airplane's airspeed indicator markings from the data on the <svg class="tape"> element.
// data-range="30,170" data-white="33,85" data-green="44,129" data-yellow="129,163" data-red="163" data-bugs="VX:60,VY:79,VA:99"
(function () {
  const narrow = matchMedia('(max-width: 600px)');
  function draw(svg) {
    const d = svg.dataset, pair = s => s.split(',').map(Number);
    const [lo, hi] = pair(d.range), W = narrow.matches ? 380 : 720, L = 16, R = W - 16;
    const x = v => L + (v - lo) * (R - L) / (hi - lo);
    const band = (k, y, h, fill) => { if (!d[k]) return ''; const [a, b] = pair(d[k]); return `<rect x="${x(a)}" y="${y}" width="${x(b) - x(a)}" height="${h}" fill="${fill}"/>`; };
    let s = band('white', 74, 7, 'var(--text)') + band('green', 84, 10, 'var(--gn)') + band('yellow', 84, 10, 'var(--am)');
    if (d.red) s += `<rect x="${x(Number(d.red)) - 2}" y="66" width="4" height="34" fill="var(--rd)"/>`;
    const step = narrow.matches ? 40 : 20;
    for (let v = Math.ceil(lo / 10) * 10; v <= hi; v += 10) {
      const major = v % step === 0;
      s += `<path d="M${x(v)} 100v${major ? 11 : 6}" stroke="var(--text)" stroke-width="1.5"/>`;
      if (major) s += `<text class="tk" x="${x(v)}" y="126" text-anchor="middle">${v}</text>`;
    }
    // Speed bugs, raised a tier when two sit close together
    let last = -99, tier = 0;
    (d.bugs || '').split(',').filter(Boolean).map(b => b.split(':')).sort((a, b) => a[1] - b[1]).forEach(([name, v]) => {
      const px = x(Number(v)); tier = px - last < 44 ? 1 - tier : 0; last = px;
      const top = tier ? 4 : 30;
      s += `<path d="M${px} 72V${top + 22}" stroke="var(--cy)" stroke-width="1.5"/><rect x="${px - 19}" y="${top}" width="38" height="22" fill="var(--bg)" stroke="var(--cy)" stroke-width="1.5"/>` +
        `<text class="bug" x="${px}" y="${top + 16}" text-anchor="middle">${name[0]}<tspan dy="3" font-size="10">${name.slice(1)}</tspan></text>`;
    });
    svg.setAttribute('viewBox', `0 0 ${W} 132`);
    svg.innerHTML = s;
  }
  const all = [...document.querySelectorAll('svg.tape')];
  const run = () => all.forEach(draw);
  run(); narrow.addEventListener('change', run);
})();
