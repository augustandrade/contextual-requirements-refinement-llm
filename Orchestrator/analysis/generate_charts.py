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
_OUTPUTS_DIR = _HERE.parent / 'outputs'

DIM_COLS   = ['D1_has_ambiguity', 'D2_concern_mixing', 'D3_route', 'D4_output_complete']
DIM_LABELS = ['D1 Ambiguidade', 'D2 ConcernMix', 'D3 Rota', 'D4 Output']
DIM_COLORS = ['#5c6bc0', '#26a69a', '#ef6c00', '#8d6e63']

CTX_SENSITIVE_COLS   = ['D3_route', 'D4_output_complete']
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


# ── Chart 2: category bar por dimensão, agrupado por modelo (RQ3) ────────────
# D4 (output_complete) fica em 100% em toda categoria/modelo — sem valor
# discriminante — então é omitido aqui em vez de ocupar 1/4 do espaço visual
# à toa. Um painel por dimensão (D1/D2/D3) com barras agrupadas por modelo
# deixa a comparação entre modelos dentro de uma categoria direta (barras
# adjacentes), em vez de exigir pular entre painéis por modelo.

_CATEGORY_BY_MODEL_DIMS = [
    (c, l) for c, l in zip(DIM_COLS, DIM_LABELS) if c != 'D4_output_complete'
]


def chart_category_by_model(df: pd.DataFrame, out_dir: Path):
    """D1–D3 por categoria — 1 painel por dimensão, barras agrupadas por modelo."""
    runs  = sorted(df['run'].unique())
    dims  = _CATEGORY_BY_MODEL_DIMS
    x     = np.arange(len(CAT_IDS))
    width = 0.8 / len(runs)

    # N por categoria (igual para todos os modelos: mesmo corpus)
    ref_run = df[df['run'] == runs[0]]
    totals  = [len(ref_run[ref_run['category'] == cat]) for cat in CAT_IDS]
    tick_labels = [f'{lbl}\n(N={t})' for lbl, t in zip(CAT_LABELS_SHORT, totals)]

    fig, axes = plt.subplots(1, len(dims), figsize=(5.2 * len(dims), 5.5), sharey=True)
    if len(dims) == 1:
        axes = [axes]

    for ax, (col, label) in zip(axes, dims):
        for i, (run, color) in enumerate(zip(runs, MODEL_PALETTE)):
            sub    = df[df['run'] == run]
            vals   = [_pct(sub[sub['category'] == cat][col]) for cat in CAT_IDS]
            offset = (i - (len(runs) - 1) / 2) * width
            bars   = ax.bar(x + offset, vals, width, color=color,
                            label=_model_label(run), edgecolor='white', linewidth=0.5)
            for bar, val in zip(bars, vals):
                if not math.isnan(val):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 1.5,
                            f'{val:.0f}', ha='center', va='bottom', fontsize=6.5)

        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, fontsize=8)
        ax.set_ylim(0, 118)
        ax.yaxis.grid(True, linestyle='--', alpha=0.4)
        ax.set_axisbelow(True)

    axes[0].set_ylabel('Acurácia (%)', fontsize=10)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=len(runs), fontsize=9,
               bbox_to_anchor=(0.5, -0.05), title='Modelo')

    fig.suptitle('Desempenho por categoria do corpus — D1, D2, D3 por modelo\n'
                 '(D4 Output omitido: 100% em todos os casos, sem valor discriminante; '
                 'N por categoria indicado no eixo X)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()

    out_path = out_dir / 'category_bar__by_model.png'
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

    max_val = 0
    for ax, run in zip(axes, runs):
        fp, fn = _draw_fp_fn(ax, df[df['run'] == run], 'd1_error_type', run)
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))
    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)

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

    max_val = 0
    for ax, run in zip(axes, runs):
        fp, fn = _draw_fp_fn(ax, df[df['run'] == run], 'd2_error_type', run)
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))
    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)

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

    max_val = 0
    for ax, run in zip(axes, runs):
        sub = df[df['run'] == run]

        # total de execuções com D3 aplicável por condição
        totals = [len(sub[(sub['context'] == ctx) & sub['D3_route'].notna()])
                  for ctx in CTX_ORDER]

        fp = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_positive')])
              for ctx in CTX_ORDER]
        fn = [len(sub[(sub['context'] == ctx) & (sub['d3_error_type'] == 'false_negative')])
              for ctx in CTX_ORDER]
        max_val = max(max_val, max(fp, default=0), max(fn, default=0))

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

    for ax in axes:
        if ax.get_visible():
            ax.set_ylim(0, max_val * 1.15 if max_val else 1)

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


