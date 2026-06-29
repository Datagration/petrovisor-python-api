"""Tests for reference table provisioning (add / load / delete roundtrip)."""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from petrovisor import PetroVisor

from helpers import (
    ensure_ref_table,
    wait_for_ref_table_data,
    cleanup_ref_tables,
)

_PFX = "RTTest"
_ENTITY = f"{_PFX} Well 001"
_TABLE = f"{_PFX} Table"
_NUM_ROWS = 10


def _make_df(entity: str, num_rows: int = _NUM_ROWS) -> pd.DataFrame:
    start = datetime(2025, 1, 1)
    df = pd.DataFrame(
        {
            "Entity": [None] * num_rows,  # None avoids entity-registry sync delays
            "Time": [start + timedelta(hours=i) for i in range(num_rows)],
            "Key": list(range(num_rows)),
            "Value": np.random.uniform(0, 1, num_rows),
        }
    )
    return df


@pytest.fixture(scope="module")
def ref_table_data():
    """Module-scoped: create once, shared by all tests, teardown at end."""
    api = PetroVisor(
        workspace=os.environ.get("TEST_WORKSPACE"),
        discovery_url=os.environ.get("TEST_URL"),
        key=os.environ.get("TEST_KEY"),
    )

    df = _make_df(_ENTITY)
    ensure_ref_table(api, _TABLE, df)
    loaded = wait_for_ref_table_data(
        api, _TABLE, min_rows=_NUM_ROWS, retries=30, delay=3.0
    )
    if loaded is None:
        pytest.skip("Timed out waiting for ref table data to propagate")

    yield {
        "api": api,
        "table_name": _TABLE,
        "entity_name": _ENTITY,
        "num_rows": _NUM_ROWS,
    }

    try:
        api.delete_ref_table_data(_TABLE)
    except Exception:
        pass
    cleanup_ref_tables(api, [_TABLE])


def test_ref_table_schema_created(ref_table_data):
    api = ref_table_data["api"]
    info = api.get_ref_table_data_info(ref_table_data["table_name"])
    assert info is not None
    assert info["Key"]["Name"] == "Key"


def test_ref_table_data_roundtrip(ref_table_data):
    api = ref_table_data["api"]
    df = api.load_ref_table_data(ref_table_data["table_name"])
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 1


def test_ref_table_filter_by_entity(ref_table_data):
    api = ref_table_data["api"]
    # Rows have null Entity — filter for null entity rows using where expression
    df = api.load_ref_table_data(
        ref_table_data["table_name"],
        where="[Entity] IS NULL",
    )
    assert df is not None
    assert len(df) > 0


def test_ref_table_filter_top(ref_table_data):
    api = ref_table_data["api"]
    df = api.load_ref_table_data(ref_table_data["table_name"], top=3)
    assert df is not None
    assert len(df) <= 3


def test_ref_table_filter_date_range(ref_table_data):
    api = ref_table_data["api"]
    df = api.load_ref_table_data(
        ref_table_data["table_name"],
        date_start=datetime(2025, 1, 1),
        date_end=datetime(2025, 1, 1, 5),
    )
    assert df is not None
    assert isinstance(df, pd.DataFrame)


def test_ref_table_save_overwrites(ref_table_data):
    api = ref_table_data["api"]
    df = _make_df(ref_table_data["entity_name"])
    api.save_ref_table_data(ref_table_data["table_name"], df, skip_existing_data=False)
    loaded = wait_for_ref_table_data(api, ref_table_data["table_name"], min_rows=1)
    assert loaded is not None
    assert len(loaded) >= 1


def test_ref_table_save_skip_existing(ref_table_data):
    api = ref_table_data["api"]
    df = _make_df(ref_table_data["entity_name"])
    api.save_ref_table_data(ref_table_data["table_name"], df, skip_existing_data=True)
    loaded = wait_for_ref_table_data(api, ref_table_data["table_name"], min_rows=1)
    assert loaded is not None
    assert len(loaded) >= 1


def test_ref_table_delete_data_where_clause(ref_table_data):
    import time

    api = ref_table_data["api"]
    table_name = ref_table_data["table_name"]

    # Use keys well above the fixture's 0.._NUM_ROWS-1 to avoid collisions.
    base_key = 1000
    num = _NUM_ROWS
    start = datetime(2025, 6, 1)
    df_extra = pd.DataFrame(
        {
            "Entity": [None] * num,
            "Time": [start + timedelta(hours=i) for i in range(num)],
            "Key": list(range(base_key, base_key + num)),
            "Value": np.zeros(num),
        }
    )
    api.save_ref_table_data(table_name, df_extra, skip_existing_data=False)

    # Poll until OUR specific rows (key >= base_key) are visible — don't rely on
    # total row count since the fixture's rows may already satisfy min_rows.
    key_col = None
    for _ in range(30):
        df = api.load_ref_table_data(table_name)
        if df is not None and len(df) > 0:
            key_col = next(
                (c for c in df.columns if c == "Key" or c.startswith("Key ")), None
            )
            if key_col and (df[key_col] >= base_key).sum() >= num:
                break
        time.sleep(2)
    else:
        pytest.fail("Timed out waiting for seeded rows (key >= 1000) to propagate")

    # Delete only the lower half of our range: keys 1000..1004
    split = base_key + num // 2
    api.delete_ref_table_data(
        table_name, where=f"[Key] >= {base_key} AND [Key] < {split}"
    )

    # Poll until the deleted rows are gone
    remaining = None
    for _ in range(30):
        remaining = api.load_ref_table_data(table_name)
        if remaining is not None and len(remaining) > 0:
            kc = next(
                (c for c in remaining.columns if c == "Key" or c.startswith("Key ")),
                None,
            )
            if (
                kc
                and ((remaining[kc] >= base_key) & (remaining[kc] < split)).sum() == 0
            ):
                break
        elif remaining is None or len(remaining) == 0:
            break
        time.sleep(2)

    assert remaining is not None and len(remaining) > 0, (
        "All rows gone after partial delete"
    )
    kc = next(
        (c for c in remaining.columns if c == "Key" or c.startswith("Key ")), None
    )
    assert kc is not None, f"Key column not found in {list(remaining.columns)}"
    deleted_count = ((remaining[kc] >= base_key) & (remaining[kc] < split)).sum()
    kept_count = ((remaining[kc] >= split) & (remaining[kc] < base_key + num)).sum()
    assert deleted_count == 0, (
        f"Keys {base_key}..{split - 1} should be deleted, {deleted_count} still present"
    )
    assert kept_count > 0, (
        f"Keys {split}..{base_key + num - 1} should remain, none found"
    )


def test_ref_table_delete_data(ref_table_data):
    import time

    api = ref_table_data["api"]
    # Delete all data (not just null-entity rows — other tests may have added non-null rows)
    api.delete_ref_table_data(ref_table_data["table_name"])
    # Poll until delete propagates
    for _ in range(20):
        df = api.load_ref_table_data(ref_table_data["table_name"])
        if df is None or len(df) == 0:
            break
        time.sleep(2)
    assert df is None or len(df) == 0


def test_ref_table_names_contains_created(ref_table_data):
    from petrovisor import ItemType

    api = ref_table_data["api"]
    table_name = ref_table_data["table_name"]
    assert api.item_exists(
        ItemType.RefTable, table_name, after="create", max_retries=30, retry_delay=2.0
    )
