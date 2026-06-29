"""Tests for workspace value provisioning (add / get / delete roundtrip)."""

import uuid

import pytest
from petrovisor import PetroVisor
from petrovisor.api.enums.items import ItemType

from helpers import (
    ensure_workspace_value,
    cleanup_workspace_values,
)

_PFX = "WVTest"


@pytest.fixture(scope="session")
def wv_run_id():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def numeric_wv(api: PetroVisor, wv_run_id):
    name = f"{_PFX} Numeric {wv_run_id}"
    assert ensure_workspace_value(api, name, 42.0) is not None, (
        f"Failed to create {name}"
    )
    yield name
    cleanup_workspace_values(api, [name])


@pytest.fixture(scope="module")
def string_wv(api: PetroVisor, wv_run_id):
    name = f"{_PFX} String {wv_run_id}"
    assert ensure_workspace_value(api, name, "hello") is not None, (
        f"Failed to create {name}"
    )
    yield name
    cleanup_workspace_values(api, [name])


@pytest.fixture(scope="module")
def list_wv(api: PetroVisor, wv_run_id):
    name = f"{_PFX} List {wv_run_id}"
    assert ensure_workspace_value(api, name, ["a", "b", "c"]) is not None, (
        f"Failed to create {name}"
    )
    yield name
    cleanup_workspace_values(api, [name])


@pytest.fixture(scope="module")
def dict_wv(api: PetroVisor, wv_run_id):
    name = f"{_PFX} Dict {wv_run_id}"
    assert (
        ensure_workspace_value(api, name, {"key1": "val1", "key2": "val2"}) is not None
    ), f"Failed to create {name}"
    yield name
    cleanup_workspace_values(api, [name])


def _get_wv(api: PetroVisor, name: str, timeout: float = 30.0):
    """Poll get_workspace_value until it returns a non-None value or timeout."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = api.get_workspace_value(name, errors="raise")
            if result is not None:
                return result
        except Exception:
            pass
        time.sleep(1)
    return None


def test_numeric_workspace_value_roundtrip(api: PetroVisor, numeric_wv):
    result = _get_wv(api, numeric_wv)
    assert result is not None
    assert float(result) == pytest.approx(42.0)


def test_string_workspace_value_roundtrip(api: PetroVisor, string_wv):
    result = _get_wv(api, string_wv)
    assert result == "hello"


def test_list_workspace_value_roundtrip(api: PetroVisor, list_wv):
    result = _get_wv(api, list_wv)
    assert result is not None
    assert list(result) == ["a", "b", "c"]


def test_dict_workspace_value_roundtrip(api: PetroVisor, dict_wv):
    result = _get_wv(api, dict_wv)
    assert result is not None
    assert dict(result) == {"key1": "val1", "key2": "val2"}


def test_get_workspace_values_contains_created(api: PetroVisor, numeric_wv, string_wv):
    assert _get_wv(api, numeric_wv) is not None
    assert _get_wv(api, string_wv) is not None


def test_overwrite_workspace_value(api: PetroVisor, numeric_wv):
    result = ensure_workspace_value(api, numeric_wv, 99.0)
    assert result is not None
    assert float(result) == pytest.approx(99.0)


def test_delete_workspace_value(api: PetroVisor, wv_run_id):
    name = f"{_PFX} ToDelete {wv_run_id}"
    ensure_workspace_value(api, name, "temp")
    api.delete_workspace_value(name)
    assert not api.item_exists(
        ItemType.ConfigurationSettings, name, after="delete", max_retries=30
    )
