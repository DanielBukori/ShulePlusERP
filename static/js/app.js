/* Shell helpers: scroll reveal, animated counters, dropdowns, drawer. */
(function () {
  'use strict';

  document.documentElement.classList.add('js');

  function onReady(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  /* ---------- Scroll reveal ---------- */
  function initReveal() {
    var items = document.querySelectorAll('.sp-reveal');
    if (!items.length) return;
    if (!('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('sp-shown'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('sp-shown');
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: '0px 0px -40px 0px', threshold: 0.06 });
    items.forEach(function (el, i) {
      if (!el.style.getPropertyValue('--sp-delay')) {
        el.style.setProperty('--sp-delay', Math.min(i, 8) * 45 + 'ms');
      }
      io.observe(el);
    });

    // Salama ya mwisho: hakuna kitu kinachobaki kama hakiionekani.
    // (IO hushindwa kwenye print, screenshot ya ukurasa mzima, au viewport
    // ambayo haibadiliki - maudhui yote yalipaswa kuonekana.)
    setTimeout(function () {
      items.forEach(function (el) { el.classList.add('sp-shown'); });
      io.disconnect();
    }, 2500);
  }

  /* ---------- Animated counters: <span data-count="15"> ---------- */
  function initCounters() {
    var nodes = document.querySelectorAll('[data-count]');
    if (!nodes.length) return;
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function run(el) {
      var target = parseFloat(el.getAttribute('data-count'));
      if (isNaN(target)) return;
      var decimals = parseInt(el.getAttribute('data-count-decimals') || '0', 10);
      var prefix = el.getAttribute('data-count-prefix') || '';
      var suffix = el.getAttribute('data-count-suffix') || '';
      var fmt = function (v) {
        return prefix + v.toLocaleString('en-US', {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals
        }) + suffix;
      };
      if (reduce) { el.textContent = fmt(target); return; }
      var dur = 700, t0 = null;
      function step(ts) {
        if (!t0) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(target * eased);
        if (p < 1) requestAnimationFrame(step);
        else el.textContent = fmt(target);
      }
      el.textContent = fmt(0);
      requestAnimationFrame(step);
    }

    if (!('IntersectionObserver' in window)) { nodes.forEach(run); return; }
    var started = new WeakSet();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { started.add(en.target); run(en.target); io.unobserve(en.target); }
      });
    }, { threshold: 0.3 });
    nodes.forEach(function (el) { io.observe(el); });

    // Salama ya mwisho: kama IO haijawahi (tab isiyonekana, print, webview
    // ya zamani), nambari zisibaki 0 milele.
    setTimeout(function () {
      nodes.forEach(function (el) {
        if (!started.has(el)) run(el);
      });
      io.disconnect();
    }, 2500);
  }

  /* ---------- Popovers: [data-popover] toggles #<id> ---------- */
  function initPopovers() {
    document.addEventListener('click', function (ev) {
      var trigger = ev.target.closest && ev.target.closest('[data-popover]');
      var panelId = trigger && trigger.getAttribute('data-popover');
      document.querySelectorAll('[data-popover-panel]').forEach(function (panel) {
        if (panel.id === panelId && trigger) {
          panel.classList.toggle('hidden');
        } else {
          panel.classList.add('hidden');
        }
      });
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') {
        document.querySelectorAll('[data-popover-panel]:not(.hidden)').forEach(function (p) { p.classList.add('hidden'); });
      }
    });
  }

  /* ---------- Drawer (simu) ---------- */
  function initDrawer() {
    var bar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (!bar || !overlay) return;
    function open() { bar.classList.remove('-translate-x-full'); overlay.classList.remove('hidden'); }
    function close() { bar.classList.add('-translate-x-full'); overlay.classList.add('hidden'); }
    document.querySelectorAll('[data-drawer="open"]').forEach(function (b) { b.addEventListener('click', open); });
    document.querySelectorAll('[data-drawer="close"]').forEach(function (b) { b.addEventListener('click', close); });
    overlay.addEventListener('click', close);
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') close(); });
  }

  /* ---------- Active nav link ---------- */
  function markActiveNav() {
    var here = window.location.pathname.replace(/\/+$/, '') || '/';
    var best = null, bestLen = -1;
    document.querySelectorAll('aside nav a[href]').forEach(function (a) {
      var href = (a.getAttribute('href') || '').replace(/\/+$/, '') || '/';
      if (here === href && href.length > bestLen) { best = a; bestLen = href.length; }
      else if (!best && here.indexOf(href) === 0 && href !== '/' && href.length > bestLen) { best = a; bestLen = href.length; }
    });
    if (best) best.classList.add('is-active');
  }

  onReady(function () {
    initReveal();
    initCounters();
    initPopovers();
    initDrawer();
    markActiveNav();
  });
})();
