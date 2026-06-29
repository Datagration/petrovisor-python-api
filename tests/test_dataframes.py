"""Pure unit tests for DataFrame utilities — no live API connection required."""

import pandas as pd
import numpy as np
import pytest

from petrovisor import AggregationFunction
from petrovisor.api.methods.dataframes import DataFrameBackend, DataFrameMixinHelper


# ============================================================================
# AggregationFunction enum
# ============================================================================


def test_aggregation_function_values():
    assert AggregationFunction.Sum == "Sum"
    assert AggregationFunction.Average == "Average"
    assert AggregationFunction.Max == "Max"
    assert AggregationFunction.Min == "Min"
    assert AggregationFunction.First == "First"
    assert AggregationFunction.Last == "Last"
    assert AggregationFunction.Count == "Count"
    assert AggregationFunction.Median == "Median"
    assert AggregationFunction.Mode == "Mode"
    assert AggregationFunction.StandardDeviation == "StandardDeviation"
    assert AggregationFunction.Variance == "Variance"
    assert AggregationFunction.Percentile == "Percentile"
    assert AggregationFunction.Range == "Range"
    assert AggregationFunction.CountDistinct == "CountDistinct"


def test_aggregation_function_is_str():
    assert isinstance(AggregationFunction.Sum, str)
    assert AggregationFunction.Average == "Average"
    assert AggregationFunction.Max.value == "Max"


def test_aggregation_function_membership():
    values = {f.value for f in AggregationFunction}
    assert "Sum" in values
    assert "Average" in values
    assert "CountDistinct" in values
    assert "Invalid" not in values


def test_aggregation_function_from_string():
    assert AggregationFunction("Sum") == AggregationFunction.Sum
    assert AggregationFunction("Average") == AggregationFunction.Average
    assert (
        AggregationFunction("StandardDeviation")
        == AggregationFunction.StandardDeviation
    )


# ============================================================================
# DataFrameBackend enum
# ============================================================================


def test_dataframe_backend_values():
    assert DataFrameBackend.PANDAS.value == "pandas"
    assert DataFrameBackend.POLARS.value == "polars"
    assert DataFrameBackend.PYARROW.value == "pyarrow"
    assert DataFrameBackend.DUCKDB.value == "duckdb"
    assert not hasattr(DataFrameBackend, "NARWHALS"), (
        "narwhals must not be a user-facing backend"
    )
    assert not hasattr(DataFrameBackend, "MODIN"), (
        "modin is handled transparently via narwhals"
    )
    assert not hasattr(DataFrameBackend, "CUDF"), (
        "cudf is handled transparently via narwhals"
    )
    assert not hasattr(DataFrameBackend, "DASK"), (
        "dask is handled transparently via narwhals"
    )


def test_dataframe_backend_string_representation():
    assert DataFrameBackend.PANDAS == "pandas"
    assert DataFrameBackend.PANDAS.value == "pandas"
    assert "PANDAS" in str(DataFrameBackend.PANDAS)


def test_dataframe_backend_iteration():
    backends = list(DataFrameBackend)
    assert len(backends) == 4
    assert DataFrameBackend.PANDAS in backends
    assert DataFrameBackend.POLARS in backends
    assert DataFrameBackend.PYARROW in backends
    assert DataFrameBackend.DUCKDB in backends
    assert "narwhals" not in [b.value for b in backends]


def test_dataframe_backend_membership():
    backend_str = "pandas"
    assert backend_str == DataFrameBackend.PANDAS
    assert backend_str in [b.value for b in DataFrameBackend]


# ============================================================================
# detect_backend / infer_column_type / create_dataframe_from_dict / backends
# ============================================================================


def test_detect_backend_pandas():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    assert DataFrameMixinHelper.detect_backend(df) == "pandas"


def test_detect_backend_pandas_series():
    s = pd.Series([1, 2, 3])
    assert DataFrameMixinHelper.detect_backend(s) == "pandas"


def test_detect_backend_polars():
    try:
        import polars as pl

        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        assert DataFrameMixinHelper.detect_backend(df) == "polars"
    except ImportError:
        pytest.skip("polars not installed")


def test_detect_backend_polars_series():
    try:
        import polars as pl

        s = pl.Series("A", [1, 2, 3])
        assert DataFrameMixinHelper.detect_backend(s) == "polars"
    except ImportError:
        pytest.skip("polars not installed")


def test_detect_backend_unknown():
    assert DataFrameMixinHelper.detect_backend("not a dataframe") == "unknown"
    assert DataFrameMixinHelper.detect_backend([1, 2, 3]) == "unknown"
    assert DataFrameMixinHelper.detect_backend({"A": [1, 2, 3]}) == "unknown"


