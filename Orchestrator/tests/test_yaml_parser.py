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
    _repair_yaml_value_continuation,
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


# ---------------------------------------------------------------------------
# _repair_yaml_value_continuation — Phase 2 and Phase 4 (new in repair #6)
# ---------------------------------------------------------------------------

class TestRepairYamlValueContinuationPhase2:
    """Phase 2: list item where KEY: 'SINGLE_QUOTED_VALUE' rest is misread as mapping."""

    def test_single_line_list_item_with_mapping_key_and_single_quote(self):
        # llama3.1:8b REQ-01/C1: evidence_from_context item
        text = (
            "contextual_resolubility_validation:\n"
            "  evidence_from_context:\n"
            "    - Glossary: 'maintenance window' definition — \"Scheduled period.\""
        )
        result = _repair_yaml_value_continuation(text)
        import yaml
        parsed = yaml.safe_load(result)
        items = parsed['contextual_resolubility_validation']['evidence_from_context']
        assert len(items) == 1
        assert 'Glossary' in items[0]
        assert 'maintenance window' in items[0]
        assert 'Scheduled period' in items[0]

    def test_multiline_list_item_collapsed_then_fixed(self):
        # Phase 1 collapses two lines, then Phase 2 fixes the result
        text = (
            "root:\n"
            "  items:\n"
            "    - Label: 'foo bar' rest text and more\n"
            "      continuation of rest\n"
        )
        result = _repair_yaml_value_continuation(text)
        import yaml
        parsed = yaml.safe_load(result)
        item = parsed['root']['items'][0]
        assert isinstance(item, str)
        assert 'Label' in item
        assert 'foo bar' in item

    def test_valid_list_item_without_single_quote_issue_unchanged(self):
        # A list item like - "clean value" should not be touched by Phase 2
        text = (
            "root:\n"
            "  items:\n"
            '    - "clean double-quoted value"\n'
        )
        result = _repair_yaml_value_continuation(text)
        import yaml
        parsed = yaml.safe_load(result)
        assert parsed['root']['items'] == ['clean double-quoted value']


class TestRepairYamlValueContinuationPhase4:
    """Phase 4: list item with empty-value key followed by nested YAML + continuation."""

    def test_nested_mapping_list_item_flattened(self):
        # llama3.1:8b REQ-13/C1: evidence_from_context with glossary sub-structure
        text = (
            "contextual_resolubility_validation:\n"
            "  evidence_from_context:\n"
            "    - glossary: \n"
            "        - term: settlement request\n"
            "          definition: Message requesting settlement.\n"
            "      This definition focuses on the content.\n"
        )
        result = _repair_yaml_value_continuation(text)
        import yaml
        parsed = yaml.safe_load(result)
        items = parsed['contextual_resolubility_validation']['evidence_from_context']
        assert len(items) == 1
        assert isinstance(items[0], str)
        assert 'glossary' in items[0]
        assert 'settlement request' in items[0]

    def test_empty_value_list_item_without_nested_content_left_alone(self):
        # If a - KEY: has no following deeper lines, Phase 4 must not consume anything
        text = (
            "root:\n"
            "  items:\n"
            "    - key: \n"
            "  other_field: value\n"
        )
        result = _repair_yaml_value_continuation(text)
        # Should not crash and must not consume 'other_field'
        assert 'other_field' in result

    def test_known_schema_mapping_fields_at_sequence_level_not_flattened(self):
        # The outer ambiguity_resolubility items start with '- ambiguity_id: "..."'
        # (non-empty value) — Phase 4 must not touch them.
        text = (
            "contextual_resolubility_validation:\n"
            "  ambiguity_resolubility:\n"
            '    - ambiguity_id: "AMB-01"\n'
            '      resolubility_status: "resolvable"\n'
        )
        result = _repair_yaml_value_continuation(text)
        import yaml
        parsed = yaml.safe_load(result)
        items = parsed['contextual_resolubility_validation']['ambiguity_resolubility']
        assert items[0]['ambiguity_id'] == 'AMB-01'


class TestParseYamlBlockPhase2And4:
    """End-to-end parse_yaml_block tests for the two new llama3.1:8b patterns."""

    def test_list_item_with_mapping_key_single_quote_parseable(self):
        # Reproduces REQ-01/C1 evidence_from_context pattern
        raw = (
            "contextual_resolubility_validation:\n"
            "  ambiguity_resolubility:\n"
            "    - ambiguity_id: \"AMB-01\"\n"
            "      resolubility_status: \"resolvable\"\n"
            "      evidence_from_context:\n"
            "        - Glossary: 'maintenance window' definition — \"Scheduled period.\"\n"
            "  overall_resolubility:\n"
            "    status: fully_resolvable\n"
        )
        parsed, err = parse_yaml_block(raw, 'contextual_resolubility_validation')
        assert parsed is not None, f'Should parse but got error: {err}'
        crv = parsed['contextual_resolubility_validation']
        items = crv['ambiguity_resolubility'][0]['evidence_from_context']
        assert len(items) == 1
        assert isinstance(items[0], str)

    def test_nested_mapping_list_item_in_evidence_parseable(self):
        # Reproduces REQ-13/C1 evidence_from_context pattern
        raw = (
            "contextual_resolubility_validation:\n"
            "  ambiguity_resolubility:\n"
            "    - ambiguity_id: \"AMB-01\"\n"
            "      resolubility_status: \"resolvable\"\n"
            "      evidence_from_requirement:\n"
            "        - \"Once validated...\"\n"
            "          This phrase implies it was successful.\n"
            "      evidence_from_context:\n"
            "        - glossary: \n"
            "            - term: settlement request\n"
            "              definition: A financial instrument request.\n"
            "          This definition supports the interpretation.\n"
            "  overall_resolubility:\n"
            "    status: \"fully_resolvable\"\n"
        )
        parsed, err = parse_yaml_block(raw, 'contextual_resolubility_validation')
        assert parsed is not None, f'Should parse but got error: {err}'
        crv = parsed['contextual_resolubility_validation']
        amb = crv['ambiguity_resolubility'][0]
        assert isinstance(amb['evidence_from_requirement'][0], str)
        assert isinstance(amb['evidence_from_context'][0], str)
