# Phase 6.54 Container Side-Effect Porting Report

## Scope
- Target layer: `src/lcr/core/container`
- Objective: separate persistence, Docker runtime query, and file side effects from UI and UseCase orchestration.

## Boundary Result
- UI to Domain direct access: not introduced in this phase.
- Container side effects are treated as infrastructure operations and invoked through explicit boundaries.

## Side-Effect Classification
- Persistence side effects:
  - Environment definition read/write (`src/lcr/core/container/definitions/*.json`)
- Runtime side effects:
  - Docker build/run/image lifecycle operations (`src/lcr/core/container/manager.py`, `worker.py`)
- File generation side effects:
  - Dockerfile generation (`src/lcr/core/container/generator.py`, `templates/base.Dockerfile.j2`)

## Porting Policy
- Rule 1: UI layer must not execute direct Docker/file operations.
- Rule 2: UseCase layer orchestrates only intent and delegates operational steps to dedicated runtime/repository boundaries.
- Rule 3: Side-effect failures are returned as typed outcomes and evaluated by caller policy.

## Evidence Checklist
- `tests/test_environment_lifecycle_use_case.py`
- `tests/test_runtime_guard_use_case.py`
- `tests/test_phase61_decoupling_use_case.py`

## Gate Mapping
- Gate-S focus: no Port bypass, no reverse dependency, no UI business logic reinjection.
- Gate-F focus: runtime and lifecycle tests pass under `pytest tests/`.
