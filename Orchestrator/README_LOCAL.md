# Local Setup

## Requirements

```bash
pip install -r requirements.txt
```

Ollama must be running locally with the target model pulled:

```bash
ollama pull qwen2.5:7b
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `qwen3.5:latest` | Any model available in your Ollama instance |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_TIMEOUT` | `600` | Request timeout in seconds |

## Running the corpus

```bash
# Full corpus (45 executions)
python3 process_corpus.py

# Smoke test — 1 req per category, 1 context (~4 executions)
python3 process_corpus.py --subset

# Pilot corpus (12 executions)
python3 process_corpus.py --manifest pilot-manifest.yaml

# Resume an interrupted run
python3 process_corpus.py --resume run_001__qwen2.5-7b__2026-07-27

# Use a different model
OLLAMA_MODEL=qwen2.5:14b python3 process_corpus.py --label v2
```

## Output structure

```
outputs/runs/<run_id>/<REQ-ID>/<CTX>/
    01_input.json
    02_ambiguity_detection.json
    03_resolubility_validation.json
    04_requirement_structuring.json
    05_final_output.json
```

## Analysis

```bash
# Evaluate a run against the corpus manual reference
python3 analysis/evaluate.py

# Generate charts from evaluation results
python3 analysis/generate_charts.py
```
