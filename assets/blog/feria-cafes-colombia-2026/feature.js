/* Feature post: Cafés de Colombia 2026 — banner control, scroll journey, cups counter, notes, map. */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const io = (cb, opts) => new IntersectionObserver(cb, opts);

  /* ---- Banner: pause off-screen, honour reduced motion, manual pause button ---- */
  const hero = document.querySelector('.fx-map-hero');
  const svg = hero && hero.querySelector('svg.fx-map-overlay');
  const btn = hero && hero.querySelector('.fx-motion');
  if (hero && svg) {
    let userPaused = reduce;
    let visible = true;
    const apply = () => {
      const paused = userPaused || !visible;
      hero.classList.toggle('is-paused', paused);
      if (paused) svg.pauseAnimations(); else svg.unpauseAnimations();
      if (btn) {
        btn.textContent = userPaused ? btn.dataset.play : btn.dataset.pause;
        btn.setAttribute('aria-pressed', String(userPaused));
      }
    };
    if (reduce) svg.setCurrentTime(5); // plane mid-route, trail half drawn
    btn && btn.addEventListener('click', () => { userPaused = !userPaused; apply(); });
    io(([e]) => { visible = e.isIntersecting; apply(); }).observe(hero);
    apply();
  }

  /* ---- Floating WhatsApp: hide over the header (covers the title on small phones) and the closing pass ---- */
  const float = document.querySelector('.wa-float');
  const guards = [document.querySelector('.fx-hero'), document.querySelector('.fx-pass-cta')].filter(Boolean);
  if (float && guards.length) {
    const seen = new Set();
    const g = io((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) seen.add(e.target); else seen.delete(e.target); });
      float.classList.toggle('is-hidden', seen.size > 0);
    });
    guards.forEach((el) => g.observe(el));
  }

  /* ---- Reveal on scroll ---- */
  const revealer = io((entries) => entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('in'); revealer.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.fx-reveal').forEach((el) => revealer.observe(el));

  /* ---- Journey progress: side rail (desktop) and top bar (mobile) ---- */
  const content = document.querySelector('.fx-content');
  const journey = document.querySelector('.fx-journey');
  const bar = document.querySelector('.fx-progress');
  const stops = Array.from(document.querySelectorAll('.fx-stop'));
  const links = Array.from(document.querySelectorAll('.fx-rail a'));
  let ticking = false;
  const update = () => {
    ticking = false;
    if (!content) return;
    const r = content.getBoundingClientRect();
    const vh = window.innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.45 - r.top) / Math.max(1, r.height - vh * 0.3)));
    journey.style.setProperty('--p', p.toFixed(4));
    if (bar) { bar.style.setProperty('--p', p.toFixed(4)); bar.classList.toggle('on', r.top < vh * 0.6 && r.bottom > 0); }
    let current = null;
    stops.forEach((s) => { if (s.getBoundingClientRect().top < vh * 0.45) current = s.dataset.stop; });
    links.forEach((a) => {
      if (a.dataset.stop === current) a.setAttribute('aria-current', 'step'); else a.removeAttribute('aria-current');
    });
  };
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();

  /* ---- Cups counter ---- */
  const cups = document.querySelector('.fx-cups');
  if (cups) {
    const icons = cups.querySelectorAll('.fx-cups-grid i');
    const count = cups.querySelector('.fx-count');
    const target = Number(count.dataset.to) || icons.length;
    const fill = (n) => { icons.forEach((i, k) => i.classList.toggle('full', k < n)); count.textContent = String(n); };
    if (reduce) { fill(target); } else {
      fill(0);
      const obs = io(([e]) => {
        if (!e.isIntersecting) return;
        obs.disconnect();
        let n = 0;
        const step = () => { n += 1; fill(n); if (n < target) setTimeout(step, 45); };
        step();
      }, { threshold: 0.4 });
      obs.observe(cups);
    }
  }

  /* ---- Tasting notes: one open at a time ---- */
  document.querySelectorAll('.fx-notes').forEach((box) => {
    const buttons = box.querySelectorAll('button[aria-controls]');
    buttons.forEach((b) => b.addEventListener('click', () => {
      buttons.forEach((o) => {
        const on = o === b;
        o.setAttribute('aria-expanded', String(on));
        document.getElementById(o.getAttribute('aria-controls')).hidden = !on;
      });
    }));
  });

  /* ---- Map: select a region ---- */
  document.querySelectorAll('.fx-map').forEach((map) => {
    const buttons = map.querySelectorAll('button[data-region]');
    const select = (region) => {
      buttons.forEach((b) => {
        const on = b.dataset.region === region;
        b.setAttribute('aria-pressed', String(on));
        document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
      });
      map.querySelectorAll('.map-dot').forEach((d) => d.classList.toggle('active', d.dataset.region === region));
    };
    buttons.forEach((b) => b.addEventListener('click', () => select(b.dataset.region)));
    select('nds');
  });
})();
