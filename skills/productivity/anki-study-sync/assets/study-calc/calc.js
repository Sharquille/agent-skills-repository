/* Study Calc: a calculation card with fresh numbers on every review.
 * The front draws n, p, and r from the card's Params, renders the Prompt, and saves the
 * numbers and the typed answer; the back (marked by #calc-back) reads them, solves the
 * problem, names a recognised slip when the typed answer matches one, and shows the
 * worked steps with this review's numbers. Each kind below is one problem type. */
(function () {
  'use strict';

  // ---------- math ----------
  function C(n, r) {
    if (r < 0 || r > n) return 0;
    r = Math.min(r, n - r);
    var c = 1;
    for (var i = 1; i <= r; i++) c = c * (n - r + i) / i;
    return Math.round(c);
  }
  function fact(k) { var f = 1; for (var i = 2; i <= k; i++) f *= i; return f; }
  function P(n, p, r) { return C(n, r) * Math.pow(p, r) * Math.pow(1 - p, n - r); }
  function sum(n, p, lo, hi) { var s = 0; for (var k = lo; k <= hi; k++) s += P(n, p, k); return s; }

  // ---------- formatting ----------
  function places(x) { var s = String(x), i = s.indexOf('.'); return i < 0 ? 0 : s.length - i - 1; }
  function fixed(x, d) { var m = Math.pow(10, d); return (Math.round((x + Number.EPSILON * Math.abs(x)) * m) / m).toFixed(d); }
  function show(x) {  // a working value: enough digits to carry, trailing zeros trimmed
    if (x !== 0 && Math.abs(x) < 0.001) return Number(x.toPrecision(4)).toString();
    var s = fixed(x, 5);
    return s.indexOf('.') < 0 ? s : s.replace(/0+$/, '').replace(/\.$/, '');
  }
  function qOf(p) { return Number(fixed(1 - p, Math.max(places(p), 1))); }
  function pow(b, e) { return b + '<sup>' + e + '</sup>'; }
  var WORDS = { 0: 'Give a whole number.', 1: 'Round to one decimal place.', 2: 'Round to two decimal places.',
                3: 'Round to three decimal places.', 4: 'Round to four decimal places.' };

  function rowLine(v, k) {  // one P(k) worked with the binomial formula
    var c = C(v.n, k), pk = Math.pow(v.p, k), qk = Math.pow(v.q, v.n - k);
    return 'P(' + k + ') = C(' + v.n + ',' + k + ')&middot;' + pow(v.p, k) + '&middot;' + pow(v.q, v.n - k) +
           ' = ' + c + ' &times; ' + show(pk) + ' &times; ' + show(qk) + ' = ' + show(c * pk * qk);
  }
  function rowLines(v, lo, hi) {
    var out = [];
    for (var k = lo; k <= hi; k++) out.push(rowLine(v, k));
    return '<div class="calc-rows">' + out.join('<br>') + '</div>';
  }

  function rangeTable(v, lo, hi, total) {
    var rows = '';
    for (var k = 0; k <= v.n; k++) {
      var keep = k >= lo && k <= hi;
      rows += '<tr class="' + (keep ? 'keep' : 'drop') + '"><td>' + k + '</td><td>' + show(P(v.n, v.p, k)) +
              '</td><td>' + (keep ? '&#10003;' : '') + '</td></tr>';
    }
    return '<table class="calc-table"><tr><th>r</th><th>P(r)</th><th>in range</th></tr>' + rows +
           '<tr class="total"><td colspan="2">sum of &#10003; rows</td><td>' + show(total) + '</td></tr></table>';
  }

  // ---------- how to solve each kind: formula, when to use it, why it works ----------
  var EXACT = 'P(r) = C(n,r) &middot; ' + pow('p', 'r') + ' &middot; ' + pow('q', 'n&minus;r') + ', with C(n,r) = n! / (r!(n &minus; r)!) and q = 1 &minus; p';
  var HOW = {
    'binom-order': ['P(one named order) = ' + pow('p', 'k') + ' &middot; ' + pow('q', 'n&minus;k') + ', k = successes in that order',
                    'the question names one specific order, such as right, right, wrong',
                    'the trials are independent, so one factor per trial multiplies; the order is fixed, so there is no C(n,r)'],
    'binom-count': ['C(n,r) = n! / (r!(n &minus; r)!), the nCr key',
                    'you need how many different orders give exactly r successes in n trials',
                    'n! orders all n trials; dividing by r! and (n &minus; r)! removes reorderings of the alike successes and alike failures'],
    'binom-exact': [EXACT,
                    'the question asks for exactly r successes in n independent trials with the same p',
                    'each order with r successes has probability ' + pow('p', 'r') + pow('q', 'n&minus;r') + ', and C(n,r) counts those orders, which add'],
    'binom-atmost': ['P(r &le; k) = P(0) + P(1) + &hellip; + P(k), each P(r) by ' + EXACT,
                     'the question says "at most k" or "k or fewer"',
                     'different r values can\'t happen together, so their probabilities add; when the list is long, 1 minus the other side is shorter'],
    'binom-atleast': ['P(r &ge; m) = P(m) + &hellip; + P(n) = 1 &minus; [P(0) + &hellip; + P(m &minus; 1)], each P(r) by ' + EXACT,
                      'the question says "at least m," "m or more," or sets a quota',
                      'the binomial formula gives one exact count; "at least" is several counts, which add because they can\'t happen together'],
    'binom-atleast1': ['P(r &ge; 1) = 1 &minus; P(0) = 1 &minus; ' + pow('q', 'n'),
                       'the question says "at least one"',
                       'the only way to miss "at least one" is zero successes, and P(0) = ' + pow('q', 'n') + ' because every trial fails'],
    'binom-mean': ['&mu; = np',
                   'the question asks how many successes to expect, on average',
                   'each trial adds p successes on average, and there are n trials'],
    'binom-sd': ['&sigma; = &radic;(npq)',
                 'the question asks for the spread (standard deviation) of the number of successes',
                 'npq is the variance; the standard deviation is its square root, back in units of successes']
  };

  // ---------- problem kinds ----------
  // d: decimal places asked for. r: default [lo, hi] for r (a negative bound counts back from n).
  // table: extra slack for a sum built from three-place table values, which can drift a little.
  var KINDS = {
    'binom-order': {
      d: 4,
      solve: function (v) {
        var k = v.k, f = v.n - k, a = Math.pow(v.p, k) * Math.pow(v.q, f);
        return {
          answer: a,
          steps: [
            'Success (' + v.labels[0] + '): p = ' + v.p + '. Failure (' + v.labels[1] + '): q = 1 &minus; ' + v.p + ' = ' + v.q + '.',
            'The order ' + v.seq + ' has ' + k + ' success' + (k === 1 ? '' : 'es') + ' and ' + f + ' failure' + (f === 1 ? '' : 's') + '.',
            'One named order: multiply one factor per trial. ' + pow('p', k) + pow('q', f) + ' = ' + pow(v.p, k) + ' &times; ' + pow(v.q, f) +
              ' = ' + show(Math.pow(v.p, k)) + ' &times; ' + show(Math.pow(v.q, f)) + ' = ' + show(a) + '.'
          ],
          traps: [
            { value: C(v.n, k) * a, msg: 'You multiplied by C(' + v.n + ',' + k + '), the number of orders. The question names one order, so it counts once.' },
            { value: Math.pow(v.p, k), msg: 'You left out the failures: multiply by ' + pow('q', f) + ' too.' }
          ]
        };
      }
    },
    'binom-count': {
      d: 0, r: [1, -1],
      solve: function (v) {
        var a = C(v.n, v.r), nr = v.n - v.r;
        return {
          answer: a,
          steps: [
            'Orders with exactly r successes: C(n,r) = n! / (r!(n &minus; r)!).',
            'C(' + v.n + ',' + v.r + ') = ' + v.n + '! / (' + v.r + '! &middot; ' + nr + '!) = ' + fact(v.n) + ' / (' + fact(v.r) + ' &middot; ' + fact(nr) + ') = ' + a + '.',
            'Calculator: <code>' + v.n + ' nCr ' + v.r + '</code>.'
          ],
          traps: [
            { value: fact(v.n) / fact(nr), msg: 'You forgot to divide by ' + v.r + '!: the successes are alike, so their own orderings count once.' },
            { value: fact(v.n), msg: 'That is ' + v.n + '!, every ordering of all the trials; divide by r!(n &minus; r)!.' }
          ]
        };
      }
    },
    'binom-exact': {
      d: 3, r: [1, -1],
      solve: function (v) {
        var f = v.n - v.r, c = C(v.n, v.r), pr = Math.pow(v.p, v.r), qf = Math.pow(v.q, f), a = c * pr * qf;
        return {
          answer: a,
          steps: [
            'q = 1 &minus; p = 1 &minus; ' + v.p + ' = ' + v.q + '.',
            'Failures: n &minus; r = ' + v.n + ' &minus; ' + v.r + ' = ' + f + '.',
            'Orders: C(' + v.n + ',' + v.r + ') = ' + c + '.',
            'Powers: ' + pow(v.p, v.r) + ' &asymp; ' + show(pr) + ' and ' + pow(v.q, f) + ' &asymp; ' + show(qf) + '.',
            'Multiply: P(' + v.r + ') = ' + c + ' &times; ' + show(pr) + ' &times; ' + show(qf) + ' &asymp; ' + show(a) + '.',
            'Calculator: <code>' + v.n + ' nCr ' + v.r + ' * ' + v.p + '^' + v.r + ' * ' + v.q + '^' + f + '</code>.'
          ],
          traps: [
            { value: pr * qf, msg: 'That is one order only. Multiply by C(' + v.n + ',' + v.r + ') = ' + c + ', the number of orders.' },
            { value: c * Math.pow(v.p, f) * Math.pow(v.q, v.r), msg: 'Exponents swapped: r = ' + v.r + ' goes on p (successes) and n &minus; r = ' + f + ' on q.' }
          ]
        };
      }
    },
    'binom-atmost': {
      d: 3, r: [1, -2], table: 0.003,
      solve: function (v) {
        var a = sum(v.n, v.p, 0, v.r), steps = [
          '"At most ' + v.r + '" means r = 0, 1, &hellip;, ' + v.r + ' (' + v.r + ' included).',
          'Work each kept P(r) with the binomial formula, n = ' + v.n + ', p = ' + v.p + ', q = 1 &minus; ' + v.p + ' = ' + v.q + ':' + rowLines(v, 0, v.r),
          'All the rows, kept ones marked:' + rangeTable(v, 0, v.r, a),
          'Add the kept rows: P(r &le; ' + v.r + ') &asymp; ' + show(a) + '.'
        ];
        if (v.n - v.r < v.r + 1) steps.push('Shorter: 1 &minus; [P(' + (v.r + 1) + ') + &hellip; + P(' + v.n + ')] gives the same total.');
        return {
          answer: a, steps: steps,
          traps: [
            { value: sum(v.n, v.p, 0, v.r - 1), msg: 'You left out r = ' + v.r + '. "At most ' + v.r + '" includes ' + v.r + '.' },
            { value: sum(v.n, v.p, v.r, v.n), msg: 'That is "at least ' + v.r + '." "At most" adds from 0 up to ' + v.r + '.' },
            { value: 1 - a, msg: 'That is the complement, "more than ' + v.r + '." You subtracted when you only needed to add.' }
          ]
        };
      }
    },
    'binom-atleast': {
      d: 3, r: [2, -1], table: 0.003,
      solve: function (v) {
        var m = v.r, a = sum(v.n, v.p, m, v.n), below = sum(v.n, v.p, 0, m - 1);
        return {
          answer: a,
          steps: [
            '"At least ' + m + '" means r = ' + m + ', &hellip;, ' + v.n + ' (' + m + ' included).',
            'Work each kept P(r) with the binomial formula, n = ' + v.n + ', p = ' + v.p + ', q = 1 &minus; ' + v.p + ' = ' + v.q + ':' + rowLines(v, m, v.n),
            'All the rows, kept ones marked:' + rangeTable(v, m, v.n, a),
            'Add the kept rows, or subtract the rest from 1: 1 &minus; [P(0) + &hellip; + P(' + (m - 1) + ')] = 1 &minus; ' + show(below) + ' = ' + show(a) + '.'
          ],
          traps: [
            { value: sum(v.n, v.p, m + 1, v.n), msg: 'You left out r = ' + m + '. "At least ' + m + '" includes ' + m + '; "more than ' + m + '" starts at ' + (m + 1) + '.' },
            { value: P(v.n, v.p, m), msg: 'That is exactly ' + m + '. "At least" adds every r from ' + m + ' up to ' + v.n + '.' },
            { value: sum(v.n, v.p, 0, m), msg: 'That is "at most ' + m + '." "At least" counts up from ' + m + '.' }
          ]
        };
      }
    },
    'binom-atleast1': {
      d: 3,
      solve: function (v) {
        var p0 = Math.pow(v.q, v.n), a = 1 - p0;
        return {
          answer: a,
          steps: [
            'q = 1 &minus; ' + v.p + ' = ' + v.q + '.',
            'No successes: P(0) = ' + pow('q', 'n') + ' = ' + pow(v.q, v.n) + ' &asymp; ' + show(p0) + '.',
            'At least one is everything except none: 1 &minus; P(0) = 1 &minus; ' + show(p0) + ' = ' + show(a) + '.'
          ],
          traps: [
            { value: 1 - Math.pow(v.p, v.n), msg: 'You subtracted "all ' + v.n + ' succeed." The complement of "at least one" is "none," P(0) = ' + pow('q', 'n') + '.' },
            { value: P(v.n, v.p, 1), msg: 'That is exactly one. "At least one" also counts 2, 3, &hellip;, ' + v.n + '.' },
            { value: p0, msg: 'That is P(0), the chance of none. Subtract it from 1.' }
          ]
        };
      }
    },
    'binom-mean': {
      d: 2,
      solve: function (v) {
        var a = v.n * v.p;
        return {
          answer: a,
          steps: ['Mean (expected number of successes): &mu; = np = ' + v.n + ' &times; ' + v.p + ' = ' + show(a) + '.',
                  'It need not be a whole number: it is the long-run average.'],
          traps: [
            { value: v.n * v.q, msg: 'You used q. The mean counts successes: &mu; = np.' },
            { value: v.n * v.p * v.q, msg: 'That is npq, the variance. The mean is np.' }
          ]
        };
      }
    },
    'binom-sd': {
      d: 2,
      solve: function (v) {
        var npq = v.n * v.p * v.q, a = Math.sqrt(npq);
        return {
          answer: a,
          steps: ['q = 1 &minus; ' + v.p + ' = ' + v.q + '.',
                  'Inside the root: npq = ' + v.n + ' &times; ' + v.p + ' &times; ' + v.q + ' = ' + show(npq) + '.',
                  '&sigma; = &radic;(npq) = &radic;' + show(npq) + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: npq, msg: 'You left off the square root. npq is the variance; &sigma; = &radic;(npq).' },
            { value: Math.sqrt(v.n * v.p), msg: 'Include q under the root: &sigma; = &radic;(npq), not &radic;(np).' },
            { value: v.n * v.p, msg: 'That is the mean, &mu; = np. The standard deviation is &radic;(npq).' }
          ]
        };
      }
    }
  };

  // Exposed for the builder's tests (node); the card itself never reads it.
  if (typeof module !== 'undefined') { module.exports = { HOW: HOW, KINDS: KINDS, C: C, P: P, sum: sum, show: show, fixed: fixed, qOf: qOf }; }
  if (typeof document === 'undefined') return;

  // ---------- card ----------
  var root = document.getElementById('calc');
  if (!root) return;
  var back = !!document.getElementById('calc-back');
  function text(id) { var e = document.getElementById(id); return e ? e.textContent.trim() : ''; }
  var kindName = text('calc-kind'), kind = KINDS[kindName];
  var promptEl = document.getElementById('calc-prompt');
  var q = document.getElementById('calc-q');
  if (!kind) { q.textContent = 'Unknown calculation kind: ' + kindName; return; }
  var params = {};
  try { params = JSON.parse(text('calc-params')); } catch (e) { q.textContent = 'This card\'s Params are not valid JSON.'; return; }

  var key = 'calc:' + kindName + '|' + promptEl.textContent.trim().slice(0, 160);
  var store = null;
  try { store = window.sessionStorage; } catch (e) {}

  function bound(b, n) { return b < 0 ? n + b : b; }
  function randint(lo, hi) { return lo + Math.floor(Math.random() * (hi - lo + 1)); }
  function draw() {
    var nr = params.n || [5, 10], n = randint(nr[0], nr[1]);
    var plist = params.p || [0.5], p = plist[Math.floor(Math.random() * plist.length)];
    var v = { n: n, p: p, q: qOf(p), labels: params.labels || ['success', 'failure'] };
    var spec = params.r || kind.r;
    if (spec) {
      var lo = Math.max(0, bound(spec[0], n)), hi = Math.min(n, bound(spec[1], n));
      v.r = randint(Math.min(lo, hi), Math.max(lo, hi));
    }
    if (kindName === 'binom-order') {
      var k = randint(1, n - 1), seq = [];
      for (var i = 0; i < n; i++) seq.push(i < k);
      for (var j = n - 1; j > 0; j--) { var t = Math.floor(Math.random() * (j + 1)), s = seq[j]; seq[j] = seq[t]; seq[t] = s; }
      v.k = k;
      v.seq = seq.map(function (b) { return b ? v.labels[0] : v.labels[1]; }).join(', ');
    }
    return v;
  }
  function render(v) {
    var html = promptEl.innerHTML.replace(/\{(n|p|q|r|pct|inv|seq)\}/g, function (_, name) {
      if (name === 'pct') return Math.round(v.p * 100) + '%';
      if (name === 'inv') return String(Math.round(1 / v.p));
      return String(v[name]);
    });
    q.innerHTML = html;
    var roundEl = document.getElementById('calc-round');
    if (roundEl) roundEl.textContent = WORDS[kind.d];
  }
  function parse(s) {
    s = (s || '').replace(/\s+/g, '').replace(/,/g, '');
    if (!s) return null;
    var pct = /%$/.test(s);
    if (pct) s = s.slice(0, -1);
    var num = '(?:\\d+\\.?\\d*|\\.\\d+)';  // 12, 12., 12.5, .5
    var v, m = s.match(new RegExp('^(-?' + num + ')/(' + num + ')$'));
    if (m) v = parseFloat(m[1]) / parseFloat(m[2]);
    else if (new RegExp('^-?' + num + '(?:e-?\\d+)?$', 'i').test(s)) v = parseFloat(s);
    else return NaN;
    return pct ? v / 100 : v;
  }

  var state = null;
  if (back) {
    try { state = JSON.parse(store.getItem(key)); } catch (e) {}
    if (!state && window.__calc && window.__calc.key === key) state = window.__calc;
  }
  if (!state) state = { key: key, v: draw(), typed: '' };
  function save() { window.__calc = state; try { store.setItem(key, JSON.stringify(state)); } catch (e) {} }
  render(state.v);

  if (!back) {
    save();
    var input = document.getElementById('calc-in');
    if (input) {
      input.addEventListener('input', function () { state.typed = input.value; save(); });
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          state.typed = input.value; save();
          if (typeof pycmd === 'function') pycmd('ans');
          else input.blur();
        }
      });
      setTimeout(function () { try { input.focus(); } catch (e) {} }, 0);
    }
    return;
  }

  var out = kind.solve(state.v), d = kind.d, tol = 0.5 * Math.pow(10, -d) + 1e-9;
  var u = parse(state.typed);
  var verdict = document.getElementById('calc-verdict'), yours = document.getElementById('calc-yours');
  var answerText = fixed(out.answer, d);
  var cls = 'none', msg;
  if (u === null) msg = 'No answer typed. The answer is ' + answerText + '.';
  else if (isNaN(u)) msg = 'Couldn\'t read "' + state.typed + '" as a number. The answer is ' + answerText + '.';
  else if (Math.abs(u - out.answer) <= tol) { cls = 'ok'; msg = 'Correct: ' + answerText; }
  else if (kind.table && Math.abs(u - out.answer) <= kind.table) {
    cls = 'ok'; msg = 'Correct within table rounding. The formula gives ' + answerText + '; rounded table values can add to a slightly different total.';
  }
  else {
    cls = 'no';
    var hit = null;
    for (var i = 0; i < out.traps.length; i++) {
      var t = out.traps[i];
      if (Math.abs(t.value - out.answer) > tol && Math.abs(u - t.value) <= tol) { hit = t; break; }
    }
    var near = null;
    if (!hit) {
      for (var j = 0; j < out.traps.length; j++) {
        var w = out.traps[j], gap = Math.abs(u - w.value);
        if (Math.abs(w.value - out.answer) > tol && gap <= Math.max(0.02, 0.06 * Math.abs(w.value)) &&
            gap < Math.abs(u - out.answer)) { near = w; break; }
      }
    }
    if (hit) msg = 'Not quite. The answer is ' + answerText + '. ' + hit.msg;
    else if (near) msg = 'Not quite. The answer is ' + answerText + '. Your number is near ' + fixed(near.value, d) + '. ' +
                         near.msg + ' It is also a little off from that, so check for a power rounded too early.';
    else if (Math.abs(u - out.answer) <= 3 * Math.pow(10, -d)) msg = 'Close. The answer is ' + answerText + '. Keep extra digits until the last step, then round.';
    else msg = 'Not quite. The answer is ' + answerText + '. Compare your working with the steps below.';
  }
  verdict.innerHTML = msg;
  verdict.className = 'calc-verdict ' + cls;
  if (yours && u !== null) yours.textContent = 'You typed: ' + state.typed;
  var how = HOW[kindName], howEl = document.getElementById('calc-how');
  if (how && howEl) {
    howEl.innerHTML = '<div class="calc-how-h">How to solve it</div>' +
      '<div><b>Formula:</b> ' + how[0] + '</div><div><b>Use it when:</b> ' + how[1] + '.</div><div><b>Why it works:</b> ' + how[2] + '.</div>';
  }
  var stepsEl = document.getElementById('calc-steps');
  stepsEl.innerHTML = '<div class="calc-steps-h">Worked solution</div><ol>' +
    out.steps.map(function (s) { return '<li>' + s + '</li>'; }).join('') +
    '</ol><div class="calc-final">Answer: ' + answerText + '</div>';
})();
