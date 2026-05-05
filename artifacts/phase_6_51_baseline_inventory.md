# Phase 6.51 Baseline Inventory

Date: 2026-05-05
Standard baseline: docs/reference_standards.md

## Scope
- Target root: `src/lcr`
- UI focus files:
  - `src/lcr/ui/main_window.py`
  - `src/lcr/ui/create_env_dialog.py`
  - `src/lcr/ui/dialog_adapters.py`
- UseCase focus files:
  - `src/lcr/core/container/use_cases.py`
  - `src/lcr/core/container/lifecycle_use_cases.py`
  - `src/lcr/core/architecture/use_cases.py`

## Baseline Findings
- UI->Domain direct reference count: 0
- Reverse dependency count (UseCase->UI, Domain->UI): 0
- Circular dependency count: 0
- Port/Interface bypass in fixed checkpoints (`_run_container`, `_show_create_env_dialog`): 0

## Gate Mapping
- Gate-1 (Structure): PASS baseline captured before Phase 6.51 edits.
- Gate-2 (Functional): deferred to test baseline artifact and `pytest tests/` execution.
