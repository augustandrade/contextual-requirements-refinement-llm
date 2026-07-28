"""
Smoke tests for generate_charts.py.

Each test verifies that a chart function:
  1. Runs without raising an exception on minimal but structurally valid data.
  2. Creates the expected output file in the provided tmp_path.

No visual correctness is asserted — that would require image diffing.
All tests use synthetic DataFrames that mirror the columns produced by evaluate.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import generate_charts as gc


# ── Fixtures ──────────────────────────────────────────────────────────────────

_RUNS = ['run_001__model-a', 'run_002__model-b']
_CATS = [
    'category-01-structural',
    'category-02-linguistic',
    'category-03-domain',
    'category-04-vagueness',
    'category-05-control',
]
_CTXS = ['C0', 'C1', 'C2']

# Mapping: category → expected_resolubility (one typical value per cat)
_CAT_RES = {
    'category-01-structural': 'not_applicable',
    'category-02-linguistic': 'resolvable',
    'category-03-domain':     'resolvable',
    'category-04-vagueness':  'resolvable',
    'category-05-control':    'not_applicable',
}

def _make_eval_df(runs=_RUNS) -> pd.DataFrame:
    """Minimal evaluation DataFrame mimicking evaluate_run output (all 42 rows)."""
    rows = []
    req_n = 0
    for cat in _CATS:
        n_reqs = 2 if cat == 'category-01-structural' else 3
        for i in range(n_reqs):
            req_n += 1
            req_id = f'REQ-{req_n:02d}'
            exp_res = _CAT_RES[cat]
            # D1: True when not_applicable→False correct, else True
            d1  = True
            has_ambiguity = exp_res != 'not_applicable'
            for run in runs:
                for ctx in _CTXS:
                    # D3: True for C2, False for C0/C1 on positive cats
                    d3 = True if (ctx == 'C2' or exp_res == 'not_applicable') else False
                    d1_err = None
                    # inject one FP and one FN per dimension for non-trivial charts
                    if req_n == 2 and ctx == 'C0' and run == runs[0]:
                        d1     = False
                        d1_err = 'false_negative'
                    d3_err = None if d3 else 'false_negative'
                    rows.append({
                        'run':                   run,
                        'req_id':                req_id,
                        'context':               ctx,
                        'category':              cat,
                        'expected_resolubility': exp_res,
                        'act_has_ambiguity':     has_ambiguity,
                        'act_route':             'structured' if d3 else 'signaling',
                        'D1_has_ambiguity':      pd.array([d1],   dtype='boolean')[0],
                        'D2_route':              pd.array([d3],   dtype='boolean')[0],
                        'D3_output_complete':    pd.array([True], dtype='boolean')[0],
                        'd1_error_type':         d1_err,
                        'd2_error_type':         d3_err,
                        'ambiguity_count':       1 if has_ambiguity else 0,
                        'score':                 1.0,
                        'act_global_status':     'no_ambiguity',
                    })
    return pd.DataFrame(rows)


def _make_lift_df(runs=_RUNS) -> pd.DataFrame:
    """Minimal context_lift DataFrame mimicking evaluate_context_lift output."""
    pos_cats = [
        'category-02-linguistic',
        'category-03-domain',
        'category-04-vagueness',
    ]
    rows = []
    req_n = 4  # first positive req
    for cat in pos_cats:
        for i in range(3):
            req_n += 1
            for run in runs:
                # Pattern: 0→0→1 (context resolved)
                rows.append({
                    'run':        run,
                    'req_id':     f'REQ-{req_n:02d}',
                    'category':   cat,
                    'd2_c0':      0,
                    'd2_c1':      0,
                    'd2_c2':      1,
                    'lift_c2_c0':  1,
                    'stage_c0_c1': 0,
                    'stage_c1_c2': 1,
                    'transition':  '0→0→1',
                })
    return pd.DataFrame(rows)


def _make_taxonomy_df(runs=_RUNS) -> pd.DataFrame:
    """Minimal taxonomy_classification DataFrame."""
    req_ids = ['REQ-04', 'REQ-05', 'REQ-06', 'REQ-07']
    accepted = {
        'REQ-04': 'referential, syntactic',
        'REQ-05': 'syntactic',
        'REQ-06': 'logical, semantic',
        'REQ-07': 'vagueness',
    }
    rows = []
    for run in runs:
        for req_id in req_ids:
            rows.append({
                'run':            run,
                'req_id':         req_id,
                'accepted_types': accepted[req_id],
                'detected_types': accepted[req_id].split(', ')[0],
                'match':          True,
            })
    return pd.DataFrame(rows)


# ── Bloco 1 — Detecção ────────────────────────────────────────────────────────

def test_chart_detection_bar_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_detection_bar(df, tmp_path)
    assert (tmp_path / 'detection_bar__D1.png').exists()


def test_chart_error_type_bar_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_error_type_bar(df, tmp_path)
    assert (tmp_path / 'error_type__D1_ambiguidade.png').exists()


# ── Bloco 2 — Resolução ───────────────────────────────────────────────────────

def test_chart_context_line_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_context_line(df, tmp_path)
    assert (tmp_path / 'context_line__D2_D3.png').exists()


def test_chart_route_error_context_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_route_error_context(df, tmp_path)
    assert (tmp_path / 'error_type__D2_rota_por_contexto.png').exists()


# ── Context lift ──────────────────────────────────────────────────────────────

def test_chart_context_lift_creates_file(tmp_path):
    df_lift = _make_lift_df()
    gc.chart_context_lift(df_lift, tmp_path)
    assert (tmp_path / 'context_lift__D2_delta.png').exists()


def test_chart_context_lift_empty_positive_cats_does_not_crash(tmp_path, capsys):
    """If lift df has no positive-category rows, function warns and exits cleanly."""
    df_lift = _make_lift_df()
    # strip all positive categories
    df_neg = df_lift[df_lift['category'].isin(['category-01-structural'])].copy()
    if df_neg.empty:
        df_neg = pd.DataFrame(columns=df_lift.columns)
    gc.chart_context_lift(df_neg, tmp_path)
    captured = capsys.readouterr()
    assert 'WARN' in captured.out or not (tmp_path / 'context_lift__D2_delta.png').exists()


# ── Diagnóstico ───────────────────────────────────────────────────────────────

def test_chart_heatmap_creates_file(tmp_path):
    df = _make_eval_df(runs=['run_001__model-a'])
    run_name = 'run_001__model-a'
    gc.chart_heatmap(df[df['run'] == run_name], run_name, tmp_path)
    assert (tmp_path / f'heatmap__{run_name}.png').exists()


def test_chart_taxonomy_grid_creates_file(tmp_path):
    df_tax = _make_taxonomy_df()
    gc.chart_taxonomy_grid(df_tax, tmp_path)
    assert (tmp_path / 'taxonomy_classification.png').exists()


# ── Contratos de colunas ──────────────────────────────────────────────────────

class TestColumnContracts:
    """Verify that each chart function fails clearly on missing required columns,
    rather than silently producing a corrupt chart."""

    def test_detection_bar_requires_context_column(self, tmp_path):
        df = _make_eval_df().drop(columns=['context'])
        with pytest.raises(Exception):
            gc.chart_detection_bar(df, tmp_path)

    def test_context_line_requires_d3_route(self, tmp_path):
        df = _make_eval_df().drop(columns=['D2_route'])
        with pytest.raises(Exception):
            gc.chart_context_line(df, tmp_path)

    def test_context_lift_requires_lift_c2_c0(self, tmp_path):
        df_lift = _make_lift_df().drop(columns=['lift_c2_c0'])
        with pytest.raises(Exception):
            gc.chart_context_lift(df_lift, tmp_path)

    def test_taxonomy_grid_falls_back_without_accepted_types(self, tmp_path):
        # accepted_types has a graceful fallback — no crash, file still produced
        df_tax = _make_taxonomy_df().drop(columns=['accepted_types'])
        gc.chart_taxonomy_grid(df_tax, tmp_path)
        assert (tmp_path / 'taxonomy_classification.png').exists()


# ── Comportamento com run único ───────────────────────────────────────────────

def test_all_charts_work_with_single_run(tmp_path):
    """Charts that show one panel per model must work when there is only one run."""
    single_run = ['run_001__model-only']
    df      = _make_eval_df(runs=single_run)
    df_lift = _make_lift_df(runs=single_run)
    df_tax  = _make_taxonomy_df(runs=single_run)

    gc.chart_detection_bar(df, tmp_path)
    gc.chart_error_type_bar(df, tmp_path)
    gc.chart_context_line(df, tmp_path)
    gc.chart_route_error_context(df, tmp_path)
    gc.chart_context_lift(df_lift, tmp_path)
    gc.chart_heatmap(df[df['run'] == single_run[0]], single_run[0], tmp_path)
    gc.chart_taxonomy_grid(df_tax, tmp_path)

    assert (tmp_path / 'detection_bar__D1.png').exists()
    assert (tmp_path / 'context_lift__D2_delta.png').exists()
    assert (tmp_path / 'taxonomy_classification.png').exists()
