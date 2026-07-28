"""
Tests for AgentParseError — shape, attributes and message format.
"""
import pytest
from agents import AgentParseError


class TestAgentParseError:
    def test_is_subclass_of_runtime_error(self):
        assert issubclass(AgentParseError, RuntimeError)

    def test_message_without_parse_err(self):
        e = AgentParseError('detect_ambiguity', 'raw response')
        msg = str(e)
        assert 'detect_ambiguity' in msg
        assert 'unparsable' in msg

    def test_message_with_string_parse_err(self):
        e = AgentParseError('detect_ambiguity', 'raw response', "root key 'x' not found")
        msg = str(e)
        assert 'detect_ambiguity' in msg
        assert "root key 'x' not found" in msg

    def test_message_with_exception_parse_err(self):
        import yaml
        try:
            yaml.safe_load(': invalid [')
        except yaml.YAMLError as exc:
            e = AgentParseError('validate_resolubility', 'raw', exc)
            assert 'validate_resolubility' in str(e)
            assert e.parse_err is exc

    def test_attributes_accessible(self):
        exc = ValueError('yaml error')
        e = AgentParseError('structure_requirement', 'the raw text', exc)
        assert e.agent == 'structure_requirement'
        assert e.raw == 'the raw text'
        assert e.parse_err is exc

    def test_parse_err_none_by_default(self):
        e = AgentParseError('validate_resolubility', 'raw')
        assert e.parse_err is None

    def test_catchable_as_runtime_error(self):
        with pytest.raises(RuntimeError):
            raise AgentParseError('detect_ambiguity', 'raw')

    def test_catchable_as_agent_parse_error(self):
        with pytest.raises(AgentParseError):
            raise AgentParseError('detect_ambiguity', 'raw')
