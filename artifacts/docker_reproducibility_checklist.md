# Docker Reproducibility Checklist

- [ ] All `FROM` lines use immutable digest pinning.
- [ ] EOL apt sources redirect to archive hosts.
- [ ] Dependency resolution is constrained with `constraints.txt` where required.
- [ ] Multi-stage build is used when compiling C/C++ dependencies.