# ── Chart 4: heatmap diagnóstico por modelo ───────────────────────────────────

def chart_heatmap(df: pd.DataFrame, run_name: str, out_dir: Path):
    """Grade requisito×condição (42 linhas) × D1-D3 — diagnóstico granular.

    D4 (output_complete) fica de fora: é 100% em todo o corpus, para todo
    modelo, então não discrimina nada — só ocuparia espaço com uma coluna
    inteiramente verde.
    """
    reqs = sorted(df['req_id'].unique())
    dims = _CATEGORY_BY_MODEL_DIMS

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


# ── Chart 5: classificação por taxonomia de Pohl (Agente 1a) ─────────────────
# D1 só mede has_ambiguity; este gráfico mede se o Agente 1a acerta o TIPO
# de ambiguidade (lexical/sintática/semântica/referencial/vaguidade) nos 4
# requisitos de Cat-02 desenhados para testar cada categoria — o próprio
# objetivo de "identificar e classificar" do Agente 1a, nunca avaliado antes.

def chart_taxonomy_grid(df: pd.DataFrame, out_dir: Path):
    """Grade requisito×modelo: célula mostra o(s) tipo(s) detectado(s) e se
    o esperado (pela taxonomia de Pohl) está entre eles."""
    req_ids = list(df['req_id'].unique())
    runs    = sorted(df['run'].unique())

    fig, ax = plt.subplots(figsize=(2.6 * len(runs) + 2, 1.3 * len(req_ids) + 1.5))

    for i, req_id in enumerate(req_ids):
        row = df[df['req_id'] == req_id].iloc[0]
        expected = row['expected_type']
        for j, run in enumerate(runs):
            cell = df[(df['req_id'] == req_id) & (df['run'] == run)]
            match = bool(cell['match'].iloc[0]) if len(cell) else None
            detected = cell['detected_types'].iloc[0] if len(cell) else '—'
            color = PASS_COLOR if match else (FAIL_COLOR if match is False else NA_COLOR)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color,
                                       linewidth=0.6, edgecolor='white'))
            ax.text(j + 0.5, i + 0.5, detected, ha='center', va='center',
                    fontsize=8, color='white', wrap=True)

    ax.set_xlim(0, len(runs))
    ax.set_ylim(0, len(req_ids))
    ax.set_xticks([j + 0.5 for j in range(len(runs))])
    ax.set_xticklabels([_model_label(r) for r in runs], fontsize=9)
    ax.set_yticks([i + 0.5 for i in range(len(req_ids))])
    ax.set_yticklabels(
        [f"{r}\n(esperado: {df[df['req_id'] == r]['expected_type'].iloc[0]})" for r in req_ids],
        fontsize=9,
    )
    ax.invert_yaxis()
    ax.set_title('Classificação por tipo (Pohl) — texto na célula = tipo(s) que o Agente 1a atribuiu',
                 fontsize=10.5, fontweight='bold', pad=10)

    legend = [mpatches.Patch(color=PASS_COLOR, label='Tipo esperado presente'),
              mpatches.Patch(color=FAIL_COLOR, label='Tipo esperado ausente')]
    fig.legend(handles=legend, loc='lower center', ncol=2, fontsize=9,
               bbox_to_anchor=(0.5, -0.05))
    plt.tight_layout()

    out_path = out_dir / 'taxonomy_classification.png'
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
    chart_category_by_model(df, out_dir)
    chart_error_type_bar(df, out_dir)
    for run in runs:
        chart_heatmap(df[df['run'] == run], run, out_dir)

    print(f'\nGráficos salvos em: {out_dir}')


if __name__ == '__main__':
    main()
