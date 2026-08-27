#!/usr/bin/env python3
"""
generate_charts.py — Geração de gráficos a partir dos resultados de avaliação.

Todas as visualizações mostram resultados por modelo (sem agregação entre modelos).

BLOCO 1 — Detecção (context-free, usa C0)
  1. d1_classification         — Tabela Precision/Recall/F1 por modelo (C0 only)
  2. error_type__D1_ambiguidade — FP/FN de D1 por categoria (C0 only)
  3. heatmap__D1_req_modelo    — matriz req × modelo, pass/fail D1 (C0 only)

BLOCO 2 — Sensibilidade ao contexto (contribuição central)
  4. context_lift__route_delta — 2×2: linha C0→C3 + ΔRoute(C2−C0) + staged gains + Δ(C2−C3)

BLOCO 3 — Taxonomia Pohl (Cat-02/03/04, C0)
  5. taxonomy_classification   — matriz de confusão tipo aceito × tipo detectado
  6. taxonomy_model_heatmap    — % acerto por tipo × modelo

BLOCO 4 — Integridade do output
  7. d_output_summary_table    — tabela D_output_integrity por modelo × condição

Uso:
  python3 generate_charts.py
  python3 generate_charts.py --eval-dir outputs/evaluation/eval__2026-...
  python3 generate_charts.py --run run_002
"""

import argparse
import math
from pathlib import Path

import warnings
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

_HERE        = Path(__file__).parent
_OUTPUTS_DIR = _HERE.parent / 'outputs'

DIM_COLS   = ['D1_has_ambiguity', 'D_output_integrity']
DIM_LABELS = ['D1 Ambiguidade', 'D_output Integridade']
DIM_COLORS = ['#5c6bc0', '#8d6e63']

CTX_SENSITIVE_COLS   = ['route_structured']
CTX_SENSITIVE_LABELS = ['Rota Structured']
CTX_ORDER            = ['C0', 'C1', 'C2', 'C3']

# 5 categorias canônicas do corpus principal com labels curtos
_CANONICAL_CAT_LABELS = {
    'category-01-structural': 'Cat-01\nEstrutural',
    'category-02-linguistic': 'Cat-02\nLinguística',
    'category-03-domain':     'Cat-03\nDomínio',
    'category-04-vagueness':  'Cat-04\nVaguidade',
    'category-05-control':    'Cat-05\nControle',
}

# Mantidos para compatibilidade com código externo (evaluate.py importa DIM_COLS)
CAT_IDS          = list(_CANONICAL_CAT_LABELS.keys())
CAT_LABELS_SHORT = list(_CANONICAL_CAT_LABELS.values())


def _cats_from_data(df: pd.DataFrame):
    """Derive (cat_ids, cat_labels) from the data present in df.

    Uses the canonical mapping when standard corpus categories are present.
    Falls back to sorted unique values with generic labels for non-standard
    manifests (e.g. pilot with category_id='pilot').
    """
    present_standard = [c for c in CAT_IDS if c in df['category'].values]
    if present_standard:
        return present_standard, [_CANONICAL_CAT_LABELS[c] for c in present_standard]
    fallback = sorted(df['category'].dropna().unique())
    labels   = [
        _CANONICAL_CAT_LABELS.get(c, c.replace('category-', 'Cat-').replace('-', '\n').title())
        for c in fallback
    ]
    return fallback, labels


PASS_COLOR    = '#4caf50'
FAIL_COLOR    = '#ef5350'
NA_COLOR      = '#e0e0e0'
MODEL_PALETTE  = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a',
                  '#00838f', '#ad1457', '#558b2f', '#4527a0']
MODEL_LINES    = ['-', '--', '-.', ':', '-', '--', '-.', ':']
MODEL_MARKERS  = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']

LIFT_POS_COLOR  = '#2e7d32'   # lift=+1 (contexto resolveu)
LIFT_ZERO_COLOR = '#e0e0e0'   # lift= 0 (sem variação)
LIFT_NEG_COLOR  = '#c62828'   # lift=−1 (degradação)
STAGE_C01_COLOR = '#5c6bc0'   # ganho C0→C1
STAGE_C12_COLOR = '#26a69a'   # ganho C1→C2


# ── helpers ───────────────────────────────────────────────────────────────────

def _model_label(run_name: str) -> str:
    parts = run_name.split('__')
    return parts[1] if len(parts) >= 2 else run_name


def _model_labels(runs: list) -> dict:
    """Retorna {run_name: label} com sufixo numérico quando há runs duplicados do mesmo modelo."""
    base = {r: _model_label(r) for r in runs}
    from collections import Counter
    counts = Counter(base.values())
    seen: dict[str, int] = {}
    result = {}
    for run, label in base.items():
        if counts[label] > 1:
            seen[label] = seen.get(label, 0) + 1
            result[run] = f'{label} #{seen[label]}'
        else:
            result[run] = label
    return result


def _pct(series) -> float:
    vals = pd.Series(series).dropna()
    return float(vals.mean() * 100) if len(vals) else float('nan')


# ── BLOCO 1: Chart 1 — D1 precision/recall/specificity por modelo (C0 only) ──

def _d1_metrics(df_c0: pd.DataFrame, run: str) -> dict:
    """Calcula TP/FP/FN/TN e métricas derivadas para um run usando C0."""
    sub = df_c0[df_c0['run'] == run]
    tp = fp = fn = tn = 0
    for _, r in sub.iterrows():
        exp = r.get('expected_has_ambiguity')
        act = r.get('D1_has_ambiguity')
        if pd.isna(exp) or pd.isna(act):
            continue
        exp, act = bool(exp), bool(act)
        if exp and act:        tp += 1
        elif not exp and act:  fp += 1
        elif exp and not act:  fn += 1
        else:                  tn += 1
    precision   = tp / (tp + fp) if (tp + fp) > 0 else float('nan')
    recall      = tp / (tp + fn) if (tp + fn) > 0 else float('nan')
    specificity = tn / (tn + fp) if (tn + fp) > 0 else float('nan')
    f1 = (2 * precision * recall / (precision + recall)
          if not (math.isnan(precision) or math.isnan(recall) or (precision + recall) == 0)
          else float('nan'))
    return dict(tp=tp, fp=fp, fn=fn, tn=tn,
                precision=precision, recall=recall, specificity=specificity, f1=f1)


def _cell_color(val: float, col_vals: list, cmap_light='#e3f2fd', cmap_dark='#1565c0') -> tuple:
    """Gradiente de cor por coluna: valor baixo → azul claro, alto → azul escuro.
    Retorna (facecolor, textcolor).
    """
    finite = [v for v in col_vals if not math.isnan(v)]
    if not finite or math.isnan(val):
        return '#f5f5f5', '#000000'
    lo, hi = min(finite), max(finite)
    t = (val - lo) / (hi - lo) if hi > lo else 0.5

    def lerp(a, b, t):
        return int(a + (b - a) * t)

    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    r1, g1, b1 = hex_to_rgb(cmap_light)
    r2, g2, b2 = hex_to_rgb(cmap_dark)
    r, g, b = lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t)
    face = f'#{r:02x}{g:02x}{b:02x}'
    text = '#ffffff' if t > 0.55 else '#000000'
    return face, text


