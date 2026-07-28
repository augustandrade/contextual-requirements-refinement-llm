"""
Tests for evaluate.py / evaluate_one — scoring logic against manual reference.

No file I/O. All inputs are hand-crafted dicts that replicate the shape of
05_final_output.json and the corpus manual_reference blocks.
"""
import pytest
from evaluate import evaluate_one


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def make_final(
    has_ambiguity=False,
    route='structured',
    structured_requirements=None,
    unresolved_ambiguities=None,
    overall_status='no_ambiguity',
):
    return {
        'ambiguity_analysis': {
            'has_ambiguity': has_ambiguity,
            'ambiguities': [],
        },
        'contextual_resolubility_analysis': {
            'overall_resolubility': {'status': overall_status},
            'ambiguity_resolubility': unresolved_ambiguities or [],
        },
        'pipeline_decision': {
            'route': route,
            'overall_resolubility_status': overall_status,
        },
        'requirement_structuring': {
            'final_output_status': 'structured' if route == 'structured' else 'blocked',
            'structured_requirements': structured_requirements or [],
        },
    }


def make_ref(expected_resolubility):
    return {
        'expected_resolubility': expected_resolubility,
    }


# ---------------------------------------------------------------------------
# D1 — has_ambiguity detection
# ---------------------------------------------------------------------------

class TestD1HasAmbiguity:
    def test_not_applicable_no_ambiguity_correct(self):
        r = evaluate_one(make_final(has_ambiguity=False), make_ref('not_applicable'))
        assert r['D1_has_ambiguity'] is True

    def test_resolvable_has_ambiguity_correct(self):
        r = evaluate_one(make_final(has_ambiguity=True), make_ref('resolvable'))
        assert r['D1_has_ambiguity'] is True

    def test_unresolved_has_ambiguity_correct(self):
        r = evaluate_one(make_final(has_ambiguity=True, route='signaling', overall_status='non_resolvable'),
                         make_ref('unresolved'))
        assert r['D1_has_ambiguity'] is True

    def test_false_positive_detected(self):
        r = evaluate_one(make_final(has_ambiguity=True), make_ref('not_applicable'))
        assert r['D1_has_ambiguity'] is False
        assert r['d1_error_type'] == 'false_positive'

    def test_false_negative_detected(self):
        r = evaluate_one(make_final(has_ambiguity=False), make_ref('resolvable'))
        assert r['D1_has_ambiguity'] is False
        assert r['d1_error_type'] == 'false_negative'

    def test_d1_error_type_none_when_correct(self):
        r = evaluate_one(make_final(has_ambiguity=False), make_ref('not_applicable'))
        assert r['d1_error_type'] is None


# ---------------------------------------------------------------------------
# D2 — route decision
# ---------------------------------------------------------------------------

class TestD2Route:
    @pytest.mark.parametrize('exp_res,route', [
        ('resolvable',    'structured'),
        ('not_applicable','structured'),
        ('unresolved',    'signaling'),
    ])
    def test_correct_route(self, exp_res, route):
        final = make_final(
            has_ambiguity=(exp_res != 'not_applicable'),
            route=route,
            overall_status='non_resolvable' if route == 'signaling' else 'no_ambiguity',
        )
        r = evaluate_one(final, make_ref(exp_res))
        assert r['D2_route'] is True

    def test_wrong_route_signaling_when_should_be_structured(self):
        final = make_final(has_ambiguity=True, route='signaling', overall_status='non_resolvable')
        r = evaluate_one(final, make_ref('resolvable'))
        assert r['D2_route'] is False
        assert r['d2_error_type'] == 'false_negative'

    def test_wrong_route_structured_when_should_be_signaling(self):
        final = make_final(has_ambiguity=True, route='structured')
        r = evaluate_one(final, make_ref('unresolved'))
        assert r['D2_route'] is False
        assert r['d2_error_type'] == 'false_positive'


# ---------------------------------------------------------------------------
# D3 — output completeness
# ---------------------------------------------------------------------------

