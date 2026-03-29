# Claude Code — Project Instructions

@AGENTS.md

## Claude-Specific Guidance

### Before Starting Any Task
- Run `uvx ty check` and `uvx ruff check petrovisor/` to establish baseline before making changes.
- Read the relevant source file(s) before suggesting modifications.
- Check @petrovisor/__init__.py for the public API surface when adding or renaming exports.

### Code Style
- Pydantic constructors: always use PascalCase aliases (`Name=`, `Start=`, etc.), not field names — `ty` warns on field-name usage due to `populate_by_name=True`. See @petrovisor/api/models/base_model.py.
- Request body dicts: annotate as `Dict[str, Any]` at declaration to prevent ty narrowing false positives.
- No speculative abstractions. No docstrings on unchanged functions. No unnecessary error handling.

### Type Checking
`uvx ty check` baseline: **3 warnings** (2 `no-matching-overload` on `pd.read_csv`, 1 `invalid-type-form` in `argument.py`). These are known false positives — see @petrovisor/models/argument.py and @petrovisor/api/methods/dataframes.py. Any new errors or warnings beyond the baseline should be fixed before committing.

### Running Tests
Tests require a live API connection. Set up credentials once:

```bash
cp .env.example .env   # then fill in values — see .env.example for key generation instructions
```

Run tests via @scripts/run_tests.py:

```bash
python scripts/run_tests.py                                              # all tests
python scripts/run_tests.py --file test_signals.py                       # one file
python scripts/run_tests.py --file test_signals.py --test <test_name>    # one test
python scripts/run_tests.py -s                                           # with stdout (no capture)
```

Credentials are injected via @tests/conftest.py which reads `TEST_WORKSPACE`, `TEST_URL`, `TEST_KEY` from the environment. Never hardcode credentials. If tests fail with auth errors, `TEST_KEY` in `.env` has expired — see AGENTS.md for how to regenerate.

### Git
- Never commit `.env` — it is git-ignored.
- `scripts/run_tests.py` is tracked in git. `sandbox/` is fully git-ignored (local scratch only).
- Branch convention: `refactor/<user>/<ticket>-<description>`.

### Refactoring Context
The codebase recently completed a full migration from specialized endpoints (`Data/Time/`, `Data/Depth/`) to unified `Data/Retrieve`, `Data/Save`, `Data/Top` endpoints. See @.claude/ENDPOINT_REFACTORING_PLAN.md for full history. Do not reintroduce the old endpoint patterns.
