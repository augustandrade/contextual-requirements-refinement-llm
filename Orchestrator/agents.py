import os
import re
from pathlib import Path

import yaml

try:
    from openai import OpenAI
    _openai_client = None
except Exception:  # optional dependency for future cloud backends
    OpenAI = None
    _openai_client = None

# Provider configuration: 'local' | 'openai' | 'ollama' | 'mock'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:latest')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '600'))

# Base directory for resolving agent prompts (TCC root)
_TCC_ROOT = Path(__file__).parent.parent

# Local model config (used when LLM_PROVIDER=local)
LOCAL_MODEL_PATH = os.getenv('LLM_LOCAL_MODEL_PATH', '')  # path to ggml model for llama.cpp

# lazy imports for local runtime
_llama_client = None
_llama_model_path = None

def _ensure_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if OpenAI is None:
        raise EnvironmentError('openai package is not installed. Install it if you want to use LLM_PROVIDER=openai')
    if not OPENAI_API_KEY:
        raise EnvironmentError('OPENAI_API_KEY is not set for OpenAI provider')
    _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

def _call_model_openai(system_prompt: str, user_content: str, timeout: int = 60):
    client = _ensure_openai_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=2000,
    )
    choice = resp.choices[0]
    message = getattr(choice, 'message', None)
    if message is not None:
        content = getattr(message, 'content', None)
        if content:
            return content
    return getattr(choice, 'text', None) or str(choice)


