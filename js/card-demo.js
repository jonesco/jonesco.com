/* Custom Card Creator — animated walkthrough of the concept on an iPhone.
   Builds the phone UI inside [data-card-demo], then plays a scripted loop:
   pick a card color, search for an emoji, drop it on the card, pinch / rotate / drag it into place, tap Done.
   Everything runs on one pausable clock, so Pause (and scrolling the phone out of view) freezes it mid-gesture. */
(() => {
  const root = document.querySelector('[data-card-demo]');
  if (!root) return;

  const SW = 390, DW = 414; // screen and device widths in the phone's own pixels

  const COLORS = [
    { name: 'Black', hex: '#1d1d1f', dark: true },
    { name: 'Yellow', hex: '#ffe600' },
    { name: 'Lime', hex: '#84bd00' },
    { name: 'Pink', hex: '#ff52c0' },
    { name: 'Lavender', hex: '#a58cff' },
    { name: 'Copper', hex: '#c98b55' },
    { name: 'Sky', hex: '#3fa9f5' },
    { name: 'Red', hex: '#f2453d' },
  ];
  const FREQUENT = '😉 💡 🙄 🤮 🥪 🚗 👍 💰 🤓 ☠️ 😞 💀 😎 😭 😢 📦 👀 😈 🔥 🚨 👆 🙏 ❤️ 🛑 😬 🤔 🥶 👅 🚫 👋'.split(' ');
  const SMILEYS = '😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇 🙂 🙃 😌 😍 🥰 😘 😗 😙 😚 😋'.split(' ');
  const CATEGORIES = '🕘 😀 🐻 🍔 ⚽ 🚗 💡 🔣 🏳️'.split(' ');

  // One scene per finished card. Positions are px from the card's center; s is a multiple of the 72px emoji.
  const SCENES = [
    {
      colors: ['Pink', 'Lime', 'Yellow'], query: 'monkey', results: ['🙈', '🙉', '🙊', '🐵', '🐒'],
      place: [
        { e: '🙈', to: { x: -104, y: 6, s: 1, r: 0 }, pinch: true },
        { e: '🙉', to: { x: 0, y: 6, s: 1, r: 0 }, pinch: true },
        { e: '🙊', to: { x: 104, y: 6, s: 1, r: 0 } },
      ],
    },
    {
      colors: ['Copper', 'Lime'], query: 'pizza', results: ['🍕', '🍝', '🧀', '🍔', '🌮'],
      place: [
        { e: '🍕', to: { x: -52, y: 16, s: 1.75, r: -26 }, pinch: true },
        { e: '🍕', to: { x: 82, y: -24, s: 1.05, r: 22 }, pinch: true },
      ],
    },
    {
      colors: ['Sky', 'Lavender'], query: 'unicorn', results: ['🦄', '🌈', '✨', '🐴', '🎠'],
      place: [{ e: '🦄', to: { x: 0, y: 8, s: 1.6, r: -8 }, pinch: true }],
    },
  ];

  /* ---------- build ---------- */

  const icon = {
    signal: '<svg viewBox="0 0 18 12"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>',
    wifi: '<svg viewBox="0 0 16 12"><path d="M8 2.6c2.3 0 4.4.9 6 2.4l1.2-1.3A10.4 10.4 0 0 0 8 .8 10.4 10.4 0 0 0 .8 3.7L2 5c1.6-1.5 3.7-2.4 6-2.4Zm0 3.6c1.3 0 2.5.5 3.4 1.3l1.2-1.3A6.7 6.7 0 0 0 8 4.4c-1.8 0-3.4.7-4.6 1.8l1.2 1.3C5.5 6.7 6.7 6.2 8 6.2Zm0 3.5L10.1 7.5A3 3 0 0 0 8 6.9c-.8 0-1.6.3-2.1.8L8 9.7Z" transform="translate(0 1.4)"/></svg>',
    battery: '<svg viewBox="0 0 27 13"><rect x=".5" y=".5" width="23" height="12" rx="3.6" fill="none" stroke="currentColor" opacity=".4"/><rect x="2.2" y="2.2" width="19.6" height="8.6" rx="2.2"/><path d="M25 4.3v4.4c.8-.3 1.4-1.2 1.4-2.2s-.6-1.9-1.4-2.2Z" opacity=".45"/></svg>',
    search: '<svg viewBox="0 0 16 16"><circle cx="6.8" cy="6.8" r="5.3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m10.8 10.8 4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    smile: '<svg viewBox="0 0 28 28"><circle cx="14" cy="14" r="11.5" fill="none" stroke="currentColor" stroke-width="2.2"/><circle cx="10" cy="11.5" r="1.7"/><circle cx="18" cy="11.5" r="1.7"/><path d="M8.8 16.3c1.2 2.2 3 3.3 5.2 3.3s4-1.1 5.2-3.3" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
    lines: '<svg viewBox="0 0 30 26"><path d="M1 2h28M1 9.3h20M1 16.6h28M1 24h20" stroke="currentColor" stroke-width="2.6"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.6 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    shift: '<svg viewBox="0 0 20 20"><path d="M10 2.5 2.5 10.5h4.2v6.5h6.6v-6.5h4.2Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    del: '<svg viewBox="0 0 26 20"><path d="M8 2h15.5c.8 0 1.5.7 1.5 1.5v13c0 .8-.7 1.5-1.5 1.5H8L1 10Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="m12 6.5 7 7m0-7-7 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    logo: '<svg viewBox="0 0 26 16"><path d="M2.5 13.5C2.5 6 5.5 2.5 8.5 2.5s4.5 4 4.5 5.5 1.5 5.5 4.5 5.5 6-3.5 6-11" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/></svg>',
  };

  const keyRow = (keys) => keys.split('').map((k) => `<span class="cc-key" data-key="${k}">${k}</span>`).join('');

  root.querySelector('.cc-fallback')?.remove();
  const stageEl = document.createElement('div');
  stageEl.className = 'cc-device-wrap';
  stageEl.innerHTML = `
  <div class="cc-device" aria-hidden="true">
    <div class="cc-screen">
      <div class="cc-status"><span class="cc-time">9:41</span><span class="cc-island"></span>
        <span class="cc-status-icons">${icon.signal}${icon.wifi}${icon.battery}</span></div>
      <div class="cc-nav"><span class="cc-title">Create your card</span><span class="cc-done">Done</span></div>
      <div class="cc-card">
        <div class="cc-card-art"></div>
        <div class="cc-brand">${icon.logo}<span>NETSPEND</span></div>
        <div class="cc-number"><span>••••</span> 3456</div>
        <div class="cc-mc"><i></i><i></i><span>mastercard</span></div>
        <div class="cc-shine"></div>
      </div>
      <div class="cc-tools">
        <span class="cc-swatch"></span>
        <span class="cc-add">${icon.smile}</span>
        <span class="cc-layers">${icon.lines}</span>
      </div>
      <div class="cc-success"><strong>Looking good!</strong><span>Your new card is on its way.</span></div>
      <div class="cc-panel" data-view="emoji">
        <div class="cc-field">${icon.search}<span class="cc-placeholder">Search Emoji</span><span class="cc-query"></span><i class="cc-caret"></i></div>
        <div class="cc-view cc-v-emoji">
          <div class="cc-groups">
            <div class="cc-group"><b>Frequently used</b><div class="cc-grid">${FREQUENT.map((e) => `<span>${e}</span>`).join('')}</div></div>
            <div class="cc-group"><b>Smileys &amp; people</b><div class="cc-grid">${SMILEYS.map((e) => `<span>${e}</span>`).join('')}</div></div>
          </div>
          <div class="cc-cats">${CATEGORIES.map((e, i) => `<span class="${i ? '' : 'on'}">${e}</span>`).join('')}${icon.del}</div>
        </div>
        <div class="cc-view cc-v-search">
          <div class="cc-results"></div>
          <div class="cc-kb">
            <div class="cc-kb-row">${keyRow('qwertyuiop')}</div>
            <div class="cc-kb-row cc-kb-mid">${keyRow('asdfghjkl')}</div>
            <div class="cc-kb-row"><span class="cc-key cc-key-fn">${icon.shift}</span>${keyRow('zxcvbnm')}<span class="cc-key cc-key-fn">${icon.del}</span></div>
            <div class="cc-kb-row"><span class="cc-key cc-key-fn cc-key-sm">123</span><span class="cc-key cc-key-fn cc-key-sm">😀</span><span class="cc-key cc-key-space">space</span><span class="cc-key cc-key-go">search</span></div>
          </div>
        </div>
        <div class="cc-view cc-v-color">
          <div class="cc-color-label">Card color</div>
          <div class="cc-dots">${COLORS.map((c) => `<span class="cc-dot${c.dark ? ' is-dark' : ''}" data-color="${c.name}" style="background:${c.hex}">${icon.check}</span>`).join('')}</div>
          <div class="cc-color-hint">Tap ${icon.smile} to add emoji</div>
        </div>
      </div>
      <div class="cc-home"></div>
      <div class="cc-touch"></div><div class="cc-touch"></div>
    </div>
  </div>`;
  root.prepend(stageEl);

  const $ = (s) => stageEl.querySelector(s);
  const device = $('.cc-device'), screen = $('.cc-screen'), card = $('.cc-card'), art = $('.cc-card-art');
  const panel = $('.cc-panel'), query = $('.cc-query'), results = $('.cc-results'), swatch = $('.cc-swatch');
  const [f1, f2] = stageEl.querySelectorAll('.cc-touch');

  // Scale the phone to whatever width the column gives it.
  const fit = () => { device.style.transform = `scale(${stageEl.clientWidth / DW})`; };
  new ResizeObserver(fit).observe(stageEl);
  fit();

  /* ---------- clock ---------- */

  let clock = 0, last = null, userPaused = false, onScreen = true, running = false;
  const tweens = new Set();
  const frame = (t) => {
    if (last !== null && !userPaused && onScreen) clock += Math.min(t - last, 50);
    last = t;
    for (const tw of tweens) {
      const p = Math.min(1, (clock - tw.start) / tw.dur);
      tw.fn(tw.ease(p));
      if (p >= 1) { tweens.delete(tw); tw.done(); }
    }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);

  const ease = {
    inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    out: (t) => 1 - Math.pow(1 - t, 3),
    linear: (t) => t,
  };
  const tween = (dur, fn = () => {}, e = ease.inOut) =>
    new Promise((done) => tweens.add({ start: clock, dur, fn, ease: e, done }));
  const wait = (ms) => tween(ms);
  const lerp = (a, b, t) => a + (b - a) * t;

  /* ---------- geometry ---------- */

  const scale = () => screen.getBoundingClientRect().width / SW;
  const center = (el) => {
    const r = el.getBoundingClientRect(), s = screen.getBoundingClientRect(), k = scale();
    return { x: (r.left + r.width / 2 - s.left) / k, y: (r.top + r.height / 2 - s.top) / k };
  };

  /* ---------- touches ---------- */

  const finger = { x: SW / 2, y: 900 };
  const place = (el, p) => { el.style.transform = `translate(${p.x}px, ${p.y}px)`; };
  place(f1, finger);

  const moveTo = async (p, dur = 520) => {
    const a = { ...finger };
    f1.classList.add('on');
    await tween(dur, (t) => { finger.x = lerp(a.x, p.x, t); finger.y = lerp(a.y, p.y, t); place(f1, finger); });
  };
  const press = (on) => f1.classList.toggle('down', on);
  const tap = async (el, dur = 520, hold = 140) => {
    await moveTo(center(el), dur);
    press(true);
    el.classList.add('pressed');
    await wait(hold);
    press(false);
    el.classList.remove('pressed');
  };
  const lift = async () => { f1.classList.remove('on'); await wait(200); };

  /* ---------- card ---------- */

  const setColor = (name) => {
    const c = COLORS.find((k) => k.name === name);
    card.style.background = c.hex;
    card.classList.toggle('is-dark', !!c.dark);
    swatch.style.background = c.hex;
    stageEl.querySelectorAll('.cc-dot').forEach((d) => d.classList.toggle('on', d.dataset.color === name));
  };

  const render = (em) => {
    const { x, y, s, r } = em.st;
    em.el.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${r}deg) scale(${s})`;
  };
  const addEmoji = (e, st) => {
    const el = document.createElement('span');
    el.className = 'cc-emoji';
    el.textContent = e;
    art.append(el);
    const em = { el, st: { ...st } };
    render(em);
    return em;
  };

  const flyToCard = async (fromEl, e, st) => {
    const a = center(fromEl), b = center(card);
    const fly = document.createElement('span');
    fly.className = 'cc-fly';
    fly.textContent = e;
    screen.append(fly);
    const s0 = 34 / 72;
    await tween(560, (t) => {
      const x = lerp(a.x, b.x + st.x, t), y = lerp(a.y, b.y + st.y, t) - Math.sin(t * Math.PI) * 60;
      fly.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px) scale(${lerp(s0, st.s, t)})`;
    }, ease.out);
    fly.remove();
    return addEmoji(e, st);
  };

  // Two fingers around the emoji: spread or squeeze to scale, turn to rotate.
  const pinch = async (em, to) => {
    const c0 = center(card);
    const at = (st, k) => {
      const d = 30 + 46 * st.s, a = ((-38 + st.r) * Math.PI) / 180;
      return { x: c0.x + st.x + k * d * Math.cos(a), y: c0.y + st.y + k * d * Math.sin(a) };
    };
    await moveTo(at(em.st, -1), 420);
    place(f2, at(em.st, 1));
    f2.classList.add('on');
    await wait(160);
    f1.classList.add('down'); f2.classList.add('down');
    em.el.classList.add('sel');
    const from = { ...em.st };
    await tween(900, (t) => {
      em.st.s = lerp(from.s, to.s, t);
      em.st.r = lerp(from.r, to.r, t);
      render(em);
      const p = at(em.st, -1);
      finger.x = p.x; finger.y = p.y;
      place(f1, p); place(f2, at(em.st, 1));
    });
    f1.classList.remove('down'); f2.classList.remove('down');
    f2.classList.remove('on');
    await wait(180);
  };

  const drag = async (em, to) => {
    const c0 = center(card);
    await moveTo({ x: c0.x + em.st.x, y: c0.y + em.st.y }, 380);
    press(true);
    em.el.classList.add('sel');
    await wait(120);
    const from = { ...em.st };
    await tween(720, (t) => {
      em.st.x = lerp(from.x, to.x, t);
      em.st.y = lerp(from.y, to.y, t);
      render(em);
      finger.x = c0.x + em.st.x; finger.y = c0.y + em.st.y;
      place(f1, finger);
    });
    press(false);
    await wait(140);
  };

  /* ---------- panel ---------- */

  const view = (v) => { panel.dataset.view = v; };
  const typeQuery = async (sc) => {
    for (const ch of sc.query) {
      const key = stageEl.querySelector(`.cc-key[data-key="${ch}"]`);
      await tap(key, 150, 70);
      query.textContent += ch;
      if (query.textContent.length === 3) showResults(sc.results);
    }
  };
  const showResults = (list) => {
    results.innerHTML = list.map((e) => `<span>${e}</span>`).join('');
    requestAnimationFrame(() => results.classList.add('on'));
  };

  const reset = () => {
    art.innerHTML = '';
    query.textContent = '';
    results.innerHTML = '';
    results.classList.remove('on');
    stageEl.classList.remove('is-done');
    panel.classList.remove('typing');
    view('emoji');
    setColor('Black');
  };

  /* ---------- the scripted loop ---------- */

  const playScene = async (sc) => {
    // Card color
    await wait(700);
    await tap(swatch, 700);
    view('color');
    await wait(380);
    for (const c of sc.colors) {
      await tap(stageEl.querySelector(`.cc-dot[data-color="${c}"]`), 420);
      setColor(c);
      await wait(380);
    }
    await tap($('.cc-add'), 520);
    view('emoji');
    await wait(450);

    // Search
    await tap($('.cc-field'), 560);
    view('search');
    panel.classList.add('typing');
    await wait(420);
    await typeQuery(sc);
    await wait(300);

    // Drop, then pinch / rotate / drag each emoji into place
    for (const p of sc.place) {
      const i = sc.results.indexOf(p.e);
      const cell = results.children[i];
      await tap(cell, 480);
      const drop = p.pinch ? { x: 0, y: 0, s: p.to.s > 1.2 ? 0.95 : 1.45, r: 0 } : { x: 0, y: 0, s: p.to.s, r: p.to.r };
      const em = await flyToCard(cell, p.e, drop);
      await wait(220);
      if (p.pinch) await pinch(em, p.to);
      if (p.to.x || p.to.y) await drag(em, p.to);
      em.el.classList.remove('sel');
      await wait(260);
    }

    // Done
    await tap($('.cc-done'), 620);
    await lift();
    stageEl.classList.add('is-done');
    await wait(3600);
    stageEl.classList.add('is-resetting');
    await wait(450);
    reset();
    await wait(150);
    stageEl.classList.remove('is-resetting');
  };

  const loop = async () => {
    running = true;
    for (let i = 0; ; i = (i + 1) % SCENES.length) await playScene(SCENES[i]);
  };

  // Static final frame of the first card, for reduced motion (and before play is pressed).
  const still = () => {
    const sc = SCENES[0];
    setColor(sc.colors[sc.colors.length - 1]);
    sc.place.forEach((p) => addEmoji(p.e, p.to));
  };

  /* ---------- controls ---------- */

  const btn = root.querySelector('.cc-toggle');
  const sync = () => {
    const playing = running && !userPaused;
    btn.innerHTML = playing
      ? '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="2" width="3.5" height="12"/><rect x="9.5" y="2" width="3.5" height="12"/></svg>'
      : '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2v12l10-6z"/></svg>';
    btn.setAttribute('aria-label', playing ? 'Pause the animation' : 'Play the animation');
  };
  btn.addEventListener('click', () => {
    if (!running) { reset(); userPaused = false; loop(); }
    else userPaused = !userPaused;
    sync();
  });

  new IntersectionObserver(([e]) => { onScreen = e.isIntersecting; }, { threshold: 0.15 }).observe(stageEl);

  reset();
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) still();
  else loop();
  sync();
})();
