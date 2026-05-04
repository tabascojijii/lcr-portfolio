# MainWindow Responsibility Diff

- Scope: `MainWindow._run_container`, `MainWindow._show_create_env_dialog`
- Baseline: `docs/reference_standards.md` Section 4 (Humble Object / dependency direction)
- Updated: 2026-05-04

## `MainWindow._run_container`

### Before Migration

- Runtime compatibility and mismatch judgement
- Environment creation requirement judgement and branch control
- Build/run orchestration decision and fallback handling

### After Migration

- Collect current UI input values
- Delegate run decision to `RuntimeExecutionPreparationUseCase`
- Delegate environment/build preparation to `EnvironmentBuildPreparationUseCase`
- Apply only UI feedback (dialogs, button states, start worker)

### Boundary Check

- Direct import from MainWindow to Domain/Infrastructure concrete implementation: 0
- UseCase boundary for "missing import -> candidate generation -> creation -> re-evaluation": single flow boundary

## `MainWindow._show_create_env_dialog`

### Before Migration

- Dialog invocation details and follow-up state handling were coupled with runtime lifecycle operations

### After Migration

- Dialog mediation delegated through `EnvironmentDialogPort`
- Environment preparation and runtime definition handling delegated to UseCase
- MainWindow keeps UI projection only (selection refresh and messages)

### Boundary Check

- Port/UseCase bypass for environment creation path: 0
- MainWindow-owned domain mutation logic: 0

## Conclusion

`MainWindow` responsibilities are constrained to input, delegation, and view update, satisfying Humble Object constraints for the two known regression methods.
