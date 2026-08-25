## Summary

<!-- What user problem does this change solve? -->

## Scope

- [ ] Core ZIP behavior
- [ ] Inspection or security policy
- [ ] CLI
- [ ] Documentation
- [ ] Tests
- [ ] Packaging or CI

## Validation

<!-- List the commands you ran and their results. -->

```text
python -m pytest -q
python -m pytest -q --comprehensive
```

## Security and Compatibility

- Does this change affect path handling, extraction, ZIP metadata, CRC checks,
  resource limits, or unsupported methods?
- Does it change JSON fields, CLI exit codes, or a Python API?
- Are optional dependencies still optional?

## Documentation

- [ ] README or user guide updated when needed.
- [ ] Migration notes updated when a public contract changes.
- [ ] No unsupported performance, AI, or archive-manager claims were added.

## Checklist

- [ ] Tests cover the changed behavior.
- [ ] `git diff --check` passes.
- [ ] No private plans, local paths, secrets, caches, or generated artifacts
      are included.
- [ ] This pull request is focused and ready for review.