def chart_d1_classification(df: pd.DataFrame, out_dir: Path):
    """Tabela estilizada P/R/F1 por modelo (C0 only) — formato padrão NLP papers.

    Convenção ACL/EMNLP: bold para melhor valor por coluna, background mais escuro
    para segundo melhor. Gradiente de cor por coluna (azul claro → escuro).
    Seção de contagens TP/FP/FN/TN abaixo para transparência.
    N pequeno anotado no título — necessário para interpretação correta.
    """
    df_c0 = df[df['context'] == 'C0']
    runs  = sorted(df['run'].unique(), key=lambda r: -_d1_metrics(df_c0[df_c0['run'] == r], r)['f1'])
    lbls  = _model_labels(runs)

    metrics = ['precision', 'recall', 'f1']
    met_hdr = ['Precision', 'Recall', 'F1']
    all_m   = {run: _d1_metrics(df_c0, run) for run in runs}

    df_ref = df_c0[df_c0['run'] == runs[0]] if runs else df_c0
    n_c0   = len(df_ref)
    n_pos  = int(df_ref['expected_has_ambiguity'].sum()) if 'expected_has_ambiguity' in df_ref.columns else '?'
    n_neg  = n_c0 - n_pos if isinstance(n_pos, int) else '?'

    n_runs = len(runs)
    max_label_len = max((len(lbls[r]) for r in runs), default=8)
    fig_w  = max(9, 1.5 * len(metrics) + max_label_len * 0.14 + 3)
    fig_h  = max(4, 0.55 * (n_runs + 6) + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')

    # ── Seção principal: P / R / F1 ──────────────────────────────────────────
    # Cabeçalho + linha por modelo + separador + seção TP/FP/FN/TN
    count_rows = ['TP', 'FP', 'FN', 'TN']
    col_labels = ['Modelo'] + met_hdr + ['TP', 'FP', 'FN', 'TN']
    n_cols     = len(col_labels)

    # Valores por coluna para gradiente e rank
    col_vals   = {m: [all_m[r][m] for r in runs] for m in metrics}
    best_idx   = {m: int(np.nanargmax(col_vals[m])) for m in metrics}
    sorted_idx = {m: np.argsort([-v if not math.isnan(v) else float('inf')
                                 for v in col_vals[m]]) for m in metrics}
    second_idx = {m: int(sorted_idx[m][1]) if len(sorted_idx[m]) > 1 else None for m in metrics}

    cell_text = []
    for run in runs:
        m = all_m[run]
        row = [lbls[run]]
        for met in metrics:
            v = m[met]
            row.append(f'{v:.2f}' if not math.isnan(v) else '—')
        for k in ['tp', 'fp', 'fn', 'tn']:
            row.append(str(m[k]))
        cell_text.append(row)

    # Coluna Modelo recebe largura proporcional ao maior label; demais dividem o resto
    model_col_w = min(0.36, max(0.22, 0.017 * max_label_len + 0.06))
    n_data_cols = len(metrics) + 4
    data_col_w  = (1.0 - model_col_w) / n_data_cols
    tbl = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        colWidths=[model_col_w] + [data_col_w] * n_data_cols,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.8)

    # Estilo cabeçalho
    for j in range(n_cols):
        cell = tbl[(0, j)]
        cell.set_facecolor('#37474f')
        cell.set_text_props(color='white', fontweight='bold')

    # Estilo coluna Modelo
    for i, run in enumerate(runs):
        tbl[(i + 1, 0)].set_facecolor('#fafafa')
        tbl[(i + 1, 0)].set_text_props(fontweight='bold')

    # Gradiente + bold/second-best nas colunas de métricas
    for j, met in enumerate(metrics):
        col_j = j + 1
        vals  = col_vals[met]
        for i, run in enumerate(runs):
            val  = all_m[run][met]
            face, text = _cell_color(val, vals)
            cell = tbl[(i + 1, col_j)]
            cell.set_facecolor(face)
            cell.set_text_props(color=text)
            if i == best_idx[met]:
                cell.set_text_props(color=text, fontweight='bold')
            elif second_idx[met] is not None and i == second_idx[met]:
                # Segundo melhor: fundo ligeiramente mais claro, texto sublinhado simulado
                # com asterisco (underline não suportado em matplotlib)
                cur = cell.get_text().get_text()
                cell.get_text().set_text(cur + ' *')

    # Estilo colunas TP/FP/FN/TN
    count_colors = {'TP': '#c8e6c9', 'FP': '#ffe0b2', 'FN': '#bbdefb', 'TN': '#c8e6c9'}
    for j, k in enumerate(['tp', 'fp', 'fn', 'tn']):
        col_j = len(metrics) + 1 + j
        # Cabeçalho da sub-seção
        tbl[(0, col_j)].set_facecolor('#546e7a')
        for i in range(n_runs):
            tbl[(i + 1, col_j)].set_facecolor(count_colors[k.upper()])

    # Separador visual entre métricas e contagens via cor de borda
    for i in range(n_runs + 1):
        tbl[(i, len(metrics))].visible_edges = 'BRTL'

    fig.suptitle(
        'D1 — Detecção de Ambiguidade: Precision / Recall / F1 por modelo (C0 only)\n'
        f'N={n_c0} req por modelo  ·  Positivos: {n_pos}  ·  Negativos: {n_neg}  '
        '·  * = segundo melhor por coluna  ·  bold = melhor',
        fontsize=9, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'd1_classification.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


def chart_d1_scatter_pr(df: pd.DataFrame, out_dir: Path):
    """Scatter Precision × Recall com iso-curvas de F1 (C0 only).

    Cada ponto = um modelo. Linhas de iso-F1 mostram contexto imediato
    do trade-off. Complementa a tabela quando o argumento é sobre
    onde cada modelo falha (alta precision vs. alto recall).
    """
    df_c0 = df[df['context'] == 'C0']
    runs  = sorted(df['run'].unique())
    lbls  = _model_labels(runs)
    all_m = {run: _d1_metrics(df_c0, run) for run in runs}

    fig, ax = plt.subplots(figsize=(8, 6))

    # Iso-curvas de F1
    r_range = np.linspace(0.01, 1.0, 300)
    for f1_val in [0.2, 0.4, 0.6, 0.8, 0.9]:
        p_range = f1_val * r_range / (2 * r_range - f1_val)
        mask    = (p_range >= 0) & (p_range <= 1)
        if mask.any():
            ax.plot(r_range[mask], p_range[mask], '--', color='#bdbdbd',
                    linewidth=0.8, zorder=1)
            xi = r_range[mask][-1]
            yi = p_range[mask][-1]
            ax.annotate(f'F1={f1_val:.1f}', (xi, yi),
                        fontsize=7, color='#9e9e9e',
                        textcoords='offset points', xytext=(4, 0), va='center')

    # Detecta posições sobrepostas — pontos ficam no lugar exato;
    # só os labels recebem offsets distintos para não se sobrepor.
    from collections import defaultdict
    pos_groups: dict = defaultdict(list)
    for run in runs:
        m = all_m[run]
        p, r = m['precision'], m['recall']
        if math.isnan(p) or math.isnan(r):
            continue
        key = (round(r, 3), round(p, 3))
        pos_groups[key].append(run)

    # Sequência de offsets de texto que evita sobreposição de labels
    _label_offsets = [(8, 8), (8, -14), (-8, 8), (-8, -14), (16, 0), (-16, 0)]
    run_annot_off: dict = {}
    for key, group in pos_groups.items():
        for i, run in enumerate(group):
            run_annot_off[run] = _label_offsets[i % len(_label_offsets)]

    # Pontos dos modelos — posição sempre exata (sem jitter)
    for run, color, mk in zip(runs, MODEL_PALETTE, MODEL_MARKERS):
        m = all_m[run]
        p, r = m['precision'], m['recall']
        if math.isnan(p) or math.isnan(r):
            continue
        xoff, yoff = run_annot_off.get(run, (8, 8))
        ax.scatter(r, p, color=color, marker=mk, s=100, zorder=3,
                   label=lbls[run], edgecolors='white', linewidths=0.7)
        ax.annotate(lbls[run], (r, p),
                    textcoords='offset points', xytext=(xoff, yoff),
                    fontsize=8, color=color, fontweight='bold')

    ax.set_xlim(-0.05, 1.15)
    ax.set_ylim(-0.05, 1.15)
    ax.set_xlabel('Recall', fontsize=11)
    ax.set_ylabel('Precision', fontsize=11)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)

    df_ref = df_c0[df_c0['run'] == runs[0]] if runs else df_c0
    n_c0   = len(df_ref)
    n_pos  = int(df_ref['expected_has_ambiguity'].sum()) if 'expected_has_ambiguity' in df_ref.columns else '?'
    ax.set_title(
        'D1 — Trade-off Precision × Recall por modelo (C0 only)\n'
        f'N={n_c0} req  ·  Positivos: {n_pos}  ·  Linhas tracejadas = iso-F1',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'd1_scatter_pr.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 1: Chart 2 — FP/FN de D1 por categoria (C0 only) ──────────────────

def chart_error_type_bar(df: pd.DataFrame, out_dir: Path):
    """Diagnóstico de erros D1 por categoria — dois painéis verticais (C0 only).

    Painel superior: FN por categoria positiva (Cat-02/03/04)
      → "Qual tipo de ambiguidade o modelo não detecta?"
    Painel inferior: FP por categoria de controle (Cat-01/05)
      → "O modelo acusa ambiguidade onde não existe?"

    Modelos como grupos de barras por categoria. Escala Y compartilhada.
    """
    df_c0  = df[df['context'] == 'C0'].copy()
    runs   = sorted(df['run'].unique())
    lbls   = _model_labels(runs)
    n_runs = len(runs)

    # Separa categorias positivas e de controle a partir dos dados
    pos_mask = df_c0['expected_has_ambiguity'].astype(str) == 'True'
    pos_cats = sorted(df_c0[pos_mask]['category'].dropna().unique())
    neg_cats = sorted(df_c0[~pos_mask]['category'].dropna().unique())

    def _cat_label(c):
        return _CANONICAL_CAT_LABELS.get(c, c.replace('category-', 'Cat-'))

    pos_labels = [_cat_label(c) for c in pos_cats]
    neg_labels = [_cat_label(c) for c in neg_cats]

    def _count(sub, cat, expect_positive: bool) -> int:
        s = sub[sub['category'] == cat]
        total = 0
        for _, row in s.iterrows():
            exp = row.get('expected_has_ambiguity')
            act = row.get('D1_has_ambiguity')
            if pd.isna(exp) or pd.isna(act):
                continue
            exp_b, act_b = bool(exp), bool(act)
            if expect_positive and exp_b and not act_b:   # FN
                total += 1
            elif not expect_positive and not exp_b and act_b:  # FP
                total += 1
        return total

    # Geometria das barras
    bar_w   = min(0.11, 0.65 / max(n_runs, 1))
    offsets = np.linspace(-(n_runs - 1) / 2, (n_runs - 1) / 2, n_runs) * bar_w

    # Escala Y compartilhada
    all_vals = (
        [_count(df_c0[df_c0['run'] == r], c, True)  for r in runs for c in pos_cats] +
        [_count(df_c0[df_c0['run'] == r], c, False) for r in runs for c in neg_cats]
    )
    y_max = max(all_vals + [1]) + 0.8

    n_pos = max(len(pos_cats), 1)
    n_neg = max(len(neg_cats), 1)
    fig_w = max(9, (n_pos + n_neg) * (n_runs * bar_w + 0.6) + 2)
    fig, (ax_fn, ax_fp) = plt.subplots(
        2, 1, figsize=(fig_w, 8),
        gridspec_kw={'hspace': 0.50},
    )

    for j, (run, color) in enumerate(zip(runs, MODEL_PALETTE)):
        sub = df_c0[df_c0['run'] == run]
        lbl = lbls[run]

        # Painel FN
        fn_vals = [_count(sub, c, True) for c in pos_cats]
        bars = ax_fn.bar(np.arange(n_pos) + offsets[j], fn_vals, bar_w,
                         color=color, label=lbl, edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, fn_vals):
            if val > 0:
                ax_fn.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.06,
                           str(val), ha='center', va='bottom',
                           fontsize=8, color=color, fontweight='bold')

        # Painel FP
        fp_vals = [_count(sub, c, False) for c in neg_cats]
        bars = ax_fp.bar(np.arange(n_neg) + offsets[j], fp_vals, bar_w,
                         color=color, label=lbl, edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, fp_vals):
            if val > 0:
                ax_fp.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.06,
                           str(val), ha='center', va='bottom',
                           fontsize=8, color=color, fontweight='bold')

    for ax, x_n, labels, ylabel, title in [
        (ax_fn, n_pos, pos_labels, 'Nº de FN',
         'Falsos Negativos — categorias positivas\n'
         '"Qual tipo de ambiguidade o modelo não detecta?"'),
        (ax_fp, n_neg, neg_labels, 'Nº de FP',
         'Falsos Positivos — categorias de controle\n'
         '"O modelo acusa ambiguidade onde não existe?"'),
    ]:
        ax.set_xticks(np.arange(x_n))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_ylim(0, y_max)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)

    handles, labels = ax_fn.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center',
               ncol=min(n_runs, 4), fontsize=9,
               bbox_to_anchor=(0.5, -0.04), frameon=True)

    fig.suptitle(
        'D1 Ambiguidade — Diagnóstico de erros por categoria (C0 only)\n'
        'Positivos: Cat-02 / 03 / 04  ·  Controle: Cat-01 / Cat-05',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'error_type__D1_ambiguidade.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 2: Chart 3 — D3/D4 por condição de contexto (RQ1) ─────────────────



# ── CONTEXT LIFT: Chart 5 — ΔD3(C2−C0) e staged gains (contribuição central) ─

def _stacked_lift(ax, x, width, pos, zero, neg, label_pos, label_zero, label_neg, y_max):
    """Helper: stacked bar +1/0/−1 com rótulos centrados em cada segmento."""
    bot1 = pos
    bot2 = [a + b for a, b in zip(pos, zero)]
    bars_p = ax.bar(x, pos,  width, color=LIFT_POS_COLOR,  label=label_pos)
    bars_z = ax.bar(x, zero, width, bottom=bot1, color=LIFT_ZERO_COLOR, label=label_zero)
    bars_n = ax.bar(x, neg,  width, bottom=bot2, color=LIFT_NEG_COLOR,  label=label_neg)
    for bar, val, bot in ([(b, v, 0)   for b, v in zip(bars_p, pos)]  +
                          [(b, v, p)   for b, v, p in zip(bars_z, zero, bot1)] +
                          [(b, v, p)   for b, v, p in zip(bars_n, neg,  bot2)]):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bot + val / 2,
                    str(val), ha='center', va='center', fontsize=9,
                    color='white', fontweight='bold')
    ax.set_ylim(0, y_max)
    ax.yaxis.grid(True, linestyle='--', alpha=0.35)
    ax.set_axisbelow(True)


