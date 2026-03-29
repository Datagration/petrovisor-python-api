Run ruff lint check and ty type check on the petrovisor package and report any issues.

```bash
uvx ruff check petrovisor/
uvx ty check
```

Report results. Baseline is 0 ruff errors and 3 known ty warnings (2 `no-matching-overload` on `pd.read_csv`, 1 `invalid-type-form` in `argument.py`). Flag anything beyond the baseline.
