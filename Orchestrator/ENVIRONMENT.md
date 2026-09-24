# Execution environment

Recorded on 2026-09-24, after the main experiment (runs of 2026-09-22 and 2026-09-23,
label `main-v1`). Every model file listed below was last modified before 2026-09-22
(latest: 2026-07-28), so the weights were not replaced between runs.

## Hardware and software

| Item | Value |
|---|---|
| Machine | MacBook Pro (Mac17,2), Apple M5, 16 GB RAM |
| Operating system | macOS 27.0 (build 26A428) |
| Ollama | 0.21.1 |
| Interface | REST `/api/chat`, `stream: false` |

## Generation parameters (all models)

`temperature=0.0`, `think=false`, `num_ctx=8192`. `num_predict`: 3000 (Agent 1), 2500
(Agents 2 and 3). `seed` not set (temperature 0.0). Defined in `Orchestrator/agents.py`.

## Models (Ollama tag, quantization Q4_K_M for all)

| Tag | Family | Parameters | Model file modified | Digest (sha256) |
|---|---|---|---|---|
| qwen3.5:4b | qwen35 | 4.7B | 2026-06-01 | 2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd |
| qwen3.5:9b | qwen35 | 9.7B | 2026-06-01 | 6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7 |
| gemma3:4b | gemma3 | 4.3B | 2026-07-28 | a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a |
| mistral:7b | llama | 7.2B | 2026-06-13 | 6577803aa9a036369e481d648a2baebb381ebc6e897f2bb9a766a2aa7bfbc1cf |
| llama3.1:8b | llama | 8.0B | 2026-07-28 | 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e |
| phi4-mini | phi3 | 3.8B | 2026-07-28 | 78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753 |
| deepseek-r1:7b | qwen2 | 7.6B | 2026-07-28 | 755ced02ce7befdb13b7ca74e1e4d08cddba4986afdb63a480f2c93d3140383f |

Limitation: the Ollama version and hardware were read after the runs, not logged by
each run (`run_metadata.json` records model, temperature and `think` only).
