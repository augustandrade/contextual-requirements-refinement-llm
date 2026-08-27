"""
Tests for evaluate.py / evaluate_one — scoring logic.

No file I/O. All inputs are hand-crafted dicts that replicate the shape of
final_output.json produced by the pipeline.

API: evaluate_one(final: dict, expected_has_ambiguity: bool) -> dict
Dimensions:
  D1_has_ambiguity   — detection correct?
  D_output_integrity — output structurally intact given the route taken?
"""
import pytest
from evaluate import evaluate_one


# ── Builders ──────────────────────────────────────────────────────────────────

def make_final(
    has_ambiguity=False,
    route='structured',
    structured_requirements=None,
    unresolved_ambiguities=None,
    overall_status='no_ambiguity',
):
    """Build a dict that mimics final_output.json."""
    return {
        'ambiguity_analysis': {
            'has_ambiguity': has_ambiguity,
            'ambiguities': [],
        },
        'contextual_resolubility_analysis': {
            'overall_resolubility': overall_status,
            'ambiguity_resolubility': unresolved_ambiguities or [],
        },
        'pipeline_decision': {
            'route': route,
            'overall_resolubility_status': overall_status,
        },
        'requirement_structuring': {
            'structured_requirements': structured_requirements or [],
        },
    }


def _sr(final_statement='The system shall do X.'):
    """Build a structured_requirement item with a valid final_statement."""
    return {'structured_id': 'SR-01', 'type': 'functional_requirement',
            'final_statement': final_statement, 'structuring_notes': []}


def _unresolved(status='unresolved'):
    return {'ambiguity_id': 'AMB-01', 'resolubility_status': status}


# ── D1 — has_ambiguity detection ──────────────────────────────────────────────

class TestD1HasAmbiguity:

    def test_no_ambiguity_expected_and_correct(self):
        r = evaluate_one(make_final(has_ambiguity=False), expected_has_ambiguity=False)
        assert r['D1_has_ambiguity'] is True
        assert r['d1_error_type'] is None

    def test_ambiguity_expected_and_correct(self):
        r = evaluate_one(make_final(has_ambiguity=True, route='signaling'),
                         expected_has_ambiguity=True)
        assert r['D1_has_ambiguity'] is True
        assert r['d1_error_type'] is None

    def test_false_positive_detected(self):
        r = evaluate_one(make_final(has_ambiguity=True), expected_has_ambiguity=False)
        assert r['D1_has_ambiguity'] is False
        assert r['d1_error_type'] == 'false_positive'

    def test_false_negative_detected(self):
        r = evaluate_one(make_final(has_ambiguity=False), expected_has_ambiguity=True)
        assert r['D1_has_ambiguity'] is False
        assert r['d1_error_type'] == 'false_negative'


# ── D_output — structural integrity of the output ─────────────────────────────

class TestDOutputIntegrity:

    def test_structured_with_valid_final_statement_is_complete(self):
        final = make_final(route='structured', structured_requirements=[_sr()])
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D_output_integrity'] is True

    def test_structured_with_empty_list_is_incomplete(self):
        final = make_final(route='structured', structured_requirements=[])
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D_output_integrity'] is False

    def test_structured_with_blank_final_statement_is_incomplete(self):
        final = make_final(route='structured', structured_requirements=[_sr('')])
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D_output_integrity'] is False

    def test_signaling_with_unresolved_item_is_complete(self):
        final = make_final(route='signaling',
                           unresolved_ambiguities=[_unresolved('unresolved')])
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['D_output_integrity'] is True

    def test_signaling_with_false_positive_item_is_incomplete(self):
        """false_positive is not an unresolved status — signaling route with only
        false_positives has no open issue to signal, so D_output is False."""
        final = make_final(route='signaling',
                           unresolved_ambiguities=[_unresolved('false_positive')])
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['D_output_integrity'] is False

    def test_signaling_with_only_resolvable_items_is_incomplete(self):
        """If all items are 'resolvable', the signaling route has no open issue to signal."""
        final = make_final(route='signaling',
                           unresolved_ambiguities=[_unresolved('resolvable')])
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['D_output_integrity'] is False

    def test_signaling_with_empty_resolubility_is_incomplete(self):
        final = make_final(route='signaling', unresolved_ambiguities=[])
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['D_output_integrity'] is False

    def test_unknown_route_gives_none(self):
        final = make_final(route='structured')
        final['pipeline_decision']['route'] = 'unknown'
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D_output_integrity'] is None


# ── Score and applicable count ────────────────────────────────────────────────

class TestScoreAndApplicable:

    def test_perfect_score_no_ambiguity(self):
        """Control case: no ambiguity expected, route structured, output complete."""
        final = make_final(has_ambiguity=False, route='structured',
                           structured_requirements=[_sr()])
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['score'] == pytest.approx(1.0)
        assert r['correct']    == 2
        assert r['applicable'] == 2

    def test_perfect_score_with_ambiguity(self):
        """Ambiguous case: correctly detected, signaling route, unresolved item present."""
        final = make_final(has_ambiguity=True, route='signaling',
                           unresolved_ambiguities=[_unresolved()])
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['score'] == pytest.approx(1.0)
        assert r['correct'] == 2

    def test_d1_wrong_d_output_correct(self):
        """FP on D1 but output is structurally OK → score = 1/2."""
        final = make_final(has_ambiguity=True, route='structured',
                           structured_requirements=[_sr()])
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D1_has_ambiguity']   is False
        assert r['D_output_integrity'] is True
        assert r['score'] == pytest.approx(1 / 2)

    def test_unknown_route_reduces_applicable_count(self):
        final = make_final(has_ambiguity=False, route='structured')
        final['pipeline_decision']['route'] = 'unknown'
        r = evaluate_one(final, expected_has_ambiguity=False)
        assert r['D_output_integrity'] is None
        assert r['applicable'] == 1     # only D1 counted

    def test_act_global_status_captured(self):
        final = make_final(overall_status='fully_resolvable')
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['act_global_status'] == 'fully_resolvable'

    def test_ambiguity_count_captured(self):
        final = make_final(has_ambiguity=True)
        final['ambiguity_analysis']['ambiguities'] = [{'id': 'A1'}, {'id': 'A2'}]
        r = evaluate_one(final, expected_has_ambiguity=True)
        assert r['ambiguity_count'] == 2
