# Data Integrity Field Matrix

| Field | Required | Format/Rule |
|---|---|---|
| container_image_digest | Yes | image repo digest (`@sha256:`) |
| git_commit_hash | Yes | 40-char lowercase hex |
| input_sha256 | Yes | map values are SHA-256 |
| output_sha256 | Yes | map values are SHA-256 |
| parameter_sha256 | Yes | SHA-256 |
| execution_log_sha256 | Yes | SHA-256 |
| path_mode | Yes | `relative_only` |