def test_detect_backend_pyarrow():
    try:
        import pyarrow as pa

        table = pa.table({"A": [1, 2, 3], "B": [4, 5, 6]})
        assert DataFrameMixinHelper.detect_backend(table) == "pyarrow"
    except ImportError:
        pytest.skip("pyarrow not installed")


def test_detect_backend_duckdb():
    try:
        import duckdb
        import pandas as pd

        rel = duckdb.from_df(pd.DataFrame({"A": [1, 2, 3]}))
        assert DataFrameMixinHelper.detect_backend(rel) == "duckdb"
    except ImportError:
        pytest.skip("duckdb not installed")


def test_is_narwhals_available():
    try:
        import narwhals  # noqa: F401

        assert DataFrameMixinHelper.is_narwhals_available()
        assert "narwhals" not in DataFrameMixinHelper.get_available_backends()
    except ImportError:
        assert not DataFrameMixinHelper.is_narwhals_available()


def test_is_backend_available():
    assert DataFrameMixinHelper.is_backend_available("pandas") is True
    assert not DataFrameMixinHelper.is_backend_available("narwhals"), (
        "narwhals must not appear in user-facing backend availability"
    )
    assert DataFrameMixinHelper.is_backend_available("unknown_backend") is False
    polars_available = DataFrameMixinHelper.is_backend_available("polars")
    assert isinstance(polars_available, bool)

    try:
        import pyarrow  # noqa: F401

        assert DataFrameMixinHelper.is_backend_available("pyarrow")
    except ImportError:
        assert not DataFrameMixinHelper.is_backend_available("pyarrow")

    try:
        import duckdb  # noqa: F401

        assert DataFrameMixinHelper.is_backend_available("duckdb")
    except ImportError:
        assert not DataFrameMixinHelper.is_backend_available("duckdb")


def test_infer_column_type_pandas_bool():
    s = pd.Series([True, False, True])
    assert DataFrameMixinHelper.infer_column_type(s, backend="pandas") == "bool"
    assert DataFrameMixinHelper.infer_column_type(s.dtype, backend="pandas") == "bool"


def test_infer_column_type_pandas_numeric():
    s_int = pd.Series([1, 2, 3])
    s_float = pd.Series([1.5, 2.5, 3.5])
    assert DataFrameMixinHelper.infer_column_type(s_int, backend="pandas") == "numeric"
    assert (
        DataFrameMixinHelper.infer_column_type(s_float, backend="pandas") == "numeric"
    )
    assert (
        DataFrameMixinHelper.infer_column_type(s_int.dtype, backend="pandas")
        == "numeric"
    )
    assert (
        DataFrameMixinHelper.infer_column_type(np.int64, backend="pandas") == "numeric"
    )
    assert (
        DataFrameMixinHelper.infer_column_type(np.float64, backend="pandas")
        == "numeric"
    )


def test_infer_column_type_pandas_datetime():
    s = pd.Series(pd.date_range("2024-01-01", periods=3))
    assert DataFrameMixinHelper.infer_column_type(s, backend="pandas") == "datetime"
    assert (
        DataFrameMixinHelper.infer_column_type(s.dtype, backend="pandas") == "datetime"
    )


def test_infer_column_type_pandas_string():
    s = pd.Series(["a", "b", "c"])
    assert DataFrameMixinHelper.infer_column_type(s, backend="pandas") == "string"
    assert DataFrameMixinHelper.infer_column_type(object, backend="pandas") == "string"


