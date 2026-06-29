Run the dev test suite using the credentials in `.env`.

Usage examples to offer the user:
- All tests: `python scripts/run_tests.py`
- Single file: `python scripts/run_tests.py --file test_signals.py`
- Single test: `python scripts/run_tests.py --file test_signals.py --test <test_name>`
- With output: add `-s` flag

If `$ARGUMENTS` is provided, pass it directly:

```bash
python scripts/run_tests.py $ARGUMENTS
```

Otherwise run all tests:

```bash
python scripts/run_tests.py
```

If credentials are missing or expired, remind the user to check `.env` against `.env.example` and refer to AGENTS.md for key generation instructions.
