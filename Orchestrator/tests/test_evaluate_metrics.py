"""
Tests for detection metrics and context-lift functions in evaluate.py.

  _detection_metrics_d1    precision / recall / specificity for D1 (has_ambiguity)
  evaluate_context_lift    ΔRoute between context conditions, staged gains, transitions

All inputs are hand-crafted dicts — no file I/O.
Ground truth rule: expected_has_ambiguity = (category_id != 'category-05-control').
"""
import pytest
from evaluate import _detection_metrics_d1, evaluate_context_lift


# ── Builders ──────────────────────────────────────────────────────────────────

# Category-05 is the only negative (control); Cat-01 through 04 are all positive.
_POS_CATS = [
    'category-01-structural',
    'category-02-linguistic',
    'category-03-domain',
    'category-04-vagueness',
]
_NEG_CATS = ['category-05-control']


def _d1_row(act_has_ambiguity: bool, category: str = 'category-02-linguistic') -> dict:
    """Build a row as evaluate_run() would produce it.

    expected_has_ambiguity is derived from category (mirrors _expected_has_ambiguity).
    """
    return {
        'expected_has_ambiguity': category != 'category-05-control',
        'act_has_ambiguity':      act_has_ambiguity,
        'category':               category,
    }


def _lift_rows(run, req_id, category, route_c0, route_c1, route_c2, route_c3=None):
    """Build C0/C1/C2 (and optionally C3) rows for evaluate_context_lift().

    route_* should be 'structured', 'signaling', or None (missing data).
    expected_has_ambiguity is derived from category.
    """
    exp_ha = (category != 'category-05-control')
    base   = {'run': run, 'req_id': req_id, 'category': category,
              'expected_has_ambiguity': exp_ha}
    rows = [
        {**base, 'context': 'C0', 'act_route': route_c0 or ''},
        {**base, 'context': 'C1', 'act_route': route_c1 or ''},
        {**base, 'context': 'C2', 'act_route': route_c2 or ''},
    ]
    if route_c3 is not None:
        rows.append({**base, 'context': 'C3', 'act_route': route_c3})
    return rows


# ── _detection_metrics_d1 ─────────────────────────────────────────────────────

class TestDetectionMetricsD1:

    def test_perfect_classifier(self):
        rows = (
            [_d1_row(True,  cat) for cat in _POS_CATS] +
            [_d1_row(False, cat) for cat in _NEG_CATS]
        )
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 4   # Cat-01, 02, 03, 04 — all correctly detected
        assert m['tn'] == 1   # Cat-05 correctly not flagged
        assert m['fp'] == 0
        assert m['fn'] == 0
        assert m['precision']   == pytest.approx(1.0)
        assert m['recall']      == pytest.approx(1.0)
        assert m['specificity'] == pytest.approx(1.0)

    def test_one_false_positive_lowers_precision_and_specificity(self):
        rows = [
            _d1_row(True,  'category-05-control'),   # FP — control flagged as ambiguous
            _d1_row(True,  'category-02-linguistic'), # TP
        ]
        m = _detection_metrics_d1(rows)
        assert m['fp'] == 1
        assert m['tn'] == 0
        assert m['tp'] == 1
        assert m['fn'] == 0
        assert m['precision']   == pytest.approx(1 / 2)
        assert m['specificity'] == pytest.approx(0.0)   # tn/(tn+fp) = 0/1
        assert m['recall']      == pytest.approx(1.0)

    def test_cat01_counts_as_positive(self):
        """Cat-01 (structural) must be a positive — not a negative/control."""
        rows = [
            _d1_row(True,  'category-01-structural'),  # TP (Cat-01 is positive)
            _d1_row(False, 'category-05-control'),     # TN
        ]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 1
        assert m['tn'] == 1
        assert m['fp'] == 0
        assert m['fn'] == 0

    def test_cat01_missed_is_false_negative(self):
        """Missing Cat-01 detection is a FN, not a TN."""
        rows = [_d1_row(False, 'category-01-structural')]  # FN
        m = _detection_metrics_d1(rows)
        assert m['fn'] == 1
        assert m['tp'] == 0
        assert m['tn'] == 0

    def test_one_false_negative_lowers_recall(self):
        rows = [
            _d1_row(False, 'category-02-linguistic'),  # FN
            _d1_row(True,  'category-03-domain'),      # TP
            _d1_row(False, 'category-05-control'),     # TN
        ]
        m = _detection_metrics_d1(rows)
        assert m['fn'] == 1
        assert m['tp'] == 1
        assert m['fp'] == 0
        assert m['recall']    == pytest.approx(1 / 2)
        assert m['precision'] == pytest.approx(1.0)

    def test_all_wrong(self):
        rows = [
            _d1_row(False, 'category-02-linguistic'),  # FN
            _d1_row(True,  'category-05-control'),     # FP
        ]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 0
        assert m['tn'] == 0
        assert m['precision']   == pytest.approx(0.0)
        assert m['recall']      == pytest.approx(0.0)
        assert m['specificity'] == pytest.approx(0.0)

    def test_no_positives_recall_is_none(self):
        rows = [_d1_row(False, 'category-05-control')]
        m = _detection_metrics_d1(rows)
        assert m['tp'] == 0
        assert m['fn'] == 0
        assert m['recall'] is None

    def test_no_negatives_specificity_is_none(self):
        rows = [_d1_row(True, 'category-02-linguistic')]
        m = _detection_metrics_d1(rows)
        assert m['tn'] == 0
        assert m['fp'] == 0
        assert m['specificity'] is None

    def test_missing_fields_skipped(self):
        """Rows without expected_has_ambiguity or act_has_ambiguity are ignored."""
        rows = [{'category': 'category-02-linguistic'}]  # no relevant fields
        m = _detection_metrics_d1(rows)
        assert m['tp'] == m['fp'] == m['fn'] == m['tn'] == 0
        assert m['precision'] is None
        assert m['recall']    is None