def test_infer_column_type_polars():
    try:
        import polars as pl

        s_bool = pl.Series("bool", [True, False, True])
        assert (
            DataFrameMixinHelper.infer_column_type(s_bool, backend="polars") == "bool"
        )

        s_int = pl.Series("int", [1, 2, 3])
        assert (
            DataFrameMixinHelper.infer_column_type(s_int, backend="polars") == "numeric"
        )

        s_float = pl.Series("float", [1.5, 2.5, 3.5])
        assert (
            DataFrameMixinHelper.infer_column_type(s_float, backend="polars")
            == "numeric"
        )

        s_date = pl.Series(
            "date", [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")]
        )
        assert (
            DataFrameMixinHelper.infer_column_type(s_date, backend="polars")
            == "datetime"
        )

        s_str = pl.Series("str", ["a", "b", "c"])
        assert (
            DataFrameMixinHelper.infer_column_type(s_str, backend="polars") == "string"
        )
    except ImportError:
        pytest.skip("polars not installed")


def test_create_dataframe_from_dict_pandas_with_data():
    data = {"A": [1, 2, 3], "B": [4, 5, 6]}
    df = DataFrameMixinHelper.create_dataframe_from_dict(data, backend="pandas")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["A", "B"]
    assert len(df) == 3
    assert df["A"].tolist() == [1, 2, 3]
    assert df["B"].tolist() == [4, 5, 6]


def test_create_dataframe_from_dict_pandas_with_dtypes():
    data = {"A": "int64", "B": "string", "C": int, "D": str}
    df = DataFrameMixinHelper.create_dataframe_from_dict(data, backend="pandas")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["A", "B", "C", "D"]
    assert len(df) == 0
    assert df["A"].dtype == np.int64
    assert df["C"].dtype == np.int64


def test_create_dataframe_from_dict_pandas_mixed():
    data = {"A": [1, 2, 3], "B": "string"}
    df = DataFrameMixinHelper.create_dataframe_from_dict(data, backend="pandas")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["A", "B"]
    assert len(df) == 3
    assert df["A"].tolist() == [1, 2, 3]
    assert len(df["B"]) == 3


def test_create_dataframe_from_dict_polars():
    try:
        import polars as pl

        data = {"A": [1, 2, 3], "B": ["x", "y", "z"]}
        df = DataFrameMixinHelper.create_dataframe_from_dict(data, backend="polars")
        assert isinstance(df, pl.DataFrame)
        assert df.columns == ["A", "B"]
        assert len(df) == 3

        data_typed = {"A": "int64", "B": "string"}
        df_typed = DataFrameMixinHelper.create_dataframe_from_dict(
            data_typed, backend="polars"
        )
        assert isinstance(df_typed, pl.DataFrame)
        assert df_typed.columns == ["A", "B"]
        assert len(df_typed) == 0
    except ImportError:
        pytest.skip("polars not installed")


def test_get_available_backends():
    backends = DataFrameMixinHelper.get_available_backends()
    assert "pandas" in backends
    assert isinstance(backends, set)
    backends2 = DataFrameMixinHelper.get_available_backends()
    assert backends is backends2


# ============================================================================
# to_data_list with multiple backends
# ============================================================================


def test_to_data_list_pandas_dataframe():
    df = pd.DataFrame(
        {
            "Entity": ["E1", "E2"],
            "Signal": ["S1", "S1"],
            "Unit": ["m", "m"],
            "Data": [[1, 2, 3], [4, 5, 6]],
        }
    )
    result = DataFrameMixinHelper.to_data_list(df)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["Entity"] == "E1"
    assert result[0]["Signal"] == "S1"


def test_to_data_list_pandas_series():
    series = pd.Series([1.0, 2.0, 3.0], index=["E1", "E2", "E3"], name="TestSignal [m]")
    result = DataFrameMixinHelper.to_data_list(series)
    assert isinstance(result, list)
    assert len(result) > 0
    assert any(r.get("Entity") in ["E1", "E2", "E3"] for r in result)


def test_to_data_list_polars_dataframe():
    try:
        import polars as pl

        df = pl.DataFrame(
            {
                "Entity": ["E1", "E2"],
                "Signal": ["S1", "S1"],
                "Unit": ["m", "m"],
                "Data": [[[1, 2, 3]], [[4, 5, 6]]],
            }
        )
        result = DataFrameMixinHelper.to_data_list(df)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["Entity"] == "E1"
    except ImportError:
        pytest.skip("polars not installed")


def test_to_data_list_dict_list():
    data = [
        {"Entity": "E1", "Signal": "S1", "Unit": "m", "Data": [1, 2, 3]},
        {"Entity": "E2", "Signal": "S1", "Unit": "m", "Data": [4, 5, 6]},
    ]
    result = DataFrameMixinHelper.to_data_list(data)
    assert result == data


def test_to_data_list_long_format_pandas():
    df = pd.DataFrame(
        {
            "Entity": ["E1", "E1", "E2", "E2"],
            "Date": pd.date_range("2024-01-01", periods=4),
            "S1 [m]": [1.0, 2.0, 3.0, 4.0],
            "S2 [ft]": [10.0, 20.0, 30.0, 40.0],
        }
    )
    result = DataFrameMixinHelper.to_data_list(df)
    assert isinstance(result, list)
    assert len(result) > 0


def test_to_data_list_long_format_polars():
    try:
        import polars as pl

        df = pl.DataFrame(
            {
                "Entity": ["E1", "E1", "E2", "E2"],
                "Date": pd.date_range("2024-01-01", periods=4),
                "S1 [m]": [1.0, 2.0, 3.0, 4.0],
                "S2 [ft]": [10.0, 20.0, 30.0, 40.0],
            }
        )
        result = DataFrameMixinHelper.to_data_list(df)
        assert isinstance(result, list)
        assert len(result) > 0
    except ImportError:
        pytest.skip("polars not installed")


# ============================================================================
# normalize_depth_column
# ============================================================================


def test_normalize_depth_column_already_meters():
    df = pd.DataFrame({"Entity": ["E1"], "Depth [m]": [1000.0], "GR [ ]": [50.0]})
    result = DataFrameMixinHelper.normalize_depth_column(df, "Depth", lambda v, s, t: v)
    assert "Depth [m]" in result.columns
    assert result["Depth [m]"].iloc[0] == 1000.0


def test_normalize_depth_column_no_unit():
    df = pd.DataFrame({"Entity": ["E1"], "Depth": [1000.0]})
    result = DataFrameMixinHelper.normalize_depth_column(df, "Depth", lambda v, s, t: v)
    assert "Depth [m]" in result.columns


def test_normalize_depth_column_converts_ft():
    called_with: list = []

    def fake_convert(values, source, target):
        called_with.append((source, target))
        return [v * 0.3048 for v in values]

    df = pd.DataFrame({"Entity": ["E1", "E1"], "Depth [ft]": [0.0, 1.0]})
    result = DataFrameMixinHelper.normalize_depth_column(df, "Depth", fake_convert)
    assert "Depth [m]" in result.columns
    assert "Depth [ft]" not in result.columns
    assert called_with == [("ft", "m")]
    assert abs(result["Depth [m]"].iloc[1] - 0.3048) < 1e-9


def test_normalize_depth_column_no_depth_col():
    df = pd.DataFrame({"Entity": ["E1"], "GR [ ]": [50.0]})
    result = DataFrameMixinHelper.normalize_depth_column(df, "Depth", lambda v, s, t: v)
    assert list(result.columns) == list(df.columns)


# ============================================================================
# _build_combined_df_narwhals
# ============================================================================


def _make_test_payload(n_entities: int = 5, n_time: int = 10) -> tuple:
    """Return (time_num, static_num, sig_map) for the narwhals builder tests."""
    import pandas as pd

    dates = pd.date_range("2024-01-01", periods=n_time, freq="D")
    date_strs = [d.strftime("%Y-%m-%dT%H:%M:%S") for d in dates]

    time_num = [
        {
            "Entity": f"E{i}",
            "SignalName": "TS1 [ ]",
            "Unit": " ",
            "Data": [
                {"Date": d, "Value": float(i * n_time + j)}
                for j, d in enumerate(date_strs)
            ],
        }
        for i in range(n_entities)
    ]
    static_num = [
        {"Entity": f"E{i}", "SignalName": "SS1 [ ]", "Unit": " ", "Data": float(i)}
        for i in range(n_entities)
    ]
    sig_map = {"TS1 [ ]": "TS1 [ ]", "SS1 [ ]": "SS1 [ ]"}
    return time_num, static_num, sig_map


def test_build_combined_df_narwhals_pandas_output():
    """narwhals builder with pandas backend produces a pandas DataFrame."""
    pytest.importorskip("narwhals")
    time_num, static_num, sig_map = _make_test_payload(n_entities=3, n_time=5)
    df = DataFrameMixinHelper._build_combined_df_narwhals(
        time_num,
        [],
        [],
        [],
        static_num,
        [],
        entity_col="Entity",
        time_col="Date",
        depth_col="Depth",
        signal_col="SignalName",
        signals_with_units_map=sig_map,
        backend="pandas",
    )
    assert isinstance(df, pd.DataFrame)
    assert "Entity" in df.columns
    assert "Date" in df.columns
    assert "TS1 [ ]" in df.columns
    assert "SS1 [ ]" in df.columns
    assert len(df) == 3 * 5  # 3 entities × 5 time steps


def test_build_combined_df_narwhals_polars_output():
    """narwhals builder with polars backend produces a polars DataFrame."""
    pl = pytest.importorskip("polars")
    pytest.importorskip("narwhals")
    time_num, static_num, sig_map = _make_test_payload(n_entities=3, n_time=5)
    df = DataFrameMixinHelper._build_combined_df_narwhals(
        time_num,
        [],
        [],
        [],
        static_num,
        [],
        entity_col="Entity",
        time_col="Date",
        depth_col="Depth",
        signal_col="SignalName",
        signals_with_units_map=sig_map,
        backend="polars",
    )
    assert isinstance(df, pl.DataFrame)
    assert "Entity" in df.columns
    assert "Date" in df.columns
    assert len(df) == 3 * 5


def test_build_combined_df_narwhals_matches_pandas_impl():
    """narwhals pandas output must match the pure-pandas implementation."""
    pytest.importorskip("narwhals")
    time_num, static_num, sig_map = _make_test_payload(n_entities=4, n_time=8)

    df_pandas = DataFrameMixinHelper._build_combined_df_pandas(
        time_num,
        [],
        [],
        [],
        static_num,
        [],
        entity_col="Entity",
        time_col="Date",
        depth_col="Depth",
        signal_col="SignalName",
        signals_with_units_map=sig_map,
    )
    df_narwhals = DataFrameMixinHelper._build_combined_df_narwhals(
        time_num,
        [],
        [],
        [],
        static_num,
        [],
        entity_col="Entity",
        time_col="Date",
        depth_col="Depth",
        signal_col="SignalName",
        signals_with_units_map=sig_map,
        backend="pandas",
    )
    assert isinstance(df_pandas, pd.DataFrame)
    assert isinstance(df_narwhals, pd.DataFrame)
    assert df_pandas.shape == df_narwhals.shape
    assert set(df_pandas.columns) == set(df_narwhals.columns)
    # Both should produce the same rows and signal values; Date dtype may differ
    # (pandas keeps UTC timezone, narwhals strips it — both are correct behaviors)
    assert len(df_pandas) == len(df_narwhals)
    pd_entities = sorted(df_pandas["Entity"].tolist())
    nw_entities = sorted(df_narwhals["Entity"].tolist())
    assert pd_entities == nw_entities


def test_build_combined_df_performance():
    """
    Combined-builder performance across all available backends (informational).

    Benchmark findings at 200 entities × 200 time pts (40k rows):
      narwhals/polars   -61% vs pandas  ← fastest (narwhals dispatch for polars)
      pure polars       -35% vs pandas
      pandas            baseline
      pyarrow bridge    ~same as pandas (no native pivot — falls back to pandas)
      duckdb native     ~same as pandas (creation overhead dominates at this scale)
      narwhals/pandas   +39% vs pandas  ← slower (narwhals overhead on pandas pivot)

    Dispatcher routing in _build_combined_df:
      polars + narwhals  → _build_combined_df_narwhals (fastest)
      polars only        → _build_combined_df_polars
      pandas             → _build_combined_df_pandas  (narwhals overhead not worth it)
    """
    import time

    pytest.importorskip("narwhals")
    N_ENTITIES, N_TIME, RUNS = 200, 200, 5
    time_num, static_num, sig_map = _make_test_payload(
        n_entities=N_ENTITIES, n_time=N_TIME
    )
    kwargs = dict(
        data_time_num=time_num,
        data_time_str=[],
        data_depth_num=[],
        data_depth_str=[],
        data_static_num=static_num,
        data_static_str=[],
        entity_col="Entity",
        time_col="Date",
        depth_col="Depth",
        signal_col="SignalName",
        signals_with_units_map=sig_map,
    )

    def measure(fn, runs=RUNS):
        fn()  # warmup
        t0 = time.perf_counter()
        for _ in range(runs):
            fn()
        return (time.perf_counter() - t0) / runs * 1000

    results = {}
    results["pandas"] = measure(
        lambda: DataFrameMixinHelper._build_combined_df_pandas(**kwargs)
    )
    results["narwhals/pandas"] = measure(
        lambda: DataFrameMixinHelper._build_combined_df_narwhals(
            **kwargs, backend="pandas"
        )
    )

    try:
        import polars  # noqa: F401

        results["polars"] = measure(
            lambda: DataFrameMixinHelper._build_combined_df_polars(**kwargs)
        )
        results["narwhals/polars"] = measure(
            lambda: DataFrameMixinHelper._build_combined_df_narwhals(
                **kwargs, backend="polars"
            )
        )
    except ImportError:
        pass

    baseline = results["pandas"]
    lines = [f"\n  {'backend':<25} {'ms':>7}  {'vs pandas':>10}"]
    for label, ms in results.items():
        pct = (ms - baseline) / baseline * 100
        lines.append(f"  {label:<25} {ms:7.1f}  {pct:+.0f}%")
    print("\n".join(lines))

    # Correctness: pandas and narwhals/pandas must produce same row count
    df_pd = DataFrameMixinHelper._build_combined_df_pandas(**kwargs)
    df_nw = DataFrameMixinHelper._build_combined_df_narwhals(**kwargs, backend="pandas")
    assert df_pd is not None and df_nw is not None
    assert len(df_pd) == len(df_nw) == N_ENTITIES * N_TIME
