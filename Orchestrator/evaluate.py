#!/usr/bin/env python3
"""
evaluate.py — Avaliação quantitativa automatizada do pipeline.

Compara cada 05_final_output.json de um run contra a referência manual
(manual_reference) do corpus controlado em quatro dimensões binárias:

  D1  has_ambiguity_correct   detecção de ambiguidade bate com expected_resolubility
  D2  concern_mixing_correct  concern_mixing detectado apenas quando esperado
  D3  route_correct           pipeline seguiu a rota certa (structured / signaling)
  D4  output_complete         Agent 3 foi/não foi invocado conforme esperado

Campos adicionais por execução:
  d1_error_type       false_positive | false_negative | null (quando D1 correto ou N/A)
  d2_error_type       false_positive | false_negative | null (quando D2 correto)
  act_global_status   fully_resolvable | non_resolvable | no_ambiguity
  ambiguity_count     número de ambiguidades detectadas pelo Agente 1a
  decomposed          True se Agente 3 produziu 2+ artefatos (concern mixing), None se não aplicável

Score por execução = D_corretas / D_aplicáveis

Uso:
  python3 evaluate.py                          # todos os runs
  python3 evaluate.py --run run_002            # run cujo nome começa com run_002
  python3 evaluate.py --exclude run_001        # ignora run específica
"""

import json
import yaml
import csv
import sys
import argparse
from datetime import datetime
from pathlib import Path

# ── Caminhos ─────────────────────────────────────────────────────────────────
_HERE      = Path(__file__).parent
_TCC_ROOT  = _HERE.parent
_CORPUS    = _TCC_ROOT / 'corpus'
_MANIFEST  = _CORPUS / 'manifest.yaml'
_RUNS_DIR  = _HERE / 'outputs' / 'runs'

# Nomes legíveis para categorias
_CAT_LABELS = {
    'category-01-structural': 'Cat-01 Estrutural',
    'category-02-linguistic': 'Cat-02 Linguística',
    'category-03-domain':     'Cat-03 Domínio',
    'category-04-control':    'Cat-04 Controle',
}


# ── Carrega corpus ────────────────────────────────────────────────────────────
def load_corpus():
    """Retorna {req_id: corpus_doc} para todos os itens do manifest."""
    manifest = yaml.safe_load(_MANIFEST.read_text(encoding='utf-8'))
    index: dict[str, dict] = {}
    for item in manifest.get('items', []):
        path = _CORPUS / item['file']
        index[item['id']] = yaml.safe_load(path.read_text(encoding='utf-8'))
    return index


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, None)
        if d is None:
            return default
    return d if d is not None else default


def _exp_has_ambiguity(exp_res: str):
    if exp_res == 'not_applicable':
        return False
    if exp_res in ('resolvable', 'unresolved'):
        return True
    return None


def _exp_route(exp_res: str):
    if exp_res == 'unresolved':
        return 'signaling'
    if exp_res in ('resolvable', 'not_applicable'):
        return 'structured'
    return None


