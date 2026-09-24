# Diagnostic: failed executions in run_004 (qwen3.5:9b, main-v1)

Executed on 2026-09-24. Documents three pipeline executions that never produced a
`final_output.json` in `run_004__qwen3.5-9b__2026-09-22T15-59__main-v1`, and the
attempts made to recover them. **No file of the original run was modified**: all
retries below ran either through `--resume` (which reproduced the failures and wrote
nothing) or on throw-away copies of the run directory.

## The three failed executions

| Execution | Agent | Failure |
|---|---|---|
| REQ-05 / C2 | 2 (resolubility check) | YAML unparsable: model reasoning ("Wait, I need to check the logic again...") leaked inside the `justification` field; `overall_resolubility` block never emitted |
| REQ-13 / C2 | 3 (structurer) | YAML unparsable: dozens of reasoning items inside `structuring_notes`; output cut off |
| REQ-13 / C3 | 3 (structurer) | Same as REQ-13 / C2 (byte-identical raw output) |

Result: 375 executions recorded out of 378 attempted (0.8%), all in qwen3.5:9b.

## Steps and evidence

1. **`--resume`** (`logs/01_resume_run004.log`): `process_corpus.py --resume` re-ran the
   pending contexts with the original parameters. The same three failures recurred
   (temperature 0.0, so deterministic). REQ-13 / C3 Agent 2 was recovered by the existing
   `_repair_yaml_embedded_quote`, but its Agent 3 failed again. Agent 1 outputs were
   byte-identical to a backup taken before the resume.
2. **Raw capture at the original limits** (`scripts/capture.py`, `logs/02_...`,
   `raw_num_predict_2500/`): the three failing calls plus the Agent 1 calls, on a copy of
   the run, saving the complete model response (the pipeline logs only 400 characters).
   Original limits: `num_ctx=8192`, `num_predict=2500` for Agents 2 and 3. The Ollama stop
   reason was not recorded in this pass.
3. **Diagnostic with a larger generation budget** (`scripts/diag.py`, `logs/03_...`,
   `raw_num_predict_6000/`): same calls with `num_predict=6000`, recording `done_reason`
   and `eval_count`. Other parameters unchanged (`temperature=0.0`, `think=false`,
   `num_ctx=8192`).

| Call | Agent | done_reason | eval_count | Outcome |
|---|---|---|---|---|
| call02 | 2, REQ-05 / C2 | stop | 3863 | Finished, but reasoning inside `justification` still breaks the YAML |
| call05 | 3, REQ-13 / C2 | **length** | 6000 | Hit the 6000-token cap: reasoning loop |
| call07 | 3, REQ-13 / C3 | **length** | 6000 | Same |
| others | 1 and 2 (non-failing) | stop | 152-362 | Normal |

## Conclusions

- Raising `num_predict` from 2500 to 6000 does not recover any of the three executions.
- REQ-13 (Agent 3): unbounded reasoning loop, not a low cap.
- REQ-05 / C2 (Agent 2): the cap was truncating, but the completed output is still invalid.
- A parser repair was considered and rejected: in REQ-05 / C2 the block that decides the
  routing (`overall_resolubility`) is absent from the truncated response, so repairing it
  would require inventing a pipeline decision.
- Therefore the three executions are reported as model failures, not recovered.

## Notes

- `scripts/*.py` are the scripts exactly as executed. They embed absolute paths of the
  session's scratch directory and expect to be run from `Orchestrator/` with a copy of the
  run directory; they are kept for traceability, not as a turnkey tool.
- Each `raw_*/callNN.txt` holds the full model response (the 2500-pass files also carry the
  first 300 characters of the user payload).
- The runs themselves (`Orchestrator/outputs/`) are versioned in the repository since commit
  `2555623`; this diagnostic lives outside that directory so it stays separate from the
  original run, which was not modified.
