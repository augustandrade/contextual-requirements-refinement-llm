#!/usr/bin/env python3
"""
Processador de corpus: itera sobre o manifesto e executa o pipeline para cada requisito e contexto.

Uso:
  python3 process_corpus.py                                   # corpus completo (42 execuções)
  python3 process_corpus.py --subset                          # 1 req por categoria, 1 contexto (~4 execuções)
  python3 process_corpus.py --manifest pilot-manifest.yaml   # corpus piloto (12 execuções)
  python3 process_corpus.py --req REQ-PILOT-04               # requisito específico (3 execuções)
  python3 process_corpus.py --req REQ-01 REQ-02              # múltiplos requisitos
  python3 process_corpus.py --resume run_001__...             # retoma run interrompida
  OLLAMA_MODEL=qwen3.5:9b python3 process_corpus.py --label pilot-v1

Requisitos: `pyyaml` (instalar via `pip install pyyaml`) ou `pip install -r requirements.txt`.
"""
import argparse
from pathlib import Path
import sys
import yaml

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
import run_pipeline as rp
from agents import ensure_ollama_running

BASE = _HERE.parent / 'corpus'
MANIFEST = BASE / 'manifest.yaml'


def _log_agent_error(req_id: str, ctx, exc: Exception) -> None:
    location = f'{req_id}/{ctx}' if ctx else req_id
    lines = [f'[ERROR] {location} — {exc}']
    if isinstance(exc, rp.AgentParseError):
        lines.append(f'  agent : {exc.agent}')
        if exc.parse_err:
            lines.append(f'  reason: {exc.parse_err}')
        lines.append(f'  raw   : {exc.raw[:400]!r}')
    action = 'skipping all contexts' if ctx is None else 'skipping'
    lines.append(f'  → {action} — use --resume to retry')
    print('\n'.join(lines), file=sys.stderr)


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
    return (run_dir / req_id / ctx / 'final_output.json').exists()


def _pick_context(contexts: dict) -> str:
    """Pick best single context for subset runs: prefer inject_context=True, fallback to first."""
    for k, v in contexts.items():
        if isinstance(v, dict) and v.get('inject_context'):
            return k
    return list(contexts.keys())[0] if contexts else 'C0'


def process_item(item, run_dir: Path, contexts: list = None):
    file_rel = item.get('file')
    req_path = BASE / file_rel
    data = load_yaml(req_path)
    if not data:
        return
    req_id    = data.get('id')
    title     = data.get('title', '')
    category  = data.get('category_name', data.get('category_id', ''))
    base_text = data.get('base_requirement_text')

    _ctxs = contexts or ['C0', 'C1', 'C2']
    pending = [ctx for ctx in _ctxs if not _already_done(run_dir, req_id, ctx)]
    if not pending:
        print(f'  {req_id}  skipped (already complete)')
        return

    # Agent 1 is context-free — run once per requirement and reuse across contexts.
    req_input = {'base_requirement_text': base_text}
    try:
        amb = rp.run_ambiguity_detector(req_input)
    except (rp.AgentParseError, RuntimeError) as e:
        _log_agent_error(req_id, None, e)
        return

    req_dir       = run_dir / req_id
    has_ambiguity = amb.get('ambiguity_detection', {}).get('has_ambiguity', False)
    amb_tag       = 'ambiguous' if has_ambiguity else 'no ambiguity'
    print(f'\n{req_id}  {amb_tag}')
    print(f'  {"ctx":<4}  {"agent-2":<18}  {"route":<10}  {"agent-3":<8}  output')

    # Save Agent 1 input/output once at the requirement level.
    rp.save_req_outputs(req_dir, req_input, amb)

    # Context only matters when there is ambiguity to resolve. Non-ambiguous
    # requirements run a single canonical pass (C0, no context injection).
    ctxs_to_run = _ctxs if has_ambiguity else ['C0']

    for ctx in ctxs_to_run:
        if _already_done(run_dir, req_id, ctx):
            print(f'  {ctx:<4}  skipped')
            continue

        ctx_block = data.get('contexts', {}).get(ctx, {})
        inject = ctx_block.get('inject_context', False)
        controlled_context = ctx_block.get('controlled_context') if inject else {}

        execution_input = {
            'execution_id': f"{req_id}-{ctx}",
            'requirement_id': req_id,
            'context_condition': ctx,
            'base_requirement_text': base_text,
            'controlled_context': controlled_context,
        }

        a2_status = a3_status = 'error'
        res = struct = None
        try:
            if has_ambiguity:
                res         = rp.run_resolubility_validator(execution_input, amb)
                crv_raw     = res.get('contextual_resolubility_validation', {}).get('overall_resolubility', {}).get('status', '')
                known       = {'fully_resolvable', 'resolvable', 'no_ambiguity', 'not_applicable',
                               'non_resolvable', 'unresolved', 'blocking'}
                raw_status  = rp.normalize_overall_resolubility_status(res)
                a2_status   = 'unexpected' if str(crv_raw).strip().lower() not in known else raw_status
            else:
                res       = rp.build_synthetic_resolubility(execution_input)
                a2_status = '—'

            route = 'structured' if rp.should_invoke_structurer(res) else 'signaling'

            if rp.should_invoke_structurer(res):
                struct      = rp.run_requirement_structurer(execution_input, res)
                struct_reqs = struct.get('requirement_structuring', {}).get('structured_requirements') or []
                a3_status   = 'ok' if struct_reqs else 'empty'
            else:
                a3_status = '—'
        except (rp.AgentParseError, RuntimeError) as e:
            _log_agent_error(req_id, ctx, e)
            print(f'  {ctx:<4}  {a2_status:<18}  {"—":<10}  {a3_status:<8}  error')
            continue

        # Pass None for synthetic resolubility and skipped structuring — save_ctx_outputs
        # omits those files so absence signals the agent was not invoked.
        r_to_save = res if has_ambiguity else None
        s_to_save = struct

        final         = rp.run_output_consolidator(execution_input, amb, res, struct)
        output_status = 'error'
        try:
            rp.save_ctx_outputs(req_dir / ctx, controlled_context, r_to_save, s_to_save, final)
            output_status = 'saved' if (req_dir / ctx / 'final_output.json').exists() else 'error'
        except Exception as e:
            print(f'[ERROR] {req_id}/{ctx} — failed to save outputs: {e}', file=sys.stderr)
        print(f'  {ctx:<4}  {a2_status:<18}  {route:<10}  {a3_status:<8}  {output_status}')


