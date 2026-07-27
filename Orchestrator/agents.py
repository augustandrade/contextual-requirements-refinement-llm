import os
import sys
from pathlib import Path

import yaml

from yaml_parser import parse_yaml_block

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:latest')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '600'))

# Base directory for resolving agent prompts (TCC root)
_TCC_ROOT = Path(__file__).parent.parent


def _load_prompt(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


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


def detect_ambiguity(execution_input: dict) -> dict:
    """Agent 1a — detects linguistic ambiguities only. Runs in parallel with detect_concern_mixing."""
    prompt_path = _TCC_ROOT / 'Agents/1a_ambiguity_detector.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    # system_prompt alone is ~2.8k tokens (taxonomy + few-shot examples);
    # num_ctx must cover prompt + user_content + num_predict or smaller
    # models silently drop the output-format instructions and fall back
    # to a schema of their own invention. num_predict is bumped too:
    # requirements with several concurrent ambiguities (e.g. compound
    # conditionals) produce long enough YAML to hit the default 1500-token
    # cap mid-string, which truncates the response into invalid YAML.
    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=3000)

    parsed = parse_yaml_block(raw, 'ambiguity_detection')
    if parsed is not None:
        return {'ambiguity_detection': parsed['ambiguity_detection']}

    print('[WARN] detect_ambiguity: parse failed — routing as no_ambiguity (Agent 2 will be skipped)', file=sys.stderr)
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
    prompt_path = _TCC_ROOT / 'Agents/1b_concern_mixing_detector.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    # same context-truncation risk as Agent 1a — see note there
    raw = _call_model_ollama(system_prompt, user_content, num_ctx=4096)

    parsed = parse_yaml_block(raw, 'concern_mixing_detection')
    if parsed is not None:
        return {'concern_mixing_detection': parsed['concern_mixing_detection']}

    print('[WARN] detect_concern_mixing: parse failed — routing as no_concern_mixing (D2 may record false negative)', file=sys.stderr)
    return {
        'concern_mixing_detection': {
            'has_concern_mixing': False,
            'functional_action': None,
            'quality_criterion': None,
            'explanation': None,
            'no_concern_mixing_reason': 'model_output_unparsable'
        },
        'model_raw': raw if raw is not None else ''
    }


def validate_resolubility(execution_input: dict, ambiguity_detection: dict) -> dict:
    prompt_path = _TCC_ROOT / 'Agents/2_resolubility_check.md'
    system_prompt = _load_prompt(prompt_path)

    # Agent 2 receives only Agent 1a output — concern mixing is handled separately by Agent 1b
    amb_block = ambiguity_detection.get('ambiguity_detection', ambiguity_detection)
    payload_exec = {
        'base_requirement_text': execution_input.get('base_requirement_text', ''),
    }
    ctx = execution_input.get('controlled_context') or {}
    if ctx:
        payload_exec['controlled_context'] = ctx

    _amb_keep = {'ambiguity_id', 'fragment', 'ambiguity_type', 'explanation', 'possible_interpretations'}
    filtered_ambiguities = [
        {k: v for k, v in amb.items() if k in _amb_keep}
        for amb in amb_block.get('ambiguities', [])
    ]

    payload = {
        'execution_input': payload_exec,
        'ambiguity_detection': {'ambiguities': filtered_ambiguities},
    }

    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    # Agent 2 receives requirement + context + Agent 1 output — needs larger ctx.
    # prompt alone is ~2.4k tokens; C2 controlled_context + a multi-ambiguity
    # Agent 1 block can add several hundred more. num_predict is also bumped:
    # a single ambiguity's justification can run 1000+ tokens on its own when
    # the model reasons at length, so the default 1500 cap can truncate
    # mid-string on cases with 2+ ambiguities to resolve.
    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=2500)

    parsed = parse_yaml_block(raw, 'contextual_resolubility_validation')
    if parsed is not None:
        # Enforce correct IDs
        crv = parsed['contextual_resolubility_validation']
        if isinstance(crv, dict):
            crv['execution_id'] = execution_input.get('execution_id')
            crv['requirement_id'] = execution_input.get('requirement_id')
            return parsed
        print(f'[WARN] validate_resolubility: root key type={type(crv).__name__}, treating as parse_error', file=sys.stderr)
    return {
        'contextual_resolubility_validation': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'ambiguity_resolubility': [],
            'overall_resolubility': {'status': 'parse_error'}
        },
        'model_raw': raw if raw is not None else ''
    }


def structure_requirement(execution_input: dict, concern_mixing: dict, resolubility: dict) -> dict:
    prompt_path = _TCC_ROOT / 'Agents/3_structurer.md'
    system_prompt = _load_prompt(prompt_path)

    # Filter resolubility block to only the fields Agent 3's input schema expects
    _crv_keep = {'ambiguity_id', 'fragment', 'supported_interpretation', 'allowed_structuring_action'}
    crv_raw = resolubility.get('contextual_resolubility_validation', {})
    filtered_ambs = [
        {k: v for k, v in item.items() if k in _crv_keep}
        for item in (crv_raw.get('ambiguity_resolubility') or [])
    ]
    filtered_crv = {}
    if filtered_ambs:
        filtered_crv['ambiguity_resolubility'] = filtered_ambs
    filtered_crv['overall_resolubility'] = {
        'status': crv_raw.get('overall_resolubility', {}).get('status', 'no_ambiguity')
    }

    ctx = execution_input.get('controlled_context') or {}
    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    if ctx:
        payload['controlled_context'] = ctx
    payload['concern_mixing_detection'] = concern_mixing.get('concern_mixing_detection', concern_mixing)
    payload['contextual_resolubility_validation'] = filtered_crv

    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    # Agent 3 receives requirement + context + Agent 2 output — needs larger ctx
    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192)

    parsed = parse_yaml_block(raw, 'requirement_structuring')
    if parsed is not None:
        # Enforce correct IDs — models sometimes invent their own
        rs = parsed['requirement_structuring']
        if isinstance(rs, dict):
            rs['execution_id'] = execution_input.get('execution_id')
            rs['requirement_id'] = execution_input.get('requirement_id')
            rs['context_condition'] = execution_input.get('context_condition')
            return parsed
        print(f'[WARN] structure_requirement: root key type={type(rs).__name__}, treating as parse_error', file=sys.stderr)
    return {
        'requirement_structuring': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'structuring_summary': 'Model returned unparsable or invalid response',
            'structured_requirements': [],
            'unsupported_inferences_avoided': [],
            'final_output_status': 'parse_error'
        },
        'model_raw': raw if raw is not None else ''
    }
