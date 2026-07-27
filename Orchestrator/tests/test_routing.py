"""
Tests for run_pipeline.py — routing, normalization and consolidation logic.

No LLM calls; all inputs are hand-crafted dicts that replicate what agents
would return in various scenarios.
"""
import pytest

from run_pipeline import (
    normalize_overall_resolubility_status,
    should_invoke_structurer,
    get_has_concern_mixing,
    run_output_consolidator,
    build_synthetic_resolubility,
    build_non_resolvable_structuring,
)


# ---------------------------------------------------------------------------
# normalize_overall_resolubility_status
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('status,expected', [
    ('fully_resolvable', 'fully_resolvable'),
    ('resolvable',       'fully_resolvable'),
    ('RESOLVABLE',       'fully_resolvable'),   # case-insensitive
    ('no_ambiguity',     'no_ambiguity'),
    ('not_applicable',   'no_ambiguity'),
    ('non_resolvable',   'non_resolvable'),
    ('unresolved',       'non_resolvable'),
    ('blocking',         'non_resolvable'),
])
def test_normalize_known_statuses(status, expected):
    res_out = {'contextual_resolubility_validation': {
        'overall_resolubility': {'status': status}
    }}
    assert normalize_overall_resolubility_status(res_out) == expected


def test_normalize_unknown_status_returns_non_resolvable_with_warning(capsys):
    res_out = {'contextual_resolubility_validation': {
        'overall_resolubility': {'status': 'totally_made_up'}
    }}
    result = normalize_overall_resolubility_status(res_out)
    assert result == 'non_resolvable'
    captured = capsys.readouterr()
    assert 'totally_made_up' in captured.err
    assert '[WARN]' in captured.err


def test_normalize_empty_status_returns_non_resolvable_with_warning(capsys):
    res_out = {'contextual_resolubility_validation': {
        'overall_resolubility': {'status': ''}
    }}
    result = normalize_overall_resolubility_status(res_out)
    assert result == 'non_resolvable'
    captured = capsys.readouterr()
    assert '[WARN]' in captured.err


def test_normalize_missing_keys_returns_non_resolvable():
    assert normalize_overall_resolubility_status({}) == 'non_resolvable'
    assert normalize_overall_resolubility_status({'contextual_resolubility_validation': {}}) == 'non_resolvable'


# ---------------------------------------------------------------------------
# should_invoke_structurer
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('status,expected', [
    ('fully_resolvable', True),
    ('no_ambiguity',     True),
    ('non_resolvable',   False),
    ('unresolved',       False),
])
def test_should_invoke_structurer(status, expected):
    res_out = {'contextual_resolubility_validation': {
        'overall_resolubility': {'status': status}
    }}
    assert should_invoke_structurer(res_out) == expected


# ---------------------------------------------------------------------------
# get_has_concern_mixing
# ---------------------------------------------------------------------------

def test_get_has_concern_mixing_true():
    cm = {'concern_mixing_detection': {'has_concern_mixing': True}}
    assert get_has_concern_mixing(cm) is True


def test_get_has_concern_mixing_false():
    cm = {'concern_mixing_detection': {'has_concern_mixing': False}}
    assert get_has_concern_mixing(cm) is False


def test_get_has_concern_mixing_missing_key():
    assert get_has_concern_mixing({}) is False


# ---------------------------------------------------------------------------
# run_output_consolidator
# ---------------------------------------------------------------------------

_EXEC = {
    'execution_id': 'REQ-01-C0',
    'requirement_id': 'REQ-01',
    'context_condition': 'C0',
    'base_requirement_text': 'The system shall do X.',
}

_AMB_NONE = {'ambiguity_detection': {'has_ambiguity': False, 'ambiguities': []}}
_CM_NONE  = {'concern_mixing_detection': {'has_concern_mixing': False}}

def _res(status):
    return {'contextual_resolubility_validation': {
        'ambiguity_resolubility': [],
        'overall_resolubility': {'status': status},
    }}

def _struct(reqs=None):
    return {'requirement_structuring': {
        'final_output_status': 'structured',
        'structured_requirements': reqs or [{'id': 'SR-01'}],
        'unsupported_inferences_avoided': [],
    }}

def _blocked():
    return {'requirement_structuring': {
        'final_output_status': 'blocked',
        'structured_requirements': [],
        'unsupported_inferences_avoided': [],
    }}


