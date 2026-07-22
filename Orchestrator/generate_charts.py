#!/usr/bin/env python3
"""
generate_charts.py — Geração de gráficos a partir dos resultados de avaliação.

Todas as visualizações mostram resultados por modelo (sem agregação entre modelos).
A consistência entre modelos é observada dentro de cada gráfico, não em separado.

  1. context_line            — D3 e D4 por C0/C1/C2, uma linha por modelo  (RQ1)
  2. category_bar            — D1–D4 por categoria, grade 2×2 por modelo    (RQ3)
  3a. error_type_bar         — FP/FN de D1 por categoria, grade 2×2         (RQ4)
  3b. error_type_d2          — FP/FN de D2 por categoria, grade 2×2         (RQ4)
  3c. route_error_context    — FP/FN de D3 por C0/C1/C2, grade 2×2         (RQ1+RQ4)
  4. status_dist             — global_status por C0/C1/C2, grade 2×2        (RQ1 diagnóstico)
  5. heatmap                 — grade req×condição, pass/fail por dimensão    (diagnóstico)

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

_HERE = Path(__file__).parent
_OUTPUTS_DIR = _HERE / 'outputs'

DIM_COLS   = ['D1_has_ambiguity', 'D4_concern_mixing', 'D2_route', 'D3_output_complete']
DIM_LABELS = ['D1 Ambiguidade', 'D2 ConcernMix', 'D3 Rota', 'D4 Output']
DIM_COLORS = ['#5c6bc0', '#26a69a', '#ef6c00', '#8d6e63']

CTX_SENSITIVE_COLS   = ['D2_route', 'D3_output_complete']
CTX_SENSITIVE_LABELS = ['D3 Rota', 'D4 Output']

CTX_ORDER = ['C0', 'C1', 'C2']

CAT_IDS          = ['category-01-structural', 'category-02-linguistic',
                    'category-03-domain',     'category-04-control']
CAT_LABELS_SHORT = ['Cat-01\nEstrutural', 'Cat-02\nLinguística',
                    'Cat-03\nDomínio',    'Cat-04\nControle']

PASS_COLOR    = '#4caf50'
FAIL_COLOR    = '#ef5350'
NA_COLOR      = '#e0e0e0'
MODEL_PALETTE = ['#1565c0', '#e65100', '#2e7d32', '#6a1b9a',
                 '#00838f', '#ad1457', '#558b2f', '#4527a0']


# ── helpers ───────────────────────────────────────────────────────────────────

def _model_label(run_name: str) -> str:
    parts = run_name.split('__')
    return parts[1] if len(parts) >= 2 else run_name


def _pct(series) -> float:
    vals = pd.Series(series).dropna()
    return float(vals.mean() * 100) if len(vals) else float('nan')


def _grid_axes(fig, runs: list) -> list:
    """Retorna lista de axes em grade 2×2, escondendo os excedentes."""
    axes = fig.subplots(2, 2).flatten()
    for i in range(len(runs), len(axes)):
        axes[i].set_visible(False)
    return axes


# ── Chart 1: context sensitivity line (RQ1) ──────────────────────────────────

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
    fig.suptitle('Impacto do nível de contexto sobre D3 e D4\n'
                 '(D1 e D2 são context-free e não variam com C0/C1/C2)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'context_line__D3_D4.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 2: category bar por modelo (RQ3) ───────────────────────────────────

def _draw_category_bars(ax, df: pd.DataFrame, title: str,
                        fontsize_title: float = 10,
                        fontsize_tick: float  = 8,
                        fontsize_label: float = 7,
                        show_legend: bool = False,
                        show_ylabel: bool = True,
                        hide_full: bool = True):
    x     = np.arange(len(CAT_IDS))
    width = 0.2

    for i, (col, label, color) in enumerate(zip(DIM_COLS, DIM_LABELS, DIM_COLORS)):
        vals   = [_pct(df[df['category'] == cat][col]) for cat in CAT_IDS]
        offset = (i - 1.5) * width
        bars   = ax.bar(x + offset, vals, width, label=label, color=color,
                        edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, vals):
            if not math.isnan(val) and not (hide_full and val >= 99.5):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 1,
                        f'{val:.0f}%', ha='center', va='bottom',
                        fontsize=fontsize_label)

    ax.set_ylim(0, 122)
    ax.set_xticks(x)
    ax.set_xticklabels(CAT_LABELS_SHORT, fontsize=fontsize_tick)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=fontsize_title, fontweight='bold')
    if show_ylabel:
        ax.set_ylabel('Acurácia (%)', fontsize=fontsize_tick + 1)
    if show_legend:
        ax.legend(title='Dimensão', fontsize=fontsize_tick - 1, loc='lower right')


def chart_category_bar(df: pd.DataFrame, out_dir: Path):
    """D1–D4 por categoria — grade 2×2, um painel por modelo."""
    runs = sorted(df['run'].unique())

    fig = plt.figure(figsize=(13, 10))
    axes = _grid_axes(fig, runs)

    for i, (ax, run) in enumerate(zip(axes, runs)):
        _draw_category_bars(ax, df[df['run'] == run],
                            title=_model_label(run),
                            fontsize_title=10, fontsize_tick=8, fontsize_label=7,
                            show_legend=False, show_ylabel=(i % 2 == 0),
                            hide_full=True)

    # Legenda compartilhada
    handles = [mpatches.Patch(color=c, label=l) for c, l in zip(DIM_COLORS, DIM_LABELS)]
    fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=9,
               bbox_to_anchor=(0.5, -0.02), title='Dimensão')

    fig.suptitle('Desempenho por categoria do corpus — D1–D4\n'
                 '(barras sem rótulo = 100%; valores mostrados apenas nos desvios)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'category_bar__D1_D4.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 3a: FP/FN D1 Ambiguidade por modelo (RQ4) ──────────────────────────

def _draw_fp_fn(ax, sub: pd.DataFrame, col: str, run: str):
    """Helper: desenha barras FP/FN por categoria, sem legenda própria.

    Rótulo do eixo X inclui o total de execuções da categoria (N) para
    contextualizar a representatividade de cada contagem de erro.
    """
    x     = np.arange(len(CAT_IDS))
    width = 0.35

    # total de instâncias avaliadas por categoria (N_reqs × N_condições)
    totals = [len(sub[sub['category'] == cat]) for cat in CAT_IDS]

    fp = [len(sub[(sub['category'] == cat) & (sub[col] == 'false_positive')])
          for cat in CAT_IDS]
    fn = [len(sub[(sub['category'] == cat) & (sub[col] == 'false_negative')])
          for cat in CAT_IDS]

    bars_fp = ax.bar(x - width / 2, fp, width,
                     label='Falso Positivo', color='#ef6c00', edgecolor='white')
    bars_fn = ax.bar(x + width / 2, fn, width,
                     label='Falso Negativo', color='#5c6bc0', edgecolor='white')

    for bar, val in list(zip(bars_fp, fp)) + list(zip(bars_fn, fn)):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.08,
                    str(val), ha='center', va='bottom', fontsize=9)

    tick_labels = [f'{lbl}\n(N={t})' for lbl, t in zip(CAT_LABELS_SHORT, totals)]

    ax.set_title(_model_label(run), fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, fontsize=8)
    ax.set_ylabel('Nº de erros', fontsize=9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    # sem legenda por painel — legenda compartilhada adicionada pelo chamador
    return fp, fn


def _fp_fn_shared_legend(fig):
    """Adiciona legenda FP/FN compartilhada abaixo de todos os painéis."""
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(color='#ef6c00', label='Falso Positivo (FP)'),
        mpatches.Patch(color='#5c6bc0', label='Falso Negativo (FN)'),
    ]
    fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=9.5,
               bbox_to_anchor=(0.5, -0.04), frameon=True, framealpha=0.95)


def chart_error_type_bar(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D1 (Ambiguidade) por categoria — grade 2×2 por modelo."""
    runs = sorted(df['run'].unique())

    fig = plt.figure(figsize=(13, 10))
    axes = _grid_axes(fig, runs)

    for ax, run in zip(axes, runs):
        _draw_fp_fn(ax, df[df['run'] == run], 'd1_error_type', run)

    _fp_fn_shared_legend(fig)
    fig.suptitle('D1 Ambiguidade — Falsos Positivos e Negativos por categoria\n'
                 '(N = total de execuções avaliadas; Cat-04 = controle, erros são exclusivamente FP)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'error_type__D1_ambiguidade.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 3b: FP/FN D2 ConcernMix por modelo (RQ4) ───────────────────────────

def chart_error_type_d2(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D2 (ConcernMix) por categoria — grade 2×2 por modelo.
    Cat-01 é a única categoria com concern mixing esperado;
    erros em Cat-02/03/04 são sempre FP.
    """
    runs = sorted(df['run'].unique())

    fig = plt.figure(figsize=(13, 10))
    axes = _grid_axes(fig, runs)

    for ax, run in zip(axes, runs):
        _draw_fp_fn(ax, df[df['run'] == run], 'd2_error_type', run)

    _fp_fn_shared_legend(fig)
    fig.suptitle('D2 ConcernMix — Falsos Positivos e Negativos por categoria\n'
                 '(N = total de execuções avaliadas; concern mixing esperado apenas em REQ-01 dentro de Cat-01)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'error_type__D2_concernmix.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 3c: FP/FN D3 Rota por contexto por modelo (RQ1 + RQ4) ─────────────

def chart_route_error_context(df: pd.DataFrame, out_dir: Path):
    """FP e FN de D3 (Rota) por condição C0/C1/C2 — grade 2×2 por modelo.

    FP = pipeline escolheu 'structured' quando deveria ter ido a 'signaling'
         (sobre-confiança — ignora ambiguidade não resolúvel).
    FN = pipeline escolheu 'signaling' quando deveria ter ido a 'structured'
         (sub-detecção — descarta resolubilidade disponível).

    Esperado: FP e FN decrescem de C0 para C2 conforme o contexto disambígua.
    D1 e D2 são context-free e, por design, não aparecem neste gráfico.
    """
    runs  = sorted(df['run'].unique())
    x     = np.arange(len(CTX_ORDER))
    width = 0.35

    fig = plt.figure(figsize=(13, 10))
    axes = _grid_axes(fig, runs)

    for ax, run in zip(axes, runs):
        sub = df[df['run'] == run]

        # total de execuções com D3 aplicável por condição
        totals = [len(sub[(sub['context'] == ctx) & sub['D2_route'].notna()])
                  for ctx in CTX_ORDER]

        fp = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_positive')])
              for ctx in CTX_ORDER]
        fn = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_negative')])
              for ctx in CTX_ORDER]

        bars_fp = ax.bar(x - width / 2, fp, width,
                         label='FP (structured indevido)', color='#ef6c00', edgecolor='white')
        bars_fn = ax.bar(x + width / 2, fn, width,
                         label='FN (signaling indevido)',  color='#5c6bc0', edgecolor='white')

        for bar, val in list(zip(bars_fp, fp)) + list(zip(bars_fn, fn)):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.08,
                        str(val), ha='center', va='bottom', fontsize=9)

        tick_labels = [f'{ctx}\n(N={t})' for ctx, t in zip(CTX_ORDER, totals)]
        ax.set_title(_model_label(run), fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=9)
        ax.set_ylabel('Nº de erros de rota', fontsize=9)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)
        # sem legenda por painel — legenda compartilhada abaixo

    import matplotlib.patches as mpatches
    fig.legend(handles=[
        mpatches.Patch(color='#ef6c00', label='FP — rota structured indevida (sobre-confiança)'),
        mpatches.Patch(color='#5c6bc0', label='FN — rota signaling indevida (sub-detecção)'),
    ], loc='lower center', ncol=2, fontsize=9,
       bbox_to_anchor=(0.5, -0.04), frameon=True, framealpha=0.95)

    fig.suptitle('D3 Rota — Erros por tipo e condição de contexto\n'
                 '(N = execuções com D3 aplicável; redução de C0 → C2 confirma impacto do contexto)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'error_type__D3_rota_por_contexto.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 4: distribuição de global_status por modelo (RQ1 diagnóstico) ──────
# REMOVIDO: chart_status_distribution — coberto com mais precisão por
# context_line (acurácia D3/D4), error_type D1/D2 (FP/FN) e D3 rota por contexto.

def _chart_status_distribution_removed(df: pd.DataFrame, out_dir: Path):
    """Status global por condição C0/C1/C2 — filtrado a requisitos com ambiguidade esperada.

    expected_resolubility varia por condição no corpus (C0 tem poucos resolúveis;
    C2 tem mais). Marcadores diamante/quadrado mostram o esperado por condição:
      ◆ verde  = expected fully_resolvable por condição (teto ideal para barra verde)
      ■ laranja = expected não-resolvido por condição (piso ideal para barra laranja)
    Legenda compartilhada abaixo dos subgráficos.
    """
    import matplotlib.patches as mpatches
    import matplotlib.lines  as mlines

    runs   = sorted(df['run'].unique())
    amb_df = df[df['expected_resolubility'].isin(['resolvable', 'unresolved'])]

    statuses = ['fully_resolvable', 'no_ambiguity', 'non_resolvable', 'unresolved']
    labels   = ['Totalmente resolúvel', 'Ambig. não detectada (FN)', 'Irresolvível', 'Não resolvido']
    colors   = ['#43a047', '#90caf9', '#e53935', '#ef6c00']

    x       = np.arange(len(CTX_ORDER))
    width   = 0.18
    offsets = np.linspace(-(len(statuses) - 1) / 2,
                           (len(statuses) - 1) / 2,
                           len(statuses)) * width

    # expected varia por condição — calculado do corpus (idêntico entre runs)
    first_run = runs[0]
    exp_resolvable   = [len(amb_df[(amb_df['run'] == first_run) &
                                   (amb_df['context'] == ctx) &
                                   (amb_df['expected_resolubility'] == 'resolvable')])
                        for ctx in CTX_ORDER]
    exp_unresolvable = [len(amb_df[(amb_df['run'] == first_run) &
                                   (amb_df['context'] == ctx) &
                                   (amb_df['expected_resolubility'] == 'unresolved')])
                        for ctx in CTX_ORDER]
    n_total = exp_resolvable[0] + exp_unresolvable[0]  # total fixo (independe de condição)

    fig = plt.figure(figsize=(13, 11))
    axes = _grid_axes(fig, runs)

    for ax, run in zip(axes, runs):
        sub = amb_df[amb_df['run'] == run]

        for status, label, color, offset in zip(statuses, labels, colors, offsets):
            counts = [len(sub[(sub['context'] == ctx) &
                              (sub['act_global_status'] == status)])
                      for ctx in CTX_ORDER]
            bars = ax.bar(x + offset, counts, width, color=color,
                          edgecolor='white', linewidth=0.5)
            for bar, val in zip(bars, counts):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.12,
                            str(val), ha='center', va='bottom', fontsize=8)

        # marcadores de referência por condição (corpus-defined)
        ax.plot(x, exp_resolvable, 'D--', color='#1b5e20',
                markersize=8, linewidth=1.4, zorder=5,
                markeredgecolor='white', markeredgewidth=0.8)
        for xi, val in zip(x, exp_resolvable):
            ax.annotate(f'{val}', (xi, val), textcoords='offset points',
                        xytext=(10, 2), fontsize=7.5, color='#1b5e20', fontstyle='italic')

        ax.plot(x, exp_unresolvable, 's:', color='#bf360c',
                markersize=8, linewidth=1.4, zorder=5,
                markeredgecolor='white', markeredgewidth=0.8)
        for xi, val in zip(x, exp_unresolvable):
            ax.annotate(f'{val}', (xi, val), textcoords='offset points',
                        xytext=(10, 2), fontsize=7.5, color='#bf360c', fontstyle='italic')

        ax.set_title(_model_label(run), fontsize=10, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(CTX_ORDER, fontsize=10)
        ax.set_xlabel('Condição de contexto', fontsize=8)
        ax.set_ylabel(f'Nº de execuções (N={n_total} c/ ambig. esperada)', fontsize=8)
        ax.set_ylim(0, n_total + 2)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)

    # legenda compartilhada abaixo de todos os painéis
    patch_handles = [mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)]
    line_handles  = [
        mlines.Line2D([], [], color='#1b5e20', linestyle='--', linewidth=1.4,
                      marker='D', markersize=7, markeredgecolor='white',
                      label='◆ Esperado como resolúvel (por condição)'),
        mlines.Line2D([], [], color='#bf360c', linestyle=':', linewidth=1.4,
                      marker='s', markersize=7, markeredgecolor='white',
                      label='■ Esperado como irresolvível (por condição)'),
    ]
    fig.legend(handles=patch_handles + line_handles,
               loc='lower center', ncol=3, fontsize=8.5,
               bbox_to_anchor=(0.5, -0.06),
               frameon=True, framealpha=0.95)

    fig.suptitle('Status do pipeline por contexto — apenas requisitos com ambiguidade esperada\n'
                 '(Cat-04 excluída; marcadores = referência esperada por condição)',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'status_distribution_by_context.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Salvo: {out_path.name}')


# ── Chart 5: heatmap diagnóstico por modelo ───────────────────────────────────

def chart_heatmap(df: pd.DataFrame, run_name: str, out_dir: Path):
    """Grade requisito×condição (42 linhas) × 4 dimensões — diagnóstico granular."""
    reqs = sorted(df['req_id'].unique())

    fig, axes = plt.subplots(
        1, len(DIM_COLS),
        figsize=(3.2 * len(DIM_COLS), max(5, 0.42 * len(reqs) * len(CTX_ORDER) / 3 + 2)),
        sharey=False,
    )

    row_labels = [f'{r} {c}' for r in reqs for c in CTX_ORDER]

    for ax, col, label in zip(axes, DIM_COLS, DIM_LABELS):
        values = []
        for req in reqs:
            for ctx in CTX_ORDER:
                cell = df[(df['req_id'] == req) & (df['context'] == ctx)][col]
                values.append(None if (len(cell) == 0 or cell.isna().all())
                              else bool(cell.iloc[0]))

        colors = [PASS_COLOR if v is True else (FAIL_COLOR if v is False else NA_COLOR)
                  for v in values]

        for i, (color, val) in enumerate(zip(colors, values)):
            ax.add_patch(plt.Rectangle((0, i), 1, 1, color=color,
                                       linewidth=0.3, edgecolor='white'))
            symbol = '✓' if val is True else ('✗' if val is False else '—')
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


# ── main ──────────────────────────────────────────────────────────────────────

def _latest_eval_dir() -> Path:
    eval_root = _OUTPUTS_DIR / 'evaluation'
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

    eval_dir = Path(args.eval_dir) if args.eval_dir else _latest_eval_dir()
    csv_path = eval_dir / 'evaluation_results.csv'
    out_dir  = eval_dir / 'charts'

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
    chart_context_line(df, out_dir)
    chart_category_bar(df, out_dir)
    chart_error_type_bar(df, out_dir)
    for run in runs:
        chart_heatmap(df[df['run'] == run], run, out_dir)

    print(f'\nGráficos salvos em: {out_dir}')


if __name__ == '__main__':
    main()
