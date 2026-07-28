#!/usr/bin/env python3
"""
evaluate.py — Avaliação quantitativa automatizada do pipeline.

Compara cada 05_final_output.json de um run contra a referência manual
(manual_reference) do corpus controlado em dois blocos:

BLOCO 1 — Detecção (context-free, calculado uma vez por requisito via C0)
  D1  has_ambiguity_correct   Agente 1a detectou (ou não) ambiguidade conforme esperado
  Métricas derivadas: precision / recall / specificity (via TP, TN, FP, FN)

BLOCO 2 — Resolução (context-dependent, calculado por condição de contexto)
  D2  route_correct            pipeline seguiu a rota certa (structured / signaling)
  D3  output_complete          Agente 3 foi/não foi invocado conforme esperado
  Context lift: ΔD2(C2 − C0), staged gains C0→C1 e C1→C2

Campos adicionais por execução:
  d1_error_type       false_positive | false_negative | null (quando D1 correto ou N/A)
  d2_error_type       false_positive | false_negative | null (quando D2 correto ou N/A)
  act_global_status   fully_resolvable | non_resolvable | no_ambiguity
  ambiguity_count     número de ambiguidades detectadas pelo Agente 1a

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
_HERE         = Path(__file__).parent
_ORCHESTRATOR = _HERE.parent
_TCC_ROOT     = _ORCHESTRATOR.parent
_CORPUS       = _TCC_ROOT / 'corpus'
_MANIFEST     = _CORPUS / 'manifest.yaml'
_RUNS_DIR     = _ORCHESTRATOR / 'outputs' / 'runs'

_CAT_LABELS = {
    'category-01-structural': 'Cat-01 Estrutural',
    'category-02-linguistic': 'Cat-02 Linguística',
    'category-03-domain':     'Cat-03 Domínio',
    'category-04-vagueness':  'Cat-04 Vaguidade',
    'category-05-control':    'Cat-05 Controle',
}

# Categorias cujos requisitos têm expected_has_ambiguity=True (positivos para D1).
# Cat-01 (defects estruturais, não ambiguidade linguística) e Cat-05 são negativos.
_POSITIVE_CATS = frozenset({'category-02-linguistic', 'category-03-domain', 'category-04-vagueness'})
_NEGATIVE_CATS = frozenset({'category-01-structural', 'category-05-control'})

# Taxonomy targets are declared per-requirement in the corpus YAML via
# `taxonomy_accepted_types`. No hardcoding here — evaluate_taxonomy reads
# accepted types directly from the loaded corpus.


# ── Carrega corpus ────────────────────────────────────────────────────────────
def load_corpus(manifest_name: str = 'manifest.yaml'):
    """Retorna {req_id: corpus_doc} para todos os itens do manifest."""
    manifest_path = _CORPUS / manifest_name
    manifest = yaml.safe_load(manifest_path.read_text(encoding='utf-8'))
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
    exp_res = manual_ref.get('expected_resolubility', '')

    d1 = d2 = d3 = None
    applicable = correct = 0

    # D1 — has_ambiguity
    exp_ha = _exp_has_ambiguity(exp_res)
    act_ha = _get(final, 'ambiguity_analysis', 'has_ambiguity', default=None)
    if exp_ha is not None:
        d1 = (act_ha == exp_ha)
        applicable += 1
        correct    += int(d1)

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

    if exp_rt is not None and d2 is False:
        d2_error_type = 'false_positive' if act_rt == 'structured' and exp_rt == 'signaling' else 'false_negative'
    else:
        d2_error_type = None

    # D3 — completude do output
    _UNRESOLVED_STATUSES = {'unresolved', 'non_resolvable', 'blocking', 'partially_resolvable'}
    act_route  = _get(final, 'pipeline_decision', 'route', default='')
    struct_reqs = _get(final, 'requirement_structuring', 'structured_requirements', default=[]) or []
    if act_route == 'structured':
        d3 = len(struct_reqs) > 0
    elif act_route == 'signaling':
        amb_items  = _get(final, 'contextual_resolubility_analysis', 'ambiguity_resolubility', default=[]) or []
        unresolved = [a for a in amb_items if isinstance(a, dict)
                      and str(a.get('resolubility_status', '')).strip().lower() in _UNRESOLVED_STATUSES]
        d3 = len(unresolved) > 0
    else:
        d3 = None

    if d3 is not None:
        applicable += 1
        correct    += int(d3)

    score = (correct / applicable) if applicable > 0 else None

    act_global_status = _get(final, 'pipeline_decision', 'overall_resolubility_status', default='')
    ambiguities       = _get(final, 'ambiguity_analysis', 'ambiguities', default=[]) or []
    ambiguity_count   = len(ambiguities)

    return {
        'D1_has_ambiguity':    d1,
        'D2_route':            d2,
        'D3_output_complete':  d3,
        'correct':             correct,
        'applicable':          applicable,
        'score':               score,
        'd1_error_type':       d1_error_type,
        'd2_error_type':       d2_error_type,
        'act_global_status':   act_global_status,
        'ambiguity_count':     ambiguity_count,
    }


# ── Processa um run ───────────────────────────────────────────────────────────
def evaluate_run(run_dir: Path, corpus: dict) -> list[dict]:
    rows: list[dict] = []
    for output_file in sorted(run_dir.rglob('final_output.json')):
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

        doc        = corpus[req_id]
        manual_ref = (doc.get('manual_reference') or {}).get(cond, {})
        if not manual_ref:
            print(f'  [WARN] manual_reference/{cond} ausente para {req_id}', file=sys.stderr)
            continue

        eval_r = evaluate_one(final, manual_ref)
        rows.append({
            'run':                   run_dir.name,
            'req_id':                req_id,
            'context':               cond,
            'category':              doc.get('category_id', ''),
            'expected_resolubility': manual_ref.get('expected_resolubility', ''),
            'act_has_ambiguity':     _get(final, 'ambiguity_analysis', 'has_ambiguity'),
            'act_route':             _get(final, 'pipeline_decision', 'route', default=''),
            **eval_r,
        })
    return rows


# ── Bloco 1: métricas de detecção (context-free, N=15 via C0) ────────────────
def _detection_metrics_d1(c0_rows: list[dict]) -> dict:
    """
    Precision, recall e specificity para D1 (has_ambiguity).

    Positivos: Cat-02, Cat-03, Cat-04 (expected_has_ambiguity=True).
    Negativos: Cat-01, Cat-05 (expected_has_ambiguity=False).
    """
    tp = fp = fn = tn = 0
    for r in c0_rows:
        exp = _exp_has_ambiguity(r.get('expected_resolubility', ''))
        act = r.get('act_has_ambiguity')
        if exp is None:
            continue
        if exp and act:
            tp += 1
        elif not exp and act:
            fp += 1
        elif exp and not act:
            fn += 1
        else:
            tn += 1
    precision   = tp / (tp + fp) if (tp + fp) > 0 else None
    recall      = tp / (tp + fn) if (tp + fn) > 0 else None
    specificity = tn / (tn + fp) if (tn + fp) > 0 else None
    return {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'precision': precision, 'recall': recall, 'specificity': specificity}


# ── Bloco 2: context lift ─────────────────────────────────────────────────────
def evaluate_context_lift(all_rows: list[dict]) -> list[dict]:
    """
    Para cada (run, req_id), calcula ΔD3 entre condições de contexto.

    Colunas de saída:
      run, req_id, category, d3_c0, d3_c1, d3_c2,
      lift_c2_c0    (d3_c2 − d3_c0, inteiro: -1 / 0 / +1)
      stage_c0_c1   (d3_c1 − d3_c0)
      stage_c1_c2   (d3_c2 − d3_c1)
      transition    (padrão legível: "0→0→1", "1→1→1", etc.)
    """
    # Indexa por (run, req_id, context)
    index: dict[tuple, dict] = {}
    for r in all_rows:
        index[(r['run'], r['req_id'], r['context'])] = r

    runs    = sorted({r['run']    for r in all_rows})
    req_ids = sorted({r['req_id'] for r in all_rows})

    lift_rows: list[dict] = []
    for run in runs:
        for req_id in req_ids:
            c0 = index.get((run, req_id, 'C0'))
            c1 = index.get((run, req_id, 'C1'))
            c2 = index.get((run, req_id, 'C2'))
            if not (c0 and c1 and c2):
                continue

            d2_c0 = c0.get('D2_route')
            d2_c1 = c1.get('D2_route')
            d2_c2 = c2.get('D2_route')

            def _bool_int(v):
                return int(v) if isinstance(v, bool) else None

            b0, b1, b2 = _bool_int(d2_c0), _bool_int(d2_c1), _bool_int(d2_c2)

            lift_c2_c0  = (b2 - b0)  if (b2 is not None and b0 is not None) else None
            stage_c0_c1 = (b1 - b0)  if (b1 is not None and b0 is not None) else None
            stage_c1_c2 = (b2 - b1)  if (b2 is not None and b1 is not None) else None

            def _bit(v):
                return str(int(v)) if isinstance(v, bool) else '?'

            transition = f'{_bit(d2_c0)}→{_bit(d2_c1)}→{_bit(d2_c2)}'

            lift_rows.append({
                'run':        run,
                'req_id':     req_id,
                'category':   c0.get('category', ''),
                'd2_c0':      b0,
                'd2_c1':      b1,
                'd2_c2':      b2,
                'lift_c2_c0':  lift_c2_c0,
                'stage_c0_c1': stage_c0_c1,
                'stage_c1_c2': stage_c1_c2,
                'transition':  transition,
            })
    return lift_rows


# ── Taxonomia de Pohl (classificação, não apenas detecção) ───────────────────
def evaluate_taxonomy(run_dir: Path, corpus: dict) -> list[dict]:
    """Para cada requisito do corpus com `taxonomy_accepted_types`, verifica se
    o Agente 1a classificou a ambiguidade em um dos tipos aceitos (Pohl 5-way).
    Usa C0 como representativo — Agente 1a é context-free.
    """
    rows: list[dict] = []
    for req_id, doc in sorted(corpus.items()):
        accepted_list = doc.get('taxonomy_accepted_types') or []
        if not accepted_list:
            continue
        accepted_types = set(accepted_list)
        output_file = run_dir / req_id / 'C0' / 'final_output.json'
        if not output_file.exists():
            continue
        final          = json.loads(output_file.read_text(encoding='utf-8'))
        ambiguities    = _get(final, 'ambiguity_analysis', 'ambiguities', default=[]) or []
        detected_types = [a.get('ambiguity_type', '') for a in ambiguities]
        match          = any(t in accepted_types for t in detected_types)
        rows.append({
            'run':            run_dir.name,
            'req_id':         req_id,
            'accepted_types': ', '.join(sorted(accepted_types)),
            'detected_types': ', '.join(detected_types) if detected_types else '(nenhuma)',
            'match':          match,
        })
    return rows


# ── Helpers de display ────────────────────────────────────────────────────────
def _pct(values: list) -> str:
    vals = [v for v in values if v is not None]
    if not vals:
        return '  —  '
    return f'{sum(vals) / len(vals) * 100:5.1f}%'


def _fmt_pct(v) -> str:
    return f'{v * 100:.1f}%' if v is not None else '—'


def _model_short(run_name: str) -> str:
    parts = run_name.split('__')
    return parts[1] if len(parts) >= 2 else run_name


# ── Sumário — Bloco 1: Detecção (context-free) ───────────────────────────────
def _summarize_detection_block(run_rows: list[dict]) -> None:
    c0_rows = [r for r in run_rows if r['context'] == 'C0']
    if not c0_rows:
        return

    W = 24
    print(f'\n  {"BLOCO 1 — Detecção (context-free, N=":}{len(c0_rows)} via C0)')
    print(f'  {"─" * 48}')
    header = f'  {"":>{W}}  {"D1 Ambig":>9}   N'
    print(header)

    for cat_id, cat_label in _CAT_LABELS.items():
        cr = [r for r in c0_rows if r['category'] == cat_id]
        if cr:
            short = cat_label.split(' ', 1)[1] if ' ' in cat_label else cat_label
            print(
                f'  {short:>{W}}  '
                f'{_pct([r["D1_has_ambiguity"] for r in cr]):>9}  '
                f'{len(cr):>3}'
            )

    print(f'  {"─" * 48}')
    print(
        f'  {"OVERALL":>{W}}  '
        f'{_pct([r["D1_has_ambiguity"] for r in c0_rows]):>9}  '
        f'{len(c0_rows):>3}'
    )

    # Precision / Recall / Specificity para D1
    m1 = _detection_metrics_d1(c0_rows)
    pos = m1['tp'] + m1['fn']
    neg = m1['tn'] + m1['fp']
    print(f'\n  Métricas de detecção — D1 (positivos: Cat-02/03/04  negativos: Cat-01/05)')
    print(f'    Positivos: {pos}  (TP={m1["tp"]} FN={m1["fn"]})   '
          f'Negativos: {neg}  (TN={m1["tn"]} FP={m1["fp"]})')
    print(f'    Precision: {_fmt_pct(m1["precision"]):>7}   '
          f'Recall: {_fmt_pct(m1["recall"]):>7}   '
          f'Specificity: {_fmt_pct(m1["specificity"]):>7}')


# ── Sumário — Bloco 2: Resolução (context-dependent) ─────────────────────────
def _summarize_resolution_block(run_rows: list[dict]) -> None:
    print(f'\n  BLOCO 2 — Resolução por condição de contexto (N={len(run_rows)})')
    print(f'  {"─" * 60}')
    header = f'  {"":>12}  {"D2 Rota":>9}  {"D3 Output":>9}   N'
    print(header)

    for cond in ['C0', 'C1', 'C2']:
        cr = [r for r in run_rows if r['context'] == cond]
        if cr:
            labels = {'C0': 'C0 (sem ctx)', 'C1': 'C1 (domínio)', 'C2': 'C2 (+ BR)'}
            print(
                f'  {labels[cond]:>12}  '
                f'{_pct([r["D2_route"]            for r in cr]):>9}  '
                f'{_pct([r["D3_output_complete"]  for r in cr]):>9}  '
                f'{len(cr):>3}'
            )


# ── Sumário — Context lift ────────────────────────────────────────────────────
def _summarize_context_lift(lift_rows: list[dict], run_name: str) -> None:
    run_lifts = [r for r in lift_rows if r['run'] == run_name]
    if not run_lifts:
        return

    # Requisitos cujo expected_resolubility transita em C2 (positivos para lift).
    # São os 9 req de Cat-02, Cat-03, Cat-04 — os únicos com expected=resolvable em C2.
    # Cat-01 e Cat-05 têm not_applicable em todas as condições → D3 esperado é
    # sempre 'structured'; eles não mudam, então seu lift teórico é 0 por design.
    ambiguous = [r for r in run_lifts if r['category'] in _POSITIVE_CATS]

    n = len(ambiguous)
    if n == 0:
        return

    lift_pos = sum(1 for r in ambiguous if r['lift_c2_c0'] == 1)
    lift_zer = sum(1 for r in ambiguous if r['lift_c2_c0'] == 0)
    lift_neg = sum(1 for r in ambiguous if r['lift_c2_c0'] == -1)
    gain_01  = sum(1 for r in ambiguous if r['stage_c0_c1'] == 1)
    gain_12  = sum(1 for r in ambiguous if r['stage_c1_c2'] == 1)

    print(f'\n  Context lift ΔD2(C2 − C0)  [N={n} req ambíguos: Cat-02/03/04]')
    print(f'  {"─" * 60}')
    print(f'    lift=+1  (C2 resolve o que C0 não resolvia): {lift_pos:>2}/{n}  ({lift_pos/n*100:.1f}%)')
    print(f'    lift= 0  (sem variação):                     {lift_zer:>2}/{n}  ({lift_zer/n*100:.1f}%)')
    print(f'    lift=−1  (degradação com contexto):          {lift_neg:>2}/{n}  ({lift_neg/n*100:.1f}%)')

    print(f'\n  Staged gains:')
    print(f'    C0→C1 (glossário):              {gain_01:>2}/{n}  ({gain_01/n*100:.1f}%)')
    print(f'    C1→C2 (regra de negócio):       {gain_12:>2}/{n}  ({gain_12/n*100:.1f}%)')

    # Tabela de transição por requisito (compacta)
    print(f'\n  Padrões de transição (D3: 0=errou 1=acertou):')
    by_pattern: dict[str, list[str]] = {}
    for r in ambiguous:
        by_pattern.setdefault(r['transition'], []).append(r['req_id'])
    for pat in sorted(by_pattern, reverse=True):
        reqs = ', '.join(sorted(by_pattern[pat]))
        print(f'    {pat}  →  {reqs}')


# ── Sumário — Taxonomia ───────────────────────────────────────────────────────
def summarize_taxonomy(rows: list[dict]) -> None:
    if not rows:
        return
    runs    = sorted({r['run']    for r in rows})
    req_ids = sorted({r['req_id'] for r in rows})

    print(f'\n{"═" * 74}')
    print('CLASSIFICAÇÃO POR TAXONOMIA DE POHL (Agente 1a)')
    print('Tipos aceitos declarados em taxonomy_accepted_types no corpus.')
    print('Conjunto único = consenso; conjunto múltiplo = ambos defensáveis.')
    print(f'{"─" * 74}')
    header = f'  {"Requisito (aceitos)":<34}' + ''.join(f'{_model_short(r):>14}' for r in runs)
    print(header)
    for req_id in req_ids:
        accepted_str = next((r['accepted_types'] for r in rows if r['req_id'] == req_id), '')
        label = req_id + ' (' + accepted_str + ')'
        line  = f'  {label:<34}'
        for run in runs:
            match = next((r['match'] for r in rows if r['run'] == run and r['req_id'] == req_id), None)
            cell  = '✓' if match else ('✗' if match is False else '—')
            line += f'{cell:>14}'
        print(line)

    total   = len(rows)
    correct = sum(1 for r in rows if r['match'])
    print(f'{"─" * 74}')
    print(f'  Acerto de classificação: {correct}/{total} ({correct/total*100:.1f}%)')


# ── Sumário principal ─────────────────────────────────────────────────────────
def summarize(all_rows: list[dict], lift_rows: list[dict]) -> None:
    if not all_rows:
        print('Nenhum resultado.')
        return

    runs: dict[str, list] = {}
    for r in all_rows:
        runs.setdefault(r['run'], []).append(r)

    for run_name, run_rows in sorted(runs.items()):
        print(f'\n{"═" * 74}')
        print(f'Run : {run_name}')
        print(f'N   : {len(run_rows)} execuções avaliadas')

        _summarize_detection_block(run_rows)
        _summarize_resolution_block(run_rows)
        _summarize_context_lift(lift_rows, run_name)

    # Comparação entre runs (se houver mais de um)
    if len(runs) > 1:
        print(f'\n{"═" * 74}')
        print('COMPARAÇÃO ENTRE RUNS — D3 por condição')
        print(f'  {"":>20}  {"C0":>8}  {"C1":>8}  {"C2":>8}  {"lift":>8}   N')
        print(f'  {"─" * 60}')
        for run_name, run_rows in sorted(runs.items()):
            label = _model_short(run_name)
            c0r   = [r for r in run_rows if r['context'] == 'C0']
            c1r   = [r for r in run_rows if r['context'] == 'C1']
            c2r   = [r for r in run_rows if r['context'] == 'C2']
            run_lift  = [r for r in lift_rows if r['run'] == run_name and r['category'] in _POSITIVE_CATS]
            n_lift    = len(run_lift)
            lift_pos  = sum(1 for r in run_lift if r['lift_c2_c0'] == 1) if n_lift else 0
            lift_pct  = f'{lift_pos/n_lift*100:.1f}%' if n_lift else '—'
            print(
                f'  {label:>20}  '
                f'{_pct([r["D2_route"] for r in c0r]):>8}  '
                f'{_pct([r["D2_route"] for r in c1r]):>8}  '
                f'{_pct([r["D2_route"] for r in c2r]):>8}  '
                f'{lift_pct:>8}  '
                f'{len(run_rows):>3}'
            )


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
        'generated_at':   datetime.now().isoformat(),
        'runs_included':  [rd.name for rd in run_dirs],
        'models':         sorted(set(models)),
        'eval_dir':       str(eval_dir),
    }
    meta_path = eval_dir / 'metadata.json'
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f'Metadata salvo: {meta_path}')


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Avalia runs do pipeline contra o corpus')
    parser.add_argument('--run',      default='', help='Prefixo do run a avaliar (ex: run_002)')
    parser.add_argument('--exclude',  default='', help='Prefixo do run a ignorar (ex: run_001)')
    parser.add_argument('--label',    default='', help='Label para nomear a pasta de saída (ex: qwen3.5-4b)')
    parser.add_argument('--manifest', default='manifest.yaml',
                        help='Manifesto do corpus (relativo a corpus/). Default: manifest.yaml')
    args = parser.parse_args()

    corpus = load_corpus(args.manifest)
    print(f'Corpus: {len(corpus)} requisitos carregados (manifest: {args.manifest})')

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

    lift_rows = evaluate_context_lift(all_rows)
    summarize(all_rows, lift_rows)

    taxonomy_rows: list[dict] = []
    for rd in run_dirs:
        taxonomy_rows.extend(evaluate_taxonomy(rd, corpus))
    summarize_taxonomy(taxonomy_rows)

    ts     = datetime.now().strftime('%Y-%m-%dT%H-%M')
    suffix = f'__{args.label}' if args.label else ''
    eval_dir = _HERE / 'outputs' / 'evaluation' / f'eval__{ts}{suffix}'
    eval_dir.mkdir(parents=True, exist_ok=True)

    export_csv(all_rows,      eval_dir / 'evaluation_results.csv')
    export_csv(lift_rows,     eval_dir / 'context_lift.csv')
    export_csv(taxonomy_rows, eval_dir / 'taxonomy_classification.csv')
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
        gc.chart_detection_bar(df, charts_dir)
        gc.chart_error_type_bar(df, charts_dir)
        gc.chart_context_line(df, charts_dir)
        gc.chart_route_error_context(df, charts_dir)
        df_lift = pd.read_csv(eval_dir / 'context_lift.csv')
        gc.chart_context_lift(df_lift, charts_dir)
        for run in sorted(df['run'].unique()):
            gc.chart_heatmap(df[df['run'] == run], run, charts_dir)
        tax_csv = eval_dir / 'taxonomy_classification.csv'
        if tax_csv.exists():
            df_tax = pd.read_csv(tax_csv)
            gc.chart_taxonomy_grid(df_tax, charts_dir)
    except Exception as e:
        print(f'  [WARN] Gráficos não gerados: {e}')

    print(f'\nResultados em: {eval_dir}')


if __name__ == '__main__':
    main()
