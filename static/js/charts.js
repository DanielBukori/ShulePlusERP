/* SPCharts - Chart.js iliyohifadhiwa ndani (static/js/vendor/chart.umd.min.js)
   Chati zote husoma rangi kutoka CSS variables, hivyo zinaendana na
   dark mode na rangi ya kila shule (--tenant-brand).

   Matumizi kwenye template:
     <div class="sp-chart"><canvas data-sp-chart="bar"
          data-chart-label="Wastani (%)"
          data-chart-series='{"labels":["Biz","His"],"values":[61.2,48.9]}'></canvas></div>
   au kutoka JS:  SPCharts.bar('#el', { labels: [...], values: [...] })
*/
(function () {
  'use strict';

  var PALETTE = [
    '#0B2545', '#D4AF37', '#0F3460', '#146B3A', '#B45309',
    '#DC2626', '#2563EB', '#7C3AED', '#0891B2', '#65A30D', '#DB2777'
  ];

  function css(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name);
    v = (v || '').trim();
    return v || fallback;
  }

  function theme() {
    return {
      brand: css('--brand', '#0B2545'),
      brand2: css('--brand-2', '#0F3460'),
      accent: css('--accent', '#D4AF37'),
      ink: css('--ink', '#111827'),
      ink3: css('--ink-3', '#6B7280'),
      line: css('--line', '#E5E7EB'),
      panel: css('--panel', '#ffffff'),
      dark: document.documentElement.classList.contains('dark')
    };
  }

  function withAlpha(hex, a) {
    var h = (hex || '').replace('#', '');
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    if (h.length !== 6) return 'rgba(11,37,69,' + a + ')';
    var n = parseInt(h, 16);
    return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a + ')';
  }

  function grad(hex) {
    return function (ctx) {
      var a = ctx.chart.ctx;
      var g = a.createLinearGradient(0, 0, 0, Math.max(ctx.chart.height, 1));
      g.addColorStop(0, withAlpha(hex, .85));
      g.addColorStop(1, withAlpha(hex, .45));
      return g;
    };
  }

  function baseOpts(t, extra) {
    var o = {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 700, easing: 'easeOutQuart' },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: false,
          labels: { color: t.ink, usePointStyle: true, boxWidth: 8, font: { size: 12 } }
        },
        tooltip: {
          backgroundColor: t.dark ? '#0B1B2E' : t.brand,
          titleColor: '#fff',
          bodyColor: '#EAF1FA',
          borderColor: withAlpha(t.accent, .7),
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          displayColors: false
        }
      }
    };
    return deepMerge(o, extra || {});
  }

  function axis(t, opts) {
    return deepMerge({
      grid: { color: withAlpha(t.line, .8), drawBorder: false },
      border: { display: false },
      ticks: { color: t.ink3, font: { size: 11 }, maxRotation: 40, autoSkipPadding: 12 }
    }, opts || {});
  }

  function deepMerge(a, b) {
    var out = JSON.parse(JSON.stringify(a));
    Object.keys(b || {}).forEach(function (k) {
      var v = b[k];
      if (v && typeof v === 'object' && !Array.isArray(v) && typeof v !== 'function') {
        out[k] = deepMerge(out[k] || {}, v);
      } else {
        out[k] = v;
      }
    });
    return out;
  }

  var registry = [];

  function make(el, cfg) {
    if (typeof Chart === 'undefined') return null;
    var node = typeof el === 'string' ? document.querySelector(el) : el;
    if (!node) return null;
    var t = theme();
    var built = cfg(t);
    var chart = new Chart(node.getContext('2d'), built);
    registry.push({ node: node, cfg: cfg, chart: chart });
    return chart;
  }

  function rebuildAll() {
    registry.slice().forEach(function (item) {
      try { item.chart.destroy(); } catch (e) { /* already gone */ }
      registry.splice(registry.indexOf(item), 1);
      if (document.body.contains(item.node)) {
        make(item.node, item.cfg);
      }
    });
  }

  var api = {
    palette: PALETTE,
    theme: theme,
    alpha: withAlpha,

    bar: function (el, d) {
      return make(el, function (t) {
        var color = d.color || t.brand;
        return {
          type: 'bar',
          data: {
            labels: d.labels,
            datasets: [{
              label: d.label || '',
              data: d.values,
              backgroundColor: d.colors || grad(color),
              borderRadius: 6,
              borderSkipped: false,
              maxBarThickness: 42
            }]
          },
          options: baseOpts(t, {
            indexAxis: d.horizontal ? 'y' : 'x',
            plugins: { legend: { display: false } },
            scales: {
              x: axis(t, d.horizontal ? { beginAtZero: true } : {}),
              y: axis(t, d.horizontal ? {} : { beginAtZero: true, max: d.max || undefined })
            }
          })
        };
      });
    },

    line: function (el, d) {
      return make(el, function (t) {
        var color = d.color || t.brand2;
        return {
          type: 'line',
          data: {
            labels: d.labels,
            datasets: [{
              label: d.label || '',
              data: d.values,
              borderColor: color,
              backgroundColor: withAlpha(color, t.dark ? .28 : .16),
              fill: d.fill !== false,
              tension: .35,
              borderWidth: 2.5,
              pointRadius: 3,
              pointHoverRadius: 6,
              pointBackgroundColor: t.panel,
              pointBorderColor: color,
              pointBorderWidth: 2
            }]
          },
          options: baseOpts(t, {
            scales: {
              x: axis(t, { grid: { display: false } }),
              y: axis(t, { beginAtZero: true, max: d.max || undefined })
            }
          })
        };
      });
    },

    doughnut: function (el, d) {
      return make(el, function (t) {
        return {
          type: 'doughnut',
          data: {
            labels: d.labels,
            datasets: [{
              data: d.values,
              backgroundColor: d.colors || PALETTE,
              borderColor: t.panel,
              borderWidth: 2,
              hoverOffset: 8
            }]
          },
          options: baseOpts(t, {
            cutout: d.cutout || '62%',
            plugins: {
              legend: { display: d.legend !== false, position: 'right' },
              tooltip: { displayColors: true }
            }
          })
        };
      });
    },

    radar: function (el, d) {
      return make(el, function (t) {
        return {
          type: 'radar',
          data: {
            labels: d.labels,
            datasets: (d.series || [{ label: d.label || '', values: d.values }]).map(function (s, i) {
              var c = s.color || PALETTE[i % PALETTE.length];
              return {
                label: s.label,
                data: s.values,
                borderColor: c,
                backgroundColor: withAlpha(c, .18),
                pointBackgroundColor: c,
                borderWidth: 2
              };
            })
          },
          options: baseOpts(t, {
            plugins: { legend: { display: true, position: 'bottom' } },
            scales: {
              r: {
                angleLines: { color: withAlpha(t.line, .9) },
                grid: { color: withAlpha(t.line, .9) },
                pointLabels: { color: t.ink3, font: { size: 11 } },
                ticks: { display: false },
                beginAtZero: true,
                max: d.max || undefined
              }
            }
          })
        };
      });
    },

    /* Mixed: bar + line (mfano malipo vs madeni) */
    combo: function (el, d) {
      return make(el, function (t) {
        return {
          data: {
            labels: d.labels,
            datasets: [
              { type: 'bar', label: d.barLabel || '', data: d.barValues, backgroundColor: grad(t.brand), borderRadius: 6, maxBarThickness: 34, order: 2 },
              { type: 'line', label: d.lineLabel || '', data: d.lineValues, borderColor: t.accent, backgroundColor: withAlpha(t.accent, .2), borderWidth: 2.5, tension: .35, pointRadius: 3, order: 1 }
            ]
          },
          options: baseOpts(t, {
            plugins: { legend: { display: true, position: 'bottom' } },
            scales: { x: axis(t, { grid: { display: false } }), y: axis(t, { beginAtZero: true }) }
          })
        };
      });
    },

    /* Hujaza kila <canvas data-sp-chart> kutoka data-chart-series (JSON) */
    autoInit: function (root) {
      (root || document).querySelectorAll('[data-sp-chart]').forEach(function (node) {
        if (node.dataset.spDone === '1') return;
        node.dataset.spDone = '1';
        var d;
        try { d = JSON.parse(node.getAttribute('data-chart-series') || '{}'); } catch (e) { return; }
        d.label = node.getAttribute('data-chart-label') || d.label || '';
        if (node.getAttribute('data-chart-horizontal') === 'true') d.horizontal = true;
        var kind = node.getAttribute('data-sp-chart');
        if (typeof api[kind] === 'function') api[kind](node, d);
      });
    },

    destroy: function (el) {
      var node = typeof el === 'string' ? document.querySelector(el) : el;
      registry.filter(function (r) { return r.node === node; }).forEach(function (r) {
        try { r.chart.destroy(); } catch (e) { /* ignore */ }
        registry.splice(registry.indexOf(r), 1);
      });
    }
  };

  window.SPCharts = api;

  document.addEventListener('sp:theme', rebuildAll);
  if (document.readyState !== 'loading') api.autoInit(document);
  else document.addEventListener('DOMContentLoaded', function () { api.autoInit(document); });
})();
