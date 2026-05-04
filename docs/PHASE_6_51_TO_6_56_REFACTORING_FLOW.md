# Refactoring Roadmap (Phase 6.51-6.56)

## 1. Purpose

This document defines the post-6.4 incremental refactoring flow to reduce AI-agent confusion and keep each step auditable, reversible, and testable.

Scope:
- Phase 6.51 through 6.56
- Focus areas: responsibility decongestion and side-effect isolation

Out of scope:
- Large-scale feature additions
- Simultaneous multi-layer rewrites

## 2. Execution Policy

- Execute phases strictly in order: 6.51 -> 6.52 -> 6.53 -> 6.54 -> 6.55 -> 6.56.
- Do not begin the next phase until the current phase acceptance criteria are fully met.
- Keep each phase independently reviewable with explicit evidence artifacts.
- If a phase fails audit, fix only that phase scope before moving forward.

## 3. Phase Breakdown

### Phase 6.51: Baseline Visualization and Freeze

Objective:
- Fix the pre-change baseline so later regressions can be measured objectively.

Work items:
- Create responsibility maps for key modules (UI / UseCase / Core / Infra boundaries).
- Enumerate side-effect points (`print`, file I/O, network I/O, subprocess) in target modules.
- Snapshot current test status and key quality gates.

Acceptance criteria:
- Responsibility map and side-effect inventory are documented.
- Baseline test results are archived.
- Refactoring target/non-target boundaries are explicitly fixed.

### Phase 6.52: Logging Standardization (`print` Elimination)

Objective:
- Improve observability and make behavior auditable.

Work items:
- Replace `print` calls in core modules with structured logging.
- Normalize log level usage (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Preserve existing runtime behavior while changing only observability mechanism.

Acceptance criteria:
- `print(` count in core target scope is zero.
- Logs include stable context keys for tracing.
- Existing tests pass without behavior regression.

### Phase 6.53: Side-Effect Porting (Analyzer Boundary)

Objective:
- Separate analysis logic from direct external dependencies.

Work items:
- Isolate PyPI/network access behind a port/gateway.
- Isolate mapping load path behind repository abstraction.
- Keep `CodeAnalyzer` focused on transformation/judgment logic.

Acceptance criteria:
- Analyzer no longer directly performs network I/O.
- Analyzer no longer directly owns mapping file load concerns.
- Unit tests cover analyzer logic with mocked ports.

### Phase 6.54: Side-Effect Porting (Container Boundary)

Objective:
- Remove direct persistence and environment-probing side effects from orchestration-heavy code.

Work items:
- Move definition/user knowledge persistence into repository components.
- Move docker environment probing into gateway components.
- Reduce direct file manipulation in high-level manager pathways.

Acceptance criteria:
- Container orchestration path depends on explicit ports for side effects.
- Direct I/O in high-level container coordination is reduced to agreed minimum.
- Regression tests pass for run/build preparation workflows.

### Phase 6.55: Responsibility Split (ContainerManager Decomposition)

Objective:
- Resolve god-class pressure in container management.

Work items:
- Split `ContainerManager` responsibilities into dedicated components (e.g., resolver/factory/repository roles).
- Keep a thin facade only where integration convenience is required.
- Re-locate logic-level tests to new component units.

Acceptance criteria:
- Core decision logic is no longer concentrated in a single large class.
- New components have clear single responsibilities.
- Existing external behavior/API contracts remain compatible or are migrated safely.

### Phase 6.56: UI Flow Unification (MainWindow Slimming)

Objective:
- Restrict UI layer to input collection, display updates, and use case invocation.

Work items:
- Unify UI state transition handling through one state API.
- Unify worker start paths to a single flow.
- Move residual non-UI side effects (e.g., save/prep actions) out of UI where applicable.

Acceptance criteria:
- MainWindow no longer contains duplicated execution/start state logic.
- UI methods are limited to presentation concerns.
- End-to-end run/build UX remains stable under regression tests.

## 4. Suggested Evidence Artifacts

- `artifacts/phase_6_51_baseline_inventory.md`
- `artifacts/phase_6_52_logging_migration_report.md`
- `artifacts/phase_6_53_analyzer_porting_report.md`
- `artifacts/phase_6_54_container_porting_report.md`
- `artifacts/phase_6_55_container_decomposition_report.md`
- `artifacts/phase_6_56_ui_flow_unification_report.md`

## 5. Audit Gate Template (Per Phase)

For each phase, verify all of the following:
- Scope compliance: no out-of-scope changes.
- Acceptance criteria: all criteria satisfied with evidence.
- Regression status: required tests/quality gates pass.
- Rollback clarity: changes are reversible at phase boundary.

## 6. Handoff Rule

Only after a phase is marked complete by audit should the next phase begin.

This preserves determinism and prevents cross-phase confusion in AI-assisted execution.
