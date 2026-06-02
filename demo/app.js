/* ═══════════════════════════════════════════════════════════
   LAMO'S CHOCOLATE — app.js
   Dubai · Switzerland · Since 2021
═══════════════════════════════════════════════════════════ */

'use strict';

/* ─── UTILITIES ─── */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const on = (el, ev, fn) => el && el.addEventListener(ev, fn);

/* ─── STATE ─── */
const state = {
  cart: JSON.parse(localStorage.getItem('lamos_cart') || '[]'),
  activeFilter: 'all',
  modalProduct: null,
  qty: 1
};

/* ═══════════════════════════════════════════════════════════
   1. PAGE LOADER
═══════════════════════════════════════════════════════════ */
function initLoader() {
  const loader = $('#loader');
  if (!loader) return;
  setTimeout(() => {
    loader.classList.add('hidden');
    document.body.style.overflow = '';
  }, 1800);
  document.body.style.overflow = 'hidden';
}

/* ═══════════════════════════════════════════════════════════
   2. CUSTOM CURSOR
═══════════════════════════════════════════════════════════ */
function initCursor() {
  const ring = $('.cursor-ring');
  const dot  = $('.cursor-dot');
  if (!ring || !dot) return;

  let mx = -100, my = -100, rx = -100, ry = -100;
  let raf;

  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    dot.style.transform = `translate(${mx}px, ${my}px) translate(-50%, -50%)`;
  });

  function animRing() {
    rx += (mx - rx) * 0.14;
    ry += (my - ry) * 0.14;
    ring.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%)`;
    raf = requestAnimationFrame(animRing);
  }
  animRing();

  /* Hover on interactive elements */
  on(document, 'mouseover', e => {
    const t = e.target.closest('a, button, .product-card, .featured-card, .pc-format-tag, .filter-btn, .modal-format');
    ring.classList.toggle('hovered', !!t);
  });

  /* Pointer lock on leaving window */
  document.addEventListener('mouseleave', () => {
    mx = -200; my = -200;
  });
}

/* ═══════════════════════════════════════════════════════════
   3. NAVIGATION
═══════════════════════════════════════════════════════════ */
function initNav() {
  const nav    = $('#nav');
  const burger = $('.nav-burger');
  const mobileNav = $('.nav-mobile');
  if (!nav) return;

  /* Scroll behaviour */
  let lastY = 0;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 60);
    /* Hide nav on fast scroll down, show on up */
    if (y > lastY + 80 && y > 300) nav.style.transform = 'translateY(-100%)';
    else nav.style.transform = '';
    lastY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });

  /* Mobile burger */
  if (burger && mobileNav) {
    on(burger, 'click', () => {
      burger.classList.toggle('open');
      mobileNav.classList.toggle('open');
      document.body.style.overflow = mobileNav.classList.contains('open') ? 'hidden' : '';
    });
    $$('a', mobileNav).forEach(a => on(a, 'click', () => {
      burger.classList.remove('open');
      mobileNav.classList.remove('open');
      document.body.style.overflow = '';
    }));
  }

  /* Active link highlighting */
  const path = window.location.pathname.split('/').pop() || 'index.html';
  $$('.nav-links a, .nav-mobile-links a').forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href === path || (href === 'index.html' && path === '')) a.classList.add('active');
  });

  /* Cart count */
  updateCartCount();
}

/* ═══════════════════════════════════════════════════════════
   4. SCROLL REVEAL
═══════════════════════════════════════════════════════════ */
function initReveal() {
  const opts = { threshold: 0.1, rootMargin: '0px 0px -60px 0px' };
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, opts);

  $$('.reveal, .reveal-left, .reveal-right').forEach(el => obs.observe(el));
}

/* ═══════════════════════════════════════════════════════════
   5. PARALLAX (hero + sections)
═══════════════════════════════════════════════════════════ */
function initParallax() {
  const targets = $$('[data-parallax]');
  if (!targets.length) return;

  const onScroll = () => {
    targets.forEach(el => {
      const speed = parseFloat(el.dataset.parallax) || 0.3;
      const rect  = el.getBoundingClientRect();
      const center = rect.top + rect.height / 2 - window.innerHeight / 2;
      el.style.transform = `translateY(${center * speed}px)`;
    });
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/* ═══════════════════════════════════════════════════════════
   6. ANIMATED COUNTERS
═══════════════════════════════════════════════════════════ */
function initCounters() {
  const counters = $$('[data-counter]');
  if (!counters.length) return;

  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        animCounter(e.target);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => obs.observe(el));
}

function animCounter(el) {
  const target = parseFloat(el.dataset.counter);
  const suffix = el.dataset.suffix || '';
  const prefix = el.dataset.prefix || '';
  const dur    = 2000;
  const steps  = 60;
  const step   = target / steps;
  let current  = 0;
  let count    = 0;

  const tick = () => {
    count++;
    current = Math.min(current + step, target);
    const display = target % 1 === 0 ? Math.round(current) : current.toFixed(1);
    el.textContent = prefix + display + suffix;
    if (count < steps) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/* ═══════════════════════════════════════════════════════════
   7. GOLD PARTICLES (Hero)
═══════════════════════════════════════════════════════════ */
function initParticles() {
  const canvas = $('#hero-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let W, H, particles;

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function createParticles() {
    particles = Array.from({ length: 60 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -Math.random() * 0.5 - 0.1,
      size: Math.random() * 1.5 + 0.3,
      alpha: Math.random() * 0.4 + 0.1,
      life: Math.random()
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.life += 0.003;
      if (p.life > 1 || p.y < 0) {
        p.x = Math.random() * W;
        p.y = H + 10;
        p.life = 0;
      }
      const alpha = p.alpha * Math.sin(p.life * Math.PI);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(201, 168, 76, ${alpha})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }

  resize();
  createParticles();
  draw();
  window.addEventListener('resize', () => { resize(); createParticles(); });
}

/* ═══════════════════════════════════════════════════════════
   8. MARQUEE (duplicate for seamless loop)
═══════════════════════════════════════════════════════════ */
function initMarquee() {
  const inner = $('.marquee-inner');
  if (!inner) return;
  const clone = inner.cloneNode(true);
  inner.parentElement.appendChild(clone);
}

/* ═══════════════════════════════════════════════════════════
   9. PRODUCT FILTER (boutique)
═══════════════════════════════════════════════════════════ */
function initFilter() {
  const btns  = $$('.filter-btn');
  const cards = $$('.product-card[data-category]');
  if (!btns.length) return;

  btns.forEach(btn => {
    on(btn, 'click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;
      state.activeFilter = filter;

      cards.forEach((card, i) => {
        const match = filter === 'all' || card.dataset.category === filter;
        card.style.transition = `opacity 0.35s ${i * 0.04}s, transform 0.35s ${i * 0.04}s`;
        if (match) {
          card.style.opacity = '1';
          card.style.transform = 'scale(1)';
          card.style.pointerEvents = '';
          card.style.position = '';
        } else {
          card.style.opacity = '0';
          card.style.transform = 'scale(0.97)';
          card.style.pointerEvents = 'none';
          card.style.position = 'absolute';
        }
      });
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   10. PRODUCT MODAL
═══════════════════════════════════════════════════════════ */
const PRODUCTS = {
  'pistachio': {
    category: 'Chocolat Dubai',
    name: 'Pistachio & Kunafa',
    desc: 'Un chocolat au lait soyeux (36% cacao, 19% matières laitières) enrobant une généreuse crème pistachio-kunafa (35%). Élaboré à partir de beurre de cacao, lait entier en poudre, masse de cacao, vanille et pistaches — une harmonie raffinée entre douceur lactée et intensité indulgente. La technique kunafa artisanale de LAMOS est exclusive, développée par des chefs primés aux Émirats.',
    formats: ['45g — CHF 9.50', '80g — CHF 15.90', '200g — CHF 34.90'],
    theme: 'ph-pistachio',
    badge: 'Signature'
  },
  'pecan': {
    category: 'Chocolat Noir',
    name: 'Pecan Praline',
    desc: 'Sous une couverture de chocolat noir (min. 55,2% cacao) se cache un praliné pécan à 55%, dont la texture soyeuse révèle une douceur subtilement boisée. Le beurre de cacao pur, la masse de cacao sélectionnée et la vanille délivrent une intensité parfaitement équilibrée. Une création qui marie caractère et finesse.',
    formats: ['80g — CHF 15.90'],
    theme: 'ph-dark',
    badge: null
  },
  'coffee': {
    category: 'Chocolat au Lait',
    name: 'Coffee Chocolate',
    desc: 'Soigneusement élaboré à partir de café finement torréfié, de lait entier et d\'une touche de vanille, ce ganache onctueux s\'entremêle à la douceur lactée du chocolat pour offrir une expérience de dégustation élégante et profondément réconfortante. Un chocolat au lait révélant un cœur café fondant — intensément aromatique.',
    formats: ['80g — CHF 15.90'],
    theme: 'ph-coffee',
    badge: null
  },
  'mascarpone': {
    category: 'Chocolat Blanc',
    name: 'Mascarpone',
    desc: 'Un chocolat blanc d\'exception enrobant un cœur crémeux au mascarpone, délicat et subtilement vanillé. Une création aérienne qui fond en bouche avec une douceur inoubliable, révélant la richesse de la crème italienne rencontrée dans l\'univers du chocolat suisse premium.',
    formats: ['80g — CHF 16.90'],
    theme: 'ph-mascarpone',
    badge: 'Nouveau'
  },
  'matcha': {
    category: 'Collection Exclusive',
    name: 'Matcha',
    desc: 'L\'alliance inattendue du matcha cérémonial japonais Grade A et du chocolat blanc suisse Carma. Une explosion de notes végétales et terreuses, équilibrée par la douceur lactée du chocolat. Une création unique qui traverse les cultures — du Japon à Dubaï, de Dubaï à Genève.',
    formats: ['80g — CHF 16.90'],
    theme: 'ph-matcha',
    badge: 'Nouveau'
  },
  'rouge': {
    category: 'Collection Exclusive',
    name: 'Fruits Rouges',
    desc: 'Un chocolat au lait intense marié à un cœur de coulis de fruits rouges — framboises, cassis et groseilles sélectionnés. L\'acidité naturelle des fruits contraste délicieusement avec la richesse du chocolat Carma, créant une danse de saveurs entre l\'Orient et l\'Europe.',
    formats: ['80g — CHF 16.90'],
    theme: 'ph-rouge',
    badge: 'Nouveau'
  }
};

function initModal() {
  const overlay = $('#product-modal');
  if (!overlay) return;

  const closeBtn = overlay.querySelector('.modal-close');
  on(closeBtn, 'click', closeModal);
  on(overlay, 'click', e => { if (e.target === overlay) closeModal(); });

  /* Format selector */
  on(overlay, 'click', e => {
    const f = e.target.closest('.modal-format');
    if (f) {
      $$('.modal-format', overlay).forEach(x => x.classList.remove('active'));
      f.classList.add('active');
    }
  });

  /* Qty */
  const minusBtn = overlay.querySelector('.qty-minus');
  const plusBtn  = overlay.querySelector('.qty-plus');
  const qtyDisplay = overlay.querySelector('.qty-display');
  on(minusBtn, 'click', () => { state.qty = Math.max(1, state.qty - 1); qtyDisplay.textContent = state.qty; });
  on(plusBtn,  'click', () => { state.qty = Math.min(20, state.qty + 1); qtyDisplay.textContent = state.qty; });

  /* Add to cart */
  const addBtn = overlay.querySelector('.modal-add-cart');
  on(addBtn, 'click', () => {
    const p = state.modalProduct;
    const fmt = overlay.querySelector('.modal-format.active');
    if (!p || !fmt) return;
    addToCart(p.name, fmt.textContent, state.qty);
    closeModal();
  });

  /* Escape key */
  on(document, 'keydown', e => { if (e.key === 'Escape') closeModal(); });

  /* Open on card click */
  $$('.pc-action-detail, [data-open-modal]').forEach(btn => {
    on(btn, 'click', e => {
      e.stopPropagation();
      const key = btn.closest('[data-product]')?.dataset.product;
      if (key) openModal(key);
    });
  });
}

function openModal(key) {
  const p = PRODUCTS[key];
  if (!p) return;
  state.modalProduct = p;
  state.qty = 1;

  const overlay = $('#product-modal');
  const qtyDisplay = overlay?.querySelector('.qty-display');
  if (qtyDisplay) qtyDisplay.textContent = '1';

  /* Populate */
  setModal('modal-category', p.category);
  setModal('modal-name',     p.name);
  setModal('modal-desc',     p.desc);

  /* Image */
  const imgEl = overlay?.querySelector('.modal-img');
  if (imgEl) {
    imgEl.innerHTML = '';
    const ph = document.createElement('div');
    ph.className = `prod-ph ${p.theme}`;
    ph.style.minHeight = '100%';
    ph.innerHTML = `<div class="prod-ph-crown">${crownSVG()}</div><span class="prod-ph-label">${p.name}</span>`;
    imgEl.appendChild(ph);
    if (p.badge) {
      const b = document.createElement('div');
      b.className = 'pc-badge' + (p.badge === 'Nouveau' ? ' pc-badge-new' : '');
      b.textContent = p.badge;
      imgEl.appendChild(b);
    }
  }

  /* Formats */
  const fmtGroup = overlay?.querySelector('.modal-format-group');
  if (fmtGroup) {
    fmtGroup.innerHTML = p.formats.map((f, i) =>
      `<button class="modal-format${i === 0 ? ' active' : ''}">${f}</button>`
    ).join('');
  }

  overlay?.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  $('#product-modal')?.classList.remove('open');
  document.body.style.overflow = '';
}

function setModal(id, val) {
  const el = $(`#${id}`);
  if (el) el.textContent = val;
}

