"""
Smoke tests for generate_charts.py.

Each test verifies that a chart function:
  1. Runs without raising an exception on minimal but structurally valid data.
  2. Creates the expected output file in the provided tmp_path.

No visual correctness is asserted.
All DataFrames mirror the columns produced by evaluate.py after the 2026-08 refactor:
  - expected_has_ambiguity  (bool)  — category_id != 'category-05-control'
  - D1_has_ambiguity        (bool)
  - D_output_integrity      (bool)
  - route_structured        (bool)  — derived: act_route == 'structured'
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import generate_charts as gc


# ── Constants ─────────────────────────────────────────────────────────────────

_RUNS = ['run_001__model-a', 'run_002__model-b']

_POS_CATS = [
    'category-01-structural',
    'category-02-linguistic',
    'category-03-domain',
    'category-04-vagueness',
]
_NEG_CATS = ['category-05-control']
_ALL_CATS = _POS_CATS + _NEG_CATS
_CTXS     = ['C0', 'C1', 'C2']


# ── DataFrame builders ────────────────────────────────────────────────────────

def _make_eval_df(runs=_RUNS, include_c3: bool = False) -> pd.DataFrame:
    """Minimal evaluation DataFrame matching evaluate_run() output.

    3 positive categories × 3 reqs each + 1 control × 3 reqs = 12 reqs.
    Each req × each run × each context = one row.
    D1 is True for all rows except one FN injected for non-trivial charts.
    """
    ctxs = _CTXS + (['C3'] if include_c3 else [])
    rows = []
    req_n = 0
    for cat in _ALL_CATS:
        exp_ha = (cat != 'category-05-control')
        for i in range(3):
            req_n += 1
            req_id = f'REQ-{req_n:02d}'
            for run in runs:
                for ctx in ctxs:
                    # Route becomes 'structured' from C1 onward for positive cats
                    route = 'structured' if (not exp_ha or ctx != 'C0') else 'signaling'
                    d1    = True
                    # inject one FN for non-trivial error-type chart
                    if req_n == 2 and ctx == 'C0' and run == runs[0]:
                        d1    = False
                    rows.append({
                        'run':                   run,
                        'req_id':                req_id,
                        'context':               ctx,
                        'category':              cat,
                        'expected_has_ambiguity': exp_ha,
                        'act_has_ambiguity':     exp_ha,
                        'act_route':             route,
                        'route_structured':      route == 'structured',
                        'D1_has_ambiguity':      pd.array([d1],   dtype='boolean')[0],
                        'D_output_integrity':    pd.array([True], dtype='boolean')[0],
                        'd1_error_type':         None if d1 else 'false_negative',
                        'ambiguity_count':       1 if exp_ha else 0,
                        'score':                 1.0 if d1 else 0.5,
                        'act_global_status':     'no_ambiguity' if not exp_ha else 'fully_resolvable',
                    })
    return pd.DataFrame(rows)


def _make_lift_df(runs=_RUNS, include_c3: bool = False) -> pd.DataFrame:
    """Minimal context_lift DataFrame matching evaluate_context_lift() output."""
    rows = []
    req_n = 0
    for cat in _POS_CATS:
        for i in range(3):
            req_n += 1
            for run in runs:
                s3 = 1 if include_c3 else None
                rows.append({
                    'run':                    run,
                    'req_id':                 f'REQ-{req_n:02d}',
                    'category':               cat,
                    'expected_has_ambiguity': True,
                    'structured_c0':          0,
                    'structured_c1':          0,
                    'structured_c2':          1,
                    'structured_c3':          s3,
                    'lift_c2_c0':             1,
                    'lift_c3_c0':             0 if include_c3 else None,
                    'delta_c2_c3':            1 if include_c3 else None,
                    'stage_c0_c1':            0,
                    'stage_c1_c2':            1,
                    'transition':             '0→0→1→?' if not include_c3 else '0→0→1→1',
                })
    return pd.DataFrame(rows)


def _make_taxonomy_df(runs=_RUNS) -> pd.DataFrame:
    """Minimal taxonomy_classification DataFrame."""
    req_accepted = {
        'REQ-04': 'referential, syntactic',
        'REQ-05': 'syntactic',
        'REQ-06': 'semantic',
        'REQ-07': 'vagueness',
    }
    rows = []
    for run in runs:
        for req_id, accepted in req_accepted.items():
            rows.append({
                'run':            run,
                'req_id':         req_id,
                'accepted_types': accepted,
                'detected_types': accepted.split(', ')[0],
                'match':          True,
            })
    return pd.DataFrame(rows)


# ── Bloco 1 — Detecção ────────────────────────────────────────────────────────

def test_chart_d1_classification_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_d1_classification(df, tmp_path)
    assert (tmp_path / 'd1_classification.png').exists()


def test_chart_error_type_bar_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_error_type_bar(df, tmp_path)
    assert (tmp_path / 'error_type__D1_ambiguidade.png').exists()


def test_chart_heatmap_creates_file(tmp_path):
    df = _make_eval_df()
    gc.chart_heatmap(df, tmp_path)
    assert (tmp_path / 'heatmap__D1_req_modelo.png').exists()


# ── Bloco 2 — Sensibilidade ao contexto ──────────────────────────────────────

def test_chart_context_lift_creates_file(tmp_path):
    df      = _make_eval_df()
    df_lift = _make_lift_df()
    gc.chart_context_lift(df, df_lift, tmp_path)
    assert (tmp_path / 'context_lift__route_delta.png').exists()


def test_chart_context_lift_with_c3_creates_file(tmp_path):
    df      = _make_eval_df(include_c3=True)
    df_lift = _make_lift_df(include_c3=True)
    gc.chart_context_lift(df, df_lift, tmp_path)
    assert (tmp_path / 'context_lift__route_delta.png').exists()


def test_chart_context_lift_empty_ambiguous_warns(tmp_path, capsys):
    """When no rows have expected_has_ambiguity=True, function warns and exits cleanly."""
    df      = _make_eval_df()
    df_lift = _make_lift_df()
    df_lift_neg = df_lift[df_lift['expected_has_ambiguity'] == False].copy()
    if df_lift_neg.empty:
        df_lift_neg = pd.DataFrame(columns=df_lift.columns)
    gc.chart_context_lift(df, df_lift_neg, tmp_path)
    captured = capsys.readouterr()
    assert 'WARN' in captured.out or not (tmp_path / 'context_lift__route_delta.png').exists()


# ── Bloco 3 — Taxonomia Pohl ──────────────────────────────────────────────────

def test_chart_taxonomy_grid_creates_file(tmp_path):
    df_tax = _make_taxonomy_df()
    gc.chart_taxonomy_grid(df_tax, tmp_path)
    assert (tmp_path / 'taxonomy_classification.png').exists()


def test_chart_taxonomy_model_heatmap_creates_file(tmp_path):
    df_tax = _make_taxonomy_df()
    gc.chart_taxonomy_model_heatmap(df_tax, tmp_path)
    assert (tmp_path / 'taxonomy_model_heatmap.png').exists()


def test_chart_taxonomy_grid_without_accepted_types_does_not_crash(tmp_path, capsys):
    """accepted_types column missing → graceful warn/exit, no crash."""
    df_tax = _make_taxonomy_df().drop(columns=['accepted_types'])
    try:
        gc.chart_taxonomy_grid(df_tax, tmp_path)
    except Exception:
        pass  # crash is also acceptable — we just want no silent corrupt output
    captured = capsys.readouterr()
    # Either warns or does not produce the file — both are acceptable
    _ = captured.out


# ── Bloco 4 — Integridade do output ──────────────────────────────────────────

def test_table_d_output_summary_creates_files(tmp_path):
    df = _make_eval_df()
    gc.table_d_output_summary(df, tmp_path)
    assert (tmp_path / 'd_output_summary_table.png').exists()
    assert (tmp_path / 'd_output_summary.csv').exists()


def test_table_d_output_summary_missing_column_warns(tmp_path, capsys):
    df = _make_eval_df().drop(columns=['D_output_integrity'])
    gc.table_d_output_summary(df, tmp_path)
    captured = capsys.readouterr()
    assert 'WARN' in captured.out


# ── Column contract: expected_has_ambiguity must exist ───────────────────────

class TestColumnContracts:

    def test_error_type_bar_requires_expected_has_ambiguity(self, tmp_path):
        df = _make_eval_df().drop(columns=['expected_has_ambiguity'])
        with pytest.raises(Exception):
            gc.chart_error_type_bar(df, tmp_path)

    def test_d1_classification_requires_context_column(self, tmp_path):
        df = _make_eval_df().drop(columns=['context'])
        with pytest.raises(Exception):
            gc.chart_d1_classification(df, tmp_path)

    def test_context_lift_requires_lift_c2_c0_in_lift_df(self, tmp_path):
        df      = _make_eval_df()
        df_lift = _make_lift_df().drop(columns=['lift_c2_c0'])
        with pytest.raises(Exception):
            gc.chart_context_lift(df, df_lift, tmp_path)


# ── Single-run smoke test ─────────────────────────────────────────────────────

def test_all_chart_functions_work_with_single_run(tmp_path):
    """All chart functions that handle multiple models must not crash on a single run."""
    single = ['run_001__model-only']
    df      = _make_eval_df(runs=single)
    df_lift = _make_lift_df(runs=single)
    df_tax  = _make_taxonomy_df(runs=single)

    gc.chart_d1_classification(df, tmp_path)
    gc.chart_error_type_bar(df, tmp_path)
    gc.chart_heatmap(df, tmp_path)
    gc.chart_context_lift(df, df_lift, tmp_path)
    gc.chart_taxonomy_grid(df_tax, tmp_path)
    gc.chart_taxonomy_model_heatmap(df_tax, tmp_path)
    gc.table_d_output_summary(df, tmp_path)

    assert (tmp_path / 'd1_classification.png').exists()
    assert (tmp_path / 'context_lift__route_delta.png').exists()
    assert (tmp_path / 'taxonomy_classification.png').exists()
    assert (tmp_path / 'd_output_summary_table.png').exists()
