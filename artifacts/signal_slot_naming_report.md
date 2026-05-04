# Signal/Slot Naming Report

- Standard reference: `docs/reference_standards.md` Section 4
- Scope: `src/lcr/ui/**/*.py`
- Scan date: 2026-05-04
- Method: static AST scan (`Signal(...)` assignments and `@Slot` methods)

## Rule Set

- Signal names must be past-participle style (e.g. `build_finished`, `executionFinished`).
- Slot names must start with an action verb (e.g. `run_*`, `update_*`, `on_*`).

## Measurement

- Files scanned: `7`
- Signals scanned: `5`
- Slots scanned: `17`
- Naming violations: `0`

## Violations

No violations detected.

## Gate Result

`PASS` (Signal/Slot naming violations = 0)
