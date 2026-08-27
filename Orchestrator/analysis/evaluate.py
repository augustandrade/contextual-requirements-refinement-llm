#!/usr/bin/env python3
"""
evaluate.py — Avaliação quantitativa automatizada do pipeline.

BLOCO 1 — Detecção (context-free, calculado via C0)
  D1  has_ambiguity_correct   Agente 1a detectou (ou não) ambiguidade.
      Ground truth: category_id != 'category-05-control'
      (Cat-01 a 04 = positivos; Cat-05 = controle negativo).
  Métricas derivadas: precision / recall / F1 / specificity (via TP, TN, FP, FN)

BLOCO 2 — Sensibilidade ao contexto (descritivo, sem gabarito de rota)
  act_route     rota que o pipeline escolheu (structured / signaling)
  Context sensitivity: ΔRoute(C2 − C0), ΔRoute(C3 − C0), Δ(C2 − C3)
  Staged gains: C0→C1 e C1→C2

BLOCO 3 — Taxonomia Pohl (context-free, C0, Cat-02/03/04)
  match         algum tipo detectado está entre taxonomy_accepted_types

BLOCO 4 — Integridade do output (D_output_integrity, todas as condições)
  D_output      output estruturalmente íntegro dado a rota tomada:
    structured → ao menos um structured_requirement com final_statement preenchido
    signaling  → ao menos um ambiguity_resolubility com status unresolved/non_resolvable

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
_RUNS_DIR     = _ORCHESTRATOR / 'outputs' / 'runs'

_CAT_LABELS = {
    'category-01-structural': 'Cat-01 Estrutural',
    'category-02-linguistic': 'Cat-02 Linguística',
    'category-03-domain':     'Cat-03 Domínio',
    'category-04-vagueness':  'Cat-04 Vaguidade',
    'category-05-control':    'Cat-05 Controle',
}


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


def _expected_has_ambiguity(doc: dict) -> bool:
    """True para todas as categorias de defeito (Cat-01 a 04); False apenas para Cat-05 (controle).
    Não usa taxonomy_accepted_types como proxy — Cat-01 não tem esse campo mas é positivo."""
    return doc.get('category_id', '') != 'category-05-control'


# ── Avalia uma execução ───────────────────────────────────────────────────────
def evaluate_one(final: dict, expected_has_ambiguity: bool) -> dict:
    """
    D1: detecção vs. ground truth (taxonomy_accepted_types).
    D3: completude estrutural do output (valida consistência interna).
    act_route: rota observada (descritivo, sem gabarito).
    """
    d1 = d3 = None
    applicable = correct = 0

    # D1 — has_ambiguity
    act_ha = _get(final, 'ambiguity_analysis', 'has_ambiguity', default=None)
    if act_ha is not None:
        d1 = (act_ha == expected_has_ambiguity)
        applicable += 1
        correct    += int(d1)

    if d1 is False:
        d1_error_type = 'false_positive' if (act_ha and not expected_has_ambiguity) else 'false_negative'
    else:
        d1_error_type = None

    # D_output — integridade estrutural do output dado a rota tomada
    _UNRESOLVED_STATUSES = {'unresolved'}
    act_route   = _get(final, 'pipeline_decision', 'route', default='')
    struct_reqs = _get(final, 'requirement_structuring', 'structured_requirements', default=[]) or []
    d_output = None
    if act_route == 'structured':
        # Verifica que há ao menos um item com final_statement não vazio
        d_output = any(
            isinstance(r, dict) and r.get('final_statement', '').strip()
            for r in struct_reqs
        )
    elif act_route == 'signaling':
        amb_items  = _get(final, 'contextual_resolubility_analysis', 'ambiguity_resolubility', default=[]) or []
        unresolved = [a for a in amb_items if isinstance(a, dict)
                      and str(a.get('resolubility_status', '')).strip().lower() in _UNRESOLVED_STATUSES]
        d_output = len(unresolved) > 0

    if d_output is not None:
        applicable += 1
        correct    += int(d_output)

    score = (correct / applicable) if applicable > 0 else None

    act_global_status = _get(final, 'pipeline_decision', 'overall_resolubility_status', default='')
    ambiguities       = _get(final, 'ambiguity_analysis', 'ambiguities', default=[]) or []
    ambiguity_count   = len(ambiguities)

    return {
        'D1_has_ambiguity':    d1,
        'D_output_integrity':  d_output,
        'correct':             correct,
        'applicable':          applicable,
        'score':               score,
        'd1_error_type':       d1_error_type,
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

        doc         = corpus[req_id]
        expected_ha = _expected_has_ambiguity(doc)
        eval_r      = evaluate_one(final, expected_ha)

        rows.append({
            'run':                    run_dir.name,
            'req_id':                 req_id,
            'context':                cond,
            'category':               doc.get('category_id', ''),
            'expected_has_ambiguity': expected_ha,
            'act_has_ambiguity':      _get(final, 'ambiguity_analysis', 'has_ambiguity'),
            'act_route':              _get(final, 'pipeline_decision', 'route', default=''),
            **eval_r,
        })
    return rows


# ── Bloco 1: métricas de detecção (context-free, N=15 via C0) ────────────────
def _detection_metrics_d1(c0_rows: list[dict]) -> dict:
    tp = fp = fn = tn = 0
    for r in c0_rows:
        exp = r.get('expected_has_ambiguity')
        act = r.get('act_has_ambiguity')
        if exp is None or act is None:
            continue
        if exp and act:       tp += 1
        elif not exp and act: fp += 1
        elif exp and not act: fn += 1
        else:                 tn += 1
    precision   = tp / (tp + fp) if (tp + fp) > 0 else None
    recall      = tp / (tp + fn) if (tp + fn) > 0 else None
    specificity = tn / (tn + fp) if (tn + fp) > 0 else None
    return {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'precision': precision, 'recall': recall, 'specificity': specificity}


# ── Bloco 2: context sensitivity ─────────────────────────────────────────────
def evaluate_context_lift(all_rows: list[dict]) -> list[dict]:
    """
    Para cada (run, req_id) com C0/C1/C2/C3, rastreia a rota observada em cada condição.

    structured_c0/c1/c2/c3 = 1 se rota foi 'structured', 0 se 'signaling', None se ausente.

    Comparações principais:
      lift_c2_c0   = C2 − C0  efeito total do contexto específico relevante
      lift_c3_c0   = C3 − C0  efeito do contexto específico irrelevante
      delta_c2_c3  = C2 − C3  efeito puro da relevância (especificidade constante)
      stage_c0_c1  = C1 − C0  efeito do contexto genérico
      stage_c1_c2  = C2 − C1  ganho de C1 para C2 (relevância sobre genérico)
    """
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
            c3 = index.get((run, req_id, 'C3'))
            if not (c0 and c1 and c2):
                continue

            def _structured(row):
                if row is None: return None
                r = row.get('act_route', '')
                if r == 'structured': return 1
                if r == 'signaling':  return 0
                return None

            s0, s1, s2, s3 = _structured(c0), _structured(c1), _structured(c2), _structured(c3)

            def _diff(a, b): return (a - b) if (a is not None and b is not None) else None

            lift_c2_c0  = _diff(s2, s0)
            lift_c3_c0  = _diff(s3, s0)
            delta_c2_c3 = _diff(s2, s3)
            stage_c0_c1 = _diff(s1, s0)
            stage_c1_c2 = _diff(s2, s1)

            def _bit(v): return str(v) if v is not None else '?'
            transition = f'{_bit(s0)}→{_bit(s1)}→{_bit(s2)}→{_bit(s3)}'

            lift_rows.append({
                'run':                    run,
                'req_id':                 req_id,
                'category':               c0.get('category', ''),
                'expected_has_ambiguity': c0.get('expected_has_ambiguity'),
                'structured_c0':          s0,
                'structured_c1':          s1,
                'structured_c2':          s2,
                'structured_c3':          s3,
                'lift_c2_c0':             lift_c2_c0,
                'lift_c3_c0':             lift_c3_c0,
                'delta_c2_c3':            delta_c2_c3,
                'stage_c0_c1':            stage_c0_c1,
                'stage_c1_c2':            stage_c1_c2,
                'transition':             transition,
            })
    return lift_rows


# ── Taxonomia de Pohl ─────────────────────────────────────────────────────────
def evaluate_taxonomy(run_dir: Path, corpus: dict) -> list[dict]:
    """Para cada requisito com taxonomy_accepted_types, verifica se o Agente 1a
    classificou a ambiguidade em um dos tipos aceitos (Pohl 5-way). Usa C0."""
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
    print(f'  {"":>{W}}  {"D1 Ambig":>9}   N')

    for cat_id, cat_label in _CAT_LABELS.items():
        cr = [r for r in c0_rows if r['category'] == cat_id]
        if cr:
            short = cat_label.split(' ', 1)[1] if ' ' in cat_label else cat_label
            print(
                f'  {short:>{W}}  '
                f'{_pct([r["D1_has_ambiguity"] for r in cr]):>9}  '
                f'{len(cr):>3}'
            )

    # Fallback para pilot ou categorias não canônicas
    other = [r for r in c0_rows if r['category'] not in _CAT_LABELS]
    if other:
        print(f'  {"Pilot":>{W}}  {_pct([r["D1_has_ambiguity"] for r in other]):>9}  {len(other):>3}')

    print(f'  {"─" * 48}')
    print(
        f'  {"OVERALL":>{W}}  '
        f'{_pct([r["D1_has_ambiguity"] for r in c0_rows]):>9}  '
        f'{len(c0_rows):>3}'
    )

    m1  = _detection_metrics_d1(c0_rows)
    pos = m1['tp'] + m1['fn']
    neg = m1['tn'] + m1['fp']
    print(f'\n  Métricas de detecção — D1')
    print(f'    Positivos (ambíguos): {pos}  (TP={m1["tp"]} FN={m1["fn"]})   '
          f'Negativos (controle): {neg}  (TN={m1["tn"]} FP={m1["fp"]})')
    print(f'    Precision: {_fmt_pct(m1["precision"]):>7}   '
          f'Recall: {_fmt_pct(m1["recall"]):>7}   '
          f'Specificity: {_fmt_pct(m1["specificity"]):>7}')


# ── Sumário — Bloco 2: Rota observada por condição ───────────────────────────
def _summarize_resolution_block(run_rows: list[dict]) -> None:
    print(f'\n  BLOCO 2 — Rota observada por condição de contexto (N={len(run_rows)})')
    print(f'  {"─" * 64}')
    print(f'  {"":>14}  {"structured":>10}  {"signaling":>9}  {"D_output":>9}   N')

    labels = {'C0': 'C0 (sem ctx)', 'C1': 'C1 (genérico)', 'C2': 'C2 (específico)', 'C3': 'C3 (irrelevante)'}
    for cond in ['C0', 'C1', 'C2', 'C3']:
        cr = [r for r in run_rows if r['context'] == cond]
        if not cr:
            continue
        n        = len(cr)
        n_struct = sum(1 for r in cr if r.get('act_route') == 'structured')
        n_signal = sum(1 for r in cr if r.get('act_route') == 'signaling')
        print(
            f'  {labels[cond]:>14}  '
            f'{n_struct/n*100:>9.1f}%  '
            f'{n_signal/n*100:>9.1f}%  '
            f'{_pct([r["D_output_integrity"] for r in cr]):>9}  '
            f'{n:>3}'
        )


# ── Sumário — Context sensitivity ────────────────────────────────────────────
def _summarize_context_lift(lift_rows: list[dict], run_name: str) -> None:
    run_lifts = [r for r in lift_rows if r['run'] == run_name]
    if not run_lifts:
        return

    ambiguous = [r for r in run_lifts if r.get('expected_has_ambiguity') is True]
    n = len(ambiguous)
    if n == 0:
        print(f'\n  [INFO] Context sensitivity: nenhum requisito com expected_has_ambiguity=True neste run.')
        return

    lift_pos = sum(1 for r in ambiguous if r['lift_c2_c0'] == 1)
    lift_zer = sum(1 for r in ambiguous if r['lift_c2_c0'] == 0)
    lift_neg = sum(1 for r in ambiguous if r['lift_c2_c0'] == -1)
    gain_01  = sum(1 for r in ambiguous if r['stage_c0_c1'] == 1)
    gain_12  = sum(1 for r in ambiguous if r['stage_c1_c2'] == 1)

    # C3 stats (only for reqs that have C3 data)
    amb_c3 = [r for r in ambiguous if r.get('structured_c3') is not None]
    n3 = len(amb_c3)

    print(f'\n  Context sensitivity  [N={n} req ambíguos]')
    print(f'  {"─" * 62}')
    print(f'  ΔRoute(C2 − C0)  — ctx específico relevante vs. baseline')
    print(f'    +1: {lift_pos:>2}/{n} ({lift_pos/n*100:.1f}%)   '
          f'0: {lift_zer:>2}/{n} ({lift_zer/n*100:.1f}%)   '
          f'−1: {lift_neg:>2}/{n} ({lift_neg/n*100:.1f}%)')
    print(f'\n  Staged transitions C0→C1→C2:')
    print(f'    C0→C1 (ctx genérico):    {gain_01:>2}/{n}  ({gain_01/n*100:.1f}%)')
    print(f'    C1→C2 (ctx específico):  {gain_12:>2}/{n}  ({gain_12/n*100:.1f}%)')

    if n3 > 0:
        c3_pos = sum(1 for r in amb_c3 if r.get('lift_c3_c0') == 1)
        c3_zer = sum(1 for r in amb_c3 if r.get('lift_c3_c0') == 0)
        c3_neg = sum(1 for r in amb_c3 if r.get('lift_c3_c0') == -1)
        rel_pos = sum(1 for r in amb_c3 if r.get('delta_c2_c3') == 1)
        rel_zer = sum(1 for r in amb_c3 if r.get('delta_c2_c3') == 0)
        rel_neg = sum(1 for r in amb_c3 if r.get('delta_c2_c3') == -1)
        print(f'\n  ΔRoute(C3 − C0)  — ctx específico IRRELEVANTE vs. baseline  [N={n3}]')
        print(f'    +1: {c3_pos:>2}/{n3} ({c3_pos/n3*100:.1f}%)   '
              f'0: {c3_zer:>2}/{n3} ({c3_zer/n3*100:.1f}%)   '
              f'−1: {c3_neg:>2}/{n3} ({c3_neg/n3*100:.1f}%)')
        print(f'\n  ΔRoute(C2 − C3)  — efeito puro da relevância  [N={n3}]')
        print(f'    +1: {rel_pos:>2}/{n3} ({rel_pos/n3*100:.1f}%)   '
              f'0: {rel_zer:>2}/{n3} ({rel_zer/n3*100:.1f}%)   '
              f'−1: {rel_neg:>2}/{n3} ({rel_neg/n3*100:.1f}%)')

    print(f'\n  Padrões de transição (0=signaling 1=structured  ?=sem dado):')
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

    if len(runs) > 1:
        print(f'\n{"═" * 74}')
        print('COMPARAÇÃO ENTRE RUNS — rota structured por condição')
        print(f'  {"":>20}  {"C0 struct%":>10}  {"C1 struct%":>10}  {"C2 struct%":>10}  {"ΔRoute+1":>9}   N')
        print(f'  {"─" * 68}')
        for run_name, run_rows in sorted(runs.items()):
            label   = _model_short(run_name)
            c0r     = [r for r in run_rows if r['context'] == 'C0']
            c1r     = [r for r in run_rows if r['context'] == 'C1']
            c2r     = [r for r in run_rows if r['context'] == 'C2']
            run_amb = [r for r in lift_rows if r['run'] == run_name
                       and r.get('expected_has_ambiguity') is True]
            n_amb    = len(run_amb)
            lift_pos = sum(1 for r in run_amb if r['lift_c2_c0'] == 1) if n_amb else 0
            lift_pct = f'{lift_pos/n_amb*100:.1f}%' if n_amb else '—'

            def _pct_struct(rows):
                if not rows: return '  —  '
                n = len(rows)
                s = sum(1 for r in rows if r.get('act_route') == 'structured')
                return f'{s/n*100:5.1f}%'

            print(
                f'  {label:>20}  '
                f'{_pct_struct(c0r):>10}  '
                f'{_pct_struct(c1r):>10}  '
                f'{_pct_struct(c2r):>10}  '
                f'{lift_pct:>9}  '
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
        'generated_at':  datetime.now().isoformat(),
        'runs_included': [rd.name for rd in run_dirs],
        'models':        sorted(set(models)),
        'eval_dir':      str(eval_dir),
    }
    meta_path = eval_dir / 'metadata.json'
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f'Metadata salvo: {meta_path}')


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Avalia runs do pipeline contra o corpus')
    parser.add_argument('--run',      default='', help='Prefixo do run a avaliar (ex: run_002)')
    parser.add_argument('--exclude',  default='', help='Prefixo do run a ignorar (ex: run_001)')
    parser.add_argument('--label',    default='', help='Label para nomear a pasta de saída')
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

    ts       = datetime.now().strftime('%Y-%m-%dT%H-%M')
    suffix   = f'__{args.label}' if args.label else ''
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
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('boolean')
        df['route_structured'] = (df['act_route'] == 'structured')
        charts_dir = eval_dir / 'charts'
        charts_dir.mkdir(exist_ok=True)
        print('\nGerando gráficos...')
        # Bloco 1 — Detecção
        gc.chart_d1_classification(df, charts_dir)
        gc.chart_error_type_bar(df, charts_dir)
        gc.chart_heatmap(df, charts_dir)
        # Bloco 2 — Sensibilidade ao contexto
        df_lift = pd.read_csv(eval_dir / 'context_lift.csv')
        gc.chart_context_lift(df, df_lift, charts_dir)
        # Bloco 3 — Taxonomia Pohl
        tax_csv = eval_dir / 'taxonomy_classification.csv'
        if tax_csv.exists():
            df_tax = pd.read_csv(tax_csv)
            gc.chart_taxonomy_grid(df_tax, charts_dir)
            gc.chart_taxonomy_model_heatmap(df_tax, charts_dir)
        # Bloco 4 — Integridade do output
        gc.table_d_output_summary(df, charts_dir)
    except Exception as e:
        print(f'  [WARN] Gráficos não gerados: {e}')

    print(f'\nResultados em: {eval_dir}')


if __name__ == '__main__':
    main()
