/* Theme: dark mode (localStorage) + tenant brand variables.
   Inahitaji <html> iwe na data-tenant-themed + --tenant-brand kutoka base template. */
(function () {
  'use strict';

  var KEY = 'shuleplus-theme';

  function preferred() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
    if (saved === 'dark' || saved === 'light') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function apply(mode) {
    document.documentElement.classList.toggle('dark', mode === 'dark');
    var btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      btn.setAttribute('aria-pressed', mode === 'dark' ? 'true' : 'false');
      btn.setAttribute('title', mode === 'dark' ? 'Washa mwonekano wa mchana' : 'Washa mwonekano wa usiku');
      var sun = btn.querySelector('[data-icon="sun"]');
      var moon = btn.querySelector('[data-icon="moon"]');
      if (sun && moon) {
        sun.style.display = mode === 'dark' ? 'block' : 'none';
        moon.style.display = mode === 'dark' ? 'none' : 'block';
      }
    }
    document.dispatchEvent(new CustomEvent('sp:theme', { detail: { mode: mode } }));
  }

  // Mara moja kabla ya rendering nyingine ili epuka "flash" nyeupe
  apply(preferred());

  window.SPTheme = {
    toggle: function () {
      var next = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
      try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
      apply(next);
    },
    mode: function () {
      return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    }
  };

  document.addEventListener('click', function (ev) {
    var t = ev.target.closest && ev.target.closest('[data-theme-toggle]');
    if (t) {
      ev.preventDefault();
      window.SPTheme.toggle();
    }
  });
})();
