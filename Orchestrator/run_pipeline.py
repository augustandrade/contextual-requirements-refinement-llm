"""Pipeline library: stages, routing, output saving.

Imported by process_corpus.py — not executed directly.
"""
import json
import re
from datetime import datetime
from pathlib import Path
import sys

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import agents as agents_mod

AgentParseError = agents_mod.AgentParseError

_OUTPUTS_DIR = _HERE / 'outputs'
_RUNS_DIR = _OUTPUTS_DIR / 'runs'


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def _slug(s: str) -> str:
    """Converte string para formato seguro em nome de diretório."""
    return re.sub(r'[^a-zA-Z0-9._-]', '-', s)


def make_run_dir(label: str = '') -> Path:
    """Cria e retorna o diretório da run com ID sequencial + modelo + timestamp."""
    ensure_dir(_RUNS_DIR)
    # Calcular próximo número sequencial
    existing = sorted([p.name for p in _RUNS_DIR.iterdir() if p.is_dir()])
    next_n = len(existing) + 1
    model_slug = _slug(agents_mod.OLLAMA_MODEL)
    ts = datetime.now().strftime('%Y-%m-%dT%H-%M')
    suffix = f'__{_slug(label)}' if label else ''
    run_name = f'run_{next_n:03d}__{model_slug}__{ts}{suffix}'
    run_dir = _RUNS_DIR / run_name
    ensure_dir(run_dir)
    return run_dir


def write_run_metadata(run_dir: Path, extra: dict = None):
    """Salva metadados da run: modelo, provider, temperatura, timestamp."""
    metadata = {
        'run_id': run_dir.name,
        'model': agents_mod.OLLAMA_MODEL,
        'provider': 'ollama',
        'ollama_host': agents_mod.OLLAMA_HOST,
        'temperature': 0.0,
        'think': False,
        'started_at': datetime.now().isoformat(),
    }
    if extra:
        metadata.update(extra)
    (run_dir / 'run_metadata.json').write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False)
    )


def load_requirement(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_ambiguity_detector(execution_input: dict):
    """Agent 1a — linguistic ambiguity detection."""
    return agents_mod.detect_ambiguity(execution_input)


def run_concern_mixing_detector(execution_input: dict):
    """Agent 1b — concern mixing detection. Runs in parallel with Agent 1a."""
    return agents_mod.detect_concern_mixing(execution_input)


def build_synthetic_resolubility(execution_input: dict) -> dict:
    """Orchestrator synthetic block when has_ambiguity: false — bypasses Agent 2."""
    return {
        'contextual_resolubility_validation': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'ambiguity_resolubility': [],
            'overall_resolubility': {'status': 'no_ambiguity'}
        }
    }


def run_resolubility_validator(execution_input: dict, ambiguity_detection: dict):
    """Agent 2 — resolubility validation. Called only when has_ambiguity: true."""
    return agents_mod.validate_resolubility(execution_input, ambiguity_detection)


def run_requirement_structurer(execution_input: dict, concern_mixing: dict, resolubility: dict):
    """Agent 3 — requirement structuring. Receives both Agent 1b and Agent 2 outputs."""
    return agents_mod.structure_requirement(execution_input, concern_mixing, resolubility)


def normalize_overall_resolubility_status(res_out: dict) -> str:
    raw_status = (
        res_out.get('contextual_resolubility_validation', {})
        .get('overall_resolubility', {})
        .get('status', '')
    )
    status = str(raw_status).strip().lower()

    if status in {'fully_resolvable', 'resolvable'}:
        return 'fully_resolvable'
    if status in {'no_ambiguity', 'not_applicable'}:
        return 'no_ambiguity'
    if status in {'non_resolvable', 'unresolved', 'blocking'}:
        return 'non_resolvable'
    print(f'[WARN] normalize_overall_resolubility_status: status desconhecido "{status}" → non_resolvable', file=sys.stderr)
    return 'non_resolvable'


