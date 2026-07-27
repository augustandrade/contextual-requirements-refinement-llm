"""
Transforms a raw LLM response string into a parsed Python dict.

Public API: parse_yaml_block(raw, root_key) -> dict | None
Everything else is an internal repair heuristic.
"""
import re
import sys

import yaml

# ---------------------------------------------------------------------------
# Step 1 — strip markdown fences
# ---------------------------------------------------------------------------

def _strip_markdown_fence(text: str) -> str:
    blocks = re.findall(r'```(?:yaml)?\s*\n(.*?)```', text, re.DOTALL)
    if blocks:
        # Prefer the last block that starts with a YAML key (not a comment)
        for block in reversed(blocks):
            stripped = block.strip()
            if stripped and not stripped.startswith('#'):
                return stripped
        return blocks[-1]
    # trailing ``` without opening fence (qwen3.5-4b artifact)
    return re.sub(r'\n```\s*$', '', text.strip())


# ---------------------------------------------------------------------------
# Step 2 — targeted repairs, applied individually then stacked
# ---------------------------------------------------------------------------

_SINGLE_QUOTED_LINE = re.compile(r"^(\s*(?:-\s+)?(?:[\w.\-]+:\s*)?)'(.*)'\s*$")


def _repair_yaml_quotes(text: str) -> str:
    """Single-quoted scalar that itself contains an unescaped single quote.
    Rewrites such lines as double-quoted scalars.
    """
    fixed_lines = []
    for line in text.split('\n'):
        m = _SINGLE_QUOTED_LINE.match(line)
        if m:
            prefix, inner = m.groups()
            if "'" in inner:
                escaped = inner.replace('\\', '\\\\').replace('"', '\\"')
                line = f'{prefix}"{escaped}"'
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


_TRAILING_GARBAGE_AFTER_QUOTE = re.compile(r'^(.*"[^"]*")[.,;]+\s*$')


def _repair_yaml_trailing_garbage(text: str) -> str:
    """Stray punctuation the model appended after a closed double-quoted scalar."""
    fixed_lines = []
    for line in text.split('\n'):
        m = _TRAILING_GARBAGE_AFTER_QUOTE.match(line)
        fixed_lines.append(m.group(1) if m else line)
    return '\n'.join(fixed_lines)


_UNESCAPED_QUOTE = re.compile(r'(?<!\\)"')
_OPENS_QUOTED_SCALAR = re.compile(r'^\s*(?:-\s+)?[\w.\-]+:\s*"')


def _repair_yaml_unterminated_quote(text: str) -> str:
    """Double-quoted scalar opened but never closed on the same line."""
    fixed_lines = []
    for line in text.split('\n'):
        if len(_UNESCAPED_QUOTE.findall(line)) == 1 and _OPENS_QUOTED_SCALAR.match(line):
            line = line + '"'
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def _repair_yaml_bad_escape(text: str) -> str:
    """Model escapes apostrophes as \\' — not a valid YAML escape sequence."""
    return text.replace("\\'", "'")


_OPENS_QUOTED_SCALAR_QUOTE_COUNT = re.compile(r'^\s*(?:-\s+)?(?:[\w.\-]+:\s*)?"')


def _repair_yaml_embedded_quote(text: str) -> str:
    """Literal unescaped " inside a double-quoted scalar closes it early."""
    fixed_lines = []
    for line in text.split('\n'):
        if _OPENS_QUOTED_SCALAR_QUOTE_COUNT.match(line):
            positions = [m.start() for m in _UNESCAPED_QUOTE.finditer(line)]
            if len(positions) > 2:
                chars = list(line)
                for pos in positions[1:-1]:
                    chars[pos] = '\\"'
                line = ''.join(chars)
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_REPAIRS = (
    lambda t: t,
    _repair_yaml_quotes,
    _repair_yaml_trailing_garbage,
    _repair_yaml_unterminated_quote,
    _repair_yaml_embedded_quote,
)


def parse_yaml_block(raw: str, root_key: str):
    """Parse a model's YAML response, retrying with targeted repairs on failure.

    Returns the parsed dict when root_key is present, or None if all attempts fail.
    """
    candidate = _repair_yaml_bad_escape(_strip_markdown_fence(raw))

    attempts = [r(candidate) for r in _REPAIRS]
    attempts.append(_repair_yaml_embedded_quote(_repair_yaml_unterminated_quote(
        _repair_yaml_trailing_garbage(_repair_yaml_quotes(candidate)))))

    for i, text in enumerate(attempts):
        try:
            parsed = yaml.safe_load(text)
        except Exception:
            continue
        if isinstance(parsed, dict) and root_key in parsed:
            if i > 0:
                repair_label = _REPAIRS[i].__name__ if i < len(_REPAIRS) else 'stacked'
                print(f'[WARN] yaml_parser: repair #{i} ({repair_label}) succeeded for root_key={root_key!r}', file=sys.stderr)
            return parsed
    return None
