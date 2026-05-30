# Controlled Corpus Package

This folder stores the canonical definition of the controlled corpus for the experiment.

## Scope

- 15 base requirements (`REQ-01` to `REQ-15`)
- 3 context levels per requirement (`C0`, `C1`, `C2`)
- 45 experimental instances derived from `base_requirement + context_level`

## Structure

- `manifest.yaml`: corpus metadata and index
- `category-01-structural/`: REQ-01 to REQ-04
- `category-02-linguistic/`: REQ-05 to REQ-08
- `category-03-domain/`: REQ-09 to REQ-12
- `category-04-control/`: REQ-13 to REQ-15

## Context semantics

- `C0`: no additional contextual evidence
- `C1`: general context, non-resolutive for the main ambiguity
- `C2`: resolutive context with explicit disambiguation evidence when applicable

## Structuring note

- Concern separation and decomposition are treated as auxiliary operations inside final requirement structuring, not as independent pipeline stages.
- When the contextual resolubility outcome is `unresolved`, the execution bypasses Agent 3 and follows the alternative formatting/review route.
- `resolvable` means the next step can adopt the supported interpretation safely; `unresolved` means the ambiguity cannot be eliminated safely with the available evidence.

## Canonical language policy

- Requirement texts: English
- Context content: English
- Metadata keys and technical values: English
