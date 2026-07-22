# Local LLM Setup

This orchestrator is provider-agnostic. For the TCC, the default runtime is local.

Recommended local model:
- Qwen2.5 7B Instruct GGUF

Why this default:
- Good balance of quality and memory usage on a MacBook Pro M5
- No Meta Llama license required
- Works well with `llama-cpp-python`

Environment variables:

```bash
export LLM_PROVIDER=local
export LLM_LOCAL_MODEL_PATH="/absolute/path/to/Qwen2.5-7B-Instruct-GGUF.gguf"
```

Optional future providers:
- `LLM_PROVIDER=openai` with `OPENAI_API_KEY`
- `LLM_PROVIDER=mock` for offline tests

Suggested install for local execution:

```bash
pip install pyyaml openai llama-cpp-python
```

Run the pipeline:

```bash
python3 TCC/Orchestrator/run_pipeline.py
```

Notes:
- Keep the `LLM_LOCAL_MODEL_PATH` pointed at a GGUF file, not a Meta Llama-only package.
- If you later want to switch providers, only the environment variables need to change.
