# PetroVisor Python API — Agent Guide

Python wrapper for the PetroVisor REST API. Package name: `petrovisor`, current version in `petrovisor/__init__.py`.

## Project Structure

```
petrovisor/          # Main package (do not modify without understanding the mixin chain)
  petrovisor.py      # PetroVisor class — composes all mixins
  api/
    base.py          # Auth, request helpers, encoding
    methods/         # One file per feature area (signals, contexts, dataframes, …)
    models/          # Pydantic v2 models (Context, Scope, Entity, Signal, …)
    enums/           # Typed enums (SignalType, TimeIncrement, …)
    protocols/       # Structural typing protocols for mixin composition
    utils/           # Validators, helpers, request utilities
  models/            # Top-level models (Argument, ContextsManager)
tests/               # pytest suite — requires live API credentials via .env
scripts/             # Utility scripts: doc generation, run_tests.py
sandbox/             # Local-only scratch files (git-ignored)
examples/            # Jupyter notebooks showing usage patterns
```

## Package Manager

Use **uv** exclusively. Do not use pip directly.

```bash
uv sync                          # install/sync dependencies
uv pip install -e .              # editable install
uv run pytest tests/             # run tests
uvx ruff format petrovisor/      # format code
uvx ruff check petrovisor/       # lint
uvx ty check                     # type-check (Astral ty, ~34 warnings baseline — all warnings, 0 errors)
```

## Code Quality — Run Before Committing

```bash
uvx ruff format petrovisor/      # auto-format (Black-compatible)
uvx ruff check petrovisor/       # F + E rules, fix with --fix
uvx ty check                     # type checker; 3 warnings are known stubs issues, rest should stay 0 errors
```

## Key Architectural Patterns

- **Mixin chain**: `PetroVisor` inherits from all method mixins. Each mixin declares its dependencies via Protocols in `api/protocols/protocols.py`.
- **Pydantic v2 models**: All models use `BaseConfigModel` with `populate_by_name=True`. Use **aliases** (PascalCase) in constructors: `Context(Name="foo")` not `Context(name="foo")` — ty will warn otherwise.
- **API requests**: All HTTP calls go through `self.get/post/put/delete` from `base.py`. Route strings are plain paths e.g. `"Signals/{name}"`.
- **Dict annotations**: Request body dicts must be annotated as `Dict[str, Any]` to avoid ty narrowing false positives.

## Running Tests

Tests hit a live PetroVisor workspace. Credentials are loaded from `.env` (see `.env.example`):

```bash
cp .env.example .env            # first time setup — fill in your values
python scripts/run_tests.py                          # run all tests
python scripts/run_tests.py --file test_signals.py  # single file
python scripts/run_tests.py --file test_signals.py --test test_load_data_time_numeric
```

`conftest.py` reads `TEST_WORKSPACE`, `TEST_URL`, `TEST_KEY` from environment.

## Getting an API Key

Authenticate once with username/password, then extract the session key for `.env`:

```python
import petrovisor as pv

api = pv.PetroVisor(
    workspace="Your Workspace",
    discovery_url="https://identity.us1.petrovisor.com",  # or eu1
    username="your@email.com",
    password="yourpassword",
)
key = api.Key   # copy this into TEST_KEY in .env
```

Keys expire — regenerate when tests start failing with auth errors.

## Signal Types

`SignalType` enum: `Static`, `String`, `TimeDependent`, `StringTimeDependent`, `DepthDependent`, `StringDepthDependent`, `PVT`.

## Common Gotchas

- `Optional[str]` params passed to functions expecting `str` — use `value or "default"` pattern.
- Set invariance: `Set[TimeIncrement]` is not `Set[str | TimeIncrement]` — annotate as the wider union.
- `_get_column_data` in `dataframes.py` accepts `Optional[int]` — returns `[]` on `None`.
- Pydantic `model_validate` is preferred over direct constructor when building from dicts with alias keys.
