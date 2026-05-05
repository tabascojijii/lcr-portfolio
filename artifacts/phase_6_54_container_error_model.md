# Phase 6.54 Container Error Model

## Error Taxonomy

| Code | Category | Recoverability | Trigger Example | Required Caller Action |
|---|---|---|---|---|
| `CNR-001` | RuntimeUnavailable | recoverable | Docker daemon not reachable | show actionable warning and allow retry |
| `CNR-002` | ImageBuildFailed | recoverable | build command non-zero exit | preserve log evidence and present rebuild option |
| `CNR-003` | ContainerRunFailed | recoverable | runtime execution failure | keep parameters and allow controlled rerun |
| `CNR-004` | DefinitionReadFailed | non-recoverable | malformed/missing definition file | stop flow and request definition remediation |
| `CNR-005` | DefinitionWriteFailed | non-recoverable | permission or serialization failure | abort mutation and keep prior state |

## Propagation Rules
- UseCase must receive typed failure information, not raw UI-side exception handling.
- Recoverable failures (`CNR-001`..`CNR-003`) must preserve execution evidence and allow deterministic retry.
- Non-recoverable failures (`CNR-004`..`CNR-005`) must stop execution immediately and require corrective action before re-run.

## Logging and Audit Alignment
- Failure records include relative path references only.
- Runtime failure logs must include stable identifiers required by Data Integrity policy.
- Warning/Error level logging is mandatory on fallback and exception paths.

## Verification Targets
- `tests/test_environment_lifecycle_use_case.py`
- `tests/test_runtime_selection.py`
- `tests/test_data_integrity_audit_use_case.py`
