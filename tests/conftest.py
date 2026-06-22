import os

import petrovisor as pv
import pytest


@pytest.fixture(scope="session")
def api():
    return pv.PetroVisor(
        workspace=os.environ.get("TEST_WORKSPACE"),
        discovery_url=os.environ.get("TEST_URL"),
        key=os.environ.get("TEST_KEY"),
    )


# Re-export helpers so existing `from conftest import ...` calls keep working.
from helpers import (  # noqa: E402, F401
    _UNIT,
    _ALL_SIGNAL_TYPES,
    ensure_entities,
    ensure_signal,
    ensure_signals,
    wait_for_save_ready,
    wait_for_data,
    cleanup,
    ensure_workspace_value,
    cleanup_workspace_values,
    ensure_ref_table,
    wait_for_ref_table_data,
    cleanup_ref_tables,
)