def _load_prompt(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _strip_markdown_fence(text: str) -> str:
    """Remove ```yaml / ``` fences that models often wrap responses in.
    When multiple fences are present (e.g. Reasoning + Output blocks),
    prefer the last block that looks like a YAML document (starts with a key:).
    """
    import re
    blocks = re.findall(r'```(?:yaml)?\s*\n(.*?)```', text, re.DOTALL)
    if blocks:
        # Prefer the last block that starts with a YAML key (not a comment)
        for block in reversed(blocks):
            stripped = block.strip()
            if stripped and not stripped.startswith('#'):
                return stripped
        return blocks[-1]
    # Case 2: trailing ``` without opening fence (qwen3.5-4b artifact)
    text = re.sub(r'\n```\s*$', '', text.strip())
    return text


_SINGLE_QUOTED_LINE = re.compile(r"^(\s*(?:-\s+)?(?:[\w.\-]+:\s*)?)'(.*)'\s*$")


def _repair_yaml_quotes(text: str) -> str:
    """Best-effort repair for the most common YAML break we see from local
    models: a single-quoted scalar that itself contains an unescaped single
    quote (e.g. `key: 'foo 'bar' baz'` or a bare list item `- 'foo 'bar' baz'`).
    In valid YAML that inner quote would need to be doubled (`''`), but models
    routinely forget this, which truncates the string and corrupts the
    surrounding block mapping/sequence. Rewrite such lines as double-quoted
    scalars instead, where an embedded single quote is just a literal
    character. The key: prefix is optional so this also catches quoted
    scalars in plain list items (`- '...'`), not just `key: '...'`.
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
    """Best-effort repair for a second common YAML break: a properly closed
    double-quoted scalar followed by stray punctuation the model appended
    outside the string (e.g. `- "some text".`), which YAML treats as
    trailing garbage after the scalar and refuses to parse. Strip it.
    """
    fixed_lines = []
    for line in text.split('\n'):
        m = _TRAILING_GARBAGE_AFTER_QUOTE.match(line)
        fixed_lines.append(m.group(1) if m else line)
    return '\n'.join(fixed_lines)


_UNESCAPED_QUOTE = re.compile(r'(?<!\\)"')
_OPENS_QUOTED_SCALAR = re.compile(r'^\s*(?:-\s+)?[\w.\-]+:\s*"')


def _repair_yaml_unterminated_quote(text: str) -> str:
    """Best-effort repair for a third common YAML break: a double-quoted
    scalar that opens with `"` but is never closed on that line (the model
    trails off, e.g. mid chain-of-thought, without a matching quote). YAML
    then folds every following line into that same open string until it
    happens to hit a later `"` elsewhere in the document, corrupting the
    structure. Close the scalar right where it was left open.
    """
    fixed_lines = []
    for line in text.split('\n'):
        if len(_UNESCAPED_QUOTE.findall(line)) == 1 and _OPENS_QUOTED_SCALAR.match(line):
            line = line + '"'
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def _repair_yaml_bad_escape(text: str) -> str:
    """Best-effort repair for a fourth common YAML break: the model escapes
    apostrophes as `\\'` (valid in Python/JSON strings, but not a recognized
    YAML escape sequence inside a double-quoted scalar), which makes the
    parser abort with "found unknown escape character". Since YAML never
    needs a backslash before a literal single quote, unescaping it is safe
    everywhere it appears.
    """
    return text.replace("\\'", "'")


_OPENS_QUOTED_SCALAR_QUOTE_COUNT = re.compile(r'^\s*(?:-\s+)?(?:[\w.\-]+:\s*)?"')


def _repair_yaml_embedded_quote(text: str) -> str:
    """Best-effort repair for a fifth common YAML break: a double-quoted
    scalar that contains a literal, unescaped `"` in the middle of the text
    (e.g. the model quotes a sub-phrase with straight double quotes instead
    of single quotes), which closes the scalar early and leaves the rest of
    the sentence as trailing garbage. Escape every quote strictly between
    the opening and the true final quote on the line.
    """
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


_LIST_ITEM_START = re.compile(r'^\s*-(\s|$)')
_KEY_LINE_START = re.compile(r'^\s*[\w.\-]+:(\s|$)')


def _repair_yaml_orphan_continuation(text: str) -> str:
    """Best-effort repair for a sixth common YAML break: the model wraps a
    sentence onto a new line without list/flow syntax (e.g. a `- key: value`
    item followed by a plain-text line at the same or deeper indent that is
    neither a new list item nor a `key: value` pair). YAML then tries to read
    that orphan line as a new mapping key and aborts with "could not find
    expected ':'". Fold it back into the previous line as a continuation of
    that scalar value instead.
    """
    fixed_lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if (stripped and not _LIST_ITEM_START.match(line) and not _KEY_LINE_START.match(stripped)
                and fixed_lines):
            fixed_lines[-1] = fixed_lines[-1].rstrip() + ' ' + stripped
            continue
        fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def _parse_yaml_block(raw: str, root_key: str):
    """Parse a model's YAML response, retrying with a few targeted repairs
    if the first attempt fails. Returns the parsed dict, or None if all
    attempts fail or the expected root_key is missing."""
    candidate = _repair_yaml_bad_escape(_strip_markdown_fence(raw))
    repairs = (
        lambda t: t,
        _repair_yaml_quotes,
        _repair_yaml_trailing_garbage,
        _repair_yaml_unterminated_quote,
        _repair_yaml_embedded_quote,
        _repair_yaml_orphan_continuation,
    )
    # try single repairs first, then stacked combinations, in increasing order
    # of how much of the raw text they alter
    attempts = []
    for r in repairs:
        attempts.append(r(candidate))
    stacked = _repair_yaml_embedded_quote(_repair_yaml_unterminated_quote(
        _repair_yaml_trailing_garbage(_repair_yaml_quotes(candidate))))
    attempts.append(stacked)
    attempts.append(_repair_yaml_orphan_continuation(stacked))

    for text in attempts:
        try:
            parsed = yaml.safe_load(text)
        except Exception:
            continue
        if isinstance(parsed, dict) and root_key in parsed:
            return parsed
    return None


def _ensure_local_client():
    global _llama_client, _llama_model_path
    if _llama_client is not None and _llama_model_path == LOCAL_MODEL_PATH:
        return _llama_client
    try:
        from llama_cpp import Llama
    except Exception:
        raise EnvironmentError('llama-cpp-python not installed. Install with `pip install "llama-cpp-python"` and provide a LOCAL GGUF model path via LLM_LOCAL_MODEL_PATH')
    if not LOCAL_MODEL_PATH:
        raise EnvironmentError('LLM_LOCAL_MODEL_PATH not set. Export path to your GGUF model (for example Qwen2.5 7B Instruct GGUF)')
    _llama_client = Llama(model_path=LOCAL_MODEL_PATH)
    _llama_model_path = LOCAL_MODEL_PATH
    return _llama_client


def _call_model_local(system_prompt: str, user_content: str, timeout: int = 60):
    client = _ensure_local_client()
    prompt = system_prompt + "\n\n" + user_content
    # llama-cpp-python supports simple call interface
    resp = client(prompt, max_tokens=2000, temperature=0.0)
    if isinstance(resp, dict):
        choices = resp.get('choices')
        if choices and isinstance(choices, list):
            c0 = choices[0]
            return c0.get('text') or (c0.get('message') or {}).get('content') or str(c0)
    return str(resp)


def _call_model_ollama(system_prompt: str, user_content: str, timeout: int = None, num_ctx: int = 2048, num_predict: int = 1500):
    """Call Ollama via REST API with thinking disabled for faster responses."""
    import urllib.request
    import json as _json
    timeout = timeout or OLLAMA_TIMEOUT
    payload = _json.dumps({
        'model': OLLAMA_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content},
        ],
        'stream': False,
        'think': False,
        'options': {
            'temperature': 0.0,
            'num_ctx': num_ctx,         # caller sets context window per agent complexity
            'num_predict': num_predict, # caller sets generation budget; verbose agents need more headroom
        },
    }).encode()
    req = urllib.request.Request(
        f'{OLLAMA_HOST}/api/chat',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = _json.loads(resp.read().decode())
            return data['message']['content']
    except Exception as e:
        raise RuntimeError(f'Ollama API call failed: {e}') from e



def _call_model_mock(payload: dict) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def detect_ambiguity(execution_input: dict) -> dict:
    """Agent 1a — detects linguistic ambiguities only. Runs in parallel with detect_concern_mixing."""
    prompt_path = _TCC_ROOT / 'Agents/1a.AmbiguityDetector/agent_prompt.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    if LLM_PROVIDER == 'openai':
        raw = _call_model_openai(system_prompt, user_content)
    elif LLM_PROVIDER == 'ollama':
        # system_prompt alone is ~2.8k tokens (taxonomy + few-shot examples);
        # num_ctx must cover prompt + user_content + num_predict or smaller
        # models silently drop the output-format instructions and fall back
        # to a schema of their own invention. num_predict is bumped too:
        # requirements with several concurrent ambiguities (e.g. compound
        # conditionals) produce long enough YAML to hit the default 1500-token
        # cap mid-string, which truncates the response into invalid YAML.
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=3000)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'ambiguity_detection': {'has_ambiguity': False, 'ambiguities': []}})

    parsed = _parse_yaml_block(raw, 'ambiguity_detection')
    if parsed is not None:
        return {'ambiguity_detection': parsed['ambiguity_detection']}

    return {
        'ambiguity_detection': {
            'has_ambiguity': False,
            'ambiguities': [],
            'no_ambiguity_reason': 'model_output_unexpected_or_unparsable'
        },
        'model_raw': raw if raw is not None else ''
    }


def detect_concern_mixing(execution_input: dict) -> dict:
    """Agent 1b — detects concern mixing only. Runs in parallel with detect_ambiguity."""
    prompt_path = _TCC_ROOT / 'Agents/1b.ConcernMixingDetector/agent_prompt.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    if LLM_PROVIDER == 'openai':
        raw = _call_model_openai(system_prompt, user_content)
    elif LLM_PROVIDER == 'ollama':
        # same context-truncation risk as Agent 1a — see note there
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=4096)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'concern_mixing_detection': {'has_concern_mixing': False,
                                                              'functional_action': None,
                                                              'quality_criterion': None,
                                                              'explanation': None}})

    parsed = _parse_yaml_block(raw, 'concern_mixing_detection')
    if parsed is not None:
        return {'concern_mixing_detection': parsed['concern_mixing_detection']}

    return {
        'concern_mixing_detection': {
            'has_concern_mixing': False,
            'functional_action': None,
            'quality_criterion': None,
            'explanation': None
        },
        'model_raw': raw if raw is not None else ''
    }


def validate_resolubility(execution_input: dict, ambiguity_detection: dict) -> dict:
    prompt_path = _TCC_ROOT / 'Agents/2.ResolubilityCheck/agent_prompt.md'
    system_prompt = _load_prompt(prompt_path)

    # Agent 2 receives only Agent 1a output — concern mixing is handled separately by Agent 1b
    amb_block = ambiguity_detection.get('ambiguity_detection', ambiguity_detection)
    payload = {
        'execution_input': {
            'context_condition': execution_input.get('context_condition', ''),
            'base_requirement_text': execution_input.get('base_requirement_text', ''),
            'controlled_context': execution_input.get('controlled_context', {}),
        },
        'ambiguity_detection': {k: v for k, v in amb_block.items() if k != 'has_concern_mixing'}
    }

    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    # Agent 2 receives requirement + context + Agent 1 output — needs larger ctx.
    # prompt alone is ~2.4k tokens; C2 controlled_context + a multi-ambiguity
    # Agent 1 block can add several hundred more. num_predict is also bumped:
    # a single ambiguity's justification can run 1000+ tokens on its own when
    # the model reasons at length, so the default 1500 cap can truncate
    # mid-string on cases with 2+ ambiguities to resolve.
    if LLM_PROVIDER == 'openai':
        raw = _call_model_openai(system_prompt, user_content)
    elif LLM_PROVIDER == 'ollama':
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=2500)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'contextual_resolubility_validation': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'has_ambiguity': False,
            'validation_summary': 'mocked',
            'ambiguity_resolubility': [],
            'overall_resolubility': {'status': 'no_ambiguity', 'explanation': ''}
        }})

    parsed = _parse_yaml_block(raw, 'contextual_resolubility_validation')
    if parsed is not None:
        # Enforce correct IDs
        crv = parsed['contextual_resolubility_validation']
        if isinstance(crv, dict):
            crv['execution_id'] = execution_input.get('execution_id')
            crv['requirement_id'] = execution_input.get('requirement_id')
            crv['context_condition'] = execution_input.get('context_condition')
        return parsed
    return {
        'contextual_resolubility_validation': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'has_ambiguity': False,
            'validation_summary': 'Model returned unparsable or invalid response',
            'ambiguity_resolubility': [],
            'overall_resolubility': {'status': 'non_resolvable', 'explanation': 'parsing_error'}
        },
        'model_raw': raw if raw is not None else ''
    }


def structure_requirement(execution_input: dict, concern_mixing: dict, resolubility: dict) -> dict:
    prompt_path = _TCC_ROOT / 'Agents/3.Structurer/agent_prompt.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {
        'context_condition': execution_input.get('context_condition', ''),
        'base_requirement_text': execution_input.get('base_requirement_text', ''),
        'controlled_context': execution_input.get('controlled_context', {}),
        'concern_mixing_detection': concern_mixing.get('concern_mixing_detection', concern_mixing),
        'contextual_resolubility_validation': resolubility.get('contextual_resolubility_validation', resolubility)
    }

    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    # Agent 3 receives requirement + context + Agent 2 output — needs larger ctx
    if LLM_PROVIDER == 'openai':
        raw = _call_model_openai(system_prompt, user_content)
    elif LLM_PROVIDER == 'ollama':
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'requirement_structuring': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'structuring_summary': 'mocked',
            'structured_requirements': [],
            'unresolved_ambiguities': [],
            'final_output_status': 'preserved'
        }})

    parsed = _parse_yaml_block(raw, 'requirement_structuring')
    if parsed is not None:
        # Enforce correct IDs — models sometimes invent their own
        rs = parsed['requirement_structuring']
        if isinstance(rs, dict):
            rs['execution_id'] = execution_input.get('execution_id')
            rs['requirement_id'] = execution_input.get('requirement_id')
            rs['context_condition'] = execution_input.get('context_condition')
        return parsed
    return {
        'requirement_structuring': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'structuring_summary': 'Model returned unparsable or invalid response',
            'structured_requirements': [],
            'unresolved_ambiguities': [],
            'final_output_status': 'partially_structured'
        },
        'model_raw': raw if raw is not None else ''
    }
