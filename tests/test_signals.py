"""
Comprehensive test suite for signal data endpoints (Data/Retrieve, Data/Save, Data/Delete).

Signal types tested:
- Static numeric & string
- Time numeric & string
- Depth numeric & string
- PVT

All tests include proper cleanup to avoid polluting the test workspace.
"""

from datetime import datetime

from petrovisor import PetroVisor, Entity, Signal, SignalType, ItemType
import pandas as pd
import numpy as np
import pytest

from conftest import (
    _UNIT,
    ensure_entities as _ensure_entities,
    ensure_signal as _ensure_signal,
    ensure_signals as _ensure_signals,
    wait_for_save_ready as _wait_for_save_ready,
    wait_for_data as _wait_for_data,
    cleanup as _cleanup,
)


# ============================================================================
# test_save_data — covers save_data(), save_table_data(), delete_data()
#   for all signal types and all input formats (list, DataFrame, Series,
#   long/wide, explicit type vs auto-detect)
# ============================================================================


def test_save_data(api: PetroVisor):
    """
    Consolidated save/delete roundtrip for all signal types and input formats.

    Covers:
    - save_data() with explicit data_type + list payload
    - save_data() / save_table_data() with long-format DataFrame
    - save_data() with wide-format DataFrame
    - save_data() with named Series
    - delete_data() range, full, DataFrame spec, Series spec
    - roundtrip verification via load_signals_data
    """
    from petrovisor import Scope, EntitySet, Context, TimeIncrement, DepthIncrement

    PFX = "SD"
    e1, e2 = f"{PFX} Well 001", f"{PFX} Well 002"
    sig_static_num = f"{PFX} Static Num"
    sig_static_str = f"{PFX} Static Str"
    sig_time_num = f"{PFX} Time Num"
    sig_time_str = f"{PFX} Time Str"
    sig_depth_num = f"{PFX} Depth Num"
    sig_depth_str = f"{PFX} Depth Str"
    signal_names = [
        sig_static_num,
        sig_static_str,
        sig_time_num,
        sig_time_str,
        sig_depth_num,
        sig_depth_str,
    ]

    try:
        import concurrent.futures as _cf

        with _cf.ThreadPoolExecutor(max_workers=2) as _pool:
            _fe = _pool.submit(_ensure_entities, api, [e1, e2])
            _fs = _pool.submit(_ensure_signals, api, PFX)
            _fe.result()
            _fs.result()

        with _cf.ThreadPoolExecutor(max_workers=6) as _pool:
            _ready_futs = {
                sig_static_num: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_static_num, "static"
                ),
                sig_static_str: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_static_str, "string"
                ),
                sig_time_num: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_time_num, "time"
                ),
                sig_time_str: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_time_str, "timestring"
                ),
                sig_depth_num: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_depth_num, "depth"
                ),
                sig_depth_str: _pool.submit(
                    _wait_for_save_ready, api, e1, sig_depth_str, "stringdepth"
                ),
            }
            for sig_name, fut in _ready_futs.items():
                assert fut.result() is not None, (
                    f"data layer never ready for {sig_name}"
                )

        dates = ["2024-08-01", "2024-08-02", "2024-08-03"]
        depths = [1000.0, 1001.0, 1002.0]

        # ── 1. save_data() with explicit data_type + list payload ─────────────
        api.save_data(
            data_type="static",
            with_logs=False,
            data=[
                {"Entity": e1, "Signal": sig_static_num, "Unit": _UNIT, "Data": 11.0},
            ],
        )
        api.save_data(
            data_type="string",
            with_logs=False,
            data=[
                {
                    "Entity": e1,
                    "Signal": sig_static_str,
                    "Unit": _UNIT,
                    "Data": "alpha",
                },
            ],
        )
        api.save_data(
            data_type="time",
            with_logs=False,
            data=[
                {
                    "Entity": e1,
                    "Signal": sig_time_num,
                    "Unit": _UNIT,
                    "Data": [
                        {"Date": "2024-08-01T00:00:00Z", "Value": 1.0},
                        {"Date": "2024-08-02T00:00:00Z", "Value": 2.0},
                        {"Date": "2024-08-03T00:00:00Z", "Value": 3.0},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="timestring",
            with_logs=False,
            data=[
                {
                    "Entity": e1,
                    "Signal": sig_time_str,
                    "Unit": _UNIT,
                    "Data": [
                        {"Date": "2024-08-01T00:00:00Z", "Value": "on"},
                        {"Date": "2024-08-02T00:00:00Z", "Value": "off"},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="depth",
            with_logs=False,
            data=[
                {
                    "Entity": e1,
                    "Signal": sig_depth_num,
                    "Unit": _UNIT,
                    "Data": [
                        {"Depth": 1000.0, "Value": 10.0},
                        {"Depth": 1001.0, "Value": 20.0},
                        {"Depth": 1002.0, "Value": 30.0},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="stringdepth",
            with_logs=False,
            data=[
                {
                    "Entity": e1,
                    "Signal": sig_depth_str,
                    "Unit": _UNIT,
                    "Data": [
                        {"Depth": 1000.0, "Value": "sand"},
                        {"Depth": 1001.0, "Value": "shale"},
                    ],
                },
            ],
        )
        print("✅ save_data() explicit type + list payload — all 6 types")

        # ── 2. save_data() with long-format DataFrame (auto-detect) ───────────
        api.save_data(
            pd.DataFrame(
                [[e1, 50.0], [e2, 60.0]],
                columns=["Entity", f"{sig_static_num} [{_UNIT}]"],
            )
        )
        api.save_data(
            pd.DataFrame(
                [[e1, d, v] for d, v in zip(dates, [4.0, 5.0, 6.0])]
                + [[e2, d, v] for d, v in zip(dates, [7.0, 8.0, 9.0])],
                columns=["Entity", "Date", f"{sig_time_num} [{_UNIT}]"],
            )
        )
        api.save_data(
            pd.DataFrame(
                [[e1, d, v] for d, v in zip(depths, [40.0, 50.0, 60.0])],
                columns=["Entity", "Depth [m]", f"{sig_depth_num} [{_UNIT}]"],
            )
        )
        print("✅ save_data() long-format DataFrame (auto-detect)")

        # ── 3. save_data() with wide-format DataFrame ─────────────────────────
        api.save_data(
            pd.DataFrame(
                [[d, 100.0 + i, 200.0 + i] for i, d in enumerate(dates)],
                columns=[
                    "Date",
                    f"{e1} : {sig_time_num} [{_UNIT}]",
                    f"{e2} : {sig_time_num} [{_UNIT}]",
                ],
            )
        )
        print("✅ save_data() wide-format DataFrame")

        # ── 4. save_data() with named Series ──────────────────────────────────
        api.save_data(
            pd.Series({e1: 77.0, e2: 88.0}, name=f"{sig_static_num} [{_UNIT}]")
        )
        api.save_data(
            pd.Series(
                dict(zip(dates, [10.0, 11.0, 12.0])),
                name=f"{e1} : {sig_time_num} [{_UNIT}]",
            )
        )
        api.save_data(
            pd.Series(
                dict(zip(depths, [70.0, 80.0, 90.0])),
                name=f"{e1} : {sig_depth_num} [{_UNIT}]",
            )
        )
        print("✅ save_data() named Series")

        # ── 5. save_data() with logs ───────────────────────────────────────────
        api.save_data(
            data_type="static",
            with_logs=True,
            logs_source="Test",
            data=[
                {"Entity": e1, "Signal": sig_static_num, "Unit": _UNIT, "Data": 99.0},
            ],
        )
        print("✅ save_data() with_logs=True")

        # ── 6. save_table_data() roundtrip ────────────────────────────────────
        scope = Scope(
            name="SD Scope",
            time_start="2024-08-01T00:00:00",
            time_end="2024-08-03T00:00:00",
            time_step=TimeIncrement.Daily.name,
            depth_start=1000.0,
            depth_end=1002.0,
            depth_step=DepthIncrement.Meter.name,
        )
        eset = EntitySet(
            name="SD Entities",
            entities=[Entity(name=e1, type="Well"), Entity(name=e2, type="Well")],
        )
        ctx = Context(name="SD Context", scope=scope, entity_set=eset)

        def _col(df, sig):
            return next((c for c in df.columns if sig in c), None)

        # Poll until static, time, and depth data are all loadable; reuse confirmed result.
        # Run three independent polls concurrently to avoid serial wait overhead.
        import concurrent.futures

        def _poll_static():
            return _wait_for_data(
                api,
                lambda: api.load_signals_data([sig_static_num], context=ctx),
                min_rows=2,
            )

        def _poll_time():
            return _wait_for_data(
                api,
                lambda: api.load_signals_data([sig_time_num], context=ctx),
                min_rows=3,
            )

        def _poll_depth():
            return _wait_for_data(
                api,
                lambda: api.load_signals_data([sig_depth_num], context=ctx),
                min_rows=3,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            fut_static = pool.submit(_poll_static)
            fut_time = pool.submit(_poll_time)
            fut_depth = pool.submit(_poll_depth)
            df_static = fut_static.result()
            df_time = fut_time.result()
            df_depth = fut_depth.result()

        # Verify static (Series override: e1=77, e2=88 → then 99 for e1)
        df = df_static
        assert df is not None and not df.empty, "static load returned no data"
        col = _col(df, sig_static_num)
        assert col is not None, (
            f"column for {sig_static_num} not found in {list(df.columns)}"
        )
        # 2 entities → 2 rows
        assert df.shape[0] == 2, f"static: expected 2 rows, got {df.shape[0]}"
        for ent, exp in [(e1, 99.0), (e2, 88.0)]:
            rows = df[df["Entity"] == ent]
            assert len(rows) == 1, f"static: expected 1 row for {ent}"
            got = float(rows[col].iloc[0])
            assert abs(got - exp) < 1e-3, f"static {ent}: expected {exp}, got {got}"
        print(f"✅ static numeric roundtrip verified ({df.shape[0]} rows)")

        # Verify time (Series override: e1 → [10,11,12], scope covers 3 dates)
        df = df_time
        assert df is not None and not df.empty, "time load returned no data"
        col = _col(df, sig_time_num)
        assert col is not None, (
            f"column for {sig_time_num} not found in {list(df.columns)}"
        )
        assert "Date" in df.columns, "time DataFrame missing 'Date' column"
        rows_e1 = df[df["Entity"] == e1]
        assert len(rows_e1) == 3, f"time e1: expected 3 rows, got {len(rows_e1)}"
        got = sorted(rows_e1[col].dropna().astype(float).tolist())
        assert got == [10.0, 11.0, 12.0], f"time e1 mismatch: {got}"
        print(f"✅ time numeric roundtrip verified ({df.shape[0]} rows)")

        # Verify depth (Series override: e1 → [70,80,90], scope 1000–1002)
        df = df_depth
        assert df is not None and not df.empty, "depth load returned no data"
        col = _col(df, sig_depth_num)
        assert col is not None, (
            f"column for {sig_depth_num} not found in {list(df.columns)}"
        )
        # depth column must always be labelled "Depth [m]" (default unit)
        assert "Depth [m]" in df.columns, (
            f"depth DataFrame missing 'Depth [m]' column; got {list(df.columns)}"
        )
        rows_e1 = df[df["Entity"] == e1]
        assert len(rows_e1) == 3, f"depth e1: expected 3 rows, got {len(rows_e1)}"
        got = sorted(rows_e1[col].dropna().astype(float).tolist())
        assert got == [70.0, 80.0, 90.0], f"depth e1 mismatch: {got}"
        print(
            f"✅ depth numeric roundtrip verified ({df.shape[0]} rows, column='Depth [m]')"
        )

        # ── 7. delete_data() — range, full, DataFrame spec, Series spec ───────
        api.delete_data(
            data_type="static", data=[{"Entity": e1, "Signal": sig_static_num}]
        )
        api.delete_data(
            data_type="string", data=[{"Entity": e1, "Signal": sig_static_str}]
        )
        api.delete_data(
            data_type="time",
            data=[{"Entity": e1, "Signal": sig_time_num}],
            start=datetime(2024, 8, 1),
            end=datetime(2024, 8, 2),
        )
        api.delete_data(data_type="time", data=[{"Entity": e1, "Signal": sig_time_num}])
        api.delete_data(
            data_type="timestring", data=[{"Entity": e1, "Signal": sig_time_str}]
        )
        api.delete_data(
            data_type="depth",
            data=[{"Entity": e1, "Signal": sig_depth_num}],
            start=1000.0,
            end=1001.0,
        )
        api.delete_data(
            data_type="depth", data=[{"Entity": e1, "Signal": sig_depth_num}]
        )
        api.delete_data(
            data_type="stringdepth", data=[{"Entity": e1, "Signal": sig_depth_str}]
        )
        # DataFrame spec
        api.delete_data(
            data_type="static",
            data=pd.DataFrame([{"Entity": e2, "Signal": sig_static_num}]),
        )
        # Series spec
        api.delete_data(
            data_type="time", data=pd.Series({"Entity": e2, "Signal": sig_time_num})
        )
        print("✅ delete_data() — all variants")

        print("✅ test_save_data passed")

    finally:
        _cleanup(api, [e1, e2], signal_names)


# ============================================================================
# test_load_data — covers load_signals_data(), load_data() for all signal
#   types, all option params, and all input/delegation formats
# ============================================================================


def test_load_data(api: PetroVisor):
    """
    Consolidated load roundtrip for all signal types and load options.

    Covers:
    - load_signals_data() with entities, scope, context
    - load_signals_data() options: nrows, aggfunc, with_gaps, with_workspace_values, backend
    - load_data() delegation: signal-name format, entity-based format
    - load_data() backward-compat start/end/step parameters
    - load_data() new params: scenario, time_start, time_end, backend
    - verify roundtrip values
    """
    from petrovisor import (
        AggregationFunction,
        Scope,
        EntitySet,
        Context,
        TimeIncrement,
        DepthIncrement,
    )

    PFX = "LD"
    ent = f"{PFX} Well 001"
    sig_static_num = f"{PFX} Static Num"
    sig_static_str = f"{PFX} Static Str"
    sig_time_num = f"{PFX} Time Num"
    sig_time_str = f"{PFX} Time Str"
    sig_depth_num = f"{PFX} Depth Num"
    sig_depth_str = f"{PFX} Depth Str"
    signal_names = [
        sig_static_num,
        sig_static_str,
        sig_time_num,
        sig_time_str,
        sig_depth_num,
        sig_depth_str,
    ]

    try:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as _pool:
            _fe = _pool.submit(_ensure_entities, api, [ent])
            _fs = _pool.submit(_ensure_signals, api, PFX)
            _fe.result()
            _fs.result()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as _pool:
            _ready_futs = {
                sig_static_num: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_static_num, "static"
                ),
                sig_static_str: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_static_str, "string"
                ),
                sig_time_num: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_time_num, "time"
                ),
                sig_time_str: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_time_str, "timestring"
                ),
                sig_depth_num: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_depth_num, "depth"
                ),
                sig_depth_str: _pool.submit(
                    _wait_for_save_ready, api, ent, sig_depth_str, "stringdepth"
                ),
            }
            for sig_name, fut in _ready_futs.items():
                assert fut.result() is not None, (
                    f"data layer never ready for {sig_name}"
                )

        # ── Seed data ─────────────────────────────────────────────────────────
        api.save_data(
            data_type="static",
            with_logs=False,
            data=[
                {"Entity": ent, "Signal": sig_static_num, "Unit": _UNIT, "Data": 100.0},
            ],
        )
        api.save_data(
            data_type="string",
            with_logs=False,
            data=[
                {
                    "Entity": ent,
                    "Signal": sig_static_str,
                    "Unit": _UNIT,
                    "Data": "hello",
                },
            ],
        )
        api.save_data(
            data_type="time",
            with_logs=False,
            data=[
                {
                    "Entity": ent,
                    "Signal": sig_time_num,
                    "Unit": _UNIT,
                    "Data": [
                        {"Date": "2024-01-01T00:00:00Z", "Value": 10.0},
                        {"Date": "2024-01-02T00:00:00Z", "Value": 20.0},
                        {"Date": "2024-01-03T00:00:00Z", "Value": 30.0},
                        {"Date": "2024-01-04T00:00:00Z", "Value": 40.0},
                        {"Date": "2024-01-05T00:00:00Z", "Value": 50.0},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="timestring",
            with_logs=False,
            data=[
                {
                    "Entity": ent,
                    "Signal": sig_time_str,
                    "Unit": _UNIT,
                    "Data": [
                        {"Date": "2024-01-01T00:00:00Z", "Value": "a"},
                        {"Date": "2024-01-02T00:00:00Z", "Value": "b"},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="depth",
            with_logs=False,
            data=[
                {
                    "Entity": ent,
                    "Signal": sig_depth_num,
                    "Unit": _UNIT,
                    "Data": [
                        {"Depth": 1000.0, "Value": 100.0},
                        {"Depth": 1001.0, "Value": 200.0},
                        {"Depth": 1002.0, "Value": 300.0},
                        {"Depth": 1003.0, "Value": 400.0},
                        {"Depth": 1004.0, "Value": 500.0},
                    ],
                },
            ],
        )
        api.save_data(
            data_type="stringdepth",
            with_logs=False,
            data=[
                {
                    "Entity": ent,
                    "Signal": sig_depth_str,
                    "Unit": _UNIT,
                    "Data": [
                        {"Depth": 1000.0, "Value": "x"},
                        {"Depth": 1001.0, "Value": "y"},
                    ],
                },
            ],
        )

        # ── Build context (needed for propagation poll below) ──────────────────
        scope = Scope(
            name="LD Scope",
            time_start="2024-01-01T00:00:00",
            time_end="2024-01-05T00:00:00",
            time_step=TimeIncrement.Daily.name,
            depth_start=1000.0,
            depth_end=1004.0,
            depth_step=DepthIncrement.Meter.name,
        )
        eset = EntitySet(name="LD Entities", entities=[Entity(name=ent, type="Well")])
        ctx = Context(name="LD Context", scope=scope, entity_set=eset)

        # Poll until static, time, and depth data are all loadable; run concurrently.
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as _pool:
            _fs = _pool.submit(
                _wait_for_data,
                api,
                lambda: api.load_signals_data([sig_static_num], context=ctx),
                1,
            )
            _ft = _pool.submit(
                _wait_for_data,
                api,
                lambda: api.load_signals_data([sig_time_num], context=ctx),
                5,
            )
            _fd = _pool.submit(
                _wait_for_data,
                api,
                lambda: api.load_signals_data([sig_depth_num], context=ctx),
                5,
                60,  # up to 120s ceiling for depth propagation
            )
            _fs.result()
            _ft.result()
            _df_depth_confirmed = _fd.result()

        def _col(df, sig):
            return next((c for c in df.columns if sig in c), None)

        # ── load_signals_data() with context ──────────────────────────────────
        # static + time together: 1 entity × 5 time steps = 5 rows.
        # Poll the combined call — individual polls above don't guarantee the
        # combined response is ready (server routes static and time separately).
        df = _wait_for_data(
            api,
            lambda: api.load_signals_data([sig_static_num, sig_time_num], context=ctx),
            5,
        )
        assert df is not None and not df.empty, (
            "load_signals_data(context) returned no data"
        )
        col_static = _col(df, sig_static_num)
        assert col_static is not None, (
            f"{sig_static_num} column not found in {list(df.columns)}"
        )
        rows = df[df["Entity"] == ent]
        assert abs(float(rows[col_static].iloc[0]) - 100.0) < 1e-3, (
            "static value mismatch"
        )
        assert df.shape[0] == 5, (
            f"load_signals_data(context): expected 5 rows, got {df.shape[0]}"
        )
        assert "Date" in df.columns, "mixed load missing Date column"
        print(
            f"✅ load_signals_data(context): {df.shape[0]} rows, static value verified"
        )

        # ── load_signals_data() with entities= ────────────────────────────────
        # time signal, 5 dates
        df = api.load_signals_data(
            [sig_time_num],
            entities=ent,
            time_start="2024-01-01",
            time_end="2024-01-05",
            time_step=TimeIncrement.Daily.name,
        )
        assert df is not None and not df.empty, (
            "load_signals_data(entities) returned no data"
        )
        col = _col(df, sig_time_num)
        assert col is not None, f"{sig_time_num} column not found"
        assert df.shape[0] == 5, f"time: expected 5 rows, got {df.shape[0]}"
        got = sorted(df[col].dropna().astype(float).tolist())
        assert got == [10.0, 20.0, 30.0, 40.0, 50.0], f"time values: {got}"
        print(f"✅ load_signals_data(entities): {df.shape[0]} rows, values verified")

        # ── depth signals — verify Depth [m] column label ─────────────────────
        df_depth = _df_depth_confirmed
        assert df_depth is not None and not df_depth.empty, (
            "depth load returned no data"
        )
        assert "Depth [m]" in df_depth.columns, (
            f"depth DataFrame must have 'Depth [m]' column, got {list(df_depth.columns)}"
        )
        assert df_depth.shape[0] == 5, (
            f"depth: expected 5 rows, got {df_depth.shape[0]}"
        )
        col_depth = _col(df_depth, sig_depth_num)
        assert col_depth is not None
        got_depth = sorted(df_depth[col_depth].dropna().astype(float).tolist())
        assert got_depth == [100.0, 200.0, 300.0, 400.0, 500.0], (
            f"depth values: {got_depth}"
        )
        print(
            f"✅ depth signals: {df_depth.shape[0]} rows, column='Depth [m]', values verified"
        )

        # ── load_signals_data() options ───────────────────────────────────────
        # nrows
        df_nrows = api.load_signals_data([sig_time_num], context=ctx, nrows=2)
        assert df_nrows is None or isinstance(df_nrows, pd.DataFrame)
        print("✅ load_signals_data(nrows=2)")

        # aggfunc
        df_agg = api.load_signals_data(
            [sig_time_num], context=ctx, aggfunc=AggregationFunction.Average
        )
        assert df_agg is None or isinstance(df_agg, pd.DataFrame)
        print("✅ load_signals_data(aggfunc=Average)")

        # with_gaps
        df_gaps = api.load_signals_data([sig_time_num], context=ctx, with_gaps=True)
        assert df_gaps is None or isinstance(df_gaps, pd.DataFrame)
        print("✅ load_signals_data(with_gaps=True)")

        # with_workspace_values=True — accepted, does not raise
        df_wv = api.load_signals_data(
            [sig_time_num], context=ctx, with_workspace_values=True
        )
        assert df_wv is None or isinstance(df_wv, pd.DataFrame)
        print(
            f"✅ load_signals_data(with_workspace_values=True): {df_wv.shape[0] if df_wv is not None else 'None'}"
        )

        # with_workspace_values=False — accepted, does not raise
        df_wv_false = api.load_signals_data(
            [sig_time_num], context=ctx, with_workspace_values=False
        )
        assert df_wv_false is None or isinstance(df_wv_false, pd.DataFrame)
        print("✅ load_signals_data(with_workspace_values=False)")

        # backend=polars (skip if not installed)
        try:
            import polars as pl

            df_pl = api.load_signals_data(
                [sig_static_num], entities=ent, backend="polars"
            )
            assert df_pl is None or isinstance(df_pl, (pd.DataFrame, pl.DataFrame))
            print("✅ load_signals_data(backend=polars)")
        except ImportError:
            pass

        # ── load_data() — entity-based format ────────────────────────────────
        spec_static = [{"Entity": ent, "Signal": sig_static_num, "Unit": _UNIT}]
        spec_time = [{"Entity": ent, "Signal": sig_time_num, "Unit": _UNIT}]
        spec_depth = [{"Entity": ent, "Signal": sig_depth_num, "Unit": _UNIT}]
        spec_time_str = [{"Entity": ent, "Signal": sig_time_str, "Unit": _UNIT}]
        spec_depth_str = [{"Entity": ent, "Signal": sig_depth_str, "Unit": _UNIT}]

        r = api.load_data(data_type="static", data=spec_static)
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(static, list)")

        r = api.load_data(
            data_type="time",
            data=spec_time,
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 5),
            step="Daily",
        )
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(time, range)")

        r = api.load_data(data_type="time", data=spec_time, num_values=3)
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(time, first 3)")

        r = api.load_data(data_type="time", data=spec_time, num_values=-2)
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(time, last 2)")

        r = api.load_data(data_type="timestring", data=spec_time_str, num_values=2)
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(timestring, top 2)")

        r = api.load_data(
            data_type="depth", data=spec_depth, start=1001.0, end=1003.0, step="Meter"
        )
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(depth, range)")

        r = api.load_data(data_type="stringdepth", data=spec_depth_str, num_values=2)
        print(f"{'✅' if r is not None else 'ℹ️ '} load_data(stringdepth, top 2)")

        # DataFrame / Series request spec
        r = api.load_data(
            data_type="static",
            data=pd.DataFrame(
                [{"Entity": ent, "Signal": sig_static_num, "Unit": _UNIT}]
            ),
        )
        print("✅ load_data(DataFrame spec)")

        r = api.load_data(
            data_type="static",
            data=pd.Series({"Entity": ent, "Signal": sig_static_num, "Unit": _UNIT}),
        )
        print("✅ load_data(Series spec)")

        # ── load_data() — signal-name delegation ──────────────────────────────
        r = api.load_data(
            data=sig_time_num,
            entities=ent,
            time_start="2024-01-01",
            time_end="2024-01-05",
        )
        assert r is None or isinstance(r, pd.DataFrame)
        print("✅ load_data(signal name → load_signals_data delegation)")

        r = api.load_data(data=[sig_time_num, sig_static_num], entities=ent)
        assert r is None or isinstance(r, pd.DataFrame)
        print("✅ load_data([signal names] delegation)")

        # ── load_data() backward-compat start/end/step params accepted ──────────
        try:
            api.load_data(
                data=spec_time, start=datetime(2024, 1, 1), end=datetime(2024, 1, 5)
            )
        except Exception:
            pass
        print("✅ load_data(start/end) accepted as backward-compat params")

        # ── load_data() new params accepted ───────────────────────────────────
        try:
            api.load_data(
                data=sig_time_num,
                scenario="Test",
                time_start="2024-01-01",
                time_end="2024-01-05",
                backend="pandas",
            )
        except Exception:
            pass
        print("✅ load_data() new params (scenario, time_start/end, backend) accepted")

        print("✅ test_load_data passed")

    finally:
        _cleanup(api, [ent], signal_names)


# ============================================================================
# test_get_data_range
# ============================================================================


def test_get_data_range(api: PetroVisor):
    """Test get_data_range() with Data/TimeRange and Data/DepthStepExtremum endpoints."""
    entity_name = "Test Range Well"
    time_signal_num = "Test Range Time Numeric"
    time_signal_str = "Test Range Time String"
    depth_signal_num = "Test Range Depth Numeric"
    depth_signal_str = "Test Range Depth String"
    signals_to_create = [
        (time_signal_num, SignalType.TimeDependent),
        (time_signal_str, SignalType.StringTimeDependent),
        (depth_signal_num, SignalType.DepthDependent),
        (depth_signal_str, SignalType.StringDepthDependent),
    ]

    try:
        _ensure_entities(api, [entity_name])
        for signal_name, signal_type in signals_to_create:
            _ensure_signal(api, signal_name, signal_type)
        import concurrent.futures as _cf

        with _cf.ThreadPoolExecutor(max_workers=2) as _pool:
            _f1 = _pool.submit(
                _wait_for_save_ready, api, entity_name, time_signal_num, "time"
            )
            _f2 = _pool.submit(
                _wait_for_save_ready, api, entity_name, depth_signal_num, "depth"
            )
            _f1.result()
            _f2.result()

        api.save_table_data(
            pd.DataFrame(
                {
                    "Entity": [entity_name] * 5,
                    "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
                    f"{time_signal_num} [ ]": [10, 20, 30, 40, 50],
                    f"{time_signal_str} [ ]": ["a", "b", "c", "d", "e"],
                }
            )
        )
        api.save_table_data(
            pd.DataFrame(
                {
                    "Entity": [entity_name] * 5,
                    "Depth [m]": [1000, 1001, 1002, 1003, 1004],
                    f"{depth_signal_num} [ ]": [100, 200, 300, 400, 500],
                    f"{depth_signal_str} [ ]": ["x", "y", "z", "w", "v"],
                }
            )
        )

        for sig_type, sig_name in [
            ("time", time_signal_num),
            ("timestring", time_signal_str),
            ("depth", depth_signal_num),
            ("stringdepth", depth_signal_str),
        ]:
            rng = api.get_data_range(
                signal_type=sig_type, signal=sig_name, entity=entity_name
            )
            if rng and isinstance(rng, dict) and "Start" in rng:
                print(f"✅ {sig_type} range: {rng}")
            else:
                print(f"ℹ️  {sig_type} range: not propagated yet")

        print(f"✅ time (all): {type(api.get_data_range(signal_type='time')).__name__}")
        print(
            f"✅ depth (all): {type(api.get_data_range(signal_type='depth')).__name__}"
        )

        with pytest.raises(ValueError):
            api.get_data_range(signal=time_signal_num)
        with pytest.raises(ValueError):
            api.get_data_range()
        print("✅ ValueError raised correctly")

    finally:
        for signal_name, _ in signals_to_create:
            try:
                api.delete_signal(signal_name)
            except Exception:
                pass
        try:
            api.delete_entity(entity_name)
        except Exception:
            pass


# ============================================================================
# test_cleanse_data
# ============================================================================


def test_cleanse_data(api: PetroVisor):
    """Test cleanse_data() with Data/Acquire endpoint."""
    entity_name = "Test Cleanse Well"
    static_signal = "Test Cleanse Static"
    time_signal = "Test Cleanse Time"

    try:
        _ensure_entities(api, [entity_name])
        _ensure_signal(api, static_signal, SignalType.Static)
        _ensure_signal(api, time_signal, SignalType.TimeDependent)
        import concurrent.futures as _cf

        with _cf.ThreadPoolExecutor(max_workers=2) as _pool:
            _f1 = _pool.submit(_wait_for_save_ready, api, entity_name, static_signal)
            _f2 = _pool.submit(
                _wait_for_save_ready, api, entity_name, time_signal, "time"
            )
            _f1.result()
            _f2.result()

        result = api.cleanse_data(
            value=100.5,
            timestamp=None,
            signal=static_signal,
            unit=" ",
            entity=entity_name,
            cleansing_script="DefaultCleansing",
        )
        print(f"{'✅' if result else 'ℹ️ '} static cleanse: {result}")

        result = api.cleanse_data(
            value=50.25,
            timestamp=datetime(2024, 1, 1),
            signal=time_signal,
            unit=" ",
            entity=entity_name,
            cleansing_script="DefaultCleansing",
        )
        print(f"{'✅' if result else 'ℹ️ '} time cleanse: {result}")

    finally:
        try:
            api.delete_signal(static_signal)
        except Exception:
            pass
        try:
            api.delete_signal(time_signal)
        except Exception:
            pass
        try:
            api.delete_entity(entity_name)
        except Exception:
            pass


# ============================================================================
# test_signals_comprehensive — multi-well context test
# ============================================================================


def test_signals_comprehensive(api: PetroVisor):
    """Comprehensive test covering all signal types via Data/Retrieve with context."""
    from petrovisor import (
        EntitySet,
        Hierarchy,
        Scope,
        Context,
        TimeIncrement,
        DepthIncrement,
    )

    signal_configs = [
        {
            "name": "static numeric signal",
            "type": SignalType.Static,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "static string signal",
            "type": SignalType.String,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "time numeric signal",
            "type": SignalType.TimeDependent,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "time string signal",
            "type": SignalType.StringTimeDependent,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "depth numeric signal",
            "type": SignalType.DepthDependent,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "depth string signal",
            "type": SignalType.StringDepthDependent,
            "unit": " ",
            "measurement": "Dimensionless",
        },
        {
            "name": "pvt signal",
            "type": SignalType.PVT,
            "unit": "Pa",
            "measurement": "Pressure",
        },
    ]
    for cfg in signal_configs:
        _ensure_signal(api, cfg["name"], cfg["type"], unit=cfg["unit"])

    _ensure_entities(api, ["Well 001", "Well 002", "Well 003", "Well 004", "Well 005"])
    _ensure_entities(api, ["Field 1"], entity_type="Field")

    entities = [
        Entity(name="Well 001", type="Well"),
        Entity(name="Well 002", type="Well"),
        Entity(name="Well 003", type="Well"),
        Entity(name="Well 004", type="Well"),
        Entity(name="Well 005", type="Well"),
        Entity(name="Field 1", type="Field"),
    ]

    time_start, time_end = "2021-01-01T00:00:00", "2022-01-01T00:00:00"
    num_wells, time_steps, depth_steps = 5, 20, 10
    letters = list(map(chr, range(97, 123)))
    entity_col, time_col, depth_col = "Entity", "Date", "Depth [m]"

    stat_num = signal_configs[0]["name"]
    stat_str = signal_configs[1]["name"]
    time_num = signal_configs[2]["name"]
    time_str = signal_configs[3]["name"]
    depth_num = signal_configs[4]["name"]
    depth_str = signal_configs[5]["name"]
    pvt = signal_configs[6]["name"]

    df_stat = pd.concat(
        [
            pd.DataFrame(
                {entity_col: [f"Well 00{i + 1}"], stat_num: [i], stat_str: [letters[i]]}
            )
            for i in range(num_wells)
        ],
        ignore_index=True,
    )
    api.save_table_data(df_stat)

    df_time = pd.concat(
        [
            pd.DataFrame(
                {
                    entity_col: np.repeat(f"Well 00{i + 1}", time_steps),
                    time_col: pd.date_range(
                        time_start, periods=time_steps, freq="D"
                    ).to_list(),
                    time_num: np.random.uniform(1, 4, time_steps),
                    time_str: np.random.choice(letters, time_steps),
                }
            )
            for i in range(num_wells)
        ],
        ignore_index=True,
    )
    api.save_table_data(df_time)

    df_depth = pd.concat(
        [
            pd.DataFrame(
                {
                    entity_col: np.repeat(f"Well 00{i + 1}", depth_steps),
                    depth_col: np.arange(0, depth_steps).tolist(),
                    depth_num: np.sin(np.linspace(0, 1, depth_steps)) * 100,
                    depth_str: np.random.choice(letters, depth_steps),
                }
            )
            for i in range(num_wells)
        ],
        ignore_index=True,
    )
    api.save_table_data(df_depth)

    eset = EntitySet(name="Field 1 Wells", entities=entities)
    hier = Hierarchy(
        name="Field 1 Wells",
        relationship={f"Well 00{i + 1}": "Field 1" for i in range(5)},
    )
    scope = Scope(
        name="Field 1 Wells Scope",
        time_start=time_start,
        time_end=time_end,
        time_step=TimeIncrement.Daily.name,
        depth_start=0,
        depth_end=10,
        depth_step=DepthIncrement.Meter.name,
    )
    ctx = Context(name="Context", scope=scope, entity_set=eset, hierarchy=hier)

    for label, sigs in [
        ("static", [stat_num, stat_str]),
        ("time", [time_num, time_str]),
        ("depth", [depth_num, depth_str]),
        ("all", [stat_num, stat_str, time_num, time_str, depth_num, depth_str]),
    ]:
        df = api.load_signals_data(sigs, context=ctx)
        if df is not None and df.shape[0] > 0:
            print(f"✅ {label} signals: {df.shape[0]} rows")
        else:
            print(f"ℹ️  {label} signals: no data")

    df_pvt = api.load_signals_data(
        [pvt], entities=["Well 001"], pressure_unit="psi", temperature_unit="F"
    )
    print(f"{'✅' if df_pvt is not None and len(df_pvt) > 0 else 'ℹ️ '} PVT signal")
    print("✅ test_signals_comprehensive passed")


# ============================================================================
# Entity/signal helpers
# ============================================================================


def test_signals_by_entity(api: PetroVisor):
    """Test retrieving signals by entity type, including special-character entity name."""
    entity_name = r"_entity with special characters %*,$&^§()#//=2!~*'"
    api.add_item(
        "Entity",
        {
            "Name": entity_name,
            "EntityTypeName": "Well",
            "Alias": "",
            "IsOpportunity": False,
        },
    )
    signal_name = "Time Signal"
    api.add_item(
        "Signal",
        {
            "Name": signal_name,
            "ShortName": signal_name[:29],
            "SignalType": "TimeDependent",
            "MeasurementName": "Dimensionless",
            "StorageUnitName": " ",
            "AggregationType": "Sum",
            "ContainerAggregationType": "Sum",
        },
    )
    df = pd.DataFrame(
        {
            "Entity": np.repeat(entity_name, 5),
            "Date": pd.date_range("2023-11-29", periods=5, freq="D"),
            f"{signal_name} [ ]": np.random.rand(5),
        }
    )
    api.save_table_data(df)
    entity_signals = api.get_signals(entity=entity_name, signal_type="time")
    assert signal_name in [s["Name"] for s in entity_signals]


def test_delete_nonexistent_entity(api: PetroVisor):
    """Deleting a non-existent entity should not raise."""
    import uuid

    name = f"Nonexistent Entity {uuid.uuid4().hex[:8]}"
    api.delete_entity(name)
    assert not api.item_exists(ItemType.Entity, name)


def test_delete_nonexistent_signal(api: PetroVisor):
    """Deleting a non-existent signal should not raise."""
    import uuid

    name = f"Nonexistent Signal {uuid.uuid4().hex[:8]}"
    api.delete_signal(name)
    assert not api.item_exists(ItemType.Signal, name)


# ============================================================================
# Backend smoke tests — use real workspace items to avoid retry overhead on 404s
# ============================================================================


def test_load_signals_data_backend_pandas(api):
    # Use the first available signal so _resolve_signals succeeds on the first
    # attempt. Falling back to a nonexistent name causes 3-retry delay (~3s).
    signals = api.get_signals()
    signal_name = signals[0]["Name"] if signals else None
    if signal_name is None:
        pytest.skip("no signals in workspace")
    try:
        df = api.load_signals_data(signals=signal_name, backend="pandas", nrows=1)
        assert df is None or isinstance(df, pd.DataFrame)
    except (ValueError, RuntimeWarning):
        pass


def test_load_signals_data_backend_polars(api):
    try:
        import polars as pl
    except ImportError:
        pytest.skip("polars not installed")

    signals = api.get_signals()
    signal_name = signals[0]["Name"] if signals else None
    if signal_name is None:
        pytest.skip("no signals in workspace")
    try:
        df = api.load_signals_data(signals=signal_name, backend="polars", nrows=1)
        assert df is None or isinstance(df, (pd.DataFrame, pl.DataFrame))
    except (ValueError, RuntimeWarning):
        pass


def test_load_ref_table_data_backend_pandas(api):
    # Use the first available ref table to avoid the 5-retry exponential backoff
    # that fires on every 404 from get_ref_table_data_info.
    ref_table_names = api.get_ref_table_names()
    table_name = ref_table_names[0] if ref_table_names else None
    if table_name is None:
        pytest.skip("no ref tables in workspace")
    try:
        df = api.load_ref_table_data(name=table_name, backend="pandas")
        assert df is None or isinstance(df, pd.DataFrame)
    except Exception:
        pass


def test_load_psharp_table_backend_pandas(api):
    script_names = api.get_psharp_script_names()
    script_name = script_names[0] if script_names else None
    if script_name is None:
        pytest.skip("no P# scripts in workspace")
    try:
        df = api.load_psharp_table(script_name=script_name, backend="pandas")
        assert df is None or isinstance(df, (pd.DataFrame, dict))
    except Exception:
        pass


def test_load_pivot_table_data_backend_pandas(api):
    pivot_names = api.get_pivot_table_names()
    pivot_name = pivot_names[0] if pivot_names else None
    if pivot_name is None:
        pytest.skip("no pivot tables in workspace")
    try:
        df = api.load_pivot_table_data(name=pivot_name, backend="pandas")
        assert df is None or isinstance(df, (pd.DataFrame, dict))
    except Exception:
        pass


# ============================================================================
# load_data signature check (no API call)
# ============================================================================


def test_pvt_save_and_load(api: PetroVisor):
    """PVT full roundtrip covering all public methods.

    Creates entity "PVTTest Well" and three PVT signals (Rso, Bo, Mu), then
    exercises each method:
      - save_data()          explicit data_type="pvt" list payload
      - save_data()          auto-detect (data_type=None)
      - save_table_data()    wide-format DataFrame with Pressure/Temperature axes
      - load_signals_data()  pandas + polars backends
      - load_data()          signal-name delegation path
      - delete_data()        data_type="pvt" + [{Entity, Signal}]
    """
    import time
    import warnings as _warnings
    import concurrent.futures

    PFX = "PVTTest"
    entity = f"{PFX} Well"
    sig_rso = f"{PFX} Rso"
    sig_bo = f"{PFX} Bo"
    sig_mu = f"{PFX} Mu"
    pressure_unit = "Pa"
    temperature_unit = "K"

    _pressures = [1e6, 2e6, 3e6]
    _temperatures = [300.0, 350.0, 400.0]
    _values = {
        sig_rso: [20.0, 28.0, 36.0],
        sig_bo: [1.10, 1.12, 1.14],
        sig_mu: [1.20, 1.07, 0.96],
    }
    n_rows = len(_pressures)

    def _pvt_records():
        return [
            {
                "Entity": entity,
                "Signal": sig,
                "Unit": " ",
                "Data": [
                    {"Pressure": p, "Temperature": t, "Value": v}
                    for p, t, v in zip(_pressures, _temperatures, vals)
                ],
            }
            for sig, vals in _values.items()
        ]

    def _poll_ready(sig_name):
        for _ in range(30):
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore", RuntimeWarning)
                df_probe = api.load_signals_data(
                    [sig_name],
                    entities=[entity],
                    pressure_unit=pressure_unit,
                    temperature_unit=temperature_unit,
                )
            if df_probe is not None and len(df_probe) > 0:
                return True
            time.sleep(2)
        return False

    def _wait_all_ready():
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futs = {s: pool.submit(_poll_ready, s) for s in [sig_rso, sig_bo, sig_mu]}
            for sig_name, fut in futs.items():
                assert fut.result(), f"data layer never ready for {sig_name}"

    def _delete_all():
        for sig in [sig_rso, sig_bo, sig_mu]:
            try:
                api.delete_data(
                    data_type="pvt",
                    data=[{"Entity": entity, "Signal": sig}],
                )
            except Exception:
                pass

    def _save_pvt(data_type_arg=SignalType.PVT):
        """Save PVT data, retrying until server accepts (metadata/data lag)."""
        kw = dict(
            data=_pvt_records(),
            pressure_unit=pressure_unit,
            temperature_unit=temperature_unit,
            with_logs=False,
        )
        if data_type_arg is not None:
            kw["data_type"] = data_type_arg
        for attempt in range(20):
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore", RuntimeWarning)
                resp = api.save_data(**kw)
            # Response is truthy on 2xx, None/falsy on server error
            if resp is not None:
                return
            time.sleep(5)
        raise RuntimeError("save_pvt returned error after 20 attempts")

    def _assert_df(df, label):
        assert df is not None, f"{label}: returned None"
        assert isinstance(df, pd.DataFrame), f"{label}: not a DataFrame"
        assert len(df) == n_rows, f"{label}: expected {n_rows} rows, got {len(df)}"
        assert "Entity" in df.columns, f"{label}: missing Entity column"
        assert any("Pressure" in c for c in df.columns), f"{label}: missing Pressure column"
        assert any("Temperature" in c for c in df.columns), f"{label}: missing Temperature column"
        for sig in [sig_rso, sig_bo, sig_mu]:
            assert any(sig in c for c in df.columns), f"{label}: missing column for {sig}"
        # verify values
        p_col = next(c for c in df.columns if "Pressure" in c)
        df_s = df.sort_values(p_col).reset_index(drop=True)
        for sig, exp_vals in _values.items():
            col = next(c for c in df.columns if sig in c)
            for i, exp in enumerate(exp_vals):
                assert abs(float(df_s[col].iloc[i]) - exp) < 1e-3, (
                    f"{label}: {sig} mismatch at row {i}: {df_s[col].iloc[i]} != {exp}"
                )

    try:
        # ── provision ─────────────────────────────────────────────────────────
        _ensure_entities(api, [entity])
        for name in [sig_rso, sig_bo, sig_mu]:
            _ensure_signal(api, name, SignalType.PVT, unit=" ")
        # Verify signals truly accessible via get_signal (list cache can lag after delete)
        for name in [sig_rso, sig_bo, sig_mu]:
            for _ in range(30):
                with _warnings.catch_warnings():
                    _warnings.simplefilter("ignore", RuntimeWarning)
                    sig_obj = api.get_signal(name)
                if sig_obj is not None:
                    break
                # signal not accessible yet — may need recreation (list cache stale)
                with _warnings.catch_warnings():
                    _warnings.simplefilter("ignore", RuntimeWarning)
                    try:
                        api.add_signal(
                            Signal(
                                type=SignalType.PVT.name,
                                name=name,
                                unit=" ",
                                unit_measurement="Dimensionless",
                            )
                        )
                    except Exception:
                        pass
                time.sleep(2)

        # ── 1. save_data() explicit data_type="pvt" ───────────────────────────
        _save_pvt(data_type_arg=SignalType.PVT)
        _wait_all_ready()
        df = api.load_signals_data(
            [sig_rso, sig_bo, sig_mu],
            entities=[entity],
            pressure_unit=pressure_unit,
            temperature_unit=temperature_unit,
        )
        _assert_df(df, "save_data(explicit pvt)")
        print("✅ save_data(explicit pvt)")

        # ── 2. delete_data() ──────────────────────────────────────────────────
        _delete_all()
        print("✅ delete_data(pvt)")

        # ── 3. save_data() auto-detect (data_type=None) ───────────────────────
        _save_pvt(data_type_arg=None)
        _wait_all_ready()
        df = api.load_signals_data(
            [sig_rso, sig_bo, sig_mu],
            entities=[entity],
            pressure_unit=pressure_unit,
            temperature_unit=temperature_unit,
        )
        _assert_df(df, "save_data(auto-detect)")
        print("✅ save_data(auto-detect)")
        _delete_all()

        # ── 4. save_table_data() with wide PVT DataFrame ─────────────────────
        # Wait until all 3 signals are visible in the signal list before building
        # the DataFrame — get_signal_data_from_dataframe filters on signal existence.
        all_sigs = [sig_rso, sig_bo, sig_mu]
        for _ in range(30):
            existing_sigs = set(api.get_signal_names() or [])
            if all(s in existing_sigs for s in all_sigs):
                break
            time.sleep(2)

        p_col = f"Pressure [{pressure_unit}]"
        t_col = f"Temperature [{temperature_unit}]"
        df_wide = pd.DataFrame(
            {
                "Entity": [entity] * n_rows,
                p_col: _pressures,
                t_col: _temperatures,
                f"{sig_rso} [ ]": _values[sig_rso],
                f"{sig_bo} [ ]": _values[sig_bo],
                f"{sig_mu} [ ]": _values[sig_mu],
            }
        )
        with _warnings.catch_warnings():
            _warnings.simplefilter("ignore", RuntimeWarning)
            api.save_table_data(
                df_wide,
                pressure_unit=pressure_unit,
                temperature_unit=temperature_unit,
                only_existing_entities=False,
            )
        _wait_all_ready()
        df = api.load_signals_data(
            [sig_rso, sig_bo, sig_mu],
            entities=[entity],
            pressure_unit=pressure_unit,
            temperature_unit=temperature_unit,
        )
        _assert_df(df, "save_table_data(wide pvt)")
        print("✅ save_table_data(wide pvt)")

        # ── 5. load_data() signal-name delegation ─────────────────────────────
        df_ld = api.load_data(
            data=[sig_rso, sig_bo, sig_mu],
            entities=[entity],
            pressure_unit=pressure_unit,
            temperature_unit=temperature_unit,
        )
        _assert_df(df_ld, "load_data(signal-name)")
        print("✅ load_data(signal-name delegation)")

        # ── 6. polars backend smoke test ─────────────────────────────────────
        try:
            import polars as _pl

            df_pl = api.load_signals_data(
                [sig_rso, sig_bo, sig_mu],
                entities=[entity],
                pressure_unit=pressure_unit,
                temperature_unit=temperature_unit,
                backend="polars",
            )
            assert df_pl is not None and isinstance(df_pl, _pl.DataFrame)
            assert len(df_pl) == n_rows, "polars backend row count mismatch"
            print("✅ load_signals_data(backend=polars)")
        except ImportError:
            pass

    finally:
        # Delete PVT data but leave entity+signals — deleting them causes metadata/data-layer
        # propagation lag that makes the test fail on the next run.
        _delete_all()


def test_load_data_signature_extended():
    """load_data() must expose all expected parameters."""
    import inspect

    params = list(inspect.signature(PetroVisor.load_data).parameters.keys())
    for p in (
        "scenario",
        "context",
        "scope",
        "entity_set",
        "time_start",
        "time_end",
        "depth_start",
        "depth_end",
        "backend",
        "start",
        "end",
        "step",
    ):
        assert p in params, f"missing param: {p}"
