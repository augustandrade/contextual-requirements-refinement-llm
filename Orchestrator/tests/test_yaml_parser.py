"""
Tests for yaml_parser.py — the YAML extraction and repair logic.

All tests are pure (no I/O, no model calls). Each repair function is tested
with a case that triggers it and a no-op case to confirm it doesn't corrupt
valid input. parse_yaml_block is tested end-to-end with the (parsed, err)
tuple API.
"""
import pytest

from yaml_parser import (
    _strip_markdown_fence,
    _repair_yaml_bad_escape,
    _repair_yaml_quotes,
    _repair_yaml_trailing_garbage,
    _repair_yaml_unterminated_quote,
    _repair_yaml_embedded_quote,
    parse_yaml_block,
)

ROOT = 'ambiguity_detection'


# ---------------------------------------------------------------------------
# _strip_markdown_fence
# ---------------------------------------------------------------------------

class TestStripMarkdownFence:
    def test_yaml_tagged_fence(self):
        raw = "```yaml\nkey: value\n```"
        assert _strip_markdown_fence(raw) == "key: value"

    def test_untagged_fence(self):
        raw = "```\nkey: value\n```"
        assert _strip_markdown_fence(raw) == "key: value"

    def test_trailing_fence_only(self):
        raw = "key: value\n```"
        assert _strip_markdown_fence(raw) == "key: value"

    def test_multiple_blocks_prefers_last_non_comment(self):
        raw = "```yaml\n# comment only\n```\n```yaml\nkey: value\n```"
        assert _strip_markdown_fence(raw) == "key: value"

    def test_no_fence_returns_text(self):
        raw = "key: value"
        assert _strip_markdown_fence(raw) == "key: value"

    def test_whitespace_stripped_around_content(self):
        raw = "```yaml\n\n  key: value  \n\n```"
        assert _strip_markdown_fence(raw).strip() == "key: value"


# ---------------------------------------------------------------------------
# Individual repair functions
# ---------------------------------------------------------------------------

class TestRepairBadEscape:
    def test_replaces_backslash_apostrophe(self):
        assert _repair_yaml_bad_escape("key: 'it\\'s fine'") == "key: 'it's fine'"

    def test_leaves_clean_input_untouched(self):
        text = "key: 'clean value'"
        assert _repair_yaml_bad_escape(text) == text


class TestRepairYamlQuotes:
    def test_converts_single_quoted_with_apostrophe_to_double_quoted(self):
        line = "  explanation: 'it's unclear'"
        result = _repair_yaml_quotes(line)
        assert result.startswith('  explanation: "')
        assert result.endswith('"')
        assert "it's unclear" in result

    def test_leaves_single_quoted_without_apostrophe_untouched(self):
        line = "  explanation: 'clean text'"
        assert _repair_yaml_quotes(line) == line

    def test_leaves_unquoted_line_untouched(self):
        line = "  has_ambiguity: false"
        assert _repair_yaml_quotes(line) == line

    def test_multiline_only_fixes_affected_line(self):
        text = "root:\n  a: 'clean'\n  b: 'it's bad'\n"
        result = _repair_yaml_quotes(text)
        assert "  a: 'clean'" in result
        assert '  b: "it\'s bad"' in result


class TestRepairTrailingGarbage:
    def test_removes_period_after_closing_quote(self):
        line = '  explanation: "some text".'
        assert _repair_yaml_trailing_garbage(line) == '  explanation: "some text"'

    def test_removes_comma_after_closing_quote(self):
        line = '  explanation: "some text",'
        assert _repair_yaml_trailing_garbage(line) == '  explanation: "some text"'

    def test_leaves_clean_quoted_line_untouched(self):
        line = '  explanation: "some text"'
        assert _repair_yaml_trailing_garbage(line) == line

    def test_leaves_unquoted_line_untouched(self):
        line = '  has_ambiguity: false'
        assert _repair_yaml_trailing_garbage(line) == line


class TestRepairUnterminatedQuote:
    def test_closes_unclosed_double_quote(self):
        line = '  explanation: "unclosed'
        assert _repair_yaml_unterminated_quote(line) == '  explanation: "unclosed"'

    def test_leaves_closed_quote_untouched(self):
        line = '  explanation: "properly closed"'
        assert _repair_yaml_unterminated_quote(line) == line

    def test_leaves_unquoted_line_untouched(self):
        line = '  has_ambiguity: false'
        assert _repair_yaml_unterminated_quote(line) == line


