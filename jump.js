// Jump-to menu: names the section you're reading, and closes after a pick, an outside click, or Escape.
(function () {
  const menu = document.querySelector('.jump-menu');
  if (!menu) return;
  const cur = menu.querySelector('.jump-current'), summary = menu.querySelector('summary');
  const links = [...menu.querySelectorAll('ol a')];
  const heads = links.map(a => document.getElementById(a.hash.slice(1)));
  const empty = cur.textContent;
  links.forEach(a => a.addEventListener('click', () => { menu.open = false; }));
  document.addEventListener('click', e => { if (!menu.contains(e.target)) menu.open = false; });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && menu.open) { menu.open = false; summary.focus(); } });
  function update() {
    const line = menu.getBoundingClientRect().bottom + 24;
    let i = -1;
    heads.forEach((h, j) => { if (h.getBoundingClientRect().top <= line) i = j; });
    cur.textContent = i < 0 ? empty : links[i].querySelector('span').textContent;
    links.forEach((a, j) => j === i ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current'));
  }
  addEventListener('scroll', update, { passive: true });
  update();
})();
