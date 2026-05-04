# Known Regression Checklist (`_run_container`, `_show_create_env_dialog`)

- Baseline: `docs/reference_standards.md`
- Updated: 2026-05-04
- Purpose: Prevent recurrence on two previously sensitive methods.

## Checklist: `MainWindow._run_container`

- [x] Direct import to Domain/Infrastructure concrete classes does not exist.
- [x] Capability judgement and mismatch guard are handled in UseCase layer.
- [x] Environment creation decision path is not hard-coded in MainWindow.
- [x] MainWindow logic is limited to input collection and UI presentation update.
- [x] Regression tests for run decision and button states are passing.

## Checklist: `MainWindow._show_create_env_dialog`

- [x] Environment creation logic is reached only through Port/UseCase flow.
- [x] Dialog adapter mediates UI-specific behavior.
- [x] Runtime definition reload/selection reflects UseCase output.
- [x] No concrete Domain/Infrastructure dependency is introduced in MainWindow.
- [x] Regression tests for dialog reason display and flow remain passing.

## Audit Result

- Violations: 0
- Gate status: PASS