/* ═══════════════════════════════════════════════════════════
   11. CART
═══════════════════════════════════════════════════════════ */
function addToCart(name, format, qty) {
  const existing = state.cart.find(i => i.name === name && i.format === format);
  if (existing) existing.qty += qty;
  else state.cart.push({ name, format, qty });

  localStorage.setItem('lamos_cart', JSON.stringify(state.cart));
  updateCartCount();
  showCartToast(name, qty);
}

function updateCartCount() {
  const total = state.cart.reduce((s, i) => s + i.qty, 0);
  $$('.cart-count').forEach(el => { el.textContent = total; el.style.display = total ? '' : 'none'; });
}

function showCartToast(name, qty) {
  const toast = $('#cart-toast');
  if (!toast) return;
  const titleEl = toast.querySelector('.cart-toast-title');
  const descEl  = toast.querySelector('.cart-toast-desc');
  if (titleEl) titleEl.textContent = 'Ajouté au panier';
  if (descEl)  descEl.textContent  = `${qty}× ${name}`;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

/* Quick-add on product card */
function initQuickAdd() {
  $$('.pc-action-buy').forEach(btn => {
    on(btn, 'click', e => {
      e.stopPropagation();
      const card = btn.closest('[data-product]');
      if (!card) return;
      const key = card.dataset.product;
      const p   = PRODUCTS[key];
      if (!p) return;
      const fmt = p.formats[0]; // default: first format
      addToCart(p.name, fmt, 1);
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   12. CONTACT / ORDER FORM VALIDATION
═══════════════════════════════════════════════════════════ */
function initForms() {
  $$('form[data-validate]').forEach(form => {
    on(form, 'submit', e => {
      e.preventDefault();
      if (validateForm(form)) submitForm(form);
    });

    /* Real-time validation */
    $$('[required]', form).forEach(input => {
      on(input, 'blur', () => validateField(input));
      on(input, 'input', () => { if (input.classList.contains('error')) validateField(input); });
    });
  });
}

function validateField(input) {
  const group = input.closest('.form-group');
  const errEl = group?.querySelector('.form-error-msg');
  let valid = true;
  let msg   = '';

  if (!input.value.trim()) {
    valid = false; msg = 'Ce champ est requis.';
  } else if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) {
    valid = false; msg = 'Adresse e-mail invalide.';
  } else if (input.type === 'tel' && input.value.length < 8) {
    valid = false; msg = 'Numéro de téléphone invalide.';
  }

  input.classList.toggle('error', !valid);
  group?.classList.toggle('has-error', !valid);
  if (errEl) errEl.textContent = msg;
  return valid;
}

function validateForm(form) {
  const fields = $$('[required]', form);
  return fields.map(validateField).every(Boolean);
}

function submitForm(form) {
  const btn = form.querySelector('[type="submit"]');
  if (btn) { btn.textContent = 'Envoi en cours…'; btn.disabled = true; }

  setTimeout(() => {
    form.style.display = 'none';
    const success = form.nextElementSibling;
    if (success?.classList.contains('form-success')) success.classList.add('show');
  }, 1400);
}

/* ═══════════════════════════════════════════════════════════
   13. PAGE TRANSITIONS
═══════════════════════════════════════════════════════════ */
function initPageTransitions() {
  const cover = $('#page-cover');
  if (!cover) return;

  /* Exit on internal link click */
  on(document, 'click', e => {
    const a = e.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('tel') || a.target === '_blank') return;
    e.preventDefault();
    cover.classList.remove('exit');
    cover.classList.add('enter');
    setTimeout(() => { window.location.href = href; }, 480);
  });

  /* Entry animation */
  cover.classList.add('exit');
  setTimeout(() => cover.classList.remove('exit'), 500);
}

/* ═══════════════════════════════════════════════════════════
   14. MAGNETIC BUTTONS
═══════════════════════════════════════════════════════════ */
function initMagnetic() {
  $$('.btn-gold, .btn-lg').forEach(btn => {
    on(btn, 'mousemove', e => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width  / 2;
      const cy = rect.top  + rect.height / 2;
      const dx = (e.clientX - cx) * 0.25;
      const dy = (e.clientY - cy) * 0.35;
      btn.style.transform = `translate(${dx}px, ${dy}px)`;
    });
    on(btn, 'mouseleave', () => { btn.style.transform = ''; });
  });
}

/* ═══════════════════════════════════════════════════════════
   15. NEWSLETTER (footer)
═══════════════════════════════════════════════════════════ */
function initNewsletter() {
  const form = $('.footer-newsletter');
  if (!form) return;
  const btn   = form.querySelector('button');
  const input = form.querySelector('input');
  on(btn, 'click', () => {
    if (!input || !input.value.includes('@')) {
      input.classList.add('error'); return;
    }
    input.classList.remove('error');
    btn.textContent = '✓ Inscrit';
    btn.style.background = 'var(--c-green2)';
    input.value = ''; input.disabled = true; btn.disabled = true;
  });
}

/* ═══════════════════════════════════════════════════════════
   CROWN SVG HELPER
═══════════════════════════════════════════════════════════ */
function crownSVG(color = '#c9a84c') {
  return `<svg viewBox="0 0 100 80" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="50,8 68,28 88,14 82,52 18,52 12,14 32,28" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>
    <rect x="16" y="54" width="68" height="5" fill="${color}"/>
    <rect x="12" y="62" width="76" height="3.5" fill="none" stroke="${color}" stroke-width="1.5"/>
    <circle cx="50" cy="8" r="4" fill="${color}"/>
    <circle cx="12" cy="14" r="3.5" fill="${color}"/>
    <circle cx="88" cy="14" r="3.5" fill="${color}"/>
  </svg>`;
}

/* ═══════════════════════════════════════════════════════════
   16. TIMELINE ANIMATION (about)
═══════════════════════════════════════════════════════════ */
function initTimeline() {
  const line = $('.timeline-line');
  if (!line) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.animation = 'timelineGrow 1.5s var(--ease-out) forwards';
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  obs.observe(line);
  const style = document.createElement('style');
  style.textContent = '@keyframes timelineGrow { from { scaleY: 0; transform-origin: top; } to { scaleY: 1; } }';
  document.head.appendChild(style);
}

/* ═══════════════════════════════════════════════════════════
   INIT ALL
═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initLoader();
  initCursor();
  initNav();
  initReveal();
  initParallax();
  initCounters();
  initParticles();
  initMarquee();
  initFilter();
  initModal();
  initQuickAdd();
  initForms();
  initPageTransitions();
  initMagnetic();
  initNewsletter();
  initTimeline();
});