class TestRepairEmbeddedQuote:
    def test_escapes_inner_double_quotes(self):
        line = '  explanation: "some "inner" text"'
        result = _repair_yaml_embedded_quote(line)
        assert '\\"inner\\"' in result
        assert result.startswith('  explanation: "')
        assert result.endswith('"')

    def test_leaves_exactly_two_quotes_untouched(self):
        line = '  explanation: "clean text"'
        assert _repair_yaml_embedded_quote(line) == line

    def test_leaves_unquoted_line_untouched(self):
        line = '  has_ambiguity: false'
        assert _repair_yaml_embedded_quote(line) == line


# ---------------------------------------------------------------------------
# parse_yaml_block — end-to-end with (parsed, err) tuple API
# ---------------------------------------------------------------------------

def _wrap(content: str) -> str:
    return f"```yaml\n{content}\n```"


class TestParseYamlBlock:
    def test_valid_yaml_returns_dict_and_no_error(self):
        raw = _wrap(f"{ROOT}:\n  has_ambiguity: false\n  ambiguities: []")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed == {ROOT: {'has_ambiguity': False, 'ambiguities': []}}
        assert err is None

    def test_valid_yaml_no_fence_also_parsed(self):
        raw = f"{ROOT}:\n  has_ambiguity: false"
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is not None
        assert err is None

    def test_wrong_root_key_returns_none_with_description(self):
        raw = _wrap(f"{ROOT}:\n  has_ambiguity: false")
        parsed, err = parse_yaml_block(raw, 'wrong_key')
        assert parsed is None
        assert err is not None
        assert 'wrong_key' in str(err)

    def test_root_key_value_null_returned_as_dict(self):
        # yaml_parser sees the key → returns the dict; agent must check isinstance
        raw = _wrap(f"{ROOT}: null")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed == {ROOT: None}
        assert err is None

    def test_broken_yaml_returns_none_and_scanner_error(self):
        raw = _wrap("- : invalid\n  broken: [unclosed")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is None
        assert err is not None

    def test_empty_string_returns_none(self):
        parsed, err = parse_yaml_block('', ROOT)
        assert parsed is None
        assert err is not None

    def test_bad_escape_fixed_before_attempts(self):
        # \' replaced by ' before the attempt loop — identity succeeds
        raw = _wrap(f"{ROOT}:\n  explanation: 'it\\'s fine'")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is not None
        assert err is None

    def test_single_quoted_apostrophe_fixed_by_repair(self):
        # identity → ScannerError; _repair_yaml_quotes fixes it
        content = f"{ROOT}:\n  has_ambiguity: true\n  explanation: 'it's ambiguous'"
        raw = _wrap(content)
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is not None
        assert err is None

    def test_unterminated_quote_fixed_by_repair(self):
        # identity → ScannerError; _repair_yaml_unterminated_quote fixes it
        content = f'{ROOT}:\n  has_ambiguity: true\n  explanation: "unclosed'
        raw = _wrap(content)
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is not None
        assert err is None

    def test_embedded_quote_fixed_by_repair(self):
        content = f'{ROOT}:\n  explanation: "some "embedded" text"'
        raw = _wrap(content)
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is not None
        assert err is None

    def test_last_err_is_exception_not_string_on_scanner_error(self):
        import yaml
        raw = _wrap("{{invalid: [")
        _, err = parse_yaml_block(raw, ROOT)
        assert isinstance(err, (yaml.YAMLError, Exception))

    def test_list_value_returned_successfully_agent_handles_type_check(self):
        # yaml_parser does NOT inspect the type of the root key's value;
        # it returns the full parsed dict so agents.py can do the isinstance check.
        # A list value is NOT a structural mismatch from yaml_parser's perspective.
        raw = _wrap(f"{ROOT}:\n  - item1\n  - item2")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed == {ROOT: ['item1', 'item2']}
        assert err is None

    def test_last_err_is_string_when_root_key_missing(self):
        # YAML parses ok but root_key is absent → last_err is a descriptive str
        raw = _wrap("other_key:\n  field: value")
        parsed, err = parse_yaml_block(raw, ROOT)
        assert parsed is None
        assert isinstance(err, str)
        assert ROOT in err
