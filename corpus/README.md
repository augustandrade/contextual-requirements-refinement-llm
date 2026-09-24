# Controlled Corpus Package

This folder stores the canonical definition of the controlled corpus for the experiment.

## Scope

- 15 base requirements (`REQ-01` to `REQ-15`)
- 4 context levels per requirement (`C0`, `C1`, `C2`, `C3`)
- 60 possible experimental instances per model, derived from `base_requirement + context_level`
- Only `C0` is always executed; `C1`–`C3` run only when Agent 1 detects ambiguity in `C0` (including false positives on the control group)
- Ceiling of 420 executions across the 7 models (60 × 7)
- Pilot: 6 author-written requirements (`pilot/`, `pilot-manifest.yaml`), used to tune prompts; not part of the experiment

## Structure

- `manifest.yaml`: corpus metadata and index
- `category-01-structural/`: REQ-01 to REQ-03
- `category-02-linguistic/`: REQ-04 to REQ-06
- `category-03-domain/`: REQ-07 to REQ-09
- `category-04-vagueness/`: REQ-10 to REQ-12
- `category-05-control/`: REQ-13 to REQ-15 (negative control: well-formed requirements)
- `pilot/`: REQ-PILOT-01 to REQ-PILOT-06

## Context semantics

- `C0`: no contextual evidence
- `C1`: system domain and glossary of peripheral terms, excluding the ambiguous fragment
- `C2`: C1 plus content that directly addresses the ambiguous fragment (relevant, specific)
- `C3`: C1 plus specific content about a different aspect of the requirement, never the ambiguous fragment (irrelevant, specific)
- C2 vs C3 isolates relevance (specificity held constant); C3 vs C1 isolates specificity; C1 vs C0 measures the effect of generic context

## Structuring note

- Concern separation and decomposition are treated as auxiliary operations inside final requirement structuring, not as independent pipeline stages.
- When the contextual resolubility outcome is `unresolved`, the execution bypasses Agent 3 and follows the `signaling` route.
- `resolvable` means the next step can adopt the supported interpretation safely; `unresolved` means the ambiguity cannot be eliminated safely with the available evidence.

## Canonical language policy

- Requirement texts: English
- Context content: English
- Metadata keys and technical values: English