def get_has_concern_mixing(cm_out: dict) -> bool:
    return bool(
        cm_out.get('concern_mixing_detection', {})
        .get('has_concern_mixing', False)
    )


def should_invoke_structurer(res_out: dict) -> bool:
    return normalize_overall_resolubility_status(res_out) in {'fully_resolvable', 'no_ambiguity'}


def build_non_resolvable_structuring(execution_input: dict) -> dict:
    """Orchestrator placeholder when Agent 3 is not invoked due to unresolved ambiguity."""
    return {
        'requirement_structuring': {
            'execution_id': execution_input.get('execution_id'),
            'requirement_id': execution_input.get('requirement_id'),
            'context_condition': execution_input.get('context_condition'),
            'structuring_summary': 'Structuring skipped: unresolved ambiguity requires human clarification.',
            'structured_requirements': [],
            'unsupported_inferences_avoided': [],
            'final_output_status': 'blocked'
        }
    }


def run_output_consolidator(execution_input: dict, amb_out: dict, cm_out: dict, res_out: dict, struct_out: dict):
    normalized_status = normalize_overall_resolubility_status(res_out)
    route = 'structured' if normalized_status in {'fully_resolvable', 'no_ambiguity'} else 'signaling'
    struct_out = struct_out or {}

    validation = res_out.get('contextual_resolubility_validation', {})
    ambiguity_items = validation.get('ambiguity_resolubility', []) or []
    unresolved_ambiguities = [
        item for item in ambiguity_items
        if isinstance(item, dict) and str(item.get('resolubility_status', '')).strip().lower()
        in {'unresolved', 'non_resolvable', 'blocking', 'partially_resolvable'}
    ]
    missing_information = []
    for item in unresolved_ambiguities:
        missing_information.extend(item.get('missing_information', []) or [])

    final = {
        'execution_id': execution_input.get('execution_id'),
        'requirement_id': execution_input.get('requirement_id'),
        'context_condition': execution_input.get('context_condition'),
        'input_requirement': execution_input.get('base_requirement_text'),
        'ambiguity_analysis': amb_out.get('ambiguity_detection'),
        'concern_mixing_analysis': cm_out.get('concern_mixing_detection'),
        'contextual_resolubility_analysis': res_out.get('contextual_resolubility_validation'),
        'pipeline_decision': {
            'overall_resolubility_status': normalized_status,
            'has_concern_mixing': get_has_concern_mixing(cm_out),
            'route': route,
            'structurer_invoked': route == 'structured'
        },
        'requirement_structuring': struct_out.get('requirement_structuring'),
        'non_resolvable_signal': {
            'unresolved_ambiguities': unresolved_ambiguities,
            'missing_information': missing_information,
            'requires_human_clarification': route == 'signaling'
        },
        'final_assessment_notes': (
            'Structured output generated from supported interpretation.'
            if route == 'structured'
            else 'Automatic structuring skipped due to non_resolvable ambiguity; clarification required.'
        )
    }
    return final


def save_outputs(base_dir: Path, execution_id: str, execution_input: dict, a, cm, r, s, final):
    outdir = base_dir / execution_id
    ensure_dir(outdir)
    (outdir / '01_input.json').write_text(json.dumps(execution_input, indent=2, ensure_ascii=False))
    (outdir / '02a_ambiguity_detection.json').write_text(json.dumps(a, indent=2, ensure_ascii=False))
    (outdir / '02b_concern_mixing_detection.json').write_text(json.dumps(cm, indent=2, ensure_ascii=False))
    (outdir / '03_resolubility_validation.json').write_text(json.dumps(r, indent=2, ensure_ascii=False))
    (outdir / '04_requirement_structuring.json').write_text(json.dumps(s, indent=2, ensure_ascii=False))
    (outdir / '05_final_output.json').write_text(json.dumps(final, indent=2, ensure_ascii=False))