# ── evaluate_context_lift ─────────────────────────────────────────────────────

class TestEvaluateContextLift:

    def test_lift_plus_one_context_resolved(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          'signaling', 'signaling', 'structured')
        lift = evaluate_context_lift(rows)
        assert len(lift) == 1
        r = lift[0]
        assert r['lift_c2_c0']  == 1
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 1
        assert r['transition']  == '0→0→1→?'

    def test_lift_zero_always_correct(self):
        rows = _lift_rows('run_1', 'REQ-13', 'category-05-control',
                          'structured', 'structured', 'structured')
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 0
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '1→1→1→?'

    def test_lift_zero_always_wrong(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          'signaling', 'signaling', 'signaling')
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 0
        assert r['stage_c0_c1'] == 0
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '0→0→0→?'

    def test_lift_minus_one_degradation(self):
        rows = _lift_rows('run_1', 'REQ-05', 'category-02-linguistic',
                          'structured', 'structured', 'signaling')
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == -1
        assert r['stage_c1_c2'] == -1
        assert r['transition']  == '1→1→0→?'

    def test_gain_at_c1_stage_only(self):
        rows = _lift_rows('run_1', 'REQ-07', 'category-03-domain',
                          'signaling', 'structured', 'structured')
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 1
        assert r['stage_c0_c1'] == 1
        assert r['stage_c1_c2'] == 0
        assert r['transition']  == '0→1→1→?'

    def test_with_c3_included(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          'signaling', 'signaling', 'structured', 'signaling')
        lift = evaluate_context_lift(rows)
        r = lift[0]
        assert r['lift_c2_c0']  == 1
        assert r['lift_c3_c0']  == 0
        assert r['delta_c2_c3'] == 1
        assert r['transition']  == '0→0→1→0'

    def test_missing_condition_row_skipped(self):
        rows = _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                          'signaling', 'signaling', 'structured')
        rows_no_c2 = [r for r in rows if r['context'] != 'C2']
        lift = evaluate_context_lift(rows_no_c2)
        assert len(lift) == 0

    def test_multiple_runs_independent(self):
        rows = (
            _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                       'signaling', 'signaling', 'structured') +
            _lift_rows('run_2', 'REQ-10', 'category-04-vagueness',
                       'signaling', 'signaling', 'signaling')
        )
        lift = evaluate_context_lift(rows)
        assert len(lift) == 2
        by_run = {r['run']: r for r in lift}
        assert by_run['run_1']['lift_c2_c0'] == 1
        assert by_run['run_2']['lift_c2_c0'] == 0

    def test_multiple_reqs_same_run(self):
        rows = (
            _lift_rows('run_1', 'REQ-04', 'category-02-linguistic',
                       'signaling', 'signaling', 'structured') +
            _lift_rows('run_1', 'REQ-10', 'category-04-vagueness',
                       'structured', 'structured', 'structured')
        )
        lift = evaluate_context_lift(rows)
        assert len(lift) == 2
        by_req = {r['req_id']: r for r in lift}
        assert by_req['REQ-04']['lift_c2_c0'] == 1
        assert by_req['REQ-10']['lift_c2_c0'] == 0

    def test_unknown_route_produces_none_lift(self):
        """Rows with act_route='' produce structured=None → lift=None."""
        rows = _lift_rows('run_1', 'REQ-01', 'category-01-structural',
                          '', '', '')
        lift = evaluate_context_lift(rows)
        assert len(lift) == 1
        r = lift[0]
        assert r['lift_c2_c0']  is None
        assert r['stage_c0_c1'] is None
        assert r['stage_c1_c2'] is None
        assert '?' in r['transition']

    def test_output_includes_category_and_run(self):
        rows = _lift_rows('run_42', 'REQ-11', 'category-04-vagueness',
                          'signaling', 'signaling', 'structured')
        r = evaluate_context_lift(rows)[0]
        assert r['run']      == 'run_42'
        assert r['req_id']   == 'REQ-11'
        assert r['category'] == 'category-04-vagueness'
