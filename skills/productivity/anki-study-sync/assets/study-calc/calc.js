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

  // ---------- kinds that build their own data set or table each review ----------
  // gen(params) returns the drawn values; v.ph fills the prompt's placeholders, v.d sets
  // the decimal places when it differs from the kind's default.
  function ri(a) { return a[0] + Math.floor(Math.random() * (a[1] - a[0] + 1)); }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  function total(xs) { var s = 0; for (var i = 0; i < xs.length; i++) s += xs[i]; return s; }
  function ordered(xs) { return xs.slice().sort(function (a, b) { return a - b; }); }
  function med(s) { var n = s.length, m = Math.floor(n / 2); return n % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
  function draws(n, range) { var xs = []; for (var i = 0; i < n; i++) xs.push(ri(range)); return xs; }
  function joinList(xs) { return xs.map(show).join(', '); }
  function sumLine(xs) { return xs.map(show).join(' + ') + ' = ' + show(total(xs)); }
  function grid(head, rows) {
    return '<table class="calc-table"><tr>' + head.map(function (h) { return '<th>' + h + '</th>'; }).join('') + '</tr>' +
      rows.map(function (r) { return '<tr>' + r.map(function (c) { return '<td>' + c + '</td>'; }).join('') + '</tr>'; }).join('') + '</table>';
  }
  function listWords(items) {
    return items.length < 3 ? items.join(' and ') : items.slice(0, -1).join(', ') + ', and ' + items[items.length - 1];
  }
  function parts(sum, k, step, min) {  // k random parts of sum, each a multiple of step and at least min
    var out = [], i;
    for (i = 0; i < k; i++) out.push(min);
    for (var left = Math.round((sum - k * min) / step); left > 0; left--) out[Math.floor(Math.random() * k)] += step;
    return out;
  }
  function dp(P, d) { return P.d != null ? P.d : d; }
  function classTable(P) {
    var k = ri(P.k || [5, 6]), w = ri(P.width || [5, 10]), start = ri(P.start || [1, 20]), rows = [];
    for (var i = 0; i < k; i++) { var lo = start + i * w; rows.push({ lo: lo, hi: lo + w - 1, f: ri(P.f || [2, 20]) }); }
    return { k: k, w: w, rows: rows, n: total(rows.map(function (r) { return r.f; })) };
  }
  function classHtml(t) { return grid(['Class', 'Frequency'], t.rows.map(function (r) { return [r.lo + '&ndash;' + r.hi, r.f]; })); }
  function lin(a, b, x) {  // "a + bx" with signs written out
    var bx = (Math.abs(b) === 1 ? '' : show(Math.abs(b))) + x;
    if (a === 0) return (b < 0 ? '&minus;' : '') + bx;
    return show(a) + (b < 0 ? ' &minus; ' : ' + ') + bx;
  }

  var MORE = {
    // ----- 2.1 frequency tables -----
    'class-width': {
      d: 0,
      how: ['class width = (largest value &minus; smallest value) &divide; number of classes, then increase to the next whole number',
            'you are building a frequency table for whole-number data',
            'the classes must reach the largest value; rounding down or keeping a decimal would leave values without a class'],
      gen: function (P) {
        var k, lo, hi;
        do { k = pick(P.k || [5, 6, 7, 8]); lo = ri(P.min || [1, 20]); hi = lo + ri(P.spread || [30, 90]); } while ((hi - lo) % k === 0);
        return { k: k, lo: lo, hi: hi, ph: { min: lo, max: hi, k: k } };
      },
      solve: function (v) {
        var spread = v.hi - v.lo, q = spread / v.k, a = Math.floor(q) + 1;
        return {
          answer: a,
          steps: ['Spread of the data: ' + v.hi + ' &minus; ' + v.lo + ' = ' + spread + '.',
                  'Divide by the number of classes: ' + spread + ' &divide; ' + v.k + ' &asymp; ' + show(q) + '.',
                  'Increase to the next whole number: the class width is ' + a + '.',
                  'Check: ' + v.k + ' classes &times; ' + a + ' = ' + v.k * a + ' covers the spread of ' + spread + '.'],
          traps: [
            { value: Math.floor(q), msg: 'You rounded down. For whole-number data the width always goes up to the next whole number, or the classes stop short of the largest value.' },
            { value: q, tol: 0.01, msg: 'That is the quotient itself. Integer data need a whole-number width: increase it to the next whole number.' }
          ]
        };
      }
    },
    'class-midpoint': {
      d: 1,
      how: ['midpoint = (lower class limit + upper class limit) &divide; 2',
            'one number must stand for a whole class, as in a histogram or a grouped mean',
            'the midpoint sits halfway between the class\'s two limits'],
      gen: function (P) {
        var lo = ri(P.lower || [1, 40]), w = ri(P.width || [5, 12]);
        return { lo: lo, hi: lo + w - 1, w: w, d: dp(P, 1), ph: { lower: lo, upper: lo + w - 1 } };
      },
      solve: function (v) {
        var a = (v.lo + v.hi) / 2;
        return {
          answer: a,
          steps: ['Add the two limits: ' + v.lo + ' + ' + v.hi + ' = ' + (v.lo + v.hi) + '.',
                  'Divide by 2: ' + (v.lo + v.hi) + ' &divide; 2 = ' + show(a) + '.'],
          traps: [
            { value: (v.lo + v.lo + v.w) / 2, msg: 'You averaged with the next class\'s lower limit (' + (v.lo + v.w) + '). Use this class\'s own two limits.' },
            { value: (v.hi - v.lo) / 2, msg: 'You subtracted. The midpoint adds the two limits, then divides by 2.' },
            { value: v.lo + v.hi, msg: 'You added the limits but didn\'t divide by 2.' }
          ]
        };
      }
    },
    'rel-freq': {
      d: 2,
      how: ['relative frequency = f &divide; n, where n = &Sigma;f',
            'you want a class\'s share of all the data, such as to compare data sets of different sizes',
            'a class\'s count over the total count is its proportion; all the classes\' shares total 1'],
      gen: function (P) {
        var t = classTable(P), j = ri([0, t.k - 1]), r = t.rows[j];
        return { t: t, j: j, d: dp(P, 2), ph: { table: classHtml(t), cls: r.lo + '&ndash;' + r.hi } };
      },
      solve: function (v) {
        var fs = v.t.rows.map(function (r) { return r.f; }), f = fs[v.j], n = v.t.n, a = f / n;
        var cum = total(fs.slice(0, v.j + 1));
        var traps = [{ value: f / v.t.k, msg: 'You divided by the number of classes (' + v.t.k + '). Divide by n, the total count.' }];
        if (v.j > 0) traps.push({ value: cum / n, msg: 'That is the cumulative share up to this class. Use this class\'s own count.' });
        return {
          answer: a,
          steps: ['Total count: n = ' + sumLine(fs) + '.',
                  'This class\'s count: f = ' + f + '.',
                  'Relative frequency: f &divide; n = ' + f + ' &divide; ' + n + ' &asymp; ' + show(a) + '.'],
          traps: traps
        };
      }
    },
    'cum-freq': {
      d: 0,
      how: ['cumulative frequency at an upper boundary = the class frequencies added up through that class',
            'the question asks how many values are below a cutoff',
            'a class\'s upper boundary sits above every value in it and in the classes before it'],
      gen: function (P) {
        var t = classTable(P), j = ri([1, t.k - 2]);
        return { t: t, j: j, ph: { table: classHtml(t), cut: show(t.rows[j].hi + 0.5) } };
      },
      solve: function (v) {
        var rows = v.t.rows, fs = rows.map(function (r) { return r.f; }), j = v.j, a = total(fs.slice(0, j + 1));
        var run = [], s = 0;
        for (var i = 0; i <= j; i++) { s += fs[i]; run.push('below ' + show(rows[i].hi + 0.5) + ': ' + s); }
        return {
          answer: a,
          steps: ['Upper boundaries are upper limits + 0.5, so ' + show(rows[j].hi + 0.5) + ' is the upper boundary of the class ' + rows[j].lo + '&ndash;' + rows[j].hi + '.',
                  'Every value in that class and the classes before it is below the cutoff.',
                  'Running totals: ' + run.join('; ') + '.'],
          traps: [
            { value: fs[j], msg: 'That is one class\'s count. "Less than the cutoff" includes every class below it too.' },
            { value: total(fs.slice(0, j)), msg: 'You stopped a class early: the class ' + rows[j].lo + '&ndash;' + rows[j].hi + ' lies below its own upper boundary, so it counts.' },
            { value: total(fs.slice(0, j + 2)), msg: 'You went a class too far: the next class starts above the cutoff.' }
          ]
        };
      }
    },
    'grouped-mean': {
      d: 2,
      how: ['x&#772; &asymp; &Sigma;(x &middot; f) &divide; n, with x = class midpoint and n = &Sigma;f',
            'you only have a frequency table, not the raw values',
            'each midpoint stands in for every value in its class, weighted by its frequency; it is an estimate'],
      gen: function (P) { var t = classTable(P); return { t: t, d: dp(P, 2), ph: { table: classHtml(t) } }; },
      solve: function (v) {
        var rows = v.t.rows, mids = rows.map(function (r) { return (r.lo + r.hi) / 2; });
        var prods = rows.map(function (r, i) { return mids[i] * r.f; }), n = v.t.n, a = total(prods) / n;
        return {
          answer: a,
          steps: ['Midpoints, (lower + upper) &divide; 2: ' + joinList(mids) + '.',
                  'Midpoint &times; frequency: ' + rows.map(function (r, i) { return show(mids[i]) + ' &times; ' + r.f + ' = ' + show(prods[i]); }).join('; ') + '.',
                  'Add the products: &Sigma;(x &middot; f) = ' + show(total(prods)) + '; total frequency n = ' + n + '.',
                  'Divide: ' + show(total(prods)) + ' &divide; ' + n + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: total(mids) / mids.length, msg: 'You averaged the midpoints and ignored the frequencies. Weight each midpoint by its frequency.' },
            { value: total(prods) / v.t.k, msg: 'You divided by the number of classes. Divide by n = &Sigma;f, the total count.' }
          ]
        };
      }
    },
    // ----- 3.1 center -----
    'mean': {
      d: 1,
      how: ['x&#772; = &Sigma;x &divide; n (a sample); &mu; = &Sigma;x &divide; N (a population)',
            'every value should count, as in a test average',
            'the mean shares the total equally among all the values'],
      gen: function (P) { var xs = draws(ri(P.n || [5, 9]), P.x || [10, 99]); return { xs: xs, d: dp(P, 1), ph: { data: joinList(xs), n: xs.length } }; },
      solve: function (v) {
        var n = v.xs.length, s = total(v.xs), a = s / n;
        return {
          answer: a,
          steps: ['Add the values: &Sigma;x = ' + sumLine(v.xs) + '.', 'Count them: n = ' + n + '.', 'Divide: ' + s + ' &divide; ' + n + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: s / (n - 1), msg: 'You divided by n &minus; 1. The mean divides by n, the number of values.' },
            { value: med(ordered(v.xs)), msg: 'That is the median. The mean adds every value and divides by n.' }
          ]
        };
      }
    },
    'median': {
      d: 1,
      how: ['median = the middle value of the ordered data, at position (n + 1) &divide; 2; for an even n, average the two middle values',
            'you want a center that resists extreme values',
            'half the ordered values sit at or below it and half at or above'],
      gen: function (P) { var xs = draws(ri(P.n || [6, 11]), P.x || [10, 99]); return { xs: xs, d: dp(P, 1), ph: { data: joinList(xs), n: xs.length } }; },
      solve: function (v) {
        var s = ordered(v.xs), n = s.length, pos = (n + 1) / 2, a = med(s);
        return {
          answer: a,
          steps: ['Order the data: ' + joinList(s) + '.',
                  'Middle position: (n + 1) &divide; 2 = (' + n + ' + 1) &divide; 2 = ' + show(pos) + '.',
                  n % 2 ? 'Odd n: the median is value number ' + pos + ', which is ' + show(a) + '.'
                        : 'Even n: average values ' + (n / 2) + ' and ' + (n / 2 + 1) + ': (' + show(s[n / 2 - 1]) + ' + ' + show(s[n / 2]) + ') &divide; 2 = ' + show(a) + '.'],
          traps: [
            { value: med(v.xs), msg: 'You took the middle of the list as given. Order the data first.' },
            { value: pos, msg: 'That is the median\'s position, not its value. Look up that position in the ordered data.' },
            { value: total(v.xs) / n, msg: 'That is the mean. The median is the middle of the ordered values.' }
          ]
        };
      }
    },
    'middle-position': {
      d: 1,
      how: ['middle position = (n + 1) &divide; 2',
            'the data set is too large to find the middle by eye',
            'it counts in from either end to the same spot; a result ending in .5 points between two values'],
      gen: function (P) { var n = ri(P.n || [25, 150]); return { n: n, ph: { n: n } }; },
      solve: function (v) {
        var a = (v.n + 1) / 2;
        return {
          answer: a,
          steps: ['(n + 1) &divide; 2 = (' + v.n + ' + 1) &divide; 2 = ' + show(a) + '.',
                  v.n % 2 ? 'A whole number: the median is value number ' + a + '.' : 'Ends in .5: the median averages values ' + (a - 0.5) + ' and ' + (a + 0.5) + '.'],
          traps: [{ value: v.n / 2, msg: 'You divided n by 2. The middle position is (n + 1) &divide; 2.' }]
        };
      }
    },
    'weighted-avg': {
      d: 1,
      how: ['weighted average = &Sigma;(x &middot; w) &divide; &Sigma;w',
            'some values count more than others, such as a final worth more than a midterm',
            'each value counts in proportion to its weight; a plain mean would count them all equally'],
      gen: function (P) {
        var labels = P.items || ['Homework', 'Midterm', 'Final'], ws = parts(100, labels.length, 5, 15);
        var xs = draws(labels.length, P.x || [60, 100]);
        return { labels: labels, ws: ws, xs: xs, d: dp(P, 1),
                 ph: { table: grid(['Part', 'Score', 'Weight'], labels.map(function (l, i) { return [l, xs[i], ws[i] + '%']; })) } };
      },
      solve: function (v) {
        var prods = v.xs.map(function (x, i) { return x * v.ws[i] / 100; }), a = total(prods);
        return {
          answer: a,
          steps: ['Write each weight as a decimal and multiply: ' + v.xs.map(function (x, i) { return x + ' &times; ' + show(v.ws[i] / 100) + ' = ' + show(prods[i]); }).join('; ') + '.',
                  'Add the products: &Sigma;(x &middot; w) = ' + show(a) + '.',
                  'Add the weights: &Sigma;w = ' + v.ws.map(function (w) { return show(w / 100); }).join(' + ') + ' = 1.',
                  'Divide: ' + show(a) + ' &divide; 1 = ' + show(a) + '.'],
          traps: [
            { value: total(v.xs) / v.xs.length, msg: 'That is a plain mean, which counts every part equally. Weight each score by its percentage.' },
            { value: a * 100, msg: 'You used the weights as whole percents and didn\'t divide by &Sigma;w = 100.' }
          ]
        };
      }
    },
    'trimmed-mean': {
      d: 1,
      how: ['5% trimmed mean: remove 5% of n (rounded to a whole number) from each end of the ordered data, then average the rest',
            'a few extreme values would distort the mean',
            'it resists outliers like the median but still uses most of the actual values'],
      gen: function (P) {
        var xs = ordered(draws(ri(P.n || [20, 20]), P.x || [15, 60]));
        xs[xs.length - 1] += ri(P.outlier || [20, 40]);  // one high value to trim
        return { xs: ordered(xs), d: dp(P, 1), ph: { data: joinList(ordered(xs)), n: xs.length } };
      },
      solve: function (v) {
        var n = v.xs.length, k = Math.round(0.05 * n), kept = v.xs.slice(k, n - k), a = total(kept) / kept.length;
        return {
          answer: a,
          steps: ['How many to remove from each end: 0.05 &times; ' + n + ' = ' + show(0.05 * n) + ', so ' + k + '.',
                  'Remove the lowest ' + k + ' (' + joinList(v.xs.slice(0, k)) + ') and the highest ' + k + ' (' + joinList(v.xs.slice(n - k)) + '), leaving ' + kept.length + ' values.',
                  'Sum of what remains: ' + show(total(kept)) + '.',
                  'Divide: ' + show(total(kept)) + ' &divide; ' + kept.length + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: total(v.xs) / n, msg: 'That is the untrimmed mean. Remove ' + k + ' value(s) from each end first.' },
            { value: total(v.xs.slice(0, n - k)) / (n - k), msg: 'You trimmed only the high end. Trim the same number from both ends.' },
            { value: total(kept) / n, msg: 'You divided by the original n. Divide by the ' + kept.length + ' values left.' }
          ]
        };
      }
    },
    // ----- 3.2 variation -----
    'range': {
      d: 0,
      how: ['range = largest value &minus; smallest value',
            'you need a quick sense of spread in the data\'s own units',
            'it is the distance between the two extremes, so it ignores every value in between'],
      gen: function (P) { var xs = draws(ri(P.n || [7, 12]), P.x || [10, 99]); return { xs: xs, ph: { data: joinList(xs) } }; },
      solve: function (v) {
        var s = ordered(v.xs), a = s[s.length - 1] - s[0];
        return {
          answer: a,
          steps: ['Find the actual largest and smallest values: ' + s[s.length - 1] + ' and ' + s[0] + '.',
                  'Subtract: ' + s[s.length - 1] + ' &minus; ' + s[0] + ' = ' + a + '.'],
          traps: [{ value: v.xs[v.xs.length - 1] - v.xs[0], msg: 'You subtracted the list\'s first value from its last. Use the largest and smallest values.' }]
        };
      }
    },
    'sd': {
      d: 2,
      how: function (v) {
        if (v.ask === 'sigma') return ['&sigma; = &radic;(&Sigma;(x &minus; &mu;)&sup2; &divide; N)', 'the data are a whole population', 'a population divides by N; only a sample needs n &minus; 1'];
        if (v.ask === 's2') return ['s&sup2; = &Sigma;(x &minus; x&#772;)&sup2; &divide; (n &minus; 1)', 'the data are a sample and the question asks for the variance', 'squaring stops deviations from canceling; n &minus; 1 makes it a better estimate of the population\'s spread'];
        return ['s = &radic;(&Sigma;(x &minus; x&#772;)&sup2; &divide; (n &minus; 1))', 'the data are a sample and the question asks for the standard deviation', 'the square root of the variance puts the spread back in the data\'s units'];
      },
      gen: function (P) {
        var xs, n = ri(P.n || [5, 7]);
        do { xs = draws(n, P.x || [1, 15]); } while (total(xs) % n !== 0 || ordered(xs)[0] === ordered(xs)[n - 1]);
        return { xs: xs, ask: P.ask || 's', d: dp(P, 2), ph: { data: joinList(xs), n: n } };
      },
      solve: function (v) {
        var n = v.xs.length, m = total(v.xs) / n, devs = v.xs.map(function (x) { return x - m; });
        var sq = devs.map(function (d) { return d * d; }), ss = total(sq);
        var s2 = ss / (n - 1), s = Math.sqrt(s2), g2 = ss / n, g = Math.sqrt(g2);
        var pop = v.ask === 'sigma', a = v.ask === 's2' ? s2 : pop ? g : s;
        var steps = ['Mean: ' + total(v.xs) + ' &divide; ' + n + ' = ' + show(m) + '.',
                     'Deviations x &minus; ' + show(m) + ': ' + joinList(devs) + ' (they add to 0).',
                     'Square them: ' + joinList(sq) + '; add: ' + show(ss) + '.',
                     pop ? 'Divide by N = ' + n + ': &sigma;&sup2; = ' + show(ss) + ' &divide; ' + n + ' = ' + show(g2) + '.'
                         : 'Divide by n &minus; 1 = ' + (n - 1) + ': s&sup2; = ' + show(ss) + ' &divide; ' + (n - 1) + ' = ' + show(s2) + '.'];
        if (v.ask !== 's2') steps.push('Square root: ' + (pop ? '&sigma; = &radic;' + show(g2) + ' &asymp; ' + show(g) : 's = &radic;' + show(s2) + ' &asymp; ' + show(s)) + '.');
        var traps = v.ask === 's2'
          ? [{ value: s, msg: 'You took the square root. The variance stops before the root.' },
             { value: g2, msg: 'You divided by n. A sample divides by n &minus; 1.' }]
          : pop
          ? [{ value: s, msg: 'You divided by N &minus; 1, the sample formula. A whole population divides by N.' },
             { value: g2, msg: 'You left off the square root; that is the variance.' }]
          : [{ value: g, msg: 'You divided by n. A sample divides by n &minus; 1.' },
             { value: s2, msg: 'You left off the square root; that is the variance s&sup2;.' },
             { value: Math.sqrt(ss), msg: 'You took the root of the sum of squares without dividing by n &minus; 1 first.' }];
        return { answer: a, steps: steps, traps: traps };
      }
    },
    // ----- 3.3 position -----
    'quartiles': {
      d: 1,
      how: function (v) {
        return [v.ask === 'iqr' ? 'IQR = Q<sub>3</sub> &minus; Q<sub>1</sub>' : 'Q<sub>1</sub> = median of the lower half; Q<sub>3</sub> = median of the upper half',
                v.ask === 'iqr' ? 'you want the spread of the middle half, resisting extreme values' : 'you need the cut points that split ordered data into quarters',
                'finding quartiles is finding three medians; with an odd n, the middle value goes in neither half'];
      },
      gen: function (P) {
        var n = ri(P.n || [8, 13]);
        if (P.parity === 'odd' && n % 2 === 0) n += 1;
        if (P.parity === 'even' && n % 2 === 1) n += 1;
        var xs = ordered(draws(n, P.x || [10, 99]));
        return { xs: xs, ask: P.ask || 'iqr', d: dp(P, 1), ph: { data: joinList(xs), n: n } };
      },
      solve: function (v) {
        var s = v.xs, n = s.length, h = Math.floor(n / 2), low = s.slice(0, h), up = s.slice(n - h);
        var q1 = med(low), q2 = med(s), q3 = med(up);
        var lowIn = s.slice(0, Math.ceil(n / 2)), upIn = s.slice(Math.floor(n / 2));
        var q1in = med(lowIn), q3in = med(upIn);
        var a = v.ask === 'q1' ? q1 : v.ask === 'q3' ? q3 : q3 - q1;
        var steps = ['Q<sub>2</sub> position: (' + n + ' + 1) &divide; 2 = ' + show((n + 1) / 2) + ', so Q<sub>2</sub> = ' + show(q2) + '.',
                     (n % 2 ? 'Odd n: leave out the median value itself. ' : 'Even n: split between the two middle values. ') +
                       'Lower half: ' + joinList(low) + '. Upper half: ' + joinList(up) + '.',
                     'Q<sub>1</sub> = median of the lower half = ' + show(q1) + '; Q<sub>3</sub> = median of the upper half = ' + show(q3) + '.'];
        if (v.ask === 'iqr') steps.push('IQR = Q<sub>3</sub> &minus; Q<sub>1</sub> = ' + show(q3) + ' &minus; ' + show(q1) + ' = ' + show(q3 - q1) + '.');
        var leftIn = 'You included the median\'s value in the halves. This course leaves it out when n is odd.';
        var traps = v.ask === 'q1'
          ? [{ value: q1in, msg: leftIn }, { value: q2, msg: 'That is Q<sub>2</sub>, the median. Q<sub>1</sub> is the median of the lower half.' }]
          : v.ask === 'q3'
          ? [{ value: q3in, msg: leftIn }, { value: q2, msg: 'That is Q<sub>2</sub>, the median. Q<sub>3</sub> is the median of the upper half.' }]
          : [{ value: q3in - q1in, msg: leftIn },
             { value: s[n - 1] - s[0], msg: 'That is the range. The IQR is Q<sub>3</sub> &minus; Q<sub>1</sub>.' },
             { value: q3 - q2, msg: 'You subtracted the median. The IQR is Q<sub>3</sub> &minus; Q<sub>1</sub>.' }];
        return { answer: a, steps: steps, traps: traps };
      }
    },
    // ----- 5.1 probability basics -----
    'prob-relfreq': {
      d: 3,
      how: ['P(event) = f &divide; n', 'you counted how often the event happened in a sample',
            'the event\'s share of the observations estimates its probability, better as n grows'],
      gen: function (P) {
        var n = ri(P.n || [50, 500]), f = Math.max(1, Math.min(n - 1, Math.round(n * ri(P.share || [5, 60]) / 100)));
        return { n: n, f: f, d: dp(P, 3), ph: { n: n, f: f } };
      },
      solve: function (v) {
        var a = v.f / v.n;
        return {
          answer: a,
          steps: ['f = ' + v.f + ' times the event happened; n = ' + v.n + ' observations.', 'Divide: ' + v.f + ' &divide; ' + v.n + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: (v.n - v.f) / v.n, msg: 'That is the share where it did not happen. The event\'s count is f = ' + v.f + '.' },
            { value: v.f / (v.n - v.f), msg: 'You divided by the other outcomes. Divide by the whole sample, n = ' + v.n + '.' }
          ]
        };
      }
    },
    'prob-equal': {
      d: 3,
      how: function (v) {
        return v.ask === 'not'
          ? ['P(not A) = 1 &minus; P(A), with P(A) = favorable &divide; total', 'the question asks for the chance something does not happen', 'A and not-A cover every outcome once, so their probabilities add to 1']
          : ['P(A) = favorable outcomes &divide; total outcomes', 'every outcome is equally likely, as with a random draw', 'with equally likely outcomes, each one carries the same share of the probability'];
      },
      gen: function (P) {
        var labels = P.labels || ['red', 'blue', 'green'], cs = draws(labels.length, P.c || [2, 9]);
        return { labels: labels, cs: cs, ask: P.ask || 'p',
                 ph: { counts: listWords(labels.map(function (l, i) { return cs[i] + ' ' + l; })), target: labels[0], total: total(cs) } };
      },
      solve: function (v) {
        var N = total(v.cs), c = v.cs[0], p = c / N, not = v.ask === 'not', a = not ? 1 - p : p;
        var steps = ['Total outcomes: ' + sumLine(v.cs) + '.', 'Favorable (' + v.labels[0] + '): ' + c + ', so P(' + v.labels[0] + ') = ' + c + ' &divide; ' + N + ' &asymp; ' + show(p) + '.'];
        if (not) steps.push('Complement: 1 &minus; ' + show(p) + ' = ' + show(a) + ' (or ' + (N - c) + ' &divide; ' + N + ').');
        var traps = [{ value: c / (N - c), msg: 'You divided by the other outcomes. Divide by the total, ' + N + '.' }];
        traps.push(not ? { value: p, msg: 'That is P(' + v.labels[0] + ') itself. Subtract it from 1.' }
                       : { value: (N - c) / N, msg: 'That is the chance of not ' + v.labels[0] + '.' });
        return { answer: a, steps: steps, traps: traps };
      }
    },
    // ----- 5.2 rules -----
    'mult-indep': {
      d: 3,
      how: ['P(A and B) = P(A) &middot; P(B) for independent events', 'the question asks for both events and one can\'t change the other\'s chance',
            'B keeps its plain probability whether or not A happened, so the chances multiply'],
      gen: function (P) { var pa = pick(P.pa || [0.9, 0.8]), pb = pick(P.pb || [0.7, 0.6]); return { pa: pa, pb: pb, d: dp(P, 3), ph: { pa: pa, pb: pb } }; },
      solve: function (v) {
        var a = v.pa * v.pb;
        return {
          answer: a,
          steps: ['Independent, so multiply: ' + v.pa + ' &times; ' + v.pb + ' = ' + show(a) + '.'],
          traps: [
            { value: v.pa + v.pb, msg: 'You added. "And" with independent events multiplies.' },
            { value: v.pa + v.pb - v.pa * v.pb, msg: 'That is P(A or B). "And" is just the product.' },
            { value: (1 - v.pa) * (1 - v.pb), msg: 'That is the chance neither happens.' }
          ]
        };
      }
    },
    'mult-dep': {
      d: 3,
      how: ['P(A and B) = P(A) &middot; P(B | A)', 'the first event changes the second\'s chance, as when drawing without replacement',
            'after the first draw, one fewer item of that kind and one fewer item in total remain'],
      gen: function (P) { var A = ri(P.a || [3, 8]), B = ri(P.b || [4, 12]); return { A: A, B: B, d: dp(P, 3), ph: { a: A, b: B, total: A + B } }; },
      solve: function (v) {
        var N = v.A + v.B, a = (v.A / N) * ((v.A - 1) / (N - 1));
        return {
          answer: a,
          steps: ['First draw: P(A) = ' + v.A + ' &divide; ' + N + '.',
                  'Second draw, given the first matched: ' + (v.A - 1) + ' of the ' + (N - 1) + ' left, so P(B | A) = ' + (v.A - 1) + ' &divide; ' + (N - 1) + '.',
                  'Multiply: (' + v.A + '/' + N + ') &times; (' + (v.A - 1) + '/' + (N - 1) + ') = ' + v.A * (v.A - 1) + '/' + N * (N - 1) + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: (v.A / N) * (v.A / N), msg: 'You treated the draws as independent. Without replacement, ' + (v.A - 1) + ' of ' + (N - 1) + ' remain for the second draw.' },
            { value: (v.A / N) * ((v.A - 1) / N), msg: 'You kept the old total, ' + N + ', for the second draw. One item is gone: use ' + (N - 1) + '.' }
          ]
        };
      }
    },
    'conditional-table': {
      d: 3,
      how: ['P(A | B) = P(A and B) &divide; P(B) = count in both &divide; count in B', 'the question says "given," "if," or "among those who"',
            'knowing B happened shrinks the table to B\'s row; A\'s chance is judged only there'],
      gen: function (P) {
        var rows = P.rows || ['Freshman', 'Sophomore'], cols = P.cols || ['Female', 'Male'];
        var cells = rows.map(function () { return draws(cols.length, P.c || [3, 25]); });
        var i = ri([0, rows.length - 1]), j = ri([0, cols.length - 1]);
        var body = rows.map(function (r, k) { return [r].concat(cells[k]).concat([total(cells[k])]); });
        body.push(['Total'].concat(cols.map(function (c, k) { return total(cells.map(function (row) { return row[k]; })); })).concat([total(cells.map(total))]));
        return { rows: rows, cols: cols, cells: cells, i: i, j: j, d: dp(P, 3),
                 ph: { table: grid([''].concat(cols).concat(['Total']), body), given: rows[i], event: cols[j] } };
      },
      solve: function (v) {
        var row = v.cells[v.i], cell = row[v.j], rowT = total(row);
        var colT = total(v.cells.map(function (r) { return r[v.j]; })), grand = total(v.cells.map(total)), a = cell / rowT;
        return {
          answer: a,
          steps: ['Given ' + v.rows[v.i] + ': use only that row. Its total is ' + sumLine(row) + '.',
                  'Inside that row, ' + v.cols[v.j] + ': ' + cell + '.',
                  'Divide by the given row\'s total: ' + cell + ' &divide; ' + rowT + ' &asymp; ' + show(a) + '.'],
          traps: [
            { value: cell / grand, msg: 'You divided by the grand total, ' + grand + '. That is P(' + v.rows[v.i] + ' and ' + v.cols[v.j] + '). "Given" divides by the given row\'s total.' },
            { value: cell / colT, msg: 'You divided by the ' + v.cols[v.j] + ' column total. The given event\'s total goes in the denominator.' },
            { value: rowT / grand, msg: 'That is P(' + v.rows[v.i] + ') itself.' }
          ]
        };
      }
    },
    'add-general': {
      d: 2,
      how: ['P(A or B) = P(A) + P(B) &minus; P(A and B)', 'the question asks for either event, and they can happen together',
            'adding P(A) and P(B) counts the overlap twice; subtracting it once fixes that'],
      gen: function (P) {
        var pa = pick(P.pa || [0.4, 0.5]), pb = pick(P.pb || [0.3, 0.35]);
        var ok = (P.pab || [0.1, 0.15, 0.2]).filter(function (x) { return x < Math.min(pa, pb) && x >= pa + pb - 1; });
        var pab = ok.length ? pick(ok) : Math.round(pa * pb * 100) / 100;
        return { pa: pa, pb: pb, pab: pab, d: dp(P, 2), ph: { pa: pa, pb: pb, pab: pab } };
      },
      solve: function (v) {
        var a = v.pa + v.pb - v.pab;
        return {
          answer: a,
          steps: ['Add: ' + v.pa + ' + ' + v.pb + ' = ' + show(v.pa + v.pb) + '.', 'Subtract the overlap once: ' + show(v.pa + v.pb) + ' &minus; ' + v.pab + ' = ' + show(a) + '.'],
          traps: [
            { value: v.pa + v.pb, msg: 'You counted the overlap twice. Subtract P(A and B) = ' + v.pab + '.' },
            { value: v.pab, msg: 'That is P(A and B). "Or" includes either one.' },
            { value: v.pa * v.pb, msg: 'You multiplied. "Or" uses the addition rule.' }
          ]
        };
      }
    },
    'add-exclusive': {
      d: 2,
      how: ['P(A or B) = P(A) + P(B) for mutually exclusive events', 'the question asks for either of two outcomes that can\'t happen together',
            'they share no outcomes, so their overlap is 0 and nothing needs subtracting'],
      gen: function (P) {
        var labels = P.labels || ['A', 'B', 'AB', 'O'], pc = parts(100, labels.length, 1, P.min || 5), i = ri([0, labels.length - 1]), j;
        do { j = ri([0, labels.length - 1]); } while (j === i);
        return { labels: labels, pc: pc, i: i, j: j, d: dp(P, 2),
                 ph: { table: grid([P.head || 'Category', 'Percent'], labels.map(function (l, k) { return [l, pc[k] + '%']; })), a: labels[i], b: labels[j] } };
      },
      solve: function (v) {
        var pa = v.pc[v.i] / 100, pb = v.pc[v.j] / 100, a = pa + pb;
        return {
          answer: a,
          steps: ['As probabilities: P(' + v.labels[v.i] + ') = ' + show(pa) + ' and P(' + v.labels[v.j] + ') = ' + show(pb) + '.',
                  'Mutually exclusive (they can\'t happen together), so add: ' + show(pa) + ' + ' + show(pb) + ' = ' + show(a) + '.'],
          traps: [
            { value: pa * pb, msg: 'You multiplied. "Or" adds.' },
            { value: pa + pb - pa * pb, msg: 'You subtracted an overlap. These outcomes can\'t happen together, so the overlap is 0.' }
          ]
        };
      }
    },
    // ----- 6.1 discrete distributions -----
    'share-table': {
      d: 2,
      how: ['P(x) = count for x &divide; total count', 'you have counts and need a probability distribution',
            'each value\'s relative frequency is its probability; the column should sum to 1'],
      gen: function (P) {
        var labels = P.labels || ['0', '1', '2', '3'], cs = draws(labels.length, P.c || [5, 60]), i = ri([0, labels.length - 1]);
        return { labels: labels, cs: cs, i: i, d: dp(P, 2),
                 ph: { table: grid([P.head || 'Value', 'Count'], labels.map(function (l, k) { return [l, cs[k]]; })), target: labels[i] } };
      },
      solve: function (v) {
        var n = total(v.cs), a = v.cs[v.i] / n;
        return {
          answer: a,
          steps: ['Total count: ' + sumLine(v.cs) + '.', 'Divide the count for ' + v.labels[v.i] + ' by the total: ' + v.cs[v.i] + ' &divide; ' + n + ' &asymp; ' + show(a) + '.'],
          traps: [{ value: v.cs[v.i] / v.cs.length, msg: 'You divided by the number of rows. Divide by the total count, ' + n + '.' }]
        };
      }
    },
    'dist': {
      d: 2,
      how: function (v) {
        return v.ask === 'sd'
          ? ['&sigma; = &radic;(&Sigma;(x &minus; &mu;)&sup2; &middot; P(x)), after &mu; = &Sigma;x &middot; P(x)', 'you have a discrete probability distribution and need its spread', 'each squared distance from &mu; is weighted by how likely that value is']
          : ['&mu; = &Sigma;x &middot; P(x)', 'you have a discrete probability distribution and need its mean (expected value)', 'each value counts in proportion to its probability; &mu; is the long-run average'];
      },
      gen: function (P) {
        var xs = P.x || [0, 1, 2, 3, 4], ps = parts(100, xs.length, 1, P.min || 3).map(function (k) { return k / 100; }), ask = P.ask || 'mean';
        return { xs: xs, ps: ps, ask: ask, d: dp(P, ask === 'sd' ? 3 : 2),
                 ph: { table: grid(['x', 'P(x)'], xs.map(function (x, i) { return [x, show(ps[i])]; })) } };
      },
      solve: function (v) {
        var xp = v.xs.map(function (x, i) { return x * v.ps[i]; }), mu = total(xp);
        var d2 = v.xs.map(function (x) { return (x - mu) * (x - mu); }), w = d2.map(function (d, i) { return d * v.ps[i]; });
        var vr = total(w), sd = Math.sqrt(vr);
        var steps = ['x &middot; P(x): ' + v.xs.map(function (x, i) { return x + '(' + show(v.ps[i]) + ') = ' + show(xp[i]); }).join('; ') + '.',
                     'Add for the mean: &mu; = ' + show(mu) + '.'];
        if (v.ask === 'sd') steps.push('(x &minus; &mu;)&sup2;: ' + joinList(d2) + '.',
                                       'Times P(x): ' + joinList(w) + '; add: ' + show(vr) + '.',
                                       'Square root: &sigma; = &radic;' + show(vr) + ' &asymp; ' + show(sd) + '.');
        var traps = v.ask === 'sd'
          ? [{ value: vr, msg: 'You left off the square root; that is the variance.' },
             { value: Math.sqrt(total(d2) / v.xs.length), msg: 'You averaged the squared distances equally. Weight each one by P(x).' }]
          : [{ value: total(v.xs) / v.xs.length, msg: 'You averaged the x values without their probabilities. Multiply each by P(x), then add.' },
             { value: mu / v.xs.length, msg: 'You divided &Sigma;x&middot;P(x) by the number of values. The sum is already the mean.' }];
        return { answer: v.ask === 'sd' ? sd : mu, steps: steps, traps: traps };
      }
    },
    'linear': {
      d: 2,
      how: function (v) {
        return v.ask === 'sd'
          ? ['&sigma;<sub>L</sub> = |b|&sigma; for L = a + bx', 'one random variable is shifted by a and scaled by b', 'adding a moves every value equally, so the spread ignores a; scaling by b stretches distances by |b|']
          : ['&mu;<sub>L</sub> = a + b&mu; for L = a + bx', 'one random variable is shifted by a and scaled by b', 'the mean moves and stretches exactly as each value does'];
      },
      gen: function (P) {
        var mu = pick(P.mu || [10]), sg = pick(P.sigma || [2]), a = pick(P.a || [5]), b = pick(P.b || [2]);
        return { mu: mu, sg: sg, a: a, b: b, ask: P.ask || 'mean', d: dp(P, 2), ph: { mu: mu, sigma: sg, a: a, b: b, expr: lin(a, b, 'x') } };
      },
      solve: function (v) {
        if (v.ask === 'sd') {
          var s = Math.abs(v.b) * v.sg;
          return { answer: s,
                   steps: ['&sigma;<sub>L</sub> = |b|&sigma; = |' + show(v.b) + '| &times; ' + show(v.sg) + ' = ' + show(s) + '.', 'The constant a = ' + show(v.a) + ' doesn\'t change the spread.'],
                   traps: [{ value: v.b * v.sg, msg: 'A standard deviation is never negative: use |b|.' },
                           { value: v.a + Math.abs(v.b) * v.sg, msg: 'You added a. Shifting every value doesn\'t change the spread.' },
                           { value: v.b * v.b * v.sg, msg: 'You used b&sup2;. That goes with the variance; &sigma;<sub>L</sub> = |b|&sigma;.' }] };
        }
        var m = v.a + v.b * v.mu;
        return { answer: m,
                 steps: ['&mu;<sub>L</sub> = a + b&mu; = ' + show(v.a) + ' + (' + show(v.b) + ')(' + show(v.mu) + ') = ' + show(m) + '.'],
                 traps: [{ value: v.b * v.mu, msg: 'You left out a. &mu;<sub>L</sub> = a + b&mu;.' },
                         { value: v.a + v.mu, msg: 'You left out b. Multiply &mu; by b first.' }] };
      }
    },
    'combo': {
      d: 2,
      how: function (v) {
        return v.ask === 'sd'
          ? ['&sigma;<sub>W</sub> = &radic;(a&sup2;&sigma;<sub>1</sub>&sup2; + b&sup2;&sigma;<sub>2</sub>&sup2;) for W = ax<sub>1</sub> + bx<sub>2</sub>, x<sub>1</sub> and x<sub>2</sub> independent', 'two independent random variables are combined', 'for independent variables the variances add, even for a difference; standard deviations don\'t add']
          : ['&mu;<sub>W</sub> = a&mu;<sub>1</sub> + b&mu;<sub>2</sub>', 'two random variables are combined', 'means combine exactly like the variables do'];
      },
      gen: function (P) {
        var m1 = pick(P.mu1 || [10]), s1 = pick(P.s1 || [2]), m2 = pick(P.mu2 || [8]), s2 = pick(P.s2 || [3]), a = pick(P.a || [1]), b = pick(P.b || [1, -1]);
        var W = (a === 1 ? '' : show(a)) + 'x<sub>1</sub>' + (b < 0 ? ' &minus; ' : ' + ') + (Math.abs(b) === 1 ? '' : show(Math.abs(b))) + 'x<sub>2</sub>';
        return { m1: m1, s1: s1, m2: m2, s2: s2, a: a, b: b, ask: P.ask || 'sd', d: dp(P, (P.ask || 'sd') === 'sd' ? 3 : 2),
                 ph: { mu1: m1, s1: s1, mu2: m2, s2: s2, a: a, b: b, expr: W } };
      },
      solve: function (v) {
        if (v.ask === 'mean') {
          var m = v.a * v.m1 + v.b * v.m2;
          return { answer: m,
                   steps: ['&mu;<sub>W</sub> = (' + show(v.a) + ')(' + show(v.m1) + ') + (' + show(v.b) + ')(' + show(v.m2) + ') = ' + show(m) + '.'],
                   traps: [{ value: v.a * v.m1 + Math.abs(v.b) * v.m2, msg: 'You added where W subtracts. Keep b\'s sign in the mean.' }] };
        }
        var var1 = v.a * v.a * v.s1 * v.s1, var2 = v.b * v.b * v.s2 * v.s2, vw = var1 + var2, s = Math.sqrt(vw);
        return { answer: s,
                 steps: ['Variances: a&sup2;&sigma;<sub>1</sub>&sup2; = ' + show(v.a * v.a) + ' &times; ' + show(v.s1 * v.s1) + ' = ' + show(var1) +
                           ' and b&sup2;&sigma;<sub>2</sub>&sup2; = ' + show(v.b * v.b) + ' &times; ' + show(v.s2 * v.s2) + ' = ' + show(var2) + '.',
                         'Add them (they add even when W subtracts): ' + show(var1) + ' + ' + show(var2) + ' = ' + show(vw) + '.',
                         'Square root: &sigma;<sub>W</sub> = &radic;' + show(vw) + ' &asymp; ' + show(s) + '.'],
                 traps: [{ value: Math.abs(v.a) * v.s1 + Math.abs(v.b) * v.s2, msg: 'You added the standard deviations. Add the variances, then take the root.' },
                         { value: Math.sqrt(Math.abs(var1 - var2)), msg: 'You subtracted the variances. For independent variables they add, even for a difference.' },
                         { value: vw, msg: 'You left off the square root; that is the variance.' }] };
      }
    }
  };
  for (var name in MORE) if (Object.prototype.hasOwnProperty.call(MORE, name)) KINDS[name] = MORE[name];

  // Exposed for the builder's tests (node); the card itself never reads it.
  function howFor(name, v) { var h = (KINDS[name] && KINDS[name].how) || HOW[name]; return typeof h === 'function' ? h(v) : h; }
  if (typeof module !== 'undefined') { module.exports = { howFor: howFor, HOW: HOW, KINDS: KINDS, C: C, P: P, sum: sum, show: show, fixed: fixed, qOf: qOf }; }
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
    if (kind.gen) return kind.gen(params);
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
    var html = promptEl.innerHTML.replace(/\{([a-z0-9]+)\}/g, function (all, name) {
      if (v.ph) return v.ph[name] != null ? String(v.ph[name]) : all;
      if (name === 'pct') return Math.round(v.p * 100) + '%';
      if (name === 'inv') return String(Math.round(1 / v.p));
      return String(v[name]);
    });
    q.innerHTML = html;
    var roundEl = document.getElementById('calc-round');
    if (roundEl) roundEl.textContent = WORDS[v.d != null ? v.d : kind.d];
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

  var out = kind.solve(state.v), d = state.v.d != null ? state.v.d : kind.d;
  var tol = d === 0 ? 1e-9 : 0.5 * Math.pow(10, -d) + 1e-9;  // a whole-number answer must be exact
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
      if (Math.abs(t.value - out.answer) > tol && Math.abs(u - t.value) <= (t.tol || tol)) { hit = t; break; }
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
                         near.msg + ' It is also a little off from that, so check for a value rounded too early.';
    else if (Math.abs(u - out.answer) <= 3 * Math.pow(10, -d)) msg = 'Close. The answer is ' + answerText + '. Keep extra digits until the last step, then round.';
    else msg = 'Not quite. The answer is ' + answerText + '. Compare your working with the steps below.';
  }
  verdict.innerHTML = msg;
  verdict.className = 'calc-verdict ' + cls;
  if (yours && u !== null) yours.textContent = 'You typed: ' + state.typed;
  var how = howFor(kindName, state.v), howEl = document.getElementById('calc-how');
  if (how && howEl) {
    howEl.innerHTML = '<div class="calc-how-h">How to solve it</div>' +
      '<div><b>Formula:</b> ' + how[0] + '</div><div><b>Use it when:</b> ' + how[1] + '.</div><div><b>Why it works:</b> ' + how[2] + '.</div>';
  }
  var stepsEl = document.getElementById('calc-steps');
  stepsEl.innerHTML = '<div class="calc-steps-h">Worked solution</div><ol>' +
    out.steps.map(function (s) { return '<li>' + s + '</li>'; }).join('') +
    '</ol><div class="calc-final">Answer: ' + answerText + '</div>';
})();
