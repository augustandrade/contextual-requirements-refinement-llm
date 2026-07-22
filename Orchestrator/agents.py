import os
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


def _call_model_ollama(system_prompt: str, user_content: str, timeout: int = None, num_ctx: int = 2048):
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
            'num_ctx': num_ctx,    # caller sets context window per agent complexity
            'num_predict': 1500,   # YAML responses stay well under this limit
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
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=2048)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'ambiguity_detection': {'has_ambiguity': False, 'ambiguities': []}})

    try:
        parsed = yaml.safe_load(_strip_markdown_fence(raw))
    except Exception:
        parsed = None

    if isinstance(parsed, dict) and 'ambiguity_detection' in parsed:
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
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=2048)
    elif LLM_PROVIDER == 'local':
        raw = _call_model_local(system_prompt, user_content)
    else:
        raw = _call_model_mock({'concern_mixing_detection': {'has_concern_mixing': False,
                                                              'functional_action': None,
                                                              'quality_criterion': None,
                                                              'explanation': None}})

    try:
        parsed = yaml.safe_load(_strip_markdown_fence(raw))
    except Exception:
        parsed = None

    if isinstance(parsed, dict) and 'concern_mixing_detection' in parsed:
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
    # Agent 2 receives requirement + context + Agent 1 output — needs larger ctx
    if LLM_PROVIDER == 'openai':
        raw = _call_model_openai(system_prompt, user_content)
    elif LLM_PROVIDER == 'ollama':
        raw = _call_model_ollama(system_prompt, user_content, num_ctx=4096)
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

    try:
        parsed = yaml.safe_load(_strip_markdown_fence(raw))
        if isinstance(parsed, dict) and 'contextual_resolubility_validation' in parsed:
            # Enforce correct IDs
            crv = parsed['contextual_resolubility_validation']
            if isinstance(crv, dict):
                crv['execution_id'] = execution_input.get('execution_id')
                crv['requirement_id'] = execution_input.get('requirement_id')
                crv['context_condition'] = execution_input.get('context_condition')
            return parsed
    except Exception:
        pass
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

    try:
        parsed = yaml.safe_load(_strip_markdown_fence(raw))
        if isinstance(parsed, dict) and 'requirement_structuring' in parsed:
            # Enforce correct IDs — models sometimes invent their own
            rs = parsed['requirement_structuring']
            if isinstance(rs, dict):
                rs['execution_id'] = execution_input.get('execution_id')
                rs['requirement_id'] = execution_input.get('requirement_id')
                rs['context_condition'] = execution_input.get('context_condition')
            return parsed
    except Exception:
        pass
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