def chart_context_lift(df: pd.DataFrame, df_lift: pd.DataFrame, out_dir: Path):
    """Layout 2×2 — Context Sensitivity (apenas req com expected_has_ambiguity=True).

      (a) top-left  — Line chart: % structured por condição C0→C1→C2→C3
      (b) top-right — Stacked bar: ΔRoute(C2−C0) +1/0/−1 por modelo
      (c) bot-left  — Delta bars: ganhos por etapa C0→C1 e C1→C2
      (d) bot-right — Delta_c2_c3: efeito puro de relevância (quando C3 presente)

    Narrativa: curva geral (a) → efeito agregado (b) → onde acontece (c) → é legítimo? (d)
    Escala Y compartilhada entre (b), (c) e (d) = N req ambíguos.
    """
    df_amb = df_lift[df_lift['expected_has_ambiguity'].astype(str) == 'True'].copy()

    if df_amb.empty:
        print('  [WARN] context_lift: nenhum req com expected_has_ambiguity=True — gráfico ignorado')
        return

    runs   = sorted(df_lift['run'].unique())
    lbls   = _model_labels(runs)
    n      = len(df_amb[df_amb['run'] == runs[0]])
    y_max  = n * 1.18
    has_c3 = 'lift_c3_c0' in df_amb.columns and df_amb['lift_c3_c0'].notna().any()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_line, ax_lift  = axes[0, 0], axes[0, 1]
    ax_stage, ax_rel  = axes[1, 0], axes[1, 1]

    x     = np.arange(len(runs))
    width = 0.55

    # ── (a) Line chart — % structured nos req ambíguos por condição ──────────
    df_amb_full = df[df['expected_has_ambiguity'].astype(str) == 'True'].copy() \
        if 'expected_has_ambiguity' in df.columns else pd.DataFrame()

    ctxs       = [c for c in CTX_ORDER if c in df_amb_full['context'].values] \
        if not df_amb_full.empty else ['C0', 'C1', 'C2']
    ctx_labels = {'C0': 'C0\n(sem ctx)', 'C1': 'C1\n(genérico)',
                  'C2': 'C2\n(específico)', 'C3': 'C3\n(irrelevante)'}
    x_labels   = [ctx_labels.get(c, c) for c in ctxs]

    for run, color, ls, mk in zip(runs, MODEL_PALETTE, MODEL_LINES, MODEL_MARKERS):
        sub  = df_amb_full[df_amb_full['run'] == run] if not df_amb_full.empty else pd.DataFrame()
        vals = [_pct(sub[sub['context'] == ctx]['route_structured']) for ctx in ctxs]
        ax_line.plot(x_labels, vals, linestyle=ls, marker=mk, linewidth=2, color=color,
                     label=lbls[run], markersize=7, zorder=3)
        for xlbl, val in zip(x_labels, vals):
            if not math.isnan(val):
                ax_line.annotate(f'{val:.0f}%', (xlbl, val),
                                 textcoords='offset points', xytext=(0, 9),
                                 ha='center', fontsize=8, color=color, fontweight='bold')

    if has_c3 and len(ctxs) >= 4:
        ax_line.axvline(x=2.5, color='#bdbdbd', linewidth=1, linestyle='--', zorder=1)
        ax_line.text(2.6, 3, 'controle\nirrelevante', fontsize=7.5, color='#9e9e9e', va='bottom')

    ax_line.set_ylim(0, 115)
    ax_line.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax_line.set_axisbelow(True)
    ax_line.set_ylabel('% rota structured', fontsize=10)
    ax_line.set_title(f'Curva de comportamento por condição\n(N={n} req ambíguos por modelo)',
                      fontsize=10, fontweight='bold')
    handles, labels = ax_line.get_legend_handles_labels()
    ax_line.legend(handles, labels, fontsize=8, loc='lower right',
                   ncol=max(1, len(runs) // 4))

    # ── (b) Stacked bar — ΔRoute(C2−C0) ─────────────────────────────────────
    lift_pos  = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == 1)])  for r in runs]
    lift_zero = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == 0)])  for r in runs]
    lift_neg  = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == -1)]) for r in runs]

    _stacked_lift(ax_lift, x, width, lift_pos, lift_zero, lift_neg,
                  'lift=+1 (resolveu)', 'lift= 0 (sem variação)', 'lift=−1 (degradação)', y_max)
    ax_lift.set_title(f'ΔRoute(C2 − C0) — efeito total\n(N={n} req ambíguos)',
                      fontsize=10, fontweight='bold')
    ax_lift.set_xticks(x)
    ax_lift.set_xticklabels([lbls[r] for r in runs], fontsize=9, rotation=15, ha='right')
    ax_lift.set_ylabel('Nº de requisitos', fontsize=10)
    ax_lift.legend(fontsize=8.5, loc='upper right')

    # ── (c) Delta bars — ganhos por etapa ────────────────────────────────────
    width_s  = 0.35
    gain_c01 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c0_c1'] == 1)]) for r in runs]
    gain_c12 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c1_c2'] == 1)]) for r in runs]
    loss_c01 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c0_c1'] == -1)]) for r in runs]
    loss_c12 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c1_c2'] == -1)]) for r in runs]

    b01 = ax_stage.bar(x - width_s / 2, gain_c01, width_s,
                       color=STAGE_C01_COLOR, label='C0→C1 (ctx genérico)')
    b12 = ax_stage.bar(x + width_s / 2, gain_c12, width_s,
                       color=STAGE_C12_COLOR, label='C1→C2 (ctx específico)')

    for bar, val in list(zip(b01, gain_c01)) + list(zip(b12, gain_c12)):
        ax_stage.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                      str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')

    for i, (l01, l12) in enumerate(zip(loss_c01, loss_c12)):
        if l01 > 0:
            ax_stage.text(x[i] - width_s / 2, -0.3, f'−{l01}',
                          ha='center', va='top', fontsize=8, color=LIFT_NEG_COLOR)
        if l12 > 0:
            ax_stage.text(x[i] + width_s / 2, -0.3, f'−{l12}',
                          ha='center', va='top', fontsize=8, color=LIFT_NEG_COLOR)

    ax_stage.set_title(f'Ganhos por etapa — onde o contexto ajuda?\n(N={n} req ambíguos)',
                       fontsize=10, fontweight='bold')
    ax_stage.set_xticks(x)
    ax_stage.set_xticklabels([lbls[r] for r in runs], fontsize=9, rotation=15, ha='right')
    ax_stage.set_ylabel('Nº de requisitos com ganho', fontsize=10)
    ax_stage.set_ylim(0, y_max)
    ax_stage.yaxis.grid(True, linestyle='--', alpha=0.35)
    ax_stage.set_axisbelow(True)
    ax_stage.legend(fontsize=8.5, loc='upper right')

    # ── (d) Delta_c2_c3 — efeito puro de relevância ──────────────────────────
    if has_c3:
        df_c3   = df_amb[df_amb['lift_c3_c0'].notna()]
        runs_c3 = [r for r in runs if len(df_c3[df_c3['run'] == r]) > 0]
        x_c3    = np.arange(len(runs_c3))
        n_c3    = len(df_c3[df_c3['run'] == runs_c3[0]]) if runs_c3 else n

        rel_disc = [len(df_c3[(df_c3['run'] == r) & (df_c3['delta_c2_c3'] == 1)]) for r in runs_c3]
        rel_zero = [len(df_c3[(df_c3['run'] == r) & (df_c3['delta_c2_c3'] == 0)]) for r in runs_c3]
        rel_neg  = [len(df_c3[(df_c3['run'] == r) & (df_c3['delta_c2_c3'] == -1)]) for r in runs_c3]

        _stacked_lift(ax_rel, x_c3, width, rel_disc, rel_zero, rel_neg,
                      'C2>C3 (relevância resolveu)', 'C2=C3 (sem discriminação)',
                      'C2<C3 (irrelevante foi melhor)', y_max)
        ax_rel.set_title(f'Δ(C2 − C3) — efeito puro de relevância\n(N={n_c3} req com C3)',
                         fontsize=10, fontweight='bold')
        ax_rel.set_xticks(x_c3)
        ax_rel.set_xticklabels([lbls[r] for r in runs_c3], fontsize=9, rotation=15, ha='right')
        ax_rel.set_ylabel('Nº de requisitos', fontsize=10)
        ax_rel.legend(fontsize=8, loc='upper right')
    else:
        ax_rel.set_visible(False)

    subtitle = ('(d) Δ(C2−C3) isola efeito puro de relevância vs. especificidade'
                if has_c3 else '')
    fig.suptitle(
        'Context Sensitivity — como o contexto altera a rota do modelo\n'
        + subtitle,
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'context_lift__route_delta.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── DIAGNÓSTICO: Chart 6 — heatmap D1 req×modelo (C0 only) ──────────────────

def chart_heatmap(df: pd.DataFrame, out_dir: Path):
    """Matriz req × modelo para D1 (C0 only) — diagnóstico granular.

    Linhas = requisitos, colunas = modelos.
    Verde = detecção correta, Vermelho = erro, Cinza = N/A.
    Permite identificar quais requisitos são difíceis para todos os modelos
    e quais modelos têm padrões de erro distintos.
    """
    df_c0 = df[df['context'] == 'C0']
    reqs  = sorted(df_c0['req_id'].unique())
    runs  = sorted(df_c0['run'].unique())
    lbls  = _model_labels(runs)

    fig, ax = plt.subplots(figsize=(max(5, 1.8 * len(runs) + 1.5),
                                    max(4, 0.7 * len(reqs) + 1.5)))

    for i, req in enumerate(reqs):
        for j, run in enumerate(runs):
            cell = df_c0[(df_c0['req_id'] == req) & (df_c0['run'] == run)]['D1_has_ambiguity']
            if len(cell) == 0 or cell.isna().all():
                val, color, symbol = None, NA_COLOR, '—'
            else:
                val    = bool(cell.iloc[0])
                color  = PASS_COLOR if val else FAIL_COLOR
                symbol = '✓' if val else '✗'
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=color,
                                       linewidth=0.5, edgecolor='white'))
            ax.text(j + 0.5, i + 0.5, symbol, ha='center', va='center',
                    fontsize=11, color='white' if val is not None else '#888',
                    fontweight='bold')

    ax.set_xlim(0, len(runs))
    ax.set_ylim(0, len(reqs))
    ax.set_xticks([j + 0.5 for j in range(len(runs))])
    ax.set_xticklabels([lbls[r] for r in runs], fontsize=9)
    ax.set_yticks([i + 0.5 for i in range(len(reqs))])

    # Rótulo da linha: req_id + indicador positivo/negativo
    def _req_label(req_id: str) -> str:
        row = df_c0[df_c0['req_id'] == req_id]
        if not len(row):
            return req_id
        exp = row.iloc[0].get('expected_has_ambiguity')
        tag = '(+)' if exp else '(−)'
        return f'{req_id}  {tag}'

    ax.set_yticklabels([_req_label(r) for r in reqs], fontsize=8.5)
    ax.invert_yaxis()
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')

    legend = [mpatches.Patch(color=PASS_COLOR, label='Correto (✓)'),
              mpatches.Patch(color=FAIL_COLOR,  label='Incorreto (✗)'),
              mpatches.Patch(color=NA_COLOR,    label='N/A')]
    fig.legend(handles=legend, loc='lower center', ncol=3, fontsize=9,
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle(
        'D1 — Detecção de ambiguidade: req × modelo (C0 only)\n'
        '(+) = positivo esperado  ·  (−) = negativo esperado (controle)',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'heatmap__D1_req_modelo.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── DIAGNÓSTICO: Chart 7 — taxonomia de Pohl (Agente 1a) ─────────────────────

_TAX_EXACT_COLOR = '#2e7d32'    # verde  — todos os aceitos presentes, sem extras
_TAX_OVER_COLOR  = '#f9a825'    # amarelo — aceito presente, mas há tipos extras
_TAX_MISS_COLOR  = '#c62828'    # vermelho — nenhum tipo aceito detectado


def _taxonomy_result(accepted_str: str, detected_str: str):
    """Classify a taxonomy cell as 'exact', 'over', or 'miss'.

    accepted_types is an OR list — any one accepted type present is a valid hit.

    Returns ('exact', color) when every detected type is within the accepted set
                             (detected ⊆ accepted) and at least one matches.
    Returns ('over',  color) when at least one accepted type is detected but the
                             agent also produced types outside the accepted set.
    Returns ('miss',  color) when no accepted type appears in detected.
    """
    accepted = {t.strip() for t in accepted_str.split(',') if t.strip()}
    detected = {t.strip() for t in detected_str.split(',')
                if t.strip() and t.strip() != '(nenhuma)'}
    if not accepted:
        return 'n/a', NA_COLOR
    hit = accepted & detected
    if not hit:
        return 'miss', _TAX_MISS_COLOR
    if detected <= accepted:
        return 'exact', _TAX_EXACT_COLOR
    return 'over', _TAX_OVER_COLOR


def chart_taxonomy_grid(df: pd.DataFrame, out_dir: Path):
    """Matriz de confusão Pohl — tipo aceito × tipo detectado (agregado por todos os modelos).

    Responde: "Quando erra, confunde qual tipo com qual?"
    Verdadeiro (Y) = primeiro tipo aceito por requisito (OR list → primeiro elemento).
    Predito (X)    = tipo detectado; "múltiplos" quando o agente retornou mais de um tipo.
    Borda verde = diagonal (acerto). Linha tracejada separa tipos canônicos de categorias especiais.
    """
    from matplotlib.colors import LinearSegmentedColormap

    records = []
    for _, row in df.iterrows():
        accepted_str  = str(row.get('accepted_types', ''))
        detected_str  = str(row.get('detected_types', ''))
        accepted_list = [t.strip() for t in accepted_str.split(',') if t.strip()]
        detected_list = [t.strip() for t in detected_str.split(',')
                         if t.strip() and t.strip().lower() != '(nenhuma)']
        if not accepted_list:
            continue
        true_type = accepted_list[0]
        if not detected_list:
            pred_type = 'nenhum'
        elif len(detected_list) == 1:
            pred_type = detected_list[0]
        else:
            pred_type = 'múltiplos'
        records.append((true_type, pred_type))

    if not records:
        print('  [WARN] taxonomy_classification: sem dados para matriz de confusão')
        return

    true_types  = sorted({r[0] for r in records})
    # X inclui todos os tipos do ground truth + quaisquer tipos extras detectados
    # Isso garante que tipos nunca preditos apareçam como coluna de zeros (informação relevante)
    pred_single = sorted(
        set(true_types) | {r[1] for r in records if r[1] not in ('múltiplos', 'nenhum')}
    )
    specials    = [t for t in ('múltiplos', 'nenhum') if any(r[1] == t for r in records)]
    pred_types  = pred_single + specials

    n_true  = len(true_types)
    n_pred  = len(pred_types)
    matrix  = np.zeros((n_true, n_pred), dtype=int)
    for true, pred in records:
        matrix[true_types.index(true), pred_types.index(pred)] += 1

    total_n = len(records)
    n_runs  = len(df['run'].unique()) if 'run' in df.columns else 1
    n_reqs  = len(df['req_id'].unique()) if 'req_id' in df.columns else total_n

    fig, ax = plt.subplots(figsize=(max(6, 1.6 * n_pred + 1.5),
                                    max(4, 1.3 * n_true + 2.0)))

    cmap = LinearSegmentedColormap.from_list('conf_blue', ['#ffffff', '#1565c0'])
    im   = ax.imshow(matrix, cmap=cmap, aspect='auto',
                     vmin=0, vmax=max(matrix.max(), 1))

    threshold = matrix.max() * 0.55
    for i in range(n_true):
        for j in range(n_pred):
            val = matrix[i, j]
            pct = val / total_n * 100 if total_n > 0 else 0
            tc  = 'white' if val > threshold else '#212121'
            ax.text(j, i, f'{val}\n({pct:.0f}%)',
                    ha='center', va='center', fontsize=9, color=tc,
                    fontweight='bold' if val > 0 else 'normal')

    # Borda verde na diagonal onde pred == true
    for i, tt in enumerate(true_types):
        if tt in pred_types:
            j = pred_types.index(tt)
            ax.add_patch(plt.Rectangle(
                (j - 0.5, i - 0.5), 1, 1,
                fill=False, edgecolor='#43a047', linewidth=2.5, zorder=3,
            ))

    # Separador antes de colunas especiais
    if specials:
        ax.axvline(x=len(pred_single) - 0.5, color='#9e9e9e',
                   linewidth=1.2, linestyle='--', zorder=2)

    ax.set_xticks(range(n_pred))
    ax.set_xticklabels(pred_types, fontsize=10)
    ax.set_yticks(range(n_true))
    ax.set_yticklabels(true_types, fontsize=10)
    ax.set_xlabel('Tipo detectado pelo Agente 1a', fontsize=11, labelpad=8)
    ax.set_ylabel('Tipo aceito (ground truth)', fontsize=11, labelpad=8)

    plt.colorbar(im, ax=ax, shrink=0.75, pad=0.02, label='Nº de ocorrências')

    ax.set_title(
        'Matriz de Confusão — Taxonomia Pohl (Agente 1a)\n'
        f'{n_runs} modelo(s) × {n_reqs} requisitos = N={total_n} classificações\n'
        'Borda verde = acerto  ·  "múltiplos" = agente retornou mais de um tipo',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'taxonomy_classification.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── DIAGNÓSTICO: Chart 8b — acurácia por tipo Pohl × modelo ─────────────────

def chart_taxonomy_model_heatmap(df: pd.DataFrame, out_dir: Path):
    """Heatmap modelo × tipo Pohl — % de acerto por célula (Agente 1a).

    Pergunta: "Os modelos erram nos mesmos tipos ou cada um tem pontos cegos distintos?"
    Padrão uniforme → problema de prompt do agente.
    Padrão heterogêneo → capacidade diferente por modelo/família.

    'Acerto' = resultado 'exact' de _taxonomy_result (detected ⊆ accepted, hit ≠ ∅).
    True type = primeiro tipo da lista accepted_types (OR list → canônico).
    """
    from matplotlib.colors import LinearSegmentedColormap

    runs  = sorted(df['run'].unique())
    lbls  = _model_labels(runs)

    # Coleta tipos verdadeiros canônicos (primeiro da OR list)
    true_types = sorted({
        str(row.get('accepted_types', '')).split(',')[0].strip()
        for _, row in df.iterrows()
        if str(row.get('accepted_types', '')).strip()
    })

    n_runs  = len(runs)
    n_types = len(true_types)
    matrix  = np.full((n_runs, n_types), np.nan)
    totals  = np.zeros((n_runs, n_types), dtype=int)

    for i, run in enumerate(runs):
        sub = df[df['run'] == run]
        for j, ttype in enumerate(true_types):
            hits = []
            for _, row in sub.iterrows():
                accepted_str  = str(row.get('accepted_types', ''))
                accepted_list = [t.strip() for t in accepted_str.split(',') if t.strip()]
                if not accepted_list or accepted_list[0] != ttype:
                    continue
                detected_str = str(row.get('detected_types', ''))
                result, _    = _taxonomy_result(accepted_str, detected_str)
                hits.append(result == 'exact')
            if hits:
                matrix[i, j]  = sum(hits) / len(hits) * 100
                totals[i, j]  = len(hits)

    fig, ax = plt.subplots(figsize=(max(5, 1.5 * n_types + 1.5),
                                    max(3, 0.85 * n_runs + 1.8)))

    # Escala divergente: vermelho (0%) → branco (50%) → verde (100%)
    cmap = LinearSegmentedColormap.from_list('acc', ['#c62828', '#ffffff', '#2e7d32'])
    im   = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=100)

    for i in range(n_runs):
        for j in range(n_types):
            val = matrix[i, j]
            n   = totals[i, j]
            if np.isnan(val):
                ax.text(j, i, 'N/A', ha='center', va='center',
                        fontsize=9, color='#9e9e9e')
            else:
                tc = 'white' if (val > 65 or val < 25) else '#212121'
                ax.text(j, i, f'{val:.0f}%\n(N={n})',
                        ha='center', va='center', fontsize=9, color=tc,
                        fontweight='bold' if val > 0 else 'normal')

    ax.set_xticks(range(n_types))
    ax.set_xticklabels(true_types, fontsize=10)
    ax.set_yticks(range(n_runs))
    ax.set_yticklabels([lbls[r] for r in runs], fontsize=10)
    ax.set_xlabel('Tipo Pohl (ground truth)', fontsize=11, labelpad=8)
    ax.set_ylabel('Modelo', fontsize=11, labelpad=8)

    plt.colorbar(im, ax=ax, shrink=0.80, pad=0.02, label='% de acerto')

    ax.set_title(
        'Acurácia por tipo Pohl × modelo — Agente 1a\n'
        'Padrão uniforme → problema de prompt  ·  Heterogêneo → capacidade diferente por modelo',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'taxonomy_model_heatmap.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── DIAGNÓSTICO COMPLEMENTAR: D3 summary table ───────────────────────────────

def table_d_output_summary(df: pd.DataFrame, out_dir: Path):
    """Tabela resumo D_output_integrity por modelo × condição de contexto.

    Gera d_output_summary.csv e d_output_summary_table.png.
    D_output mede se o output estrutural do pipeline está íntegro dado a rota tomada:
      - rota structured → ao menos um structured_requirement com final_statement preenchido
      - rota signaling  → ao menos um item com resolubility_status unresolved/non_resolvable
    """
    col = 'D_output_integrity'
    if col not in df.columns:
        print(f'  [WARN] {col} não encontrada — tabela D_output ignorada')
        return

    runs      = sorted(df['run'].unique())
    ctxs      = [c for c in CTX_ORDER if c in df['context'].values]

    # Build table: rows=modelos, cols=condições + média geral
    records = []
    for run in runs:
        sub = df[df['run'] == run]
        row = {'Modelo': _model_label(run)}
        for ctx in ctxs:
            val = _pct(sub[sub['context'] == ctx][col])
            row[ctx] = round(val, 1) if not math.isnan(val) else None
        all_vals = sub[col].dropna()
        row['Média'] = round(float(all_vals.mean() * 100), 1) if len(all_vals) else None
        records.append(row)

    tbl = pd.DataFrame(records)

    # Save CSV
    csv_path = out_dir / 'd_output_summary.csv'
    tbl.to_csv(csv_path, index=False)
    print(f'  Salvo: {csv_path.name}')

    # Render as PNG table
    col_labels = ['Modelo'] + ctxs + ['Média']
    cell_text  = []
    for _, row in tbl.iterrows():
        cell_text.append([
            str(row['Modelo']),
            *[f'{row[c]:.1f}%' if row[c] is not None else '—' for c in ctxs],
            f'{row["Média"]:.1f}%' if row['Média'] is not None else '—',
        ])

    fig, ax = plt.subplots(figsize=(2.2 * len(col_labels), 0.55 * (len(runs) + 2)))
    ax.axis('off')

    tbl_obj = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc='center',
        loc='center',
    )
    tbl_obj.auto_set_font_size(False)
    tbl_obj.set_fontsize(10)
    tbl_obj.scale(1, 1.6)

    # Style header row
    for j in range(len(col_labels)):
        tbl_obj[(0, j)].set_facecolor('#37474f')
        tbl_obj[(0, j)].set_text_props(color='white', fontweight='bold')

    # Style "Média" column
    media_col = len(col_labels) - 1
    for i in range(1, len(runs) + 1):
        tbl_obj[(i, media_col)].set_facecolor('#eceff1')
        tbl_obj[(i, media_col)].set_text_props(fontweight='bold')

    # Alternate row shading
    for i in range(1, len(runs) + 1):
        if i % 2 == 0:
            for j in range(len(col_labels) - 1):
                tbl_obj[(i, j)].set_facecolor('#f5f5f5')

    fig.suptitle(
        'D_output — Integridade estrutural do output por modelo e condição de contexto\n'
        '(structured → final_statement preenchido  ·  signaling → ao menos um item unresolved)',
        fontsize=10, fontweight='bold', y=0.98,
    )
    plt.tight_layout()
    out_path = out_dir / 'd_output_summary_table.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 1: Export CSV — métricas D1 por modelo (C0 only) ───────────────────

def export_d1_metrics_csv(df: pd.DataFrame, out_dir: Path):
    """Exporta P/R/F1/Specificity + TP/FP/FN/TN por modelo em CSV (C0 only).

    Complementa o scatter e a tabela PNG com dados brutos para inclusão em
    texto ou tabelas LaTeX/Word do capítulo de Resultados.
    """
    df_c0 = df[df['context'] == 'C0']
    runs  = sorted(df['run'].unique())
    lbls  = _model_labels(runs)
    rows  = []
    for run in runs:
        m = _d1_metrics(df_c0, run)
        rows.append({
            'modelo':      lbls[run],
            'run':         run,
            'precision':   round(m['precision'],   3) if not math.isnan(m['precision'])   else None,
            'recall':      round(m['recall'],      3) if not math.isnan(m['recall'])      else None,
            'f1':          round(m['f1'],          3) if not math.isnan(m['f1'])          else None,
            'specificity': round(m['specificity'], 3) if not math.isnan(m['specificity']) else None,
            'TP': m['tp'], 'FP': m['fp'], 'FN': m['fn'], 'TN': m['tn'],
        })
    tbl = pd.DataFrame(rows)
    csv_path = out_dir / 'd1_metrics.csv'
    tbl.to_csv(csv_path, index=False)
    print(f'  Salvo: {csv_path.name}')


# ── BLOCO 3: Heatmap acerto taxonômico por categoria × modelo ─────────────────

def chart_taxonomy_category_heatmap(df_tax: pd.DataFrame, df_eval: pd.DataFrame,
                                    out_dir: Path):
    """Heatmap % acerto por categoria do corpus (Cat-02/03/04) × modelo.

    Complementa chart_taxonomy_model_heatmap (que agrupa por tipo Pohl) mostrando
    o acerto consolidado por categoria do corpus — pergunta central de RQ3:
    "Qual categoria de defeito é mais difícil de classificar?"

    Cat-02 = linguística  (ambiguidades sintáticas/referenciais/lógicas)
    Cat-03 = domínio      (lexicais/semânticas dependentes de contexto)
    Cat-04 = vaguidade    (quantificadores, termos de fronteira)

    Cada célula mostra % de itens com match=True (ao menos um tipo aceito detectado).
    N por célula é anotado.  Escala divergente: vermelho (0%) → branco (50%) → verde (100%).
    """
    from matplotlib.colors import LinearSegmentedColormap

    if df_tax.empty:
        print('  [WARN] taxonomy_category_heatmap: df_tax vazio — ignorado')
        return

    # Mapeia req_id → category a partir de df_eval (que tem a coluna category)
    req_cat: dict = {}
    if 'req_id' in df_eval.columns and 'category' in df_eval.columns:
        req_cat = df_eval[['req_id', 'category']].drop_duplicates() \
                      .set_index('req_id')['category'].to_dict()

    # Injeta categoria no df_tax quando não presente
    if 'category' not in df_tax.columns:
        df_tax = df_tax.copy()
        df_tax['category'] = df_tax['req_id'].map(req_cat)

    # Filtra somente as categorias que têm taxonomy_accepted_types (Cat-02, 03, 04)
    tax_cats = [c for c in CAT_IDS if c in df_tax['category'].values
                and c != 'category-01-structural' and c != 'category-05-control']

    if not tax_cats:
        print('  [WARN] taxonomy_category_heatmap: nenhuma categoria com dados — ignorado')
        return

    runs  = sorted(df_tax['run'].unique())
    lbls  = _model_labels(runs)
    n_cat = len(tax_cats)
    n_run = len(runs)

    # Matriz: linhas = categorias, colunas = modelos
    matrix = np.full((n_cat, n_run), np.nan)
    totals = np.zeros((n_cat, n_run), dtype=int)

    for j, run in enumerate(runs):
        sub = df_tax[df_tax['run'] == run]
        for i, cat in enumerate(tax_cats):
            cat_sub = sub[sub['category'] == cat]
            if cat_sub.empty:
                continue
            hits = cat_sub['match'].astype(bool).tolist()
            matrix[i, j]  = sum(hits) / len(hits) * 100
            totals[i, j]  = len(hits)

    cat_labels = [_CANONICAL_CAT_LABELS.get(c, c) for c in tax_cats]

    fig, ax = plt.subplots(figsize=(max(6, 1.6 * n_run + 1.5),
                                    max(3, 1.1 * n_cat + 2.0)))

    cmap = LinearSegmentedColormap.from_list('acc', ['#c62828', '#ffffff', '#2e7d32'])
    im   = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=100)

    for i in range(n_cat):
        for j in range(n_run):
            val = matrix[i, j]
            n   = totals[i, j]
            if np.isnan(val):
                ax.text(j, i, 'N/A', ha='center', va='center',
                        fontsize=9, color='#9e9e9e')
            else:
                tc = 'white' if (val > 65 or val < 25) else '#212121'
                ax.text(j, i, f'{val:.0f}%\n(N={n})',
                        ha='center', va='center', fontsize=9.5, color=tc,
                        fontweight='bold' if val > 0 else 'normal')

    ax.set_xticks(range(n_run))
    ax.set_xticklabels([lbls[r] for r in runs], fontsize=10, rotation=20, ha='right')
    ax.set_yticks(range(n_cat))
    ax.set_yticklabels([l.replace('\n', ' ') for l in cat_labels], fontsize=10)
    ax.set_xlabel('Modelo', fontsize=11, labelpad=8)
    ax.set_ylabel('Categoria do corpus', fontsize=11, labelpad=8)

    plt.colorbar(im, ax=ax, shrink=0.75, pad=0.02, label='% de acerto')

    ax.set_title(
        'Acerto taxonômico por categoria do corpus × modelo (C0 only)\n'
        'Acerto = ao menos um tipo aceito detectado  ·  Cat-02/03/04 apenas',
        fontsize=10, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'taxonomy_category_heatmap.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── main ──────────────────────────────────────────────────────────────────────

def _latest_eval_dir() -> Path:
    eval_root  = _OUTPUTS_DIR / 'evaluation'
    candidates = sorted(
        (d for d in eval_root.iterdir() if d.is_dir() and d.name.startswith('eval__')),
        key=lambda d: d.name, reverse=True,
    )
    if not candidates:
        raise SystemExit('Nenhuma pasta eval__ encontrada. Rode evaluate.py primeiro.')
    return candidates[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--eval-dir', default='')
    parser.add_argument('--run',      default='')
    args = parser.parse_args()

    eval_dir   = Path(args.eval_dir) if args.eval_dir else _latest_eval_dir()
    csv_path   = eval_dir / 'evaluation_results.csv'
    lift_path  = eval_dir / 'context_lift.csv'
    tax_path   = eval_dir / 'taxonomy_classification.csv'
    out_dir    = eval_dir / 'charts'

    if not csv_path.exists():
        raise SystemExit(f'CSV não encontrado: {csv_path}')

    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    for col in DIM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('boolean')
    df['route_structured'] = (df['act_route'] == 'structured')

    if args.run:
        df = df[df['run'].str.startswith(args.run)]
        if df.empty:
            raise SystemExit(f'Nenhuma linha para run "{args.run}"')

    runs = sorted(df['run'].unique())
    print(f'Runs encontradas: {len(runs)}')
    print('\nGerando gráficos...')

    # Bloco 1 — Detecção (C0, context-free)
    chart_d1_classification(df, out_dir)
    chart_d1_scatter_pr(df, out_dir)
    export_d1_metrics_csv(df, out_dir)
    chart_error_type_bar(df, out_dir)
    chart_heatmap(df, out_dir)

    # Bloco 2 — Sensibilidade ao contexto (2×2 composto)
    if lift_path.exists():
        df_lift = pd.read_csv(lift_path)
        if args.run:
            df_lift = df_lift[df_lift['run'].str.startswith(args.run)]
        chart_context_lift(df, df_lift, out_dir)
    else:
        print(f'  [WARN] context_lift.csv não encontrado — rode evaluate.py primeiro')

    # Bloco 3 — Taxonomia Pohl (Cat-02/03/04)
    if tax_path.exists():
        df_tax = pd.read_csv(tax_path)
        chart_taxonomy_grid(df_tax, out_dir)
        chart_taxonomy_model_heatmap(df_tax, out_dir)
        chart_taxonomy_category_heatmap(df_tax, df, out_dir)
    else:
        print(f'  [WARN] taxonomy_classification.csv não encontrado')

    # Bloco 4 — Integridade do output
    table_d_output_summary(df, out_dir)

    print(f'\nGráficos salvos em: {out_dir}')


if __name__ == '__main__':
    main()
