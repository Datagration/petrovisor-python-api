"""
Development test runner script.
Loads credentials from .env in the project root (see .env.example).

Usage (from project root):
    python scripts/run_tests.py                                              # fast then slow
    python scripts/run_tests.py --file test_signals.py                       # one file
    python scripts/run_tests.py --file test_signals.py --test test_load_data # one test
    python scripts/run_tests.py --all                                        # all tests in one pass
    python scripts/run_tests.py -s                                           # with stdout
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
import subprocess
from pathlib import Path

import pytest

# Load credentials from .env at project root
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: uv pip install python-dotenv")
    print("Falling back to existing environment variables.\n")


def _check_credentials():
    workspace = os.environ.get("TEST_WORKSPACE", "")
    url = os.environ.get("TEST_URL", "")
    key = os.environ.get("TEST_KEY", "")
    if not workspace or not url or not key:
        print("ERROR: Missing credentials. Copy .env.example to .env and fill in your values.")
        print("See AGENTS.md for instructions on generating TEST_KEY.")
        sys.exit(1)
    return workspace, url


def _print_header(label: str, workspace: str, url: str):
    print("=" * 70)
    print(f"Running {label} with Development workspace credentials")
    print("=" * 70)
    print(f"Workspace: {workspace}")
    print(f"URL:       {url}")
    print("=" * 70)
    print()


def _run_suite(test_paths: list, pytest_flags: list) -> int:
    project_root = Path(__file__).parent.parent
    paths = [str(project_root / t) if not t.startswith("/") else t for t in test_paths]
    return pytest.main(paths + pytest_flags)


def main():
    workspace, url = _check_credentials()

    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"

    args = sys.argv[1:]
    pytest_flags = [arg for arg in args if arg.startswith("-") and arg not in ["--test", "--file", "--all"]]
    if not pytest_flags:
        pytest_flags = ["-v"]

    # Single-file or single-test mode — just run it directly
    if "--file" in args or "--all" in args:
        if "--all" in args:
            test_path = str(tests_dir)
        elif "--file" in args and "--test" in args:
            file_name = args[args.index("--file") + 1]
            test_name = args[args.index("--test") + 1]
            test_path = f"{tests_dir / file_name}::{test_name}"
        else:
            file_name = args[args.index("--file") + 1]
            test_path = str(tests_dir / file_name)

        _print_header("tests", workspace, url)
        sys.exit(pytest.main([test_path] + pytest_flags))

    # Default: run fast suite first, then slow suite, print summary of both
    _print_header("fast tests", workspace, url)

    fast_script = project_root / "scripts" / "run_fast_tests.py"
    slow_script = project_root / "scripts" / "run_slow_tests.py"

    python = sys.executable
    flag_args = pytest_flags  # pass through -s / -v etc.

    fast_result = subprocess.run(
        [python, str(fast_script)] + flag_args,
        env=os.environ,
    )

    print()
    print("=" * 70)
    print("Fast tests done. Starting slow tests...")
    print("=" * 70)
    print()

    slow_result = subprocess.run(
        [python, str(slow_script)] + flag_args,
        env=os.environ,
    )

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Fast tests : {'PASSED' if fast_result.returncode == 0 else 'FAILED'}")
    print(f"  Slow tests : {'PASSED' if slow_result.returncode == 0 else 'FAILED'}")
    print("=" * 70)

    sys.exit(0 if fast_result.returncode == 0 and slow_result.returncode == 0 else 1)


if __name__ == "__main__":
    main()
