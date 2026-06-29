"""Shared provisioning helpers for integration tests.

All functions follow the same pattern:
  - ensure_*   : create the resource if absent, poll until it's readable
  - wait_for_* : poll a load function until data is visible
  - cleanup_*  : delete resources, ignoring errors

Import in test files with:
    from helpers import ensure_entities, cleanup, ...
"""

import time
from typing import Any, Callable, List, Optional

import pandas as pd
import petrovisor as pv

_UNIT = " "

_ALL_SIGNAL_TYPES = [
    ("Static Num", pv.SignalType.Static),
    ("Static Str", pv.SignalType.String),
    ("Time Num", pv.SignalType.TimeDependent),
    ("Time Str", pv.SignalType.StringTimeDependent),
    ("Depth Num", pv.SignalType.DepthDependent),
    ("Depth Str", pv.SignalType.StringDepthDependent),
]


# ── entity helpers ──────────────────────────────────────────────────


def ensure_entities(
    api: pv.PetroVisor, names: List[str], entity_type: str = "Well"
) -> None:
    """Create entities if missing, poll until all are visible.

    Uses a single batch get_entity_names() call per polling iteration instead of
    N individual item_exists() calls to minimise API round-trips.
    """
    existing = set(api.get_entity_names() or [])
    for name in names:
        if name not in existing:
            try:
                api.add_entity(pv.Entity(name=name, type=entity_type))
            except Exception:
                pass
    for _ in range(30):
        existing = set(api.get_entity_names() or [])
        if all(n in existing for n in names):
            break
        time.sleep(1)


# ── signal helpers ──────────────────────────────────────────────────


def ensure_signals(api: pv.PetroVisor, prefix: str) -> List[str]:
    """Create all standard signal types for a prefix if missing, poll until visible.

    Uses a single batch get_signal_names() call per polling iteration.
    /PetroVisorItem and individual GET both cost ~11 s on a miss, making the
    list endpoint the only safe poller.
    """
    names = [f"{prefix} {label}" for label, _ in _ALL_SIGNAL_TYPES]
    existing = set(api.get_signal_names() or [])
    for label, stype in _ALL_SIGNAL_TYPES:
        name = f"{prefix} {label}"
        if name not in existing:
            try:
                api.add_signal(
                    pv.Signal(
                        type=stype.name,
                        name=name,
                        unit=_UNIT,
                        unit_measurement="Dimensionless",
                    )
                )
            except Exception:
                pass
    for _ in range(30):
        existing = set(api.get_signal_names() or [])
        if all(n in existing for n in names):
            break
        time.sleep(1)
    return names


def ensure_signal(
    api: pv.PetroVisor,
    name: str,
    signal_type: pv.SignalType,
    unit: str = " ",
) -> None:
    """Create a single signal if missing, poll until visible via list endpoint."""
    existing = set(api.get_signal_names() or [])
    if name not in existing:
        try:
            api.add_signal(
                pv.Signal(
                    type=signal_type.name,
                    name=name,
                    unit=unit,
                    unit_measurement="Dimensionless",
                )
            )
        except Exception:
            pass
    for _ in range(30):
        existing = set(api.get_signal_names() or [])
        if name in existing:
            break
        time.sleep(1)


def wait_for_save_ready(
    api: pv.PetroVisor,
    entity: str,
    signal: str,
    data_type: str = "static",
    timeout: float = 120.0,
    delay: float = 2.0,
    # legacy positional args — ignored, kept for call-site compatibility
    retries: Optional[int] = None,
) -> Optional[Any]:
    """Probe Data/Save until entity+signal are accepted by the data layer.

    Uses a wall-clock timeout so slow HTTP round-trips don't exhaust a fixed
    retry count.  Probe dates/depths are chosen outside all real test ranges
    so probe records never contaminate load-verification assertions.

    Returns the successful save result, or None if timeout expires.
    """
    # Probe values chosen outside all test data ranges:
    #   time:  year 2000 (tests use 2024)
    #   depth: -1.0 m   (tests use 1000+ m)
    if data_type == "time":
        payload = [
            {
                "Entity": entity,
                "Signal": signal,
                "Unit": _UNIT,
                "Data": [{"Date": "2000-01-01T00:00:00", "Value": 0.0}],
            }
        ]
    elif data_type == "timestring":
        payload = [
            {
                "Entity": entity,
                "Signal": signal,
                "Unit": _UNIT,
                "Data": [{"Date": "2000-01-01T00:00:00", "Value": "probe"}],
            }
        ]
    elif data_type == "depth":
        payload = [
            {
                "Entity": entity,
                "Signal": signal,
                "Unit": _UNIT,
                "Data": [{"Depth": -1.0, "Value": 0.0}],
            }
        ]
    elif data_type == "stringdepth":
        payload = [
            {
                "Entity": entity,
                "Signal": signal,
                "Unit": _UNIT,
                "Data": [{"Depth": -1.0, "Value": "probe"}],
            }
        ]
    elif data_type == "string":
        payload = [{"Entity": entity, "Signal": signal, "Unit": _UNIT, "Data": "probe"}]
    else:
        payload = [{"Entity": entity, "Signal": signal, "Unit": _UNIT, "Data": 0.0}]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # errors="raise" means any HTTP error raises immediately (no internal retry).
        # A successful save returns None (204 No Content) — that is a success here.
        # Only exceptions indicate a failed probe.
        try:
            api.save_data(
                data_type=data_type, with_logs=False, data=payload, errors="raise"
            )
            return True
        except Exception:
            pass
        time.sleep(delay)
    return None


