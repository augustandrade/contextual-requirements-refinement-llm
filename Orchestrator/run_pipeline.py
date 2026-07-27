#!/usr/bin/env python3
"""
Protótipo de orquestrador para o pipeline de agentes descrito no TCC.

Etapas implementadas:
 - load_requirement()
 - run_ambiguity_detector()
 - run_resolubility_validator()
 - run_requirement_structurer()  # apenas quando a resolubilidade permitir
 - run_output_consolidator()  # consolidação determinística em Python

Gera arquivos em:
  outputs/runs/<run_id>/REQ-XX/CX/

Cada run é identificada por: run_<NNN>__<model>__<timestamp>
O modelo e parâmetros são lidos de agents.py em tempo de execução.

Uso: python3 run_pipeline.py
"""
import json
import re
from datetime import datetime
from pathlib import Path
import sys

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import agents as agents_mod

_OUTPUTS_DIR = _HERE / 'outputs'
_RUNS_DIR = _OUTPUTS_DIR / 'runs'
_EXAMPLE_INPUT = _HERE / 'example_input.json'


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
        'provider': agents_mod.LLM_PROVIDER,
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
    return 'non_resolvable'


def get_has_concern_mixing(cm_out: dict) -> bool:
    return bool(
        cm_out.get('concern_mixing_detection', {})
        .get('has_concern_mixing', False)
    )


def should_invoke_structurer(res_out: dict) -> bool:
    return normalize_overall_resolubility_status(res_out) in {'fully_resolvable', 'no_ambiguity'}


def build_non_resolvable_structuring(execution_input: dict, res_out: dict) -> dict:
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


def main():
    run_dir = make_run_dir()
    write_run_metadata(run_dir)

    example_path = _EXAMPLE_INPUT
    if not example_path.exists():
        print('Exemplo não encontrado:', example_path)
        return

    execution_input = load_requirement(example_path)
    execution_id = f"{execution_input.get('requirement_id')}/{execution_input.get('context_condition')}"

    # Stage 1: Agents 1a and 1b run independently (parallel by design)
    amb = run_ambiguity_detector(execution_input)
    cm = run_concern_mixing_detector(execution_input)

    # Stage 2: Agent 2 runs only when ambiguity was detected; otherwise use synthetic block
    has_ambiguity = amb.get('ambiguity_detection', {}).get('has_ambiguity', False)
    if has_ambiguity:
        res = run_resolubility_validator(execution_input, amb)
    else:
        res = build_synthetic_resolubility(execution_input)

    # Stage 3: Agent 3 runs when resolubility allows, receives both 1b and Agent 2 outputs
    if should_invoke_structurer(res):
        struct = run_requirement_structurer(execution_input, cm, res)
    else:
        struct = build_non_resolvable_structuring(execution_input, res)

    final = run_output_consolidator(execution_input, amb, cm, res, struct)
    save_outputs(run_dir, execution_id, execution_input, amb, cm, res, struct, final)
    print('Pipeline executado. Run:', run_dir.name)
    print('Saídas em', run_dir / execution_id)


if __name__ == '__main__':
    main()
