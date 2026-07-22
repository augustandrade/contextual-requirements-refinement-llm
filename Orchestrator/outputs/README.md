# Outputs — Guia de Operação do Pipeline

## 1. Verificar se o Ollama está ativo

```bash
curl http://localhost:11434/api/tags
```

Se retornar JSON com a lista de modelos, o Ollama está ativo. Se retornar erro de conexão, inicie-o:

```bash
ollama serve
```

Deixe o terminal aberto (ou rode em background com `ollama serve &`). Para verificar os modelos disponíveis:

```bash
ollama list
```

Os três modelos utilizados nos experimentos devem estar presentes:

```
qwen3.5:4b
qwen3.5:9b
gemma4:e4b
```

Se algum modelo estiver ausente, baixe-o:

```bash
ollama pull qwen3.5:4b
ollama pull qwen3.5:9b
ollama pull gemma4:e4b
```

---

## 2. Rodar o pipeline para o corpus completo

Todos os comandos devem ser executados a partir do diretório `Orchestrator/`:

```bash
cd "/Users/augustandrade/Library/Mobile Documents/com~apple~CloudDocs/[] ARQUIVOS/[] ACADEMICO/[] MBA USP/TCC/Orchestrator"
```

### qwen3.5:4b

```bash
OLLAMA_MODEL=qwen3.5:4b python3 process_corpus.py
```

### qwen3.5:9b

```bash
OLLAMA_MODEL=qwen3.5:9b python3 process_corpus.py
```

### gemma4:e4b

```bash
OLLAMA_MODEL=gemma4:e4b python3 process_corpus.py
```

### Retomar uma run interrompida

Se a execução parou no meio, use `--resume` com o nome exato da run parcial:

```bash
OLLAMA_MODEL=qwen3.5:4b python3 process_corpus.py --resume run_002__qwen3.5-4b__2026-06-13T10-44
```

O pipeline verifica quais requisitos/condições já têm `05_final_output.json` e pula automaticamente, continuando de onde parou.

---

Para rodar em background (libera o terminal):

**Terminal 1 — inicia o processo:**
```bash
OLLAMA_MODEL=qwen3.5:4b python3 -u process_corpus.py > /tmp/corpus_run.log 2>&1 &
```

**Terminal 2 — acompanha o progresso em tempo real:**
```bash
tail -f /tmp/corpus_run.log
```

Pressione Ctrl+C no Terminal 2 para parar de acompanhar — o processo continua rodando em background.

---

## 3. Avaliar os resultados e gerar gráficos

Após a conclusão das runs, execute o avaliador a partir do diretório `Orchestrator/` (os caminhos são resolvidos automaticamente a partir do script):

```bash
# Todas as runs disponíveis
python3 evaluate.py

# Uma run específica
python3 evaluate.py --run run_002

# Com label descritivo na pasta de saída
python3 evaluate.py --label qwen3.5-4b

# Ignorar uma run específica (ex: run_001 do pipeline antigo)
python3 evaluate.py --exclude run_001
```

O avaliador cria automaticamente uma pasta `outputs/evaluation/eval__<timestamp>[__<label>]/` com CSV, metadata e gráficos:

```
outputs/evaluation/
  eval__2026-06-13T10-00__qwen3.5-4b/
    metadata.json               ← runs incluídas, modelos, data de geração
    evaluation_results.csv
    charts/
      context_line__D3_D4.png        ← D3 e D4 por C0/C1/C2, uma linha por modelo (figura principal)
      category_bar__D1_D4.png        ← D1–D4 por categoria do corpus, modelos agregados
      pipeline_consolidated.png      ← perfil geral D1–D4, todos os modelos e condições
      heatmap__<run>.png             ← grade requisito × condição, pass/fail por dimensão (diagnóstico)
```

---

## 5. Estrutura de diretórios

```
outputs/
  runs/
    run_NNN__<modelo>__<timestamp>/
      run_metadata.json
      REQ-XX/
        C0/
          01_input.json
          02a_ambiguity_detection.json
          02b_concern_mixing_detection.json
          03_resolubility_validation.json
          04_requirement_structuring.json
          05_final_output.json
        C1/  ...
        C2/  ...
  evaluation/
    eval__<timestamp>[__<label>]/
      metadata.json          ← runs incluídas, modelos, data de geração
      evaluation_results.csv
      charts/
        context_line__D3_D4.png
        category_bar__D1_D4.png
        pipeline_consolidated.png
        heatmap__<run>.png
  archive/                 # runs anteriores arquivadas
```

Os Agentes 1a e 1b são executados uma vez por requisito e o output é reutilizado nas condições C0, C1 e C2 (ambos recebem apenas `base_requirement_text`, sem contexto).
