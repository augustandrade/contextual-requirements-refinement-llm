#!/usr/bin/env python3
"""
run_experiment.py — Executa o experimento completo: 7 modelos × corpus controlado → avaliação.

Uso:
  python3 run_experiment.py                        # todos os 7 modelos, corpus completo
  python3 run_experiment.py --models qwen3.5:9b    # modelo específico
  python3 run_experiment.py --dry-run              # lista o que seria executado, sem rodar
  python3 run_experiment.py --label main-v1        # sufixo para identificar as runs
  python3 run_experiment.py --skip-eval            # não roda evaluate.py ao final

O script:
  1. Inicializa o Ollama se não estiver rodando (via ensure_ollama_running).
  2. Para cada modelo, invoca process_corpus.py com OLLAMA_MODEL=<model>.
  3. Após todos os modelos, invoca evaluate.py para gerar métricas e gráficos.

Execuções esperadas: 51 instâncias × 7 modelos = 357 execuções
  (12 reqs ambíguos × 4 condições = 48 + 3 reqs controle × 1 condição = 3 = 51/modelo)
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_HERE       = Path(__file__).parent
_ANALYSIS   = _HERE / 'analysis'
_PROCESS    = _HERE / 'process_corpus.py'
_EVALUATE   = _ANALYSIS / 'evaluate.py'

MODELS = [
    'qwen3.5:4b',
    'qwen3.5:9b',
    'gemma3:4b',
    'mistral:7b',
    'llama3.1:8b',
    'phi4-mini',
    'deepseek-r1:7b',
]


def _ensure_ollama() -> None:
    sys.path.insert(0, str(_HERE))
    from agents import ensure_ollama_running
    ensure_ollama_running(timeout=60)


def _model_available(model: str) -> bool:
    """Verifica se o modelo já foi baixado no Ollama."""
    import urllib.request as _urlreq
    import json
    try:
        resp = _urlreq.urlopen('http://localhost:11434/api/tags', timeout=5)
        data = json.loads(resp.read())
        available = [m['name'] for m in data.get('models', [])]
        # Aceita match exato ou com/sem tag :latest
        return any(
            a == model or a.split(':')[0] == model.split(':')[0]
            for a in available
        )
    except Exception:
        return False


def _run_model(model: str, label: str, dry_run: bool) -> bool:
    """Executa process_corpus.py para um modelo. Retorna True se bem-sucedido."""
    tag = f'  [{model}]'
    if dry_run:
        print(f'{tag} DRY-RUN — process_corpus.py --label {label or "main"}')
        return True

    env = {**os.environ, 'OLLAMA_MODEL': model}
    cmd = [sys.executable, str(_PROCESS)]
    if label:
        cmd += ['--label', label]

    print(f'\n{tag} iniciando — {datetime.now().strftime("%H:%M:%S")}', flush=True)
    t0 = time.monotonic()
    result = subprocess.run(cmd, env=env)
    elapsed = time.monotonic() - t0
    mins, secs = divmod(int(elapsed), 60)
    status = 'OK' if result.returncode == 0 else f'ERRO (código {result.returncode})'
    print(f'{tag} {status} — {mins}m{secs:02d}s', flush=True)
    return result.returncode == 0


def _run_evaluation(dry_run: bool) -> None:
    if dry_run:
        print('\n  [eval] DRY-RUN — evaluate.py')
        return
    print(f'\n{"═" * 60}')
    print('Iniciando avaliação consolidada...', flush=True)
    result = subprocess.run([sys.executable, str(_EVALUATE)])
    if result.returncode != 0:
        print(f'[WARN] evaluate.py terminou com código {result.returncode}', file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description='Executa o experimento completo de LLMs')
    parser.add_argument('--models',    nargs='+', default=None,
                        help='Modelos a executar (padrão: todos os 7)')
    parser.add_argument('--label',     default='main-v1',
                        help='Sufixo de identificação das runs (padrão: main-v1)')
    parser.add_argument('--dry-run',   action='store_true',
                        help='Lista o que seria executado sem rodar nada')
    parser.add_argument('--skip-eval', action='store_true',
                        help='Não executa evaluate.py ao final')
    args = parser.parse_args()

    models = args.models or MODELS

    print('=' * 60)
    print('EXPERIMENTO — Pipeline multi-agente LLM')
    print(f'Modelos   : {len(models)}')
    print(f'Label     : {args.label}')
    print(f'Instâncias: 51 por modelo  (48 ambíguas + 3 controle)')
    print(f'Total     : {51 * len(models)} execuções estimadas')
    print('=' * 60)

    if not args.dry_run:
        print('\nInicializando Ollama...')
        try:
            _ensure_ollama()
        except RuntimeError as e:
            sys.exit(f'Erro: {e}')

        # Avisa modelos não disponíveis antes de começar
        missing = [m for m in models if not _model_available(m)]
        if missing:
            print('\n[AVISO] Os seguintes modelos não foram encontrados no Ollama:')
            for m in missing:
                print(f'  ollama pull {m}')
            resp = input('\nDeseja continuar mesmo assim? (s/N) ').strip().lower()
            if resp != 's':
                sys.exit('Abortado.')

    results: dict[str, bool] = {}
    t_total = time.monotonic()

    for i, model in enumerate(models, 1):
        print(f'\n[{i}/{len(models)}] {model}')
        ok = _run_model(model, args.label, args.dry_run)
        results[model] = ok
        if not ok:
            print(f'  [WARN] {model} falhou — continuando com o próximo modelo', file=sys.stderr)

    elapsed_total = time.monotonic() - t_total
    h, rem = divmod(int(elapsed_total), 3600)
    m, s   = divmod(rem, 60)

    print(f'\n{"═" * 60}')
    print(f'Resumo — tempo total: {h}h{m:02d}m{s:02d}s')
    for model, ok in results.items():
        mark = '✓' if ok else '✗'
        print(f'  {mark}  {model}')

    failed = [m for m, ok in results.items() if not ok]
    if failed:
        print(f'\n{len(failed)} modelo(s) com falha. Para retentar:')
        for m in failed:
            print(f'  python3 run_experiment.py --models {m} --label {args.label}')

    if not args.skip_eval:
        _run_evaluation(args.dry_run)
    else:
        print('\nAvaliação pulada (--skip-eval). Para rodar manualmente:')
        print(f'  python3 analysis/evaluate.py')


if __name__ == '__main__':
    main()
