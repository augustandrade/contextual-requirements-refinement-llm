"""
Tests for process_corpus._log_agent_error — diagnostic output formatting.

No file I/O; uses capsys to inspect stderr output.
"""
import pytest
from agents import AgentParseError
from process_corpus import _log_agent_error


class TestLogAgentError:
    def test_generic_error_without_ctx_says_skipping_all_contexts(self, capsys):
        _log_agent_error('REQ-01', None, RuntimeError('connection refused'))
        err = capsys.readouterr().err
        assert '[ERROR] REQ-01' in err
        assert 'connection refused' in err
        assert 'skipping all contexts' in err
        assert '--resume' in err

    def test_generic_error_with_ctx_says_skipping(self, capsys):
        _log_agent_error('REQ-01', 'C1', RuntimeError('timeout'))
        err = capsys.readouterr().err
        assert '[ERROR] REQ-01/C1' in err
        assert 'skipping' in err
        assert 'skipping all contexts' not in err

    def test_agent_parse_error_shows_agent_reason_raw(self, capsys):
        exc = AgentParseError('detect_ambiguity', 'the raw output', "root key not found")
        _log_agent_error('REQ-02', 'C0', exc)
        err = capsys.readouterr().err
        assert 'detect_ambiguity' in err
        assert 'root key not found' in err
        assert 'the raw output' in err

    def test_agent_parse_error_without_parse_err_omits_reason_line(self, capsys):
        exc = AgentParseError('validate_resolubility', 'raw output')
        _log_agent_error('REQ-03', 'C0', exc)
        err = capsys.readouterr().err
        assert 'validate_resolubility' in err
        assert 'reason:' not in err

    def test_raw_truncated_at_400_chars(self, capsys):
        long_raw = 'x' * 600
        exc = AgentParseError('detect_ambiguity', long_raw)
        _log_agent_error('REQ-04', 'C0', exc)
        err = capsys.readouterr().err
        # repr of raw[:400] has exactly 400 'x's — 401 consecutive x's cannot appear
        assert 'x' * 401 not in err

    def test_ctx_none_location_is_req_id_only(self, capsys):
        _log_agent_error('REQ-05', None, RuntimeError('err'))
        err = capsys.readouterr().err
        assert 'REQ-05/' not in err  # no slash when ctx is None
        assert 'REQ-05' in err

    def test_agent_parse_error_is_also_logged_as_error_header(self, capsys):
        exc = AgentParseError('structure_requirement', 'raw', 'yaml parse error')
        _log_agent_error('REQ-06', 'C2', exc)
        err = capsys.readouterr().err
        assert '[ERROR]' in err
