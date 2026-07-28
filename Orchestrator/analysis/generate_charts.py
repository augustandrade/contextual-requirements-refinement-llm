#!/usr/bin/env python3
"""
generate_charts.py — Geração de gráficos a partir dos resultados de avaliação.

Todas as visualizações mostram resultados por modelo (sem agregação entre modelos).

BLOCO 1 — Detecção (context-free, usa C0)
  1. detection_bar         — D1/D2 accuracy por categoria (C0 only, N=3/cat)
  2a. error_type_d1        — FP/FN de D1 por categoria (C0 only)
  2b. error_type_d2        — FP/FN de D2 por categoria (C0 only)

BLOCO 2 — Resolução (context-dependent)
  3. context_line          — D3 e D4 por C0/C1/C2, uma linha por modelo
  4. route_error_context   — FP/FN de D3 por C0/C1/C2

CONTEXT LIFT (contribuição central)
  5. context_lift          — ΔD3(C2−C0): lift=+1/0/−1 e staged gains por modelo

DIAGNÓSTICO
  6. heatmap               — grade req×condição, pass/fail D1–D3
  7. taxonomy_grid         — classificação por tipo (Pohl), Agente 1a

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

DIM_COLS   = ['D1_has_ambiguity', 'D2_concern_mixing', 'D3_route', 'D4_output_complete']
DIM_LABELS = ['D1 Ambiguidade', 'D2 ConcernMix', 'D3 Rota', 'D4 Output']
DIM_COLORS = ['#5c6bc0', '#26a69a', '#ef6c00', '#8d6e63']

CTX_SENSITIVE_COLS   = ['D3_route', 'D4_output_complete']
CTX_SENSITIVE_LABELS = ['D3 Rota', 'D4 Output']
CTX_ORDER            = ['C0', 'C1', 'C2']

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

# Categorias positivas (expected ambiguity = True) para D1
_POSITIVE_CATS = frozenset({'category-02-linguistic', 'category-03-domain', 'category-04-vagueness'})

PASS_COLOR    = '#4caf50'
FAIL_COLOR    = '#ef5350'
NA_COLOR      = '#e0e0e0'
MODEL_PALETTE = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a',
                 '#00838f', '#ad1457', '#558b2f', '#4527a0']

LIFT_POS_COLOR  = '#2e7d32'   # lift=+1 (contexto resolveu)
LIFT_ZERO_COLOR = '#e0e0e0'   # lift= 0 (sem variação)
LIFT_NEG_COLOR  = '#c62828'   # lift=−1 (degradação)
STAGE_C01_COLOR = '#5c6bc0'   # ganho C0→C1
STAGE_C12_COLOR = '#26a69a'   # ganho C1→C2


# ── helpers ───────────────────────────────────────────────────────────────────

def _model_label(run_name: str) -> str:
    parts = run_name.split('__')
    return parts[1] if len(parts) >= 2 else run_name


def _pct(series) -> float:
    vals = pd.Series(series).dropna()
    return float(vals.mean() * 100) if len(vals) else float('nan')


def _grid_axes(fig, runs: list) -> list:
    axes = fig.subplots(2, 2).flatten()
    for i in range(len(runs), len(axes)):
        axes[i].set_visible(False)
    return axes


# ── BLOCO 1: Chart 1 — D1/D2 accuracy por categoria (C0 only) ────────────────

def chart_detection_bar(df: pd.DataFrame, out_dir: Path):
    """D1 e D2 por categoria — usa apenas C0 (context-free, N=3 por categoria)."""
    df_c0       = df[df['context'] == 'C0']
    runs        = sorted(df['run'].unique())
    cat_ids, cat_labels = _cats_from_data(df_c0)
    x     = np.arange(len(cat_ids))
    width = 0.8 / len(runs)

    dims = [('D1_has_ambiguity', 'D1 Ambiguidade'), ('D2_concern_mixing', 'D2 ConcernMix')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), sharey=True)

    for ax, (col, label) in zip(axes, dims):
        ref_run    = df_c0[df_c0['run'] == runs[0]]
        totals     = [len(ref_run[ref_run['category'] == cat]) for cat in cat_ids]
        tick_labels = [f'{lbl}\n(N={t})' for lbl, t in zip(cat_labels, totals)]

        for i, (run, color) in enumerate(zip(runs, MODEL_PALETTE)):
            sub    = df_c0[df_c0['run'] == run]
            vals   = [_pct(sub[sub['category'] == cat][col]) for cat in cat_ids]
            offset = (i - (len(runs) - 1) / 2) * width
            bars   = ax.bar(x + offset, vals, width, color=color,
                            label=_model_label(run), edgecolor='white', linewidth=0.5)
            for bar, val in zip(bars, vals):
                if not math.isnan(val):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 1.5,
                            f'{val:.0f}', ha='center', va='bottom', fontsize=7)

        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=7.5)
        ax.set_ylim(0, 120)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)

    axes[0].set_ylabel('Acurácia (%)', fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=len(runs), fontsize=9,
               bbox_to_anchor=(0.5, -0.05), title='Modelo')
    n_per_cat = len(df_c0[df_c0['run'] == runs[0]]) // max(len(cat_ids), 1)
    fig.suptitle(
        'Bloco 1 — Detecção (context-free)\n'
        f'D1 e D2 calculados via C0 (N={n_per_cat} por categoria por modelo)',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'detection_bar__D1_D2.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 1: Charts 2a/2b — FP/FN de D1 e D2 (C0 only) ──────────────────────

def _draw_fp_fn_c0(ax, sub_c0: pd.DataFrame, col: str, run: str):
    """Helper: barras FP/FN por categoria usando apenas linhas C0."""
    cat_ids, cat_labels = _cats_from_data(sub_c0)
    x     = np.arange(len(cat_ids))
    width = 0.35
    totals = [len(sub_c0[sub_c0['category'] == cat]) for cat in cat_ids]
    fp = [len(sub_c0[(sub_c0['category'] == cat) & (sub_c0[col] == 'false_positive')])
          for cat in cat_ids]
    fn = [len(sub_c0[(sub_c0['category'] == cat) & (sub_c0[col] == 'false_negative')])
          for cat in cat_ids]

    bars_fp = ax.bar(x - width / 2, fp, width, label='Falso Positivo',
                     color='#ef6c00', edgecolor='white')
    bars_fn = ax.bar(x + width / 2, fn, width, label='Falso Negativo',
                     color='#5c6bc0', edgecolor='white')

    for bar, val in list(zip(bars_fp, fp)) + list(zip(bars_fn, fn)):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                    str(val), ha='center', va='bottom', fontsize=9)

    tick_labels = [f'{lbl}\n(N={t})' for lbl, t in zip(cat_labels, totals)]
    ax.set_title(_model_label(run), fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, fontsize=7.5)
    ax.set_ylabel('Nº de erros', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    return fp, fn


def _fp_fn_shared_legend(fig):
    handles = [
        mpatches.Patch(color='#ef6c00', label='Falso Positivo (FP)'),
        mpatches.Patch(color='#5c6bc0', label='Falso Negativo (FN)'),
    ]
    fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=9.5,
               bbox_to_anchor=(0.5, -0.04), frameon=True, framealpha=0.95)


def chart_error_type_bar(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D1 por categoria (C0 only) — grade 2×2 por modelo."""
    df_c0 = df[df['context'] == 'C0']
    runs  = sorted(df['run'].unique())
    fig   = plt.figure(figsize=(13, 10))
    axes  = _grid_axes(fig, runs)
    max_val = 0
    for ax, run in zip(axes, runs):
        fp, fn = _draw_fp_fn_c0(ax, df_c0[df_c0['run'] == run], 'd1_error_type', run)
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))
    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)
    _fp_fn_shared_legend(fig)
    fig.suptitle(
        'D1 Ambiguidade — Falsos Positivos e Negativos por categoria (C0 only)\n'
        'Positivos: Cat-02/03/04  |  Negativos (controle): Cat-01, Cat-05',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'error_type__D1_ambiguidade.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


def chart_error_type_d2(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D2 por categoria (C0 only) — grade 2×2 por modelo."""
    df_c0 = df[df['context'] == 'C0']
    runs  = sorted(df['run'].unique())
    fig   = plt.figure(figsize=(13, 10))
    axes  = _grid_axes(fig, runs)
    max_val = 0
    for ax, run in zip(axes, runs):
        fp, fn = _draw_fp_fn_c0(ax, df_c0[df_c0['run'] == run], 'd2_error_type', run)
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))
    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)
    _fp_fn_shared_legend(fig)
    fig.suptitle(
        'D2 ConcernMix — Falsos Positivos e Negativos por categoria (C0 only)\n'
        'Positivos: Cat-01 (REQ-01..03)  |  Negativos: Cat-02..05',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'error_type__D2_concernmix.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 2: Chart 3 — D3/D4 por condição de contexto (RQ1) ─────────────────

def chart_context_line(df: pd.DataFrame, out_dir: Path):
    """D3 e D4 por condição C0/C1/C2 — uma linha por modelo."""
    runs = sorted(df['run'].unique())
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    for ax, col, label in zip(axes, CTX_SENSITIVE_COLS, CTX_SENSITIVE_LABELS):
        for run, color in zip(runs, MODEL_PALETTE):
            sub  = df[df['run'] == run]
            vals = [_pct(sub[sub['context'] == ctx][col]) for ctx in CTX_ORDER]
            ax.plot(CTX_ORDER, vals, 'o-', linewidth=2, color=color,
                    label=_model_label(run), markersize=7)
            for ctx, val in zip(CTX_ORDER, vals):
                if not math.isnan(val):
                    ax.annotate(f'{val:.0f}%', (ctx, val),
                                textcoords='offset points', xytext=(0, 9),
                                ha='center', fontsize=7.5, color=color)
        ax.set_title(label, fontsize=10, fontweight='bold')
        ax.set_ylim(0, 115)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)
        ax.set_xlabel('Condição de contexto', fontsize=9)

    axes[0].set_ylabel('Acurácia (%)', fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=len(runs),
               fontsize=9, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle(
        'Bloco 2 — Resolução: impacto do contexto sobre D3 e D4\n'
        '(D1/D2 são context-free; variação de C0→C2 é o efeito do contexto)',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'context_line__D3_D4.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── BLOCO 2: Chart 4 — FP/FN D3 por contexto (RQ1 + RQ4) ────────────────────

def chart_route_error_context(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D3 por condição C0/C1/C2 — grade 2×2 por modelo."""
    runs  = sorted(df['run'].unique())
    x     = np.arange(len(CTX_ORDER))
    width = 0.35
    fig   = plt.figure(figsize=(13, 10))
    axes  = _grid_axes(fig, runs)
    max_val = 0

    for ax, run in zip(axes, runs):
        sub    = df[df['run'] == run]
        totals = [len(sub[(sub['context'] == ctx) & sub['D3_route'].notna()])
                  for ctx in CTX_ORDER]
        fp = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_positive')])
              for ctx in CTX_ORDER]
        fn = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_negative')])
              for ctx in CTX_ORDER]
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))

        bars_fp = ax.bar(x - width / 2, fp, width,
                         color='#ef6c00', edgecolor='white')
        bars_fn = ax.bar(x + width / 2, fn, width,
                         color='#5c6bc0', edgecolor='white')
        for bar, val in list(zip(bars_fp, fp)) + list(zip(bars_fn, fn)):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                        str(val), ha='center', va='bottom', fontsize=9)

        tick_labels = [f'{ctx}\n(N={t})' for ctx, t in zip(CTX_ORDER, totals)]
        ax.set_title(_model_label(run), fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=9)
        ax.set_ylabel('Nº de erros de rota', fontsize=9)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)

    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)

    fig.legend(handles=[
        mpatches.Patch(color='#ef6c00', label='FP — rota structured indevida (sobre-confiança)'),
        mpatches.Patch(color='#5c6bc0', label='FN — rota signaling indevida (sub-detecção)'),
    ], loc='lower center', ncol=2, fontsize=9,
       bbox_to_anchor=(0.5, -0.04), frameon=True, framealpha=0.95)
    fig.suptitle(
        'D3 Rota — Erros por tipo e condição de contexto\n'
        '(redução de C0 → C2 confirma impacto do contexto controlado)',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'error_type__D3_rota_por_contexto.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── CONTEXT LIFT: Chart 5 — ΔD3(C2−C0) e staged gains (contribuição central) ─

def chart_context_lift(df_lift: pd.DataFrame, out_dir: Path):
    """
    Duas sub-figuras por modelo:
      (a) distribuição de lift=+1/0/−1 entre os N req ambíguos (Cat-02/03/04)
      (b) staged gains C0→C1 (glossário) e C1→C2 (regra de negócio)

    Só inclui Cat-02, Cat-03, Cat-04 — os únicos com transição esperada em C2.
    Cat-01 e Cat-05 têm not_applicable em todas as condições e ficam fora.
    """
    pos_cats = {'category-02-linguistic', 'category-03-domain', 'category-04-vagueness'}
    df_amb   = df_lift[df_lift['category'].isin(pos_cats)].copy()

    if df_amb.empty:
        print('  [WARN] context_lift: nenhuma linha de categoria positiva — gráfico ignorado')
        return

    runs = sorted(df_lift['run'].unique())
    n    = len(df_amb[df_amb['run'] == runs[0]])  # N req por modelo

    fig, (ax_lift, ax_stage) = plt.subplots(1, 2, figsize=(12, 5))

    x     = np.arange(len(runs))
    width = 0.55

    # (a) distribuição de lift (stacked bar)
    lift_pos  = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == 1)])  for r in runs]
    lift_zero = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == 0)])  for r in runs]
    lift_neg  = [len(df_amb[(df_amb['run'] == r) & (df_amb['lift_c2_c0'] == -1)]) for r in runs]

    bars_pos  = ax_lift.bar(x, lift_pos,  width, color=LIFT_POS_COLOR,  label='lift=+1 (contexto resolveu)')
    bars_zero = ax_lift.bar(x, lift_zero, width, bottom=lift_pos,
                            color=LIFT_ZERO_COLOR, label='lift= 0 (sem variação)')
    bot2      = [a + b for a, b in zip(lift_pos, lift_zero)]
    bars_neg  = ax_lift.bar(x, lift_neg,  width, bottom=bot2,
                            color=LIFT_NEG_COLOR,  label='lift=−1 (degradação)')

    for bar, val, bot in [(b, v, 0) for b, v in zip(bars_pos, lift_pos)] + \
                         [(b, v, p) for b, v, p in zip(bars_zero, lift_zero, lift_pos)] + \
                         [(b, v, p) for b, v, p in zip(bars_neg, lift_neg, bot2)]:
        if val > 0:
            ax_lift.text(bar.get_x() + bar.get_width() / 2, bot + val / 2,
                         str(val), ha='center', va='center', fontsize=9,
                         color='white', fontweight='bold')

    ax_lift.set_title(f'ΔD3(C2 − C0) — lift por modelo\n(N={n} req: Cat-02, Cat-03, Cat-04)',
                      fontsize=10, fontweight='bold')
    ax_lift.set_xticks(x)
    ax_lift.set_xticklabels([_model_label(r) for r in runs], fontsize=9, rotation=15, ha='right')
    ax_lift.set_ylabel('Nº de requisitos', fontsize=10)
    ax_lift.set_ylim(0, n * 1.15)
    ax_lift.yaxis.grid(True, linestyle='--', alpha=0.35)
    ax_lift.set_axisbelow(True)
    ax_lift.legend(fontsize=8.5, loc='upper right')

    # (b) staged gains (grouped bar)
    width_s  = 0.35
    gain_c01 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c0_c1'] == 1)]) for r in runs]
    gain_c12 = [len(df_amb[(df_amb['run'] == r) & (df_amb['stage_c1_c2'] == 1)]) for r in runs]

    b01 = ax_stage.bar(x - width_s / 2, gain_c01, width_s,
                       color=STAGE_C01_COLOR, label='C0→C1 (glossário)')
    b12 = ax_stage.bar(x + width_s / 2, gain_c12, width_s,
                       color=STAGE_C12_COLOR, label='C1→C2 (regra de negócio)')

    for bar, val in list(zip(b01, gain_c01)) + list(zip(b12, gain_c12)):
        ax_stage.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                      str(val), ha='center', va='bottom', fontsize=9)

    ax_stage.set_title(f'Staged gains — onde o contexto ajuda?\n(N={n} req por modelo)',
                       fontsize=10, fontweight='bold')
    ax_stage.set_xticks(x)
    ax_stage.set_xticklabels([_model_label(r) for r in runs], fontsize=9, rotation=15, ha='right')
    ax_stage.set_ylabel('Nº de requisitos com melhoria', fontsize=10)
    ax_stage.set_ylim(0, n * 1.2)
    ax_stage.yaxis.grid(True, linestyle='--', alpha=0.35)
    ax_stage.set_axisbelow(True)
    ax_stage.legend(fontsize=8.5, loc='upper right')

    fig.suptitle(
        'Context Lift — impacto do contexto controlado sobre a resolubilidade (D3)\n'
        'Staged gains separam contribuição do glossário (C1) da regra de negócio (C2)',
        fontsize=11, fontweight='bold',
    )
    plt.tight_layout()
    out_path = out_dir / 'context_lift__D3_delta.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── DIAGNÓSTICO: Chart 6 — heatmap req×condição ──────────────────────────────

