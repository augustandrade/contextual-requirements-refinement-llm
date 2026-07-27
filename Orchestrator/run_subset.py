#!/usr/bin/env python3
"""Run one example per corpus category through the pipeline (for quick checks).

Usage:
  python3 run_subset.py
  OLLAMA_MODEL=qwen3.5:9b python3 run_subset.py
  OLLAMA_MODEL=qwen3.5:9b python3 run_subset.py --label quick-check
"""
import argparse
from pathlib import Path
import yaml
import json
import agents as agents_mod
import run_pipeline as rp


def pick_context(item: dict):
    contexts = item.get('contexts', {})
    # prefer a context with inject_context true
    for k, v in contexts.items():
        if isinstance(v, dict) and v.get('inject_context'):
            return k, v
    # fallback to first context
    if contexts:
        k = list(contexts.keys())[0]
        return k, contexts[k]
    return 'C0', {'inject_context': False}


def to_execution_input(item: dict, context_key: str, context_val: dict):
    execution_id = f"{item.get('id')}/{context_key}"
    controlled_context = context_val.get('controlled_context') if context_val.get('inject_context') else {}
    return {
        'execution_id': execution_id,
        'requirement_id': item.get('id'),
        'context_condition': context_key,
        'base_requirement_text': item.get('base_requirement_text'),
        'controlled_context': controlled_context
    }


def main():
    parser = argparse.ArgumentParser(description='Executa um subset do corpus (um req por categoria).')
    parser.add_argument('--label', default='', help='Label opcional para identificar a run (ex: "subset-test")')
    args = parser.parse_args()

    run_dir = rp.make_run_dir(label=args.label or 'subset')
    rp.write_run_metadata(run_dir, extra={'corpus': 'subset', 'label': args.label or None})
    print(f'Run iniciada: {run_dir.name}')

    corpus_dir = Path(__file__).parent.parent / 'corpus'
    categories = sorted([p for p in corpus_dir.iterdir() if p.is_dir()])
    summary = []

    for cat in categories:
        files = sorted(cat.glob('*.yaml'))
        if not files:
            continue
        item = yaml.safe_load(files[0].read_text(encoding='utf-8'))
        ctx_key, ctx_val = pick_context(item)
        exec_input = to_execution_input(item, ctx_key, ctx_val)

        print('Running:', exec_input['requirement_id'], exec_input['context_condition'])
        amb = agents_mod.detect_ambiguity(exec_input)
        cm = agents_mod.detect_concern_mixing(exec_input)
        has_ambiguity = amb.get('ambiguity_detection', {}).get('has_ambiguity', False)
        if has_ambiguity:
            res = agents_mod.validate_resolubility(exec_input, amb)
        else:
            res = rp.build_synthetic_resolubility(exec_input)
        if rp.should_invoke_structurer(res):
            struct = agents_mod.structure_requirement(exec_input, cm, res)
        else:
            struct = rp.build_non_resolvable_structuring(exec_input)
        final = rp.run_output_consolidator(exec_input, amb, cm, res, struct)

        rp.save_outputs(run_dir, exec_input['execution_id'], exec_input, amb, cm, res, struct, final)
        summary.append({
            'requirement_id': exec_input['requirement_id'],
            'context': exec_input['context_condition'],
            'status': 'done'
        })

    print(f'\nConcluído. Run: {run_dir.name}')
    print(f'Saídas em: {run_dir}')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
