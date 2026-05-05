# Docker Digest Lock Evidence

- Evidence source: generated Dockerfiles under `src/lcr/core/container/images`.
- Policy: first `FROM` line must include `@sha256:<64-hex>`.
- Validation test: `tests/test_dockerfile_digest_policy.py`.
