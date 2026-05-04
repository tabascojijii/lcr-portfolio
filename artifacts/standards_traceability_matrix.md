# Standards Traceability Matrix

- Baseline: `docs/reference_standards.md`
- Updated: 2026-05-04
- Update timing rule: at M1 completion and before each phase transition gate.

| Standard Section | KPI | Evidence Artifact | Verification Method | Gate Timing |
| --- | --- | --- | --- | --- |
| Section 4 (UI Architecture) | UI->Domain direct references = 0 | `artifacts/architecture_decoupling_assessment.md` | Import graph scan + boundary review | M1 completion / before Phase C-D-E transitions |
| Section 4 (UI Architecture) | MainWindow business logic count = 0 | `artifacts/mainwindow_responsibility_diff.md` | Responsibility diff against migrated UseCases | M1 completion / before Phase C-D-E transitions |
| Section 4 (Signal/Slot naming) | Naming violations = 0 | `artifacts/signal_slot_naming_report.md` | AST static audit for `Signal` / `@Slot` | M1 completion / before Phase C-D-E transitions |
| Section 3 (Data Integrity) | Required audit metadata missing count = 0 | `tests/test_audit_metadata_reference_schema.py` | Schema-required field validation in test suite | Phase C gate |
| Section 3 (Data Integrity) | Relative path portability check pass = 100% | `tests/test_audit_metadata_use_case.py` | Relative path check in metadata use case tests | Phase C gate |
| Section 2 (Docker reproducibility) | Digest policy violations = 0 | `tests/test_dockerfile_digest_policy.py` | Dockerfile policy tests (digest pinning) | Phase D gate |
| Section 1 (Objective audit) | REJECT-triggering structural violations = 0 | `artifacts/architecture_decoupling_assessment.md` | EMCS-style violation listing and fixed thresholds | Every phase gate |

## Gate Decision Note

Any KPI above threshold or missing evidence artifact is treated as `REJECT_TO_PM` at phase transition.