class TestRunOutputConsolidator:
    def test_structured_route_no_ambiguity(self):
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('no_ambiguity'), _struct())
        pd = final['pipeline_decision']
        assert pd['route'] == 'structured'
        assert pd['overall_resolubility_status'] == 'no_ambiguity'

    def test_structured_route_fully_resolvable(self):
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('fully_resolvable'), _struct())
        assert final['pipeline_decision']['route'] == 'structured'

    def test_signaling_route_non_resolvable(self):
        unresolved = [{'ambiguity_id': 'A1', 'resolubility_status': 'non_resolvable',
                       'missing_information': ['clarify X']}]
        res = {'contextual_resolubility_validation': {
            'ambiguity_resolubility': unresolved,
            'overall_resolubility': {'status': 'non_resolvable'},
        }}
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, res, _blocked())
        assert final['pipeline_decision']['route'] == 'signaling'

    def test_output_contains_all_top_level_keys(self):
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('no_ambiguity'), _struct())
        for key in ('execution_id', 'requirement_id', 'context_condition', 'input_requirement',
                    'ambiguity_analysis', 'concern_mixing_analysis',
                    'contextual_resolubility_analysis', 'pipeline_decision',
                    'requirement_structuring'):
            assert key in final, f'missing key: {key}'

    def test_input_requirement_copied_from_execution_input(self):
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('no_ambiguity'), _struct())
        assert final['input_requirement'] == _EXEC['base_requirement_text']

    def test_ids_copied_from_execution_input(self):
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('no_ambiguity'), _struct())
        assert final['execution_id'] == 'REQ-01-C0'
        assert final['requirement_id'] == 'REQ-01'
        assert final['context_condition'] == 'C0'

    def test_struct_out_none_handled(self):
        # build_non_resolvable_structuring returns a dict, but test robustness
        final = run_output_consolidator(_EXEC, _AMB_NONE, _CM_NONE, _res('non_resolvable'), None)
        assert final['requirement_structuring'] is None


# ---------------------------------------------------------------------------
# build_synthetic_resolubility
# ---------------------------------------------------------------------------

class TestBuildSyntheticResolubility:
    _EI = {'execution_id': 'REQ-01-C0', 'requirement_id': 'REQ-01'}

    def test_status_is_no_ambiguity(self):
        out = build_synthetic_resolubility(self._EI)
        crv = out['contextual_resolubility_validation']
        assert crv['overall_resolubility']['status'] == 'no_ambiguity'

    def test_ambiguity_resolubility_empty(self):
        out = build_synthetic_resolubility(self._EI)
        assert out['contextual_resolubility_validation']['ambiguity_resolubility'] == []

    def test_ids_copied_from_execution_input(self):
        out = build_synthetic_resolubility(self._EI)
        crv = out['contextual_resolubility_validation']
        assert crv['execution_id'] == 'REQ-01-C0'
        assert crv['requirement_id'] == 'REQ-01'

    def test_empty_execution_input_does_not_crash(self):
        out = build_synthetic_resolubility({})
        crv = out['contextual_resolubility_validation']
        assert crv['execution_id'] is None
        assert crv['requirement_id'] is None


# ---------------------------------------------------------------------------
# build_non_resolvable_structuring
# ---------------------------------------------------------------------------

class TestBuildNonResolvableStructuring:
    _EI = {'execution_id': 'REQ-01-C0', 'requirement_id': 'REQ-01', 'context_condition': 'C0'}

    def test_final_output_status_blocked(self):
        out = build_non_resolvable_structuring(self._EI)
        assert out['requirement_structuring']['final_output_status'] == 'blocked'

    def test_structured_requirements_empty(self):
        out = build_non_resolvable_structuring(self._EI)
        assert out['requirement_structuring']['structured_requirements'] == []

    def test_ids_and_context_copied(self):
        out = build_non_resolvable_structuring(self._EI)
        rs = out['requirement_structuring']
        assert rs['execution_id'] == 'REQ-01-C0'
        assert rs['requirement_id'] == 'REQ-01'
        assert rs['context_condition'] == 'C0'

    def test_compatible_with_consolidator_struct_out(self):
        out = build_non_resolvable_structuring(self._EI)
        rs = out['requirement_structuring']
        assert 'unsupported_inferences_avoided' in rs
        assert isinstance(rs['unsupported_inferences_avoided'], list)