def wait_for_data(
    api: pv.PetroVisor,
    load_fn: Callable,
    min_rows: int = 1,
    retries: int = 60,
    delay: float = 2.0,
    predicate: Optional[Callable] = None,
) -> Optional[Any]:
    """Poll load_fn() until it returns a non-empty result with at least min_rows.

    If *predicate* is given, also require predicate(result) to be True.
    """
    for _ in range(retries):
        try:
            result = load_fn()
            if result is not None and len(result) >= min_rows:
                if predicate is None or predicate(result):
                    return result
        except Exception:
            pass
        time.sleep(delay)
    return None


def cleanup(
    api: pv.PetroVisor, entity_names: List[str], signal_names: List[str]
) -> None:
    """Delete signals then entities concurrently, ignoring errors."""
    import concurrent.futures

    def _del_signal(n):
        try:
            api.delete_signal(n)
        except Exception:
            pass

    def _del_entity(n):
        try:
            api.delete_entity(n)
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        sig_futs = [pool.submit(_del_signal, n) for n in signal_names]
        for f in concurrent.futures.as_completed(sig_futs):
            f.result()

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ent_futs = [pool.submit(_del_entity, n) for n in entity_names]
        for f in concurrent.futures.as_completed(ent_futs):
            f.result()


# ── workspace value helpers ──────────────────────────────────────────────────


def ensure_workspace_value(
    api: pv.PetroVisor,
    name: str,
    value: Any,
    unit: str = "",
    retries: int = 30,
    delay: float = 1.0,
) -> Any:
    """Write a workspace value and wait until it is confirmed readable.

    Strategy:
    1. Write via add_workspace_value.
    2. Poll the names list (cheap, fast) until the name appears.
    3. Once visible in the list, poll GET until it returns a value.
    Returns the confirmed value, or None if timeout expires.
    """
    deadline = time.monotonic() + retries * delay * 3

    while time.monotonic() < deadline:
        try:
            api.add_workspace_value(name, value, unit=unit)
        except Exception:
            pass

        # Step 2: wait for name to appear in the list (cheap).
        list_deadline = time.monotonic() + 30.0
        while time.monotonic() < list_deadline:
            if name in (api.get_workspace_value_names() or []):
                break
            time.sleep(delay)
        else:
            continue  # never appeared — retry the write

        # Step 3: name is in list; poll GET until it returns a parsed value.
        # errors="raise" fails fast on 404 (no 7s retry loop), caught below.
        get_deadline = time.monotonic() + 30.0
        while time.monotonic() < get_deadline:
            try:
                result = api.get_workspace_value(name, errors="raise")
                if result is not None:
                    return result
            except Exception:
                pass
            time.sleep(delay)

    return None


def cleanup_workspace_values(api: pv.PetroVisor, names: List[str]) -> None:
    """Delete workspace values that exist, ignoring errors."""
    existing = set(api.get_workspace_value_names() or [])
    for n in names:
        if n not in existing:
            continue
        try:
            api.delete_workspace_value(n)
        except Exception:
            pass


# ── reference table helpers ──────────────────────────────────────────────────


def ensure_ref_table(
    api: pv.PetroVisor,
    name: str,
    df: pd.DataFrame,
    retries: int = 30,
    delay: float = 3.0,
) -> None:
    """Create reference table with initial data, poll until schema and data are readable.

    Separates schema creation from data seeding to handle the eventual-consistency
    window where a freshly-created entity isn't yet recognized by the ref table
    data layer (which maintains its own entity registry).
    """
    # Step 1: Create schema only (empty df avoids triggering the data-layer entity check)
    empty_df = df.iloc[0:0]
    if not api.item_exists(pv.ItemType.RefTable, name):
        try:
            api.add_ref_table(name, empty_df)
        except Exception:
            pass

    # Step 2: Wait for schema to propagate
    for _ in range(retries):
        try:
            if api.get_ref_table_data_info(name):
                break
        except Exception:
            pass
        time.sleep(delay)

    # Step 3: Retry data seeding until entity is recognized by the data layer
    for _ in range(retries):
        try:
            result = api.save_ref_table_data(name, df)
            if result is not None:
                return
        except Exception:
            pass
        time.sleep(delay)


def wait_for_ref_table_data(
    api: pv.PetroVisor,
    name: str,
    min_rows: int = 1,
    retries: int = 20,
    delay: float = 2.0,
) -> Optional[pd.DataFrame]:
    """Poll load_ref_table_data until at least min_rows are visible."""
    for _ in range(retries):
        try:
            df = api.load_ref_table_data(name)
            if df is not None and len(df) >= min_rows:
                return df
        except Exception:
            pass
        time.sleep(delay)
    return None


def cleanup_ref_tables(api: pv.PetroVisor, names: List[str]) -> None:
    """Delete reference tables (data + definition), ignoring errors."""
    for n in names:
        try:
            api.delete_ref_table(n)
        except Exception:
            pass