class TestD3OutputComplete:
    def test_structured_with_results_complete(self):
        final = make_final(route='structured', structured_requirements=[{'id': 'SR-01'}])
        r = evaluate_one(final, make_ref('resolvable'))
        assert r['D3_output_complete'] is True

    def test_structured_with_empty_results_incomplete(self):
        final = make_final(route='structured', structured_requirements=[])
        r = evaluate_one(final, make_ref('resolvable'))
        assert r['D3_output_complete'] is False

    def test_signaling_with_unresolved_complete(self):
        final = make_final(
            has_ambiguity=True, route='signaling', overall_status='non_resolvable',
            unresolved_ambiguities=[{'ambiguity_id': 'A1', 'resolubility_status': 'non_resolvable'}],
        )
        r = evaluate_one(final, make_ref('unresolved'))
        assert r['D3_output_complete'] is True

    def test_signaling_with_empty_unresolved_incomplete(self):
        final = make_final(
            has_ambiguity=True, route='signaling', overall_status='non_resolvable',
            unresolved_ambiguities=[],
        )
        r = evaluate_one(final, make_ref('unresolved'))
        assert r['D3_output_complete'] is False


# ---------------------------------------------------------------------------
# Score and applicable dimensions
# ---------------------------------------------------------------------------

class TestScoreAndApplicable:
    def test_perfect_score(self):
        final = make_final(
            has_ambiguity=False, route='structured',
            structured_requirements=[{'id': 'SR-01'}],
        )
        r = evaluate_one(final, make_ref('not_applicable'))
        assert r['score'] == 1.0

    def test_partial_score(self):
        # D1 correct, D3 correct, D4 wrong (empty structured_requirements)
        final = make_final(route='structured', structured_requirements=[])
        r = evaluate_one(final, make_ref('not_applicable'))
        assert r['score'] == pytest.approx(2 / 3)

    def test_d1_not_applicable_counted_as_correct(self):
        # expected_resolubility='not_applicable' → _exp_has_ambiguity returns False
        # (no ambiguity expected) → D1 IS evaluated; with has_ambiguity=False it is True
        final = make_final(route='structured', structured_requirements=[{'id': 'SR-01'}])
        ref = make_ref('not_applicable')
        r = evaluate_one(final, ref)
        assert r['D1_has_ambiguity'] is True
        assert r['applicable'] == 3

    def test_all_wrong_score_zero(self):
        final = make_final(
            has_ambiguity=True,           # wrong (expected not_applicable)
            route='signaling',            # wrong (expected structured)
            unresolved_ambiguities=[],    # empty → D4 False
            overall_status='non_resolvable',
        )
        r = evaluate_one(final, make_ref('not_applicable'))
        assert r['score'] == 0.0

    def test_act_global_status_captured(self):
        final = make_final(overall_status='fully_resolvable')
        r = evaluate_one(final, make_ref('resolvable'))
        assert r['act_global_status'] == 'fully_resolvable'

    def test_ambiguity_count_captured(self):
        final = make_final(has_ambiguity=False)
        final['ambiguity_analysis']['ambiguities'] = [{'id': 'A1'}, {'id': 'A2'}]
        r = evaluate_one(final, make_ref('not_applicable'))
        assert r['ambiguity_count'] == 2


# ---------------------------------------------------------------------------
# Edge cases — unknown expected_resolubility and unknown act_route
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unknown_expected_resolubility_d1_and_d3_not_applicable(self):
        # _exp_has_ambiguity and _exp_route both return None for unknown values
        # → only D4 is applicable
        final = make_final(route='structured', structured_requirements=[{'id': 'SR-01'}])
        r = evaluate_one(final, make_ref('totally_unknown'))
        assert r['D1_has_ambiguity'] is None
        assert r['D2_route'] is None
        assert r['applicable'] == 1

    def test_unknown_expected_resolubility_score_uses_d4_only(self):
        final = make_final(route='structured', structured_requirements=[{'id': 'SR-01'}])
        r = evaluate_one(final, make_ref('totally_unknown'))
        # D4 correct → 1/1
        assert r['score'] == 1.0

    def test_unknown_act_route_d4_not_applicable(self):
        final = make_final(route='structured', structured_requirements=[{'id': 'SR-01'}])
        final['pipeline_decision']['route'] = 'unknown'
        r = evaluate_one(final, make_ref('not_applicable'))
        assert r['D3_output_complete'] is None