def main():
    parser = argparse.ArgumentParser(description='Processa corpus em uma nova run.')
    parser.add_argument('--label',    default='', help='Label opcional para a run (ex: "prompt-v2")')
    parser.add_argument('--manifest', default=None, help='Manifesto alternativo (relativo a corpus/). Default: manifest.yaml')
    parser.add_argument('--resume',   default='', help='Nome da run a retomar (ex: run_002__qwen3.5-4b__2026-06-13T10-44)')
    parser.add_argument('--subset',   action='store_true', help='Smoke test: 1 req por categoria, 1 contexto (~4 execuções)')
    parser.add_argument('--req',      nargs='+', metavar='REQ_ID', help='Rodar apenas para requisito(s) específico(s) (ex: REQ-PILOT-04)')
    args = parser.parse_args()

    ensure_ollama_running()

    manifest_path = BASE / args.manifest if args.manifest else MANIFEST

    if args.resume:
        run_dir = rp._RUNS_DIR / args.resume
        if not run_dir.exists():
            print(f'Erro: run não encontrada em {run_dir}')
            return
        print(f'Retomando run: {run_dir.name}')
    else:
        run_dir = rp.make_run_dir(label=args.label or ('subset' if args.subset else ''))
        rp.write_run_metadata(run_dir, extra={
            'corpus': str(manifest_path.name),
            'label': args.label or None,
            'subset': args.subset or None,
        })
        print(f'Run iniciada: {run_dir.name}')

    manifest = load_yaml(manifest_path)
    if not manifest:
        print('Erro: manifesto não encontrado em', MANIFEST)
        return

    items = manifest.get('items', [])

    if args.req:
        req_set = set(args.req)
        items = [it for it in items if it.get('id') in req_set]
        if not items:
            print(f'Erro: nenhum item encontrado para {args.req}')
            return

    if args.subset:
        # Pick the first req_id from each category, one context per item
        first_per_cat = {}
        for cat in manifest.get('methodology', {}).get('categories', []):
            req_ids = cat.get('req_ids', [])
            if req_ids:
                first_per_cat[cat['id']] = req_ids[0]
        subset_ids = set(first_per_cat.values())
        items = [it for it in items if it.get('id') in subset_ids]

        for it in items:
            data = load_yaml(BASE / it['file'])
            if not data:
                continue
            ctx = _pick_context(data.get('contexts', {}))
            process_item(it, run_dir, contexts=[ctx])
    else:
        for it in items:
            process_item(it, run_dir)

    print(f'\nConcluído. Saídas em: {run_dir}')


if __name__ == '__main__':
    main()
