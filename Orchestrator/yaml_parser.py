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

_CLOSED_QUOTED_SCALAR = re.compile(r'^(\s*(?:-\s+)?(?:[\w.\-]+:\s*)?)".*"\s*$')
_YAML_STRUCTURAL = re.compile(r'^\s*(?:[\w.\-]+\s*:|-\s)')


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


_LIST_ITEM_MAPPING_SINGLE_QUOTE = re.compile(
    r"^(\s+- )([\w][\w\s]*): ('(?:[^'\\]|\\.)*')(.+)$"
)

_EMPTY_VALUE_LIST_ITEM = re.compile(r'^(\s+- )([\w][\w\s]*): *$')


def _repair_yaml_value_continuation(text: str) -> str:
    """Merge continuation text after quoted scalars into the value.

    llama3.1:8b produces four problematic patterns handled in order:

    Phase 1 — Collapse multi-line double-quoted scalars into one line.
    Phase 2 — Fix list items YAML misparses as mappings:
                 - Glossary: 'maintenance window' definition — "..."
               YAML sees KEY='Glossary', VALUE='maintenance window', then
               errors on ' definition'. Fix: wrap the whole content in "…".
    Phase 3 — Merge deeper-indented non-structural continuation lines into
               the preceding closed quoted scalar.
    Phase 4 — Flatten list items whose value is an empty key followed by
               nested YAML (- KEY:\n  sub: val\n  continuation…). The model
               dumps a controlled-context sub-structure where a plain string
               was expected; flatten the entire block into a single "…" item.
    """
    # Phase 1: collapse multi-line double-quoted scalars into one line each
    lines = text.split('\n')
    collapsed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        count = len(_UNESCAPED_QUOTE.findall(line))
        if count % 2 == 1:  # unclosed quote — consume lines until closed
            combined = line.rstrip()
            j = i + 1
            while j < len(lines) and count % 2 == 1:
                count += len(_UNESCAPED_QUOTE.findall(lines[j]))
                combined += ' ' + lines[j].strip()
                j += 1
            collapsed.append(combined)
            i = j
        else:
            collapsed.append(line)
            i += 1

    # Phase 2: list item where content begins KEY: 'SINGLE_QUOTED' rest text.
    # After Phase 1 all such items are on one line; wrap the whole value in "…".
    fixed2 = []
    for line in collapsed:
        m = _LIST_ITEM_MAPPING_SINGLE_QUOTE.match(line)
        if m:
            prefix, key, sq_val, rest = m.groups()
            full = f'{key}: {sq_val}{rest}'
            escaped = full.replace('\\', '\\\\').replace('"', '\\"')
            line = f'{prefix}"{escaped}"'
        fixed2.append(line)

    # Phase 3: merge non-structural continuation lines into preceding closed scalar
    result3 = []
    i = 0
    while i < len(fixed2):
        line = fixed2[i]
        m = _CLOSED_QUOTED_SCALAR.match(line)
        if m and i + 1 < len(fixed2):
            curr_indent = len(line) - len(line.lstrip())
            merged = line.rstrip()
            j = i + 1
            while j < len(fixed2):
                next_line = fixed2[j]
                if not next_line.strip():
                    break
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent > curr_indent and not _YAML_STRUCTURAL.match(next_line):
                    if merged.endswith('"'):
                        merged = merged[:-1] + ' ' + next_line.strip() + '"'
                    j += 1
                else:
                    break
            if j > i + 1:
                result3.append(merged)
                i = j
                continue
        result3.append(line)
        i += 1

    # Phase 4: flatten list items whose key has an empty value followed by
    # deeper-indented nested YAML (and optional same-parent continuation text).
    # The model sometimes dumps a context sub-structure (e.g. glossary list)
    # where the schema expects a plain string.
    result4 = []
    i = 0
    while i < len(result3):
        line = result3[i]
        m = _EMPTY_VALUE_LIST_ITEM.match(line)
        if m:
            prefix, key = m.groups()
            base_indent = len(line) - len(line.lstrip())
            j = i + 1
            parts = []
            while j < len(result3):
                next_line = result3[j]
                if not next_line.strip():
                    break
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent > base_indent:
                    parts.append(next_line.strip())
                    j += 1
                else:
                    break
            if parts:
                full_text = key + ': ' + ' '.join(parts)
                escaped = full_text.replace('\\', '\\\\').replace('"', '\\"')
                result4.append(f'{prefix}"{escaped}"')
                i = j
                continue
        result4.append(line)
        i += 1

    return '\n'.join(result4)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_REPAIRS = (
    lambda t: t,
    _repair_yaml_quotes,
    _repair_yaml_trailing_garbage,
    _repair_yaml_unterminated_quote,
    _repair_yaml_embedded_quote,
    _repair_yaml_value_continuation,
)


def parse_yaml_block(raw: str, root_key: str):
    """Parse a model's YAML response, retrying with targeted repairs on failure.

    Returns (parsed_dict, None) on success, or (None, last_err) on failure.
    last_err is the last yaml exception, or a string describing a structural
    mismatch (parsed ok but root key absent or not a dict).
    """
    candidate = _repair_yaml_bad_escape(_strip_markdown_fence(raw))

    attempts = [r(candidate) for r in _REPAIRS]
    attempts.append(_repair_yaml_embedded_quote(_repair_yaml_unterminated_quote(
        _repair_yaml_trailing_garbage(_repair_yaml_quotes(candidate)))))

    last_err = None
    for i, text in enumerate(attempts):
        try:
            parsed = yaml.safe_load(text)
        except Exception as exc:
            last_err = exc
            continue
        if isinstance(parsed, dict) and root_key in parsed:
            if i > 0:
                repair_label = _REPAIRS[i].__name__ if i < len(_REPAIRS) else 'stacked'
                print(f'[WARN] yaml_parser: repair #{i} ({repair_label}) succeeded for root_key={root_key!r}', file=sys.stderr)
            return parsed, None
        if last_err is None:
            last_err = f'parsed ok but root key {root_key!r} not found (got {type(parsed).__name__})'
    return None, last_err
