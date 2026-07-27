"""
Tests for the new metrics and lift functions added to evaluate.py:

  _detection_metrics_d1    precision / recall / specificity for D1 (has_ambiguity)
  _detection_metrics_d2    precision / recall / specificity for D2 (concern_mixing)
  evaluate_context_lift    ΔD3 between context conditions, staged gains, transitions

All inputs are hand-crafted dicts — no file I/O.
"""
import pytest
from evaluate import _detection_metrics_d1, _detection_metrics_d2, evaluate_context_lift


# ── Builders ─────────────────────────────────────────────────────────────────

_POS_CATS = ['category-02-linguistic', 'category-03-domain', 'category-04-vagueness']
_NEG_CATS = ['category-01-structural', 'category-05-control']


def _d1_row(expected_resolubility, act_has_ambiguity, category='category-02-linguistic'):
    return {
        'expected_resolubility': expected_resolubility,
        'act_has_ambiguity':     act_has_ambiguity,
        'category':              category,
        'act_has_concern_mixing': False,
    }


def _d2_row(category, act_has_concern_mixing):
    return {
        'category':              category,
        'act_has_concern_mixing': act_has_concern_mixing,
        'expected_resolubility': 'not_applicable',
        'act_has_ambiguity':     False,
    }


def _lift_rows(run, req_id, category, d3_c0, d3_c1, d3_c2):
    """Build three rows (C0/C1/C2) for a single requirement."""
    base = {'run': run, 'req_id': req_id, 'category': category,
            'act_route': 'structured', 'score': 1.0}
    return [
        {**base, 'context': 'C0', 'D3_route': d3_c0},
        {**base, 'context': 'C1', 'D3_route': d3_c1},
        {**base, 'context': 'C2', 'D3_route': d3_c2},
    ]


# ── _detection_metrics_d1 ─────────────────────────────────────────────────────

class TestDetectionMetricsD1:

    def test_perfect_classifier(self):
        rows = (
            [_d1_row('resolvable',    True,  cat) for cat in _POS_CATS] +
            [_d1_row('not_applicable', False, cat) for cat in _NEG_CATS]
        )
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 3
        assert m['tn'] == 2
        assert m['fp'] == 0
        assert m['fn'] == 0
        assert m['precision']   == pytest.approx(1.0)
        assert m['recall']      == pytest.approx(1.0)
        assert m['specificity'] == pytest.approx(1.0)

    def test_one_false_positive_lowers_precision_and_specificity(self):
        rows = [
            _d1_row('not_applicable', True,  'category-05-control'),   # FP
            _d1_row('not_applicable', False, 'category-01-structural'), # TN
            _d1_row('resolvable',     True,  'category-02-linguistic'), # TP
        ]
        m = _detection_metrics_d1(rows)
        assert m['fp'] == 1
        assert m['tn'] == 1
        assert m['tp'] == 1
        assert m['fn'] == 0
        assert m['precision']   == pytest.approx(1 / 2)
        assert m['specificity'] == pytest.approx(1 / 2)
        assert m['recall']      == pytest.approx(1.0)

    def test_one_false_negative_lowers_recall(self):
        rows = [
            _d1_row('resolvable', False, 'category-02-linguistic'),  # FN
            _d1_row('resolvable', True,  'category-03-domain'),      # TP
            _d1_row('not_applicable', False, 'category-05-control'), # TN
        ]
        m = _detection_metrics_d1(rows)
        assert m['fn'] == 1
        assert m['tp'] == 1
        assert m['fp'] == 0
        assert m['recall']    == pytest.approx(1 / 2)
        assert m['precision'] == pytest.approx(1.0)

    def test_all_wrong(self):
        rows = [
            _d1_row('resolvable',     False, 'category-02-linguistic'),  # FN
            _d1_row('not_applicable', True,  'category-05-control'),      # FP
        ]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 0
        assert m['tn'] == 0
        assert m['precision']   == pytest.approx(0.0)
        assert m['recall']      == pytest.approx(0.0)
        assert m['specificity'] == pytest.approx(0.0)

    def test_unresolved_counts_as_positive(self):
        rows = [_d1_row('unresolved', True, 'category-04-vagueness')]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 1
        assert m['fn'] == 0

    def test_unknown_resolubility_skipped(self):
        rows = [_d1_row('totally_unknown', True, 'category-02-linguistic')]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 0
        assert m['fp'] == 0
        assert m['fn'] == 0
        assert m['tn'] == 0
        assert m['precision'] is None
        assert m['recall']    is None

    def test_no_positives_recall_is_none(self):
        rows = [_d1_row('not_applicable', False, 'category-05-control')]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 0
        assert m['fn'] == 0
        assert m['recall'] is None

    def test_no_negatives_specificity_is_none(self):
        rows = [_d1_row('resolvable', True, 'category-02-linguistic')]
        m = _detection_metrics_d1(rows)
        assert m['tn'] == 0
        assert m['fp'] == 0
        assert m['specificity'] is None


# ── _detection_metrics_d2 ─────────────────────────────────────────────────────

