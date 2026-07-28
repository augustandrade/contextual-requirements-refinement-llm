import os
from pathlib import Path

import yaml

from yaml_parser import parse_yaml_block


class AgentParseError(RuntimeError):
    """Raised when an agent's model response cannot be parsed as valid YAML.

    Callers must catch this, log req_id/ctx and self.raw, skip the execution,
    and rely on --resume to retry. Do NOT fall back to a placeholder result.
    """
    def __init__(self, agent: str, raw: str, parse_err=None):
        reason = f': {parse_err}' if parse_err else ''
        super().__init__(f'{agent}: model response unparsable{reason}')
        self.agent = agent
        self.raw = raw
        self.parse_err = parse_err

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3.5:latest')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '600'))

# Base directory for resolving agent prompts (TCC root)
_TCC_ROOT = Path(__file__).parent.parent


def ensure_ollama_running(timeout: int = 30) -> None:
    """Start Ollama if not already running, then block until ready.

    Pings OLLAMA_HOST/api/tags. If unreachable, launches `ollama serve`
    as a background process and polls until the server responds or timeout
    expires. Safe to call when Ollama is already up — it returns immediately.
    """
    import subprocess
    import time
    import urllib.request as _urlreq

    health_url = f'{OLLAMA_HOST}/api/tags'

    try:
        _urlreq.urlopen(health_url, timeout=3)
        return  # already running
    except Exception:
        pass

    print('Ollama não está rodando — iniciando servidor...', flush=True)
    subprocess.Popen(
        ['ollama', 'serve'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _urlreq.urlopen(health_url, timeout=2)
            print('Ollama pronto.', flush=True)
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError(
        f'Ollama não respondeu após {timeout}s. '
        'Verifique se está instalado e se o modelo está disponível.'
    )


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

    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=3000)

    parsed, parse_err = parse_yaml_block(raw, 'ambiguity_detection')
    if parsed is not None:
        ad = parsed['ambiguity_detection']
        if not isinstance(ad, dict):
            raise AgentParseError('detect_ambiguity', raw,
                                  f"root key 'ambiguity_detection' is not a dict (got {type(ad).__name__})")
        return {'ambiguity_detection': ad}
    raise AgentParseError('detect_ambiguity', raw, parse_err)


def detect_concern_mixing(execution_input: dict) -> dict:
    """Agent 1b — detects concern mixing only. Runs in parallel with detect_ambiguity."""
    prompt_path = _TCC_ROOT / 'Agents/1b_concern_mixing_detector.md'
    system_prompt = _load_prompt(prompt_path)

    payload = {'base_requirement_text': execution_input.get('base_requirement_text', '')}
    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192)

    parsed, parse_err = parse_yaml_block(raw, 'concern_mixing_detection')
    if parsed is not None:
        cmd = parsed['concern_mixing_detection']
        if not isinstance(cmd, dict):
            raise AgentParseError('detect_concern_mixing', raw,
                                  f"root key 'concern_mixing_detection' is not a dict (got {type(cmd).__name__})")
        return {'concern_mixing_detection': cmd}
    raise AgentParseError('detect_concern_mixing', raw, parse_err)


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

    parsed, parse_err = parse_yaml_block(raw, 'contextual_resolubility_validation')
    if parsed is None:
        raise AgentParseError('validate_resolubility', raw, parse_err)
    crv = parsed['contextual_resolubility_validation']
    if not isinstance(crv, dict):
        raise AgentParseError('validate_resolubility', raw, parse_err)
    crv['execution_id'] = execution_input.get('execution_id')
    crv['requirement_id'] = execution_input.get('requirement_id')
    return parsed


def structure_requirement(execution_input: dict, concern_mixing: dict, resolubility: dict) -> dict:
    prompt_path = _TCC_ROOT / 'Agents/3_structurer.md'
    system_prompt = _load_prompt(prompt_path)

    # Filter resolubility block to only the fields Agent 3's input schema expects
    _crv_keep = {'ambiguity_id', 'fragment', 'resolubility_status', 'supported_interpretation'}
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

    _cmd_keep = {'has_concern_mixing', 'functional_action', 'quality_criterion'}
    cmd_raw = concern_mixing.get('concern_mixing_detection', concern_mixing)
    payload['concern_mixing_detection'] = {k: v for k, v in cmd_raw.items() if k in _cmd_keep}
    payload['contextual_resolubility_validation'] = filtered_crv

    user_content = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    # Agent 3 receives requirement + context + Agent 2 output — needs larger ctx
    raw = _call_model_ollama(system_prompt, user_content, num_ctx=8192, num_predict=2500)

    parsed, parse_err = parse_yaml_block(raw, 'requirement_structuring')
    if parsed is None:
        raise AgentParseError('structure_requirement', raw, parse_err)
    rs = parsed['requirement_structuring']
    if not isinstance(rs, dict):
        raise AgentParseError('structure_requirement', raw, parse_err)
    rs['execution_id'] = execution_input.get('execution_id')
    rs['requirement_id'] = execution_input.get('requirement_id')
    rs['context_condition'] = execution_input.get('context_condition')
    return parsed
