"""
Development test runner script.
Loads credentials from .env in the project root (see .env.example).

Usage (from project root):
    python scripts/run_tests.py
    python scripts/run_tests.py --file test_signals.py
    python scripts/run_tests.py --file test_signals.py --test test_load_data_time_numeric
    python scripts/run_tests.py --all
    python scripts/run_tests.py -s            # disable output capture
    python scripts/run_tests.py -v --file test_signals.py

Getting TEST_KEY (run once, paste result into .env):
    import petrovisor as pv
    api = pv.PetroVisor(
        workspace="Your Workspace",
        discovery_url="https://identity.us1.petrovisor.com",
        username="your@email.com",
        password="yourpassword",
    )
    print(api.Key)
"""

import os
import sys
from pathlib import Path

import pytest

# Load credentials from .env at project root
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: uv pip install python-dotenv")
    print("Falling back to existing environment variables.\n")


def main():
    workspace = os.environ.get("TEST_WORKSPACE", "")
    url = os.environ.get("TEST_URL", "")
    key = os.environ.get("TEST_KEY", "")

    if not workspace or not url or not key:
        print("ERROR: Missing credentials. Copy .env.example to .env and fill in your values.")
        print("See AGENTS.md for instructions on generating TEST_KEY.")
        sys.exit(1)

    print("=" * 70)
    print("Running tests with Development workspace credentials")
    print("=" * 70)
    print(f"Workspace: {workspace}")
    print(f"URL:       {url}")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"

    args = sys.argv[1:]

    # Collect explicit pytest flags (-v, -s, -x, etc.)
    pytest_flags = [arg for arg in args if arg.startswith("-") and arg not in ["--test", "--file", "--all"]]
    if not pytest_flags:
        pytest_flags = ["-v"]

    if "--all" in args:
        test_path = str(tests_dir)
    elif "--file" in args and "--test" in args:
        file_name = args[args.index("--file") + 1]
        test_name = args[args.index("--test") + 1]
        test_path = f"{tests_dir / file_name}::{test_name}"
    elif "--file" in args:
        file_name = args[args.index("--file") + 1]
        test_path = str(tests_dir / file_name)
    elif "--test" in args:
        print("ERROR: --test requires --file to be specified")
        print("Usage: python scripts/run_tests.py --file <filename> --test <testname>")
        sys.exit(1)
    else:
        test_path = str(tests_dir)

    sys.exit(pytest.main([test_path] + pytest_flags))


if __name__ == "__main__":
    main()