class TestDetectionMetricsD2:

    def test_perfect_classifier(self):
        rows = (
            [_d2_row('category-01-structural', True)] * 3 +   # TP × 3
            [_d2_row(cat, False) for cat in _POS_CATS] +      # TN × 3
            [_d2_row('category-05-control', False)]            # TN × 1
        )
        m = _detection_metrics_d2(rows)
        assert m['tp'] == 3
        assert m['tn'] == 4
        assert m['fp'] == 0
        assert m['fn'] == 0
        assert m['precision']   == pytest.approx(1.0)
        assert m['recall']      == pytest.approx(1.0)
        assert m['specificity'] == pytest.approx(1.0)

    def test_false_positive_non_structural_cat(self):
        rows = [_d2_row('category-02-linguistic', True)]   # FP: Cat-02 não tem concern mixing
        m = _detection_metrics_d2(rows)
        assert m['fp'] == 1
        assert m['tp'] == 0
        assert m['precision'] == pytest.approx(0.0)

    def test_false_negative_structural_cat_not_detected(self):
        rows = [_d2_row('category-01-structural', False)]  # FN: Cat-01 esperava concern mixing
        m = _detection_metrics_d2(rows)
        assert m['fn'] == 1
        assert m['tp'] == 0
        assert m['recall'] == pytest.approx(0.0)

    def test_true_negative_control_cat(self):
        rows = [_d2_row('category-05-control', False)]
        m = _detection_metrics_d2(rows)
        assert m['tn'] == 1
        assert m['fp'] == 0

    def test_no_positives_recall_is_none(self):
        rows = [_d2_row('category-05-control', False)]
        m = _detection_metrics_d2(rows)
        assert m['recall'] is None


# ── evaluate_context_lift ─────────────────────────────────────────────────────

class TestEvaluateContextLift:

    def test_lift_plus_one_context_resolved(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          d3_c0=False, d3_c1=False, d3_c2=True)
        lift = evaluate_context_lift(rows)
        assert len(lift) == 1
        r = lift[0]
        assert r['lift_c2_c0']  == 1
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 1
        assert r['transition']  == '0→0→1'

    def test_lift_zero_always_correct(self):
        rows = _lift_rows('run_1', 'REQ-13', 'category-05-control',
                          d3_c0=True, d3_c1=True, d3_c2=True)
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 0
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '1→1→1'

    def test_lift_zero_always_wrong(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          d3_c0=False, d3_c1=False, d3_c2=False)
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 0
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '0→0→0'

    def test_lift_minus_one_degradation(self):
        rows = _lift_rows('run_1', 'REQ-05', 'category-02-linguistic',
                          d3_c0=True, d3_c1=True, d3_c2=False)
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == -1
        assert r['stage_c1_c2'] == -1
        assert r['transition']  == '1→1→0'

    def test_gain_at_c1_stage_only(self):
        rows = _lift_rows('run_1', 'REQ-07', 'category-03-domain',
                          d3_c0=False, d3_c1=True, d3_c2=True)
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 1
        assert r['stage_c0_c1'] == 1
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '0→1→1'

    def test_missing_condition_row_skipped(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          d3_c0=False, d3_c1=False, d3_c2=True)
        rows_no_c2 = [r for r in rows if r['context'] != 'C2']
        lift = evaluate_context_lift(rows_no_c2)
        assert len(lift) == 0

    def test_multiple_runs_independent(self):
        rows = (
            _lift_rows('run_1', 'REQ-10', 'category-04-vagueness', False, False, True) +
            _lift_rows('run_2', 'REQ-10', 'category-04-vagueness', False, False, False)
        )
        lift = evaluate_context_lift(rows)
        assert len(lift) == 2
        by_run = {r['run']: r for r in lift}
        assert by_run['run_1']['lift_c2_c0'] == 1
        assert by_run['run_2']['lift_c2_c0'] == 0

    def test_multiple_reqs_same_run(self):
        rows = (
            _lift_rows('run_1', 'REQ-04', 'category-02-linguistic', False, False, True) +
            _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',  True,  True,  True)
        )
        lift = evaluate_context_lift(rows)
        assert len(lift) == 2
        by_req = {r['req_id']: r for r in lift}
        assert by_req['REQ-04']['lift_c2_c0'] == 1
        assert by_req['REQ-10']['lift_c2_c0'] == 0

    def test_d3_none_produces_none_lift(self):
        rows = _lift_rows('run_1', 'REQ-01', 'category-01-structural',
                          d3_c0=None, d3_c1=None, d3_c2=None)
        lift = evaluate_context_lift(rows)
        assert len(lift) == 1
        r = lift[0]
        assert r['lift_c2_c0']  is None
        assert r['stage_c0_c1'] is None
        assert r['stage_c1_c2'] is None
        assert '?' in r['transition']

    def test_output_includes_category_and_run(self):
        rows = _lift_rows('run_42', 'REQ-11', 'category-04-vagueness',
                          d3_c0=False, d3_c1=False, d3_c2=True)
        r = evaluate_context_lift(rows)[0]
        assert r['run']      == 'run_42'
        assert r['req_id']   == 'REQ-11'
        assert r['category'] == 'category-04-vagueness'
