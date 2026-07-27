#!/usr/bin/env python3
"""
Processador de corpus: itera sobre o manifesto e executa o orquestrador para cada requisito e condição de contexto.

Cada execução é salva em uma run identificada por modelo e timestamp:
  outputs/runs/run_<NNN>__<model>__<timestamp>/

Uso:
  python3 process_corpus.py
  python3 process_corpus.py --manifest pilot-manifest.yaml
  OLLAMA_MODEL=qwen3.5:9b python3 process_corpus.py
  OLLAMA_MODEL=qwen3.5:9b python3 process_corpus.py --manifest pilot-manifest.yaml --label pilot-v1

Requisitos: `pyyaml` (instalar via `pip install pyyaml`) ou `pip install -r requirements.txt`.
"""
import argparse
from pathlib import Path
import sys
import yaml

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import run_pipeline as rp

BASE = _HERE.parent / 'corpus'
MANIFEST = BASE / 'manifest.yaml'


def load_yaml(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print('Warning: file not found', path)
        return None
    except yaml.YAMLError as e:
        print('Warning: YAML parse error in', path, '-', e)
        return None


def _already_done(run_dir: Path, req_id: str, ctx: str) -> bool:
    return (run_dir / req_id / ctx / '05_final_output.json').exists()


def process_item(item, run_dir: Path):
    file_rel = item.get('file')
    req_path = BASE / file_rel
    data = load_yaml(req_path)
    if not data:
        return
    req_id = data.get('id')
    base_text = data.get('base_requirement_text')

    pending = [ctx for ctx in ['C0', 'C1', 'C2'] if not _already_done(run_dir, req_id, ctx)]
    if not pending:
        print(f'Skipped {req_id} (already complete)')
        return

    # Agents 1a and 1b receive only base_requirement_text (no context) — their
    # output is identical across C0/C1/C2 for the same requirement. Run once and
    # reuse to avoid redundant model calls.
    detection_input = {'base_requirement_text': base_text}
    amb = rp.run_ambiguity_detector(detection_input)
    cm = rp.run_concern_mixing_detector(detection_input)

    for ctx in ['C0', 'C1', 'C2']:
        if _already_done(run_dir, req_id, ctx):
            print(f'Skipped {req_id} {ctx} (already complete)')
            continue

        ctx_block = data.get('contexts', {}).get(ctx, {})
        inject = ctx_block.get('inject_context', False)
        controlled_context = ctx_block.get('controlled_context') if inject else {}

        execution_input = {
            'execution_id': f"{req_id}-{ctx}",
            'requirement_id': req_id,
            'context_condition': ctx,
            'base_requirement_text': base_text,
            'controlled_context': controlled_context
        }

        has_ambiguity = amb.get('ambiguity_detection', {}).get('has_ambiguity', False)
        if has_ambiguity:
            res = rp.run_resolubility_validator(execution_input, amb)
        else:
            res = rp.build_synthetic_resolubility(execution_input)

        if rp.should_invoke_structurer(res):
            struct = rp.run_requirement_structurer(execution_input, cm, res)
        else:
            struct = rp.build_non_resolvable_structuring(execution_input)

        final = rp.run_output_consolidator(execution_input, amb, cm, res, struct)
        rp.save_outputs(run_dir, f"{req_id}/{ctx}", execution_input, amb, cm, res, struct, final)
        print('Processed', req_id, ctx)


def main():
    parser = argparse.ArgumentParser(description='Processa corpus completo em uma nova run.')
    parser.add_argument('--label',    default='', help='Label opcional para identificar a run (ex: "prompt-v2")')
    parser.add_argument('--manifest', default=None, help='Manifesto alternativo (relativo a corpus/). Default: manifest.yaml')
    parser.add_argument('--resume',   default='', help='Nome da run a retomar (ex: run_002__qwen3.5-4b__2026-06-13T10-44)')
    args = parser.parse_args()

    manifest_path = BASE / args.manifest if args.manifest else MANIFEST

    if args.resume:
        run_dir = rp._RUNS_DIR / args.resume
        if not run_dir.exists():
            print(f'Erro: run não encontrada em {run_dir}')
            return
        print(f'Retomando run: {run_dir.name}')
    else:
        run_dir = rp.make_run_dir(label=args.label)
        rp.write_run_metadata(run_dir, extra={'corpus': str(manifest_path.name), 'label': args.label or None})
        print(f'Run iniciada: {run_dir.name}')

    manifest = load_yaml(manifest_path)
    if not manifest:
        print('Erro: manifesto não encontrado em', MANIFEST)
        return

    items = manifest.get('items', [])
    for it in items:
        process_item(it, run_dir)

    print(f'\nConcluído. Saídas em: {run_dir}')


if __name__ == '__main__':
    main()
