#!/usr/bin/env python3
"""sigma_gate.py -- the noise-floor / selection gate from the experiment-discipline skill.

Input: a table of results, one row per (arm, seed):

    arm             seed   ap
    cell_51_96      8888   72.7276
    cell_51_96      1      72.5658

Prints, for every arm: mean, n, and the verdict of its delta against the baseline,
using the same threshold in both directions. Three things it refuses to let slide:

  * sigma unknown  -> every verdict is "null". An unmeasured denominator cannot
    support a measured numerator.
  * selection      -> --k raises the threshold to sqrt(2 ln k) (floor 2). The best
    of k nulls has an expected value of about sigma*sqrt(2 ln k).
  * a negative excursion larger than the claimed gain -> the negative is the
    headline, and it is printed before the positive.

Exit codes: 0 = at least one delta resolved; 2 = sigma unknown (all null); 1 = bad input.
"""

import argparse
import math
import statistics
import sys

GAIN = 'gain'
NULL = 'null'
HARM = 'harm'


def parse_table(path):
    with open(path, encoding='utf-8-sig') as fh:
        lines = [ln.rstrip('\n') for ln in fh if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines:
        raise SystemExit('sigma_gate: empty table')
    delim = '\t' if '\t' in lines[0] else ','
    head = [c.strip().lower() for c in lines[0].split(delim)]
    try:
        i_arm, i_seed, i_ap = head.index('arm'), head.index('seed'), head.index('ap')
    except ValueError:
        raise SystemExit('sigma_gate: header must contain arm, seed, ap (got %r)' % head)
    rows = []
    for ln in lines[1:]:
        c = [x.strip() for x in ln.split(delim)]
        if len(c) <= max(i_arm, i_seed, i_ap):
            continue
        rows.append((c[i_arm], c[i_seed], float(c[i_ap])))
    if not rows:
        raise SystemExit('sigma_gate: no data rows')
    return rows


def summarise(rows):
    """-> list of (arm, mean, n, sd or None) in first-seen order"""
    order, vals = [], {}
    for arm, _seed, ap in rows:
        if arm not in vals:
            order.append(arm)
            vals[arm] = []
        vals[arm].append(ap)
    out = []
    for arm in order:
        v = vals[arm]
        sd = statistics.stdev(v) if len(v) >= 2 else None
        out.append((arm, statistics.fmean(v), len(v), sd))
    return out


def pooled_sigma(stats):
    """Pooled within-arm sd. None if no arm has replicates."""
    sds = [sd for _a, _m, _n, sd in stats if sd is not None]
    if not sds:
        return None
    return (sum(s * s for s in sds) / len(sds)) ** 0.5


def threshold_for_k(k):
    """Threshold multiplier after a search over k variants. 2.0 floor, sqrt(2 ln k) above."""
    if k is None or k <= 1:
        return 2.0
    return max(2.0, math.sqrt(2.0 * math.log(k)))


def verdict(delta, sigma, thr=2.0):
    if sigma is None:
        return NULL
    if delta >= thr * sigma:
        return GAIN
    if delta <= -thr * sigma:
        return HARM
    return NULL


def power_pairs(sigma, delta, thr=2.0):
    """Required number of paired seeds. sigma is the per-arm floor; sigma(delta)=sqrt(2)sigma."""
    return (thr * sigma * math.sqrt(2.0) / delta) ** 2


def _require_positive(name, value):
    """A zero or negative floor cannot be divided by; refuse it instead of crashing."""
    if value is not None and value <= 0:
        raise SystemExit('sigma_gate: %s must be > 0 (got %r)' % (name, value))


def report(stats, sigma, baseline, thr=2.0, out=sys.stdout):
    w = out.write
    _require_positive('sigma', sigma)
    base = next((s for s in stats if s[0] == baseline), None)
    if base is None:
        raise SystemExit('sigma_gate: baseline %r not in table' % baseline)

    w('=== arms ===\n')
    w('  %-28s %9s %6s %9s\n' % ('arm', 'mean', 'n', 'sd'))
    for arm, mean, n, sd in stats:
        w('  %-28s %9.4f %6d %9s\n' % (arm, mean, n, '-' if sd is None else '%.4f' % sd))

    w('\n=== delta vs baseline %r   (threshold %.2f sigma) ===\n' % (baseline, thr))
    w('  %-28s %9s %9s %8s  %s\n' % ('arm', 'delta', 'delta/sigma', 'verdict', ''))
    deltas = []
    for arm, mean, _n, _sd in stats:
        if arm == baseline:
            continue
        d = mean - base[1]
        r = '-' if sigma is None else '%.1f' % (d / sigma)
        v = verdict(d, sigma, thr)
        deltas.append((arm, d, v))
        w('  %-28s %+9.4f %9s %8s  %s\n' % (arm, d, r, v, 'clears the bar' if v != NULL else ''))

    w('\nsigma = %s   threshold = %.2f sigma' %
      ('UNKNOWN' if sigma is None else '%.4f' % sigma, thr))
    if sigma is None:
        w('  (no arm has replicate seeds and no --sigma was given)')
    w('\n\n')

    if sigma is None:
        w('VERDICT RULE: sigma unknown -> every delta is NULL, whatever its sign.\n')
        w('  Either run a second seed, or borrow a measured floor and say whose it is.\n')
    else:
        n_resolved = sum(1 for _a, _d, v in deltas if v != NULL)
        if n_resolved == 0:
            w('FLAT-RESULT ALARM: no arm clears %.2f sigma (%.4f).\n' % (thr, sigma))
            w('  This is a protocol symptom, not a set of null modules. Before designing\n')
            w('  the next variant, check that the recipe can express an effect at all:\n')
            w('  lr x epochs for a from-scratch run, best epoch, loss still falling.\n')

    if deltas:
        pos = [d for _a, d, _v in deltas if d > 0]
        neg = [d for _a, d, _v in deltas if d < 0]
        worst_neg = min(deltas, key=lambda t: t[1])
        best_pos = max(deltas, key=lambda t: t[1])
        # Sign symmetry does not need a sigma: if the biggest negative excursion is
        # larger than the biggest positive one, the negative explains the positive.
        asymmetric = bool(pos and neg and abs(worst_neg[1]) > best_pos[1])
        must = {arm for arm, _d, v in deltas if v == HARM}
        if asymmetric:
            must.add(worst_neg[0])
        w('\n=== contrary block (paste this into the write-up) ===\n')
        for arm, d, v in sorted(deltas, key=lambda t: -t[1]):
            tag = '  <-- MUST MENTION' if arm in must else ''
            w('  %-28s %+9.4f %8s%s\n' % (arm, d, v, tag))
        if asymmetric:
            w('\nSIGN ASYMMETRY: the largest negative delta (%.4f) is larger than the\n'
              % worst_neg[1])
            w('  largest positive one (%.4f). Whatever produced the negative is a live\n' % best_pos[1])
            w('  explanation for the positive. Explain the negative first. This test needs\n')
            w('  no sigma: it is a property of the table, not of the measurement.\n')
    return 2 if sigma is None else 0


# --------------------------------------------------------------------------- selftest
# Fixture A is SYNTHETIC: it reproduces the shape of a real false result (six single-seed
# arms, one negative excursion larger than the largest positive) without carrying anyone's
# actual measurements. Fixture B is the author's own two-seed 2x2 grid.
FIXTURE_FALSE = """arm	seed	ap
base	0	40.0
neg_a	0	38.0
neg_b	0	36.5
pos_a	0	40.4
pos_b	0	39.6
"""

GRID = """arm	seed	ap
cell_51_96	8888	72.7276
cell_51_96	1	72.5658
cell_102_96	8888	75.5771
cell_102_96	1	75.2127
cell_51_192	8888	79.1181
cell_51_192	1	79.0131
cell_102_192	8888	82.4464
cell_102_192	1	82.5575
"""


def selftest():
    import io
    import os
    import tempfile
    ok = True

    def run(text, sigma=None, baseline=None, k=1):
        fd, path = tempfile.mkstemp(suffix='.tsv')
        os.close(fd)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        rows = parse_table(path)
        os.unlink(path)
        st = summarise(rows)
        sig = sigma if sigma is not None else pooled_sigma(st)
        thr = threshold_for_k(k)
        buf = io.StringIO()
        code = report(st, sig, baseline or st[0][0], thr, out=buf)
        return code, buf.getvalue(), sig

    # case A: six single-seed arms, no floor -> must refuse to resolve anything
    code, txt, sig = run(FIXTURE_FALSE, baseline='base')
    a1 = code == 2
    a2 = sig is None
    a3 = 'sigma unknown' in txt.lower()
    a4 = 'SIGN ASYMMETRY' in txt
    a5 = 'MUST MENTION' in txt
    ok &= a1 and a2 and a3 and a4 and a5
    print('  A six single-seed arms (synthetic) : code=%d sigma=%s asym=%s must_mention=%s  %s'
          % (code, sig, a4, a5, 'PASS' if (a1 and a2 and a3 and a4 and a5) else 'FAIL'))

    # case B: two-seed 2x2, pooled floor from the replicates -> main effects must resolve
    code, txt, sig = run(GRID, baseline='cell_51_96')
    b1 = code == 0
    b2 = sig is not None and 0.10 <= sig <= 0.25
    b3 = txt.count('gain') >= 3
    b4 = 'FLAT-RESULT' not in txt
    b5 = 'SIGN ASYMMETRY' not in txt
    ok &= b1 and b2 and b3 and b4 and b5
    print('  B two-seed 2x2 grid         : code=%d sigma=%s gains>=3=%s  %s'
          % (code, '-' if sig is None else '%.4f' % sig, b3,
             'PASS' if (b1 and b2 and b3 and b4 and b5) else 'FAIL'))

    # case C: the power arithmetic quoted in SKILL.md section 1 must stay true
    c1 = abs(power_pairs(0.16, 0.26) - 3.03) < 0.05
    c2 = abs(power_pairs(0.50, 0.26) - 29.6) < 0.3
    c3 = abs(threshold_for_k(10) - 2.146) < 0.01
    c4 = threshold_for_k(1) == 2.0
    ok &= c1 and c2 and c3 and c4
    print('  C power arithmetic (SKILL 1) : n(0.16,0.26)=%.2f n(0.50,0.26)=%.2f thr(k=10)=%.3f  %s'
          % (power_pairs(0.16, 0.26), power_pairs(0.50, 0.26), threshold_for_k(10),
             'PASS' if (c1 and c2 and c3 and c4) else 'FAIL'))

    # case D: degenerate inputs are refused, never divided by
    d1 = False
    try:
        run(FIXTURE_FALSE, sigma=0.0, baseline='base')
    except SystemExit:
        d1 = True
    d2 = False
    try:
        _require_positive('--power', 0.0)
    except SystemExit:
        d2 = True
    ok &= d1 and d2
    print('  D degenerate inputs refused  : zero-sigma=%s zero-delta=%s  %s'
          % (d1, d2, 'PASS' if (d1 and d2) else 'FAIL'))

    print('\n  SELFTEST:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description='noise-floor and selection gate for experiment claims')
    ap.add_argument('table', nargs='?', help='TSV/CSV with header arm,seed,ap')
    ap.add_argument('--sigma', type=float, default=None,
                    help='measured noise floor (per-arm AP sd) instead of pooling replicates')
    ap.add_argument('--baseline', default=None, help='baseline arm (default: first row)')
    ap.add_argument('--k', type=int, default=1,
                    help='how many variants were tried before this one; raises the bar to sqrt(2 ln k)')
    ap.add_argument('--power', type=float, default=None, metavar='DELTA',
                    help='required seed pairs for an effect of DELTA at the current threshold')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    thr = threshold_for_k(a.k)
    if a.power is not None:
        if a.sigma is None:
            ap.error('--power needs --sigma (the measured per-arm floor)')
        _require_positive('--sigma', a.sigma)
        _require_positive('--power', a.power)
        raw = power_pairs(a.sigma, a.power, thr)
        need = max(1, math.ceil(raw))
        print('sigma(AP)       = %.4f' % a.sigma)
        print('sigma(delta)    = %.4f  (= sqrt(2) * sigma(AP))' % (a.sigma * math.sqrt(2.0)))
        print('threshold       = %.2f sigma  (k = %d)' % (thr, a.k))
        print('effect DELTA    = %.4f' % a.power)
        print('required pairs  = %.2f  -> round up to %d seed pairs (%d runs)' % (raw, need, 2 * need))
        return 0
    if not a.table:
        ap.error('give a table, --power, or --selftest')
    stats = summarise(parse_table(a.table))
    sigma = a.sigma if a.sigma is not None else pooled_sigma(stats)
    return report(stats, sigma, a.baseline or stats[0][0], thr)


if __name__ == '__main__':
    sys.exit(main())