# ── Avalia uma execução ───────────────────────────────────────────────────────
def evaluate_one(final: dict, manual_ref: dict) -> dict:
    """
    Retorna dict com resultado de cada dimensão (True/False/None = N/A),
    score agregado e campos diagnósticos adicionais.
    """
    exp_res     = manual_ref.get('expected_resolubility', '')
    exp_actions = manual_ref.get('expected_actions', []) or []

    d1 = d2 = d3 = d4 = None
    applicable = correct = 0

    # D1 — has_ambiguity
    exp_ha = _exp_has_ambiguity(exp_res)
    act_ha = _get(final, 'ambiguity_analysis', 'has_ambiguity', default=None)
    if exp_ha is not None:
        d1 = (act_ha == exp_ha)
        applicable += 1
        correct    += int(d1)

    # D1 error type: só preenchido quando há erro
    if exp_ha is not None and d1 is False:
        d1_error_type = 'false_positive' if act_ha and not exp_ha else 'false_negative'
    else:
        d1_error_type = None

    # D2 — route
    exp_rt = _exp_route(exp_res)
    act_rt = _get(final, 'pipeline_decision', 'route', default='')
    if exp_rt is not None:
        d2 = (act_rt == exp_rt)
        applicable += 1
        correct    += int(d2)

    # D3 — completude do output (independente de D2)
    act_route = _get(final, 'pipeline_decision', 'route', default='')
    struct_reqs = _get(final, 'requirement_structuring', 'structured_requirements', default=[]) or []
    if act_route == 'structured':
        d3 = len(struct_reqs) > 0
    elif act_route == 'signaling':
        unresolved = _get(final, 'non_resolvable_signal', 'unresolved_ambiguities', default=[]) or []
        d3 = len(unresolved) > 0
    else:
        d3 = None

    if d3 is not None:
        applicable += 1
        correct    += int(d3)

    # D4 — concern_mixing (verifica tanto falsos positivos quanto falsos negativos)
    exp_cm = 'detect_concern_mixing' in exp_actions
    act_cm = bool(_get(final, 'concern_mixing_analysis', 'has_concern_mixing', default=False))
    d4 = (act_cm == exp_cm)
    applicable += 1
    correct    += int(d4)

    # D2 error type (concern mixing): só preenchido quando há erro
    d2_error_type = None if d4 else ('false_positive' if act_cm and not exp_cm else 'false_negative')

    # D3 error type (rota): só preenchido quando há erro e a dimensão é aplicável
    # FP = routed structured quando deveria ser signaling (sobre-confiança)
    # FN = routed signaling quando deveria ser structured (sub-detecção)
    if exp_rt is not None and d2 is False:
        d3_error_type = 'false_positive' if act_rt == 'structured' and exp_rt == 'signaling' else 'false_negative'
    else:
        d3_error_type = None

    score = (correct / applicable) if applicable > 0 else None

    # ── Campos diagnósticos adicionais ───────────────────────────────────────

    # Status global retornado pelo orquestrador (via Agente 2 ou bloco sintético)
    act_global_status = _get(final, 'contextual_resolubility_analysis', 'overall_resolubility', 'status', default='')

    # Número de ambiguidades detectadas pelo Agente 1a
    ambiguities = _get(final, 'ambiguity_analysis', 'ambiguities', default=[]) or []
    ambiguity_count = len(ambiguities)

    # Decomposição efetiva: Agente 3 produziu 2+ artefatos quando concern mixing foi sinalizado
    if act_cm and act_route == 'structured':
        decomposed = len(struct_reqs) >= 2
    else:
        decomposed = None

    return {
        'D1_has_ambiguity':   d1,
        'D2_route':           d2,
        'D3_output_complete': d3,
        'D4_concern_mixing':  d4,
        'correct':            correct,
        'applicable':         applicable,
        'score':              score,
        'd1_error_type':      d1_error_type,
        'd2_error_type':      d2_error_type,
        'd3_error_type':      d3_error_type,
        'act_global_status':  act_global_status,
        'ambiguity_count':    ambiguity_count,
        'decomposed':         decomposed,
    }


# ── Processa um run ───────────────────────────────────────────────────────────
def evaluate_run(run_dir: Path, corpus: dict) -> list[dict]:
    rows: list[dict] = []
    for output_file in sorted(run_dir.rglob('05_final_output.json')):
        try:
            final = json.loads(output_file.read_text(encoding='utf-8'))
        except Exception as e:
            print(f'  [WARN] Falha ao ler {output_file.name}: {e}', file=sys.stderr)
            continue

        req_id = final.get('requirement_id', '')
        cond   = final.get('context_condition', '')

        if req_id not in corpus:
            print(f'  [WARN] {req_id} não encontrado no corpus', file=sys.stderr)
            continue

        doc = corpus[req_id]
        manual_ref = (doc.get('manual_reference') or {}).get(cond, {})
        if not manual_ref:
            print(f'  [WARN] manual_reference/{cond} ausente para {req_id}', file=sys.stderr)
            continue

        eval_r = evaluate_one(final, manual_ref)
        rows.append({
            'run':                  run_dir.name,
            'req_id':               req_id,
            'context':              cond,
            'category':             doc.get('category_id', ''),
            'expected_resolubility': manual_ref.get('expected_resolubility', ''),
            'act_has_ambiguity':    _get(final, 'ambiguity_analysis', 'has_ambiguity'),
            'act_route':            _get(final, 'pipeline_decision', 'route', default=''),
            'act_has_concern_mixing': _get(final, 'concern_mixing_analysis', 'has_concern_mixing', default=False),
            **eval_r,
        })
    return rows


# ── Helpers de display ────────────────────────────────────────────────────────
def _pct(values: list) -> str:
    vals = [v for v in values if v is not None]
    if not vals:
        return '  —  '
    return f'{sum(vals) / len(vals) * 100:5.1f}%'


def _row_line(label: str, rows: list[dict], width: int = 32, hide_detection: bool = False) -> str:
    na = '    —  '
    d1 = na if hide_detection else f'{_pct([r["D1_has_ambiguity"]  for r in rows]):>14} '
    d2 = na if hide_detection else f'{_pct([r["D4_concern_mixing"] for r in rows]):>13} '
    return (
        f'  {label:<{width}} '
        f'{d1:>14} '
        f'{d2:>13} '
        f'{_pct([r["D2_route"]           for r in rows]):>7} '
        f'{_pct([r["D3_output_complete"] for r in rows]):>12} '
        f'{_pct([r["score"]             for r in rows]):>8} '
        f'  {len(rows)}'
    )