_HEATMAP_DIMS = [
    (c, l) for c, l in zip(DIM_COLS, DIM_LABELS) if c != 'D4_output_complete'
]


def chart_heatmap(df: pd.DataFrame, run_name: str, out_dir: Path):
    """Grade req×condição D1–D3 — diagnóstico granular."""
    reqs = sorted(df['req_id'].unique())
    dims = _HEATMAP_DIMS

    fig, axes = plt.subplots(
        1, len(dims),
        figsize=(3.2 * len(dims), max(5, 0.42 * len(reqs) * len(CTX_ORDER) / 3 + 2)),
        sharey=False,
    )

    row_labels = [f'{r} {c}' for r in reqs for c in CTX_ORDER]

    for ax, (col, label) in zip(axes, dims):
        values = []
        for req in reqs:
            for ctx in CTX_ORDER:
                cell = df[(df['req_id'] == req) & (df['context'] == ctx)][col]
                values.append(None if (len(cell) == 0 or cell.isna().all())
                              else bool(cell.iloc[0]))

        for i, val in enumerate(values):
            color  = PASS_COLOR if val is True else (FAIL_COLOR if val is False else NA_COLOR)
            symbol = '✓' if val is True else ('✗' if val is False else '—')
            ax.add_patch(plt.Rectangle((0, i), 1, 1, facecolor=color,
                                       linewidth=0.3, edgecolor='white'))
            ax.text(0.5, i + 0.5, symbol, ha='center', va='center',
                    fontsize=8, color='white' if val is not None else '#888')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, len(row_labels))
        ax.set_yticks([i + 0.5 for i in range(len(row_labels))])
        ax.set_yticklabels(row_labels if ax == axes[0] else [], fontsize=7)
        ax.set_xticks([])
        ax.set_title(label, fontsize=9, fontweight='bold', pad=6)
        ax.invert_yaxis()

    legend = [mpatches.Patch(color=PASS_COLOR, label='Correto'),
              mpatches.Patch(color=FAIL_COLOR, label='Incorreto'),
              mpatches.Patch(color=NA_COLOR,   label='N/A')]
    fig.legend(handles=legend, loc='lower center', ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f'Heatmap — {_model_label(run_name)}',
                 fontsize=11, fontweight='bold', y=1.01)
    plt.tight_layout()
    out_path = out_dir / f'heatmap__{run_name}.png'
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
    """Grade req×modelo: tipo(s) detectado(s) pelo Agente 1a vs. aceitos.

    Verde   = correspondência exata (sem sobre-detecção).
    Amarelo = tipo aceito presente, mas há tipos extras detectados.
    Vermelho = nenhum tipo aceito detectado.
    """
    req_ids = list(df['req_id'].unique())
    runs    = sorted(df['run'].unique())

    fig, ax = plt.subplots(figsize=(2.6 * len(runs) + 2, 1.3 * len(req_ids) + 1.5))

    for i, req_id in enumerate(req_ids):
        row_ref        = df[df['req_id'] == req_id].iloc[0]
        accepted_label = row_ref.get('accepted_types', row_ref.get('expected_type', ''))
        for j, run in enumerate(runs):
            cell          = df[(df['req_id'] == req_id) & (df['run'] == run)]
            if not len(cell):
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=NA_COLOR,
                                           linewidth=0.6, edgecolor='white'))
                continue
            detected_str  = str(cell['detected_types'].iloc[0])
            accepted_str  = str(cell['accepted_types'].iloc[0])
            result, color = _taxonomy_result(accepted_str, detected_str)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=color,
                                       linewidth=0.6, edgecolor='white'))
            ax.text(j + 0.5, i + 0.5, detected_str, ha='center', va='center',
                    fontsize=8, color='white', wrap=True)

    ax.set_xlim(0, len(runs))
    ax.set_ylim(0, len(req_ids))
    ax.set_xticks([j + 0.5 for j in range(len(runs))])
    ax.set_xticklabels([_model_label(r) for r in runs], fontsize=9)
    ax.set_yticks([i + 0.5 for i in range(len(req_ids))])
    ax.set_yticklabels(
        [f"{r}\n(aceito: {df[df['req_id'] == r].iloc[0].get('accepted_types', '?')})"
         for r in req_ids],
        fontsize=9,
    )
    ax.invert_yaxis()
    ax.set_title(
        'Classificação por tipo (Pohl) — texto na célula = tipo(s) que o Agente 1a atribuiu\n'
        'Rótulos múltiplos = divergência na literatura (qualquer um aceito)',
        fontsize=10, fontweight='bold', pad=10,
    )
    legend = [
        mpatches.Patch(color=_TAX_EXACT_COLOR, label='Correspondência exata'),
        mpatches.Patch(color=_TAX_OVER_COLOR,  label='Aceito presente + sobre-detecção'),
        mpatches.Patch(color=_TAX_MISS_COLOR,  label='Tipo aceito ausente'),
    ]
    fig.legend(handles=legend, loc='lower center', ncol=3, fontsize=9,
               bbox_to_anchor=(0.5, -0.05))
    plt.tight_layout()
    out_path = out_dir / 'taxonomy_classification.png'
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
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('boolean')

    if args.run:
        df = df[df['run'].str.startswith(args.run)]
        if df.empty:
            raise SystemExit(f'Nenhuma linha para run "{args.run}"')

    runs = sorted(df['run'].unique())
    print(f'Runs encontradas: {len(runs)}')
    print('\nGerando gráficos...')

    # Bloco 1 — Detecção
    chart_detection_bar(df, out_dir)
    chart_error_type_bar(df, out_dir)
    chart_error_type_d2(df, out_dir)

    # Bloco 2 — Resolução
    chart_context_line(df, out_dir)
    chart_route_error_context(df, out_dir)

    # Context lift
    if lift_path.exists():
        df_lift = pd.read_csv(lift_path)
        if args.run:
            df_lift = df_lift[df_lift['run'].str.startswith(args.run)]
        chart_context_lift(df_lift, out_dir)
    else:
        print(f'  [WARN] context_lift.csv não encontrado — rode evaluate.py primeiro')

    # Diagnóstico
    for run in runs:
        chart_heatmap(df[df['run'] == run], run, out_dir)

    if tax_path.exists():
        df_tax = pd.read_csv(tax_path)
        chart_taxonomy_grid(df_tax, out_dir)
    else:
        print(f'  [WARN] taxonomy_classification.csv não encontrado')

    print(f'\nGráficos salvos em: {out_dir}')


if __name__ == '__main__':
    main()
