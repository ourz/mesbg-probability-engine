## External Probability Engine

```text
Repository: <PUBLIC_GITHUB_REPOSITORY>
Release: v0.1.0
Commit: <FULL_COMMIT_SHA>
Release archive SHA256: <SHA256>
Input schema: combat-input-v1
Output schema: combat-output-v1
Entrypoint: python -m mesbg_probability solve
Minimum Python: 3.11
Execution policy: download immutable release archive, verify SHA-256, run tests, then execute locally
```

Runtime workflow:

1. Complete FAQ/errata-first verification and decisive-input lock.
2. Retrieve the pinned release archive, never moving `main` files.
3. Verify commit and archive SHA-256.
4. Run `python -m unittest discover -s tests -v`.
5. Generate a `combat-input-v1` document with evidence references and assumptions.
6. Execute the solver.
7. Report engine version, input hash, locked inputs and separate outcome classes.
8. If any decisive input changes, discard all dependent outputs and rerun.