# ── Sumário por run ───────────────────────────────────────────────────────────
def summarize(all_rows: list[dict]) -> None:
    if not all_rows:
        print('Nenhum resultado.')
        return

    runs = {}
    for r in all_rows:
        runs.setdefault(r['run'], []).append(r)

    header = (
        f'  {"":32} '
        f'{"D1 Ambiguidade":>14} '
        f'{"D2 ConcernMix":>13} '
        f'{"D3 Rota":>7} '
        f'{"D4 Output OK":>12} '
        f'{"Score":>8}   N'
    )

    for run_name, run_rows in sorted(runs.items()):
        print(f'\n{"═" * 74}')
        print(f'Run : {run_name}')
        print(f'N   : {len(run_rows)} execuções avaliadas')
        print()
        print(header)
        print(f'  {"─" * 70}')

        # Por condição de contexto — D1/D2 são context-free (ocultados nesta seção)
        print('  [Condição de contexto]  * D1/D2 context-free — exibidos apenas no OVERALL')
        for cond in ['C0', 'C1', 'C2']:
            cr = [r for r in run_rows if r['context'] == cond]
            if cr:
                print(_row_line(f'  {cond}', cr, hide_detection=True))

        print()

        # Por categoria
        print('  [Categoria]')
        for cat_id, cat_label in _CAT_LABELS.items():
            cr = [r for r in run_rows if r['category'] == cat_id]
            if cr:
                print(_row_line(f'  {cat_label}', cr))

        print()
        print(_row_line('  OVERALL', run_rows))

    # Comparação entre runs (se houver mais de um)
    if len(runs) > 1:
        print(f'\n{"═" * 74}')
        print('COMPARAÇÃO ENTRE RUNS')
        print()
        print(header)
        print(f'  {"─" * 70}')
        for run_name, run_rows in sorted(runs.items()):
            parts = run_name.split('__')
            label = parts[1] + (' ' + parts[3] if len(parts) > 3 else '') if len(parts) > 1 else run_name
            print(_row_line(label, run_rows))


# ── Export CSV ────────────────────────────────────────────────────────────────
def export_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f'CSV exportado: {path}')


def export_metadata(run_dirs: list[Path], eval_dir: Path) -> None:
    models = []
    for rd in run_dirs:
        meta_path = rd / 'run_metadata.json'
        if meta_path.exists():
            try:
                m = json.loads(meta_path.read_text(encoding='utf-8'))
                models.append(m.get('model', ''))
            except Exception:
                pass

    metadata = {
        'generated_at': datetime.now().isoformat(),
        'runs_included': [rd.name for rd in run_dirs],
        'models': sorted(set(models)),
        'eval_dir': str(eval_dir),
    }
    meta_path = eval_dir / 'metadata.json'
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f'Metadata salvo: {meta_path}')


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Avalia runs do pipeline contra o corpus')
    parser.add_argument('--run',     default='', help='Prefixo do run a avaliar (ex: run_002)')
    parser.add_argument('--exclude', default='', help='Prefixo do run a ignorar (ex: run_001)')
    parser.add_argument('--label',   default='', help='Label para nomear a pasta de saída (ex: qwen3.5-4b)')
    args = parser.parse_args()

    corpus = load_corpus()
    print(f'Corpus: {len(corpus)} requisitos carregados')

    if not _RUNS_DIR.exists():
        sys.exit(f'Diretório não encontrado: {_RUNS_DIR}')

    run_dirs = sorted(d for d in _RUNS_DIR.iterdir() if d.is_dir())
    if args.run:
        run_dirs = [d for d in run_dirs if d.name.startswith(args.run)]
    if args.exclude:
        run_dirs = [d for d in run_dirs if not d.name.startswith(args.exclude)]

    if not run_dirs:
        sys.exit('Nenhum run encontrado.')

    print(f'Runs: {len(run_dirs)} encontrados\n')

    all_rows: list[dict] = []
    for rd in run_dirs:
        rows = evaluate_run(rd, corpus)
        print(f'  {rd.name}: {len(rows)} execuções')
        all_rows.extend(rows)

    summarize(all_rows)

    ts = datetime.now().strftime('%Y-%m-%dT%H-%M')
    suffix = f'__{args.label}' if args.label else ''
    eval_dir = _HERE / 'outputs' / 'evaluation' / f'eval__{ts}{suffix}'
    eval_dir.mkdir(parents=True, exist_ok=True)

    export_csv(all_rows, eval_dir / 'evaluation_results.csv')
    export_metadata(run_dirs, eval_dir)

    try:
        import generate_charts as gc
        import pandas as pd
        df = pd.read_csv(eval_dir / 'evaluation_results.csv')
        for col in gc.DIM_COLS:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('boolean')
        charts_dir = eval_dir / 'charts'
        charts_dir.mkdir(exist_ok=True)
        print('\nGerando gráficos...')
        gc.chart_context_line(df, charts_dir)
        gc.chart_category_bar(df, charts_dir)
        gc.chart_error_type_bar(df, charts_dir)
        gc.chart_error_type_d2(df, charts_dir)
        gc.chart_route_error_context(df, charts_dir)
        for run in sorted(df['run'].unique()):
            gc.chart_heatmap(df[df['run'] == run], run, charts_dir)
    except Exception as e:
        print(f'  [WARN] Gráficos não gerados: {e}')

    print(f'\nResultados em: {eval_dir}')


if __name__ == '__main__':
    main()
