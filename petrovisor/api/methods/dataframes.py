from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
    Tuple,
    Iterable,
    Set,
    cast,
)

import io
import re
import copy
from datetime import datetime
import pickle
from enum import Enum
import pandas as pd
import numpy as np

from petrovisor.api.enums.internal_dtypes import SignalType
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
    SupportsDataFrames,
)


# DataFrame Backend Enum
class DataFrameBackend(str, Enum):
    """
    Supported user-facing DataFrame backends.

    Narwhals is NOT listed here — it is used internally as a routing/dispatch
    layer when available (see DataFrameMixinHelper.is_narwhals_available).
    The choice of whether to route through narwhals is automatic; callers
    never need to specify it.

    Modin, cuDF, and Dask are also not listed: they are pandas-compatible
    libraries that narwhals already handles transparently.  Users who work
    with those DataFrames can pass them directly — narwhals will unwrap them —
    but the SDK does not advertise or maintain explicit code paths for them.

    Values
    ------
    PANDAS : str
        Pandas DataFrame — default and always available.
    POLARS : str
        Polars DataFrame (requires polars package).
    PYARROW : str
        PyArrow Table (requires pyarrow).
    DUCKDB : str
        DuckDB relation (requires duckdb).
    """

    PANDAS = "pandas"
    POLARS = "polars"
    PYARROW = "pyarrow"
    DUCKDB = "duckdb"


# DataFrames mixin helper
class DataFrameMixinHelper:
    """DataFrame utilities and table-format conversion methods."""

    # Reserved column name constants
    COLUMN_ENTITY = "Entity"
    COLUMN_ALIAS = "Alias"
    COLUMN_DATE = "Date"
    COLUMN_DEPTH = "Depth"

    # Backend availability cache (populated on first access)
    _available_backends: Optional[Set[str]] = None

    @staticmethod
    def is_narwhals_available() -> bool:
        """Return True when narwhals is installed.

        Narwhals is used internally as a routing/dispatch layer — it is not a
        user-facing backend.  Use this instead of
        ``is_backend_available("narwhals")`` everywhere in internal logic.
        """
        try:
            import narwhals  # type: ignore[import-untyped]  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def get_available_backends() -> Set[str]:
        """Return the set of user-facing backends that are currently installed.

        Narwhals is intentionally excluded — it is an internal dispatch layer,
        not a user-facing backend.  Use ``is_narwhals_available()`` to check
        whether narwhals is present for internal routing decisions.

        Returns
        -------
        set[str]
            Subset of DataFrameBackend values that are importable right now.
            'pandas' is always present.
        """
        # Use cached result if available
        if DataFrameMixinHelper._available_backends is not None:
            return DataFrameMixinHelper._available_backends

        backends = {"pandas"}  # pandas is always available (required dependency)

        # Check for polars
        try:
            import polars as pl  # type: ignore[import-untyped]  # noqa: F401

            backends.add(DataFrameBackend.POLARS)
        except ImportError:
            pass

        # Check for PyArrow
        try:
            import pyarrow  # type: ignore[import-untyped]  # noqa: F401

            backends.add(DataFrameBackend.PYARROW)
        except ImportError:
            pass

        # Check for DuckDB
        try:
            import duckdb  # type: ignore[import-untyped]  # noqa: F401

            backends.add(DataFrameBackend.DUCKDB)
        except ImportError:
            pass

        # Cache the result
        DataFrameMixinHelper._available_backends = backends
        return backends

    @staticmethod
    def is_backend_available(backend: str) -> bool:
        """
        Check if a specific backend is available.

        Parameters
        ----------
        backend : str
            Backend name to check

        Returns
        -------
        bool
            True if backend is available, False otherwise

        Examples
        --------
        >>> if DataFrameMixinHelper.is_backend_available('polars'):
        ...     df = api.load_signals_data(..., backend='polars')
        """
        return backend in DataFrameMixinHelper.get_available_backends()

    @staticmethod
    def detect_backend(df) -> str:
        """
        Detect DataFrame backend from input type.

        Parameters
        ----------
        df : DataFrame
            DataFrame of any backend type

        Returns
        -------
        str
            Backend name: 'pandas', 'polars', 'pyarrow', 'duckdb', or 'unknown'.
            Narwhals, modin, cuDF, and dask are intentionally excluded — they
            are either internal dispatch layers (narwhals) or pandas-compatible
            libraries handled transparently by narwhals.
        """
        # Check for pandas (most common)
        if isinstance(df, (pd.DataFrame, pd.Series)):
            return DataFrameBackend.PANDAS

        # Check for polars
        try:
            import polars as pl  # type: ignore[import-untyped]

            if isinstance(df, (pl.DataFrame, pl.Series)):
                return DataFrameBackend.POLARS
        except ImportError:
            pass

        # Check for PyArrow
        try:
            import pyarrow as pa  # type: ignore[import-untyped]

            if isinstance(df, pa.Table):
                return DataFrameBackend.PYARROW
        except ImportError:
            pass

        # Check for DuckDB
        try:
            import duckdb  # type: ignore[import-untyped]

            if isinstance(df, duckdb.DuckDBPyRelation):
                return DataFrameBackend.DUCKDB
        except ImportError:
            pass

        return "unknown"

    @staticmethod
    def is_polars_backend(backend: str) -> bool:
        """Return True when backend is 'polars' and the library is installed."""
        return (
            backend == DataFrameBackend.POLARS
            and DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS)
        )

    @staticmethod
    def df_drop_column(df: Any, col: str, backend: str) -> Any:
        """Drop a column by name — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            return nw.to_native(nw.from_native(df).drop([col]))
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df.drop(col)
        return df.drop(columns=[col])

    @staticmethod
    def df_merge(
        df_left: Any,
        df_right: Any,
        on: Union[str, List[str]],
        backend: str,
    ) -> Any:
        """Full/outer join two DataFrames on key column(s) — polars/pandas (narwhals lacks coalesce)."""
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df_left.join(df_right, on=on, how="full", coalesce=True)
        return pd.merge(df_left, df_right, on=on)

    @staticmethod
    def df_get_column_names(df: Any) -> List[str]:
        """Return column names as a plain list of strings for any supported backend."""
        # PyArrow Table uses .column_names; pandas/polars use .columns
        if hasattr(df, "column_names"):
            return list(df.column_names)
        return list(df.columns)

    @staticmethod
    def df_select_columns(df: Any, columns: List[str], backend: str) -> Any:
        """Select/reorder columns — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            return nw.to_native(nw.from_native(df).select(columns))
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df.select(columns)
        return df[columns]

    @staticmethod
    def df_rename_column(df: Any, old_name: str, new_name: str, backend: str) -> Any:
        """Rename a single column — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            return nw.to_native(nw.from_native(df).rename({old_name: new_name}))
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df.rename({old_name: new_name})
        return df.rename(columns={old_name: new_name})

    @staticmethod
    def df_head(df: Any, n: int, backend: str) -> Any:
        """Return the first n rows — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            return nw.to_native(nw.from_native(df).head(n))
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df.head(n)
        return df.iloc[:n]

    @staticmethod
    def df_fill_null(df: Any, value: Any, backend: str) -> Any:
        """Fill numeric null/NaN values with a scalar — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            ndf = nw.from_native(df)
            num_cols = [c for c in ndf.columns if ndf[c].dtype.is_numeric()]
            if not num_cols:
                return df
            return nw.to_native(
                ndf.with_columns([nw.col(c).fill_null(value) for c in num_cols])
            )
        if DataFrameMixinHelper.is_polars_backend(backend):
            import polars as pl  # type: ignore[import-untyped]

            num_cols = [c for c, t in zip(df.columns, df.dtypes) if t.is_numeric()]
            return (
                df.with_columns([pl.col(c).fill_null(value) for c in num_cols])
                if num_cols
                else df
            )
        num_cols = df.select_dtypes(include="number").columns.tolist()
        return df.fillna({c: value for c in num_cols}) if num_cols else df

    @staticmethod
    def df_fill_null_string(df: Any, value: str, backend: str) -> Any:
        """Fill string/object null values — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            ndf = nw.from_native(df)
            str_cols = [c for c in ndf.columns if ndf[c].dtype == nw.String]
            if not str_cols:
                return df
            return nw.to_native(
                ndf.with_columns([nw.col(c).fill_null(value) for c in str_cols])
            )
        if DataFrameMixinHelper.is_polars_backend(backend):
            import polars as pl  # type: ignore[import-untyped]

            str_cols = [
                c for c, t in zip(df.columns, df.dtypes) if t in (pl.String, pl.Utf8)
            ]
            return (
                df.with_columns([pl.col(c).fill_null(value) for c in str_cols])
                if str_cols
                else df
            )
        str_cols = df.select_dtypes(include="object").columns.tolist()
        return df.fillna({c: value for c in str_cols}) if str_cols else df

    @staticmethod
    def df_forward_fill(df: Any, backend: str) -> Any:
        """Forward-fill (ffill) nulls across all columns — narwhals-first, pandas fallback."""
        if DataFrameMixinHelper.is_narwhals_available():
            import narwhals as nw  # type: ignore[import-untyped]

            ndf = nw.from_native(df)
            return nw.to_native(
                ndf.with_columns(
                    [nw.col(c).fill_null(strategy="forward") for c in ndf.columns]
                )
            )
        if DataFrameMixinHelper.is_polars_backend(backend):
            return df.fill_null(strategy="forward")
        return df.ffill()

    @staticmethod
    def df_interpolate(df: Any, backend: str) -> Any:
        """Linear interpolation of numeric nulls — polars/pandas only (narwhals lacks Expr.interpolate)."""
        if DataFrameMixinHelper.is_polars_backend(backend):
            import polars as pl  # type: ignore[import-untyped]

            num_cols = [c for c, t in zip(df.columns, df.dtypes) if t.is_numeric()]
            return (
                df.with_columns([pl.col(c).interpolate() for c in num_cols])
                if num_cols
                else df
            )
        return df.interpolate(method="linear")

    @staticmethod
    def df_to_backend(df: Any, backend: str) -> Any:
        """Convert df to the requested backend type if it isn't already."""
        import pandas as _pd

        if (
            backend == DataFrameBackend.POLARS
            and DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS)
        ):
            import polars as pl  # type: ignore[import-untyped]

            if isinstance(df, _pd.DataFrame):
                return pl.from_pandas(df)
            return df  # already polars

        if backend == DataFrameBackend.PANDAS and not isinstance(df, _pd.DataFrame):
            # polars → pandas fallback
            detected = DataFrameMixinHelper.detect_backend(df)
            if detected == DataFrameBackend.POLARS:
                return df.to_pandas()

        return df

    @staticmethod
    def infer_column_type(
        dtype_or_series, backend: str = DataFrameBackend.PANDAS
    ) -> str:
        """
        Infer column type from a dtype or Series.

        Parameters
        ----------
        dtype_or_series : dtype | Series
            Dtype to check (pandas dtype, polars dtype) or a Series
        backend : str, default 'pandas'
            DataFrame backend

        Returns
        -------
        str
            Column type: 'bool', 'numeric', 'datetime', or 'string'
        """
        if backend == DataFrameBackend.PANDAS:
            from pandas.api.types import (
                is_bool_dtype,
                is_numeric_dtype,
                is_datetime64_any_dtype,
            )

            # The pandas dtype checking functions work on both Series and dtypes
            if is_bool_dtype(dtype_or_series):
                return "bool"
            elif is_numeric_dtype(dtype_or_series):
                return "numeric"
            elif is_datetime64_any_dtype(dtype_or_series):
                return "datetime"
            else:
                return "string"

        elif backend == DataFrameBackend.POLARS:
            try:
                import polars as pl  # type: ignore[import-untyped]

                # Extract dtype if it's a Series
                if hasattr(dtype_or_series, "dtype"):
                    dtype = dtype_or_series.dtype
                else:
                    dtype = dtype_or_series

                if dtype == pl.Boolean:
                    return "bool"
                elif dtype in (
                    pl.Int8,
                    pl.Int16,
                    pl.Int32,
                    pl.Int64,
                    pl.UInt8,
                    pl.UInt16,
                    pl.UInt32,
                    pl.UInt64,
                    pl.Float32,
                    pl.Float64,
                ):
                    return "numeric"
                elif dtype in (pl.Date, pl.Datetime, pl.Duration, pl.Time):
                    return "datetime"
                else:
                    return "string"
            except ImportError:
                # Fallback to pandas logic if polars not available
                return "string"

        return "string"  # default

    @staticmethod
    def create_dataframe_from_dict(
        data: Dict[str, Any], backend: str = DataFrameBackend.PANDAS, **kwargs
    ) -> Union[pd.DataFrame, Any]:
        """
        Create DataFrame from dictionary of columns.

        Parameters
        ----------
        data : dict
            Dictionary of {column_name: values}. Values can be:
            - List/array of values
            - String/type: creates empty Series with that dtype
        backend : str, default 'pandas'
            DataFrame backend ('pandas', 'polars')

        Returns
        -------
        DataFrame
            DataFrame of specified backend type

        Examples
        --------
        >>> data = {"A": [1, 2, 3], "B": [4, 5, 6]}
        >>> df = DataFrameMixinHelper.create_dataframe_from_dict(data)

        >>> data = {"A": "int64", "B": "string"}
        >>> df = DataFrameMixinHelper.create_dataframe_from_dict(data)
        """
        if backend == DataFrameBackend.PANDAS:
            # Create DataFrame with proper handling of dtypes
            df = pd.DataFrame()
            for col_name, values in data.items():
                if isinstance(values, (str, type)):
                    # Empty column with specific dtype
                    df[col_name] = pd.Series(dtype=values)
                else:
                    # Column with data
                    df[col_name] = values
            return df

        elif backend == DataFrameBackend.POLARS:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl  # type: ignore[import-untyped]

                # For polars, we need to convert dtype strings to polars dtypes
                if any(isinstance(v, (str, type)) for v in data.values()):
                    # Has dtype specifications - need to create schema
                    schema = {}
                    actual_data = {}
                    for col_name, values in data.items():
                        if isinstance(values, str):
                            # Map pandas dtype strings to polars
                            dtype_map = {
                                "int64": pl.Int64,
                                "int32": pl.Int32,
                                "float64": pl.Float64,
                                "float32": pl.Float32,
                                "string": pl.String,
                                "str": pl.String,
                                "object": pl.String,
                                "bool": pl.Boolean,
                                "datetime64": pl.Datetime,
                            }
                            schema[col_name] = dtype_map.get(values, pl.String)
                            actual_data[col_name] = []  # Empty column
                        elif isinstance(values, type):
                            # Python type
                            if values is int:
                                schema[col_name] = pl.Int64
                            elif values is float:
                                schema[col_name] = pl.Float64
                            elif values is str:
                                schema[col_name] = pl.String
                            elif values is bool:
                                schema[col_name] = pl.Boolean
                            else:
                                schema[col_name] = pl.String
                            actual_data[col_name] = []  # Empty column
                        else:
                            actual_data[col_name] = values
                    return pl.DataFrame(actual_data, schema=schema)
                else:
                    # Simple case - all data, no dtype specs
                    return pl.DataFrame(data)
            else:
                # Fallback to pandas if polars not available
                return DataFrameMixinHelper.create_dataframe_from_dict(
                    data, backend=DataFrameBackend.PANDAS
                )

        else:
            # Unknown backend - default to pandas
            return DataFrameMixinHelper.create_dataframe_from_dict(
                data, backend=DataFrameBackend.PANDAS
            )

    # set DataFrame indices
    @staticmethod
    def set_dataframe_index(
        df: pd.DataFrame,
        indices: List[str],
        inplace: bool = False,
        add_default_index: bool = False,
        default_index_name: str = "index",
        **kwargs,
    ):
        """
        Set DataFrame index

        Parameters
        ----------
        df : DataFrame
            DataFrame
        indices : list
            Columns to use as indices
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        add_default_index : bool, default False
            Whether to add default index column
        default_index_name : str, default 'index'
            Default index name

        Returns
        -------
        Tuple (DataFrame, default_index_column)
        """
        # define working DataFrame
        df_with_index = df if inplace else df.copy()
        # get column indices
        idx = [item for item in indices if item in df.columns]
        # add default index
        index_col = ""
        if add_default_index:
            # get index name which does not match any column name
            def get_default_index_name(df: pd.DataFrame):
                index_name = default_index_name
                i = 0
                while index_name in df.columns:
                    index_name = f"{default_index_name}_{i}"
                    i += 1
                return index_name

            index_col = get_default_index_name(df)
            df_with_index[index_col] = df_with_index.index
            idx.insert(0, index_col)
        # set indices
        df_with_index = df_with_index.set_index(idx)
        return df_with_index, index_col

    # create DataFrame from list
    @staticmethod
    def create_dataframe_from_list(data: List[str], **kwargs) -> Optional[pd.DataFrame]:
        """
        Create DataFrame from list of tabulated string

        Parameters
        ----------
        data : list
            List of tabulated strings
        """
        if len(data) < 1:
            return None

        # Try with default C engine first
        try:
            return pd.read_csv(io.StringIO("\n".join(data)), delimiter="\t", **kwargs)
        except pd.errors.ParserError as e:
            # Fall back to Python engine which is more flexible with inconsistent fields
            # and can handle tabs within field values better
            import warnings

            warnings.warn(
                f"Inconsistent field count detected in tab-delimited data: {e}. "
                "Using Python parser engine for more flexible parsing.",
                RuntimeWarning,
                stacklevel=2,
            )

            # Build parser options based on pandas version
            parser_options = {
                "delimiter": "\t",
                "engine": "python",
                "quoting": 3,  # csv.QUOTE_NONE - don't interpret quotes
            }

            # pandas 1.3+ uses on_bad_lines, older versions use error_bad_lines
            try:
                return pd.read_csv(
                    io.StringIO("\n".join(data)),
                    on_bad_lines="skip",
                    **parser_options,
                    **kwargs,
                )
            except TypeError:
                # Fallback for pandas < 1.3
                return pd.read_csv(
                    io.StringIO("\n".join(data)),
                    error_bad_lines=False,
                    **parser_options,
                    **kwargs,
                )

    # remove entity name from column names
    @staticmethod
    def remove_entities_from_columns(columns: Iterable[str]) -> List[str]:
        """
        Remove entity name from column names

        Parameters
        ----------
        columns : list
            Column names
        """
        return [
            c[1] if len(c) > 1 else c[0] for c in (col.split(" : ") for col in columns)
        ]

    # extract entity name from column names
    @staticmethod
    def get_entities_from_columns(columns: Iterable[str]) -> List[str]:
        """
        Extract entity name from column names

        Parameters
        ----------
        columns : list
            Column names
        """
        return [
            c[0] if len(c) > 1 else "" for c in (col.split(" : ") for col in columns)
        ]

    # get list of unique non-empty names
    @staticmethod
    def get_unique_non_empty_names(x: List[str]) -> List[str]:
        """
        get list of unique non-empty names

        Parameters
        ----------
        x : list
            List of names
        """
        return list(set([e for e in x if e]))

    # ========================================================================
    # DataFrame → Entity/Signal/Unit/Data conversion methods
    # ========================================================================

    @staticmethod
    def parse_signal_column(col: str) -> Tuple[str, str]:
        """Parse 'signal name [unit]' → ('signal name', 'unit').

        Blank unit brackets like '[ ]' return ' ' (single space) — the canonical
        dimensionless unit — truthy so that unit-fill logic is not triggered.
        """
        if "[" in col and col.endswith("]"):
            bracket_idx = col.rfind("[")
            unit = col[bracket_idx + 1 : -1].strip()
            return col[:bracket_idx].strip(), unit if unit else " "
        return col, " "

    @staticmethod
    def normalize_depth_column(
        df: pd.DataFrame,
        depth_col: str,
        convert_fn: Any,
    ) -> pd.DataFrame:
        """Convert depth values to meters and rename column to 'Depth [m]'.

        Looks for any column whose base name matches *depth_col* (e.g. 'Depth [ft]',
        'Depth [m]', plain 'Depth').  If the unit is already 'm' (or blank / absent)
        the DataFrame is returned unchanged.  Otherwise *convert_fn* is called with
        (values, source_unit, 'm') to perform the conversion.

        Parameters
        ----------
        df : pd.DataFrame
        depth_col : str
            Base depth column name (default 'Depth').
        convert_fn : callable
            Function with signature convert_fn(values, source, target) → list-like.
            Typically ``self.convert_units``.
        """
        for col in list(df.columns):
            base = col[: col.index("[")].strip() if "[" in col else col
            if base != depth_col:
                continue
            unit = col[col.index("[") + 1 : -1].strip() if "[" in col else ""
            if unit in ("m", ""):
                # already meters or no unit — just ensure column is named 'Depth [m]'
                if col != f"{depth_col} [m]":
                    df = df.rename(columns={col: f"{depth_col} [m]"})
                return df
            # convert depth values to metres
            converted = convert_fn(df[col].tolist(), unit, "m")
            if converted is not None:
                df = df.copy()
                df[col] = converted
            df = df.rename(columns={col: f"{depth_col} [m]"})
            return df
        return df

    @staticmethod
    def is_table_format(df: pd.DataFrame) -> bool:
        """True if DataFrame uses long table format (Signal [Unit] columns), not Entity/Signal/Unit/Data format."""
        return "Data" not in df.columns

    @staticmethod
    def index_records(
        sub_df: pd.DataFrame, idx_col: str, idx_key: str, val_col: str
    ) -> List[Dict]:
        """Extract {idx_key: idx_val, "Value": val} dicts from sub_df."""
        return [
            {idx_key: r[idx_col], "Value": r[val_col]}
            for r in sub_df[[idx_col, val_col]].to_dict("records")
        ]

    @staticmethod
    def table_df_to_data_list(
        df: pd.DataFrame,
        date_col: str = COLUMN_DATE,
        depth_col: str = COLUMN_DEPTH,
    ) -> List[Dict]:
        """
        Convert a table-format DataFrame to a list of Entity/Signal/Unit/Data records.

        Long format:  Entity, Date (optional), Depth [unit] (optional), Signal [Unit], ...
        Wide format:  Date (optional), Depth [unit] (optional), Entity : Signal [Unit], ...

        Parameters
        ----------
        df : DataFrame
            Table-format DataFrame
        date_col : str, default 'Date'
            Column name for dates (can be overridden, e.g., 'Timestamp' or 'Time')
        depth_col : str, default 'Depth'
            Base name for depth columns (actual column may have unit suffix like 'Depth [m]')
        """
        entity_col = DataFrameMixinHelper.COLUMN_ENTITY

        columns = list(df.columns)
        is_wide = entity_col not in columns

        # Identify index columns (Date / Depth [unit])
        index_cols: Set[str] = set()
        depth_col_name: Optional[str] = None
        for c in columns:
            if c == date_col:
                index_cols.add(c)
            else:
                base = c[: c.index("[")].strip() if "[" in c else c
                if base == depth_col:
                    depth_col_name = c
                    index_cols.add(c)

        has_date = date_col in index_cols
        has_depth = depth_col_name is not None

        records: List[Dict] = []

        if is_wide:
            # Wide: columns are "Entity : Signal [Unit]", no Entity column
            for col in columns:
                if col in index_cols:
                    continue
                if " : " not in col:
                    continue
                entity_part, signal_col = col.split(" : ", 1)
                signal_name, unit = DataFrameMixinHelper.parse_signal_column(
                    signal_col.strip()
                )
                if has_date:
                    data: Any = DataFrameMixinHelper.index_records(
                        df, date_col, "Date", col
                    )
                elif has_depth:
                    assert depth_col_name is not None
                    data = DataFrameMixinHelper.index_records(
                        df, depth_col_name, "Depth", col
                    )
                else:
                    data = df[col].iloc[0]
                records.append(
                    {
                        "Entity": entity_part.strip(),
                        "Signal": signal_name,
                        "Unit": unit,
                        "Data": data,
                    }
                )
        else:
            # Long: Entity column present
            index_cols.add(entity_col)
            index_cols.add(DataFrameMixinHelper.COLUMN_ALIAS)
            signal_cols = [c for c in columns if c not in index_cols]
            for signal_col in signal_cols:
                signal_name, unit = DataFrameMixinHelper.parse_signal_column(signal_col)
                for entity_val, entity_df in df.groupby(entity_col, sort=False):
                    if has_date:
                        data = DataFrameMixinHelper.index_records(
                            entity_df, date_col, "Date", signal_col
                        )
                    elif has_depth:
                        assert depth_col_name is not None
                        data = DataFrameMixinHelper.index_records(
                            entity_df, depth_col_name, "Depth", signal_col
                        )
                    else:
                        data = entity_df[signal_col].iloc[0]
                    records.append(
                        {
                            "Entity": str(entity_val),
                            "Signal": signal_name,
                            "Unit": unit,
                            "Data": data,
                        }
                    )
        return records

    @staticmethod
    def series_to_data_list(
        s: pd.Series,
        date_col: str = COLUMN_DATE,
        depth_col: str = COLUMN_DEPTH,
    ) -> List[Dict]:
        """
        Convert a named Series to Entity/Signal/Unit/Data records.

        Three conventions:
          1. Row dict (no name, or name has no signal-format):
               pd.Series({'Entity': 'Well', 'Date': '...', 'Signal [unit]': val})
          2. Named time/depth series for one entity:
               pd.Series([v1, v2], index=[date1, date2], name='Entity : Signal [unit]')
          3. Named static series for multiple entities:
               pd.Series({'Well1': v1, 'Well2': v2}, name='Signal [unit]')

        Parameters
        ----------
        s : Series
            Input Series
        date_col : str, default 'Date'
            Column name for dates (used when converting row-dict fallback)
        depth_col : str, default 'Depth'
            Base name for depth columns
        """
        name = s.name
        if name is not None:
            name_str = str(name)
            if " : " in name_str:
                # Convention 2: "Entity : Signal [unit]", index = dates or depths
                entity_part, signal_col = name_str.split(" : ", 1)
                signal_name, unit = DataFrameMixinHelper.parse_signal_column(
                    signal_col.strip()
                )
                first_idx = s.index[0] if len(s) > 0 else None
                if isinstance(first_idx, (int, float, np.integer, np.floating)):
                    data: Any = [{"Depth": idx, "Value": val} for idx, val in s.items()]
                else:
                    data = [{"Date": idx, "Value": val} for idx, val in s.items()]
                return [
                    {
                        "Entity": entity_part.strip(),
                        "Signal": signal_name,
                        "Unit": unit,
                        "Data": data,
                    }
                ]
            if "[" in name_str and name_str.endswith("]"):
                # Convention 3: "Signal [unit]", index = entity names → static per entity
                signal_name, unit = DataFrameMixinHelper.parse_signal_column(name_str)
                return [
                    {
                        "Entity": str(entity),
                        "Signal": signal_name,
                        "Unit": unit,
                        "Data": val,
                    }
                    for entity, val in s.items()
                ]
        # Convention 1: treat as a single long-format row
        d = s.to_dict()
        if "Data" not in d:
            return DataFrameMixinHelper.table_df_to_data_list(
                pd.DataFrame([d]), date_col=date_col, depth_col=depth_col
            )
        return [d]

    @staticmethod
    def to_data_list(
        data: Union[List[Dict], Any],
        date_col: str = COLUMN_DATE,
        depth_col: str = COLUMN_DEPTH,
    ) -> List[Dict]:
        """
        Convert data input to a list of Entity/Signal/Unit/Data records.

        Accepts:
          - DataFrame in long format  (Entity, Date/Depth, Signal [Unit] columns)
          - DataFrame in wide format  (Date/Depth, Entity : Signal [Unit] columns)
          - DataFrame in record format (Entity, Signal, Unit, Data columns)
          - Series  (named time/depth series, named static series, or row dict)
          - List of dicts
          - Supports multiple DataFrame backends (pandas, polars, narwhals, etc.)

        Parameters
        ----------
        data : list[dict] | DataFrame | Series | Any
            Input data (any DataFrame backend)
        date_col : str, default 'Date'
            Column name for dates (can be 'Timestamp', 'Time', etc.)
        depth_col : str, default 'Depth'
            Base name for depth columns
        """
        # Unwrap narwhals wrappers to their native type first
        if DataFrameMixinHelper.is_narwhals_available() and hasattr(
            data, "__narwhals_dataframe__"
        ):
            import narwhals as nw

            data = nw.to_native(data, pass_through=True)

        # Detect backend and convert non-pandas DataFrames to pandas
        backend = DataFrameMixinHelper.detect_backend(data)

        if backend == DataFrameBackend.POLARS:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl

                if isinstance(data, (pl.DataFrame, pl.Series)):
                    data = data.to_pandas()
        elif backend not in (
            DataFrameBackend.PANDAS,
            DataFrameBackend.PYARROW,
            DataFrameBackend.DUCKDB,
            "unknown",
        ):
            # pandas-compatible backends (modin, cudf, dask, …) — fall back to .to_pandas()
            to_pandas_fn = getattr(data, "to_pandas", None)
            if callable(to_pandas_fn):
                data = to_pandas_fn()

        # Now process as pandas DataFrame/Series
        if isinstance(data, pd.DataFrame):
            if DataFrameMixinHelper.is_table_format(data):
                return DataFrameMixinHelper.table_df_to_data_list(
                    data, date_col=date_col, depth_col=depth_col
                )
            return cast(List[Dict], data.to_dict("records"))
        elif isinstance(data, pd.Series):
            return DataFrameMixinHelper.series_to_data_list(
                data, date_col=date_col, depth_col=depth_col
            )
        return list(data)

    # ---- DataFrame builders for signals data ----

    @staticmethod
    def _build_indexed_df(
        data_num: List[Dict],
        data_str: List[Dict],
        index_col: str,
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        backend: str = DataFrameBackend.PANDAS,
        parse_dates: bool = True,
    ) -> Optional[Any]:
        """Build a wide pivot DataFrame from indexed (time or depth) response data.

        Supports both pandas and native polars construction (no pandas→polars conversion).
        """
        if not data_num and not data_str:
            return None

        if DataFrameMixinHelper.is_polars_backend(backend):
            return DataFrameMixinHelper._build_indexed_df_polars(
                data_num,
                data_str,
                index_col,
                entity_col,
                signal_col,
                signals_with_units_map,
                parse_dates,
            )
        return DataFrameMixinHelper._build_indexed_df_pandas(
            data_num,
            data_str,
            index_col,
            entity_col,
            signal_col,
            signals_with_units_map,
            parse_dates,
        )

    @staticmethod
    def _build_indexed_df_pandas(
        data_num: List[Dict],
        data_str: List[Dict],
        index_col: str,
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        parse_dates: bool,
    ) -> Optional["pd.DataFrame"]:
        data = [*(data_num or []), *(data_str or [])]
        if not data:
            return None
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col
        unit_key = "UnitName" if response_entity_key == "EntityName" else "Unit"
        meta = [response_entity_key, signal_col, unit_key]
        df_normalized = pd.json_normalize(
            data,
            meta=meta,
            record_path=["Data"],
            errors="ignore",
        )
        if index_col not in df_normalized.columns:
            return None
        df = df_normalized.pivot(
            index=[response_entity_key, index_col],
            columns=signal_col,
            values="Value",
        )
        df.columns.name = None
        df = df.rename(columns=signals_with_units_map).reset_index()
        if response_entity_key != entity_col:
            df = df.rename(columns={response_entity_key: entity_col})
        if parse_dates and index_col in df.columns:
            df[index_col] = pd.to_datetime(df[index_col])
        return df

    @staticmethod
    def _build_indexed_df_polars(
        data_num: List[Dict],
        data_str: List[Dict],
        index_col: str,
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        parse_dates: bool,
    ) -> Optional[Any]:
        import polars as pl

        dfs: List[Any] = []
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        def _build_one(items: List[Dict], val_schema: Any) -> Optional[Any]:
            rows = [
                {
                    entity_col: item[response_entity_key],
                    "__sig__": item[signal_col],
                    index_col: point.get(index_col),
                    "Value": val_schema(point["Value"])
                    if point.get("Value") is not None
                    else None,
                }
                for item in items
                for point in item.get("Data", [])
                if index_col in point
            ]
            if not rows:
                return None
            schema: Dict[str, Any] = {
                entity_col: pl.String,
                "__sig__": pl.String,
                index_col: pl.String,
                "Value": pl.Float64 if val_schema is float else pl.String,
            }
            df = pl.DataFrame(rows, schema=schema)
            df = df.pivot(values="Value", index=[entity_col, index_col], on="__sig__")
            rename = {
                k: v for k, v in signals_with_units_map.items() if k in df.columns
            }
            return df.rename(rename) if rename else df

        if data_num:
            df_num = _build_one(data_num, float)
            if df_num is not None:
                dfs.append(df_num)
        if data_str:
            df_str = _build_one(data_str, str)
            if df_str is not None:
                dfs.append(df_str)
        if not dfs:
            return None
        df = (
            dfs[0]
            if len(dfs) == 1
            else dfs[0].join(
                dfs[1], on=[entity_col, index_col], how="full", coalesce=True
            )
        )
        if parse_dates and index_col in df.columns:
            df = df.with_columns(
                pl.col(index_col).str.to_datetime(
                    format="%Y-%m-%dT%H:%M:%S",
                    time_unit="us",
                    strict=False,
                )
            )
        return df

    @staticmethod
    def _build_static_df(
        data_num: List[Dict],
        data_str: List[Dict],
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        backend: str = DataFrameBackend.PANDAS,
    ) -> Optional[Any]:
        """Build a wide pivot DataFrame from static scalar response data."""
        if not data_num and not data_str:
            return None
        if DataFrameMixinHelper.is_polars_backend(backend):
            return DataFrameMixinHelper._build_static_df_polars(
                data_num,
                data_str,
                entity_col,
                signal_col,
                signals_with_units_map,
            )
        return DataFrameMixinHelper._build_static_df_pandas(
            data_num,
            data_str,
            entity_col,
            signal_col,
            signals_with_units_map,
        )

    @staticmethod
    def _build_static_df_pandas(
        data_num: List[Dict],
        data_str: List[Dict],
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
    ) -> Optional["pd.DataFrame"]:
        data = [*(data_num or []), *(data_str or [])]
        if not data:
            return None
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col
        df_normalized = pd.json_normalize(data)
        if (
            response_entity_key not in df_normalized.columns
            or signal_col not in df_normalized.columns
        ):
            return None
        df = df_normalized.pivot(
            index=response_entity_key, columns=signal_col, values="Data"
        )
        df.columns.name = None
        df = df.rename(columns=signals_with_units_map).reset_index()
        if response_entity_key != entity_col:
            df = df.rename(columns={response_entity_key: entity_col})
        return df

    @staticmethod
    def _build_static_df_polars(
        data_num: List[Dict],
        data_str: List[Dict],
        entity_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
    ) -> Optional[Any]:
        import polars as pl

        dfs: List[Any] = []
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        def _build_one(items: List[Dict], val_schema: Any) -> Optional[Any]:
            rows = [
                {
                    entity_col: item[response_entity_key],
                    "__sig__": item[signal_col],
                    "Data": val_schema(item["Data"])
                    if item.get("Data") is not None
                    else None,
                }
                for item in items
            ]
            if not rows:
                return None
            schema: Dict[str, Any] = {
                entity_col: pl.String,
                "__sig__": pl.String,
                "Data": pl.Float64 if val_schema is float else pl.String,
            }
            df = pl.DataFrame(rows, schema=schema)
            df = df.pivot(values="Data", index=entity_col, on="__sig__")
            rename = {
                k: v for k, v in signals_with_units_map.items() if k in df.columns
            }
            return df.rename(rename) if rename else df

        if data_num:
            df_num = _build_one(data_num, float)
            if df_num is not None:
                dfs.append(df_num)
        if data_str:
            df_str = _build_one(data_str, str)
            if df_str is not None:
                dfs.append(df_str)
        if not dfs:
            return None
        return (
            dfs[0]
            if len(dfs) == 1
            else dfs[0].join(dfs[1], on=entity_col, how="full", coalesce=True)
        )

    @staticmethod
    def _build_combined_df(
        data_time_num: List[Dict],
        data_time_str: List[Dict],
        data_depth_num: List[Dict],
        data_depth_str: List[Dict],
        data_static_num: List[Dict],
        data_static_str: List[Dict],
        entity_col: str,
        time_col: str,
        depth_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        backend: str = DataFrameBackend.PANDAS,
    ) -> Optional[Any]:
        """Build all signal types (time, depth, static) into one DataFrame in a single pass.

        Routing strategy (benchmarked at 200×200 / 500×500 / 1000×1000):

        backend="pandas"
            → _build_combined_df_no_pivot  (fastest pandas path, avoids pivot entirely)

        backend="polars" (or any non-pandas backend) + narwhals installed
            → _build_combined_df_narwhals  (narwhals dispatches to polars pivot; −77 to −82%)
              Bridge backends (pyarrow, duckdb, dask, modin, cudf): built as polars
              via narwhals, then converted to the target type at the very end.

        backend="polars" + narwhals NOT installed
            → _build_combined_df_polars    (direct polars pivot)

        anything else + narwhals NOT installed + polars NOT installed
            → _build_combined_df_pandas    (json_normalize + pandas pivot fallback)

        Narwhals is never a user-facing backend value — it is selected automatically
        as the internal dispatch layer when installed.
        """
        _args = (
            data_time_num,
            data_time_str,
            data_depth_num,
            data_depth_str,
            data_static_num,
            data_static_str,
            entity_col,
            time_col,
            depth_col,
            signal_col,
            signals_with_units_map,
        )
        # pandas backend: no_pivot is the fastest pandas-native path
        if backend == DataFrameBackend.PANDAS:
            return DataFrameMixinHelper._build_combined_df_no_pivot(*_args)
        # all non-pandas backends go through narwhals (polars pivot + bridge for pyarrow/duckdb)
        try:
            import narwhals  # noqa: F401

            return DataFrameMixinHelper._build_combined_df_narwhals(
                *_args, backend=backend
            )
        except ImportError:
            pass
        if DataFrameMixinHelper.is_polars_backend(backend):
            return DataFrameMixinHelper._build_combined_df_polars(*_args)
        return DataFrameMixinHelper._build_combined_df_pandas(*_args)

    @staticmethod
    def _build_combined_df_pandas(
        data_time_num: List[Dict],
        data_time_str: List[Dict],
        data_depth_num: List[Dict],
        data_depth_str: List[Dict],
        data_static_num: List[Dict],
        data_static_str: List[Dict],
        entity_col: str,
        time_col: str,
        depth_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
    ) -> Optional["pd.DataFrame"]:
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        def _pivot_indexed(data: List[Dict], idx: str) -> Optional["pd.DataFrame"]:
            if not data:
                return None
            unit_key = "UnitName" if response_entity_key == "EntityName" else "Unit"
            df = pd.json_normalize(
                data,
                meta=[response_entity_key, signal_col, unit_key],
                record_path=["Data"],
                errors="ignore",
            )
            if idx not in df.columns:
                return None
            df = df.pivot(
                index=[response_entity_key, idx], columns=signal_col, values="Value"
            )
            df.columns.name = None
            df = df.rename(columns=signals_with_units_map).reset_index()
            if response_entity_key != entity_col:
                df = df.rename(columns={response_entity_key: entity_col})
            if idx == time_col:
                df[time_col] = pd.to_datetime(df[time_col])
            return df

        def _pivot_static(data: List[Dict]) -> Optional["pd.DataFrame"]:
            if not data:
                return None
            df = pd.json_normalize(data)
            if response_entity_key not in df.columns or signal_col not in df.columns:
                return None
            df = df.pivot(index=response_entity_key, columns=signal_col, values="Data")
            df.columns.name = None
            df = df.rename(columns=signals_with_units_map).reset_index()
            if response_entity_key != entity_col:
                df = df.rename(columns={response_entity_key: entity_col})
            return df

        frames = [
            f
            for f in [
                _pivot_indexed([*data_time_num, *data_time_str], time_col),
                _pivot_indexed([*data_depth_num, *data_depth_str], depth_col),
                _pivot_static([*data_static_num, *data_static_str]),
            ]
            if f is not None and not f.empty
        ]
        if not frames:
            return None
        if len(frames) == 1:
            return frames[0]
        df = frames[0]
        for right in frames[1:]:
            df = pd.merge(df, right, on=entity_col, how="outer")
        return df

    @staticmethod
    def _build_combined_df_polars(
        data_time_num: List[Dict],
        data_time_str: List[Dict],
        data_depth_num: List[Dict],
        data_depth_str: List[Dict],
        data_static_num: List[Dict],
        data_static_str: List[Dict],
        entity_col: str,
        time_col: str,
        depth_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
    ) -> Optional[Any]:
        import polars as pl

        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        def _pivot_indexed(
            num: List[Dict], str_: List[Dict], idx: str
        ) -> Optional[Any]:
            dfs: List[Any] = []
            for items, val_fn, val_type in [
                (num, float, pl.Float64),
                (str_, str, pl.String),
            ]:
                if not items:
                    continue
                rows = [
                    {
                        entity_col: item[response_entity_key],
                        "__sig__": item[signal_col],
                        idx: point.get(idx),
                        "Value": val_fn(point["Value"])
                        if point.get("Value") is not None
                        else None,
                    }
                    for item in items
                    for point in item.get("Data", [])
                    if idx in point
                ]
                if not rows:
                    continue
                df = pl.DataFrame(
                    rows,
                    schema={
                        entity_col: pl.String,
                        "__sig__": pl.String,
                        idx: pl.String,
                        "Value": val_type,
                    },
                ).pivot(values="Value", index=[entity_col, idx], on="__sig__")
                rename = {
                    k: v for k, v in signals_with_units_map.items() if k in df.columns
                }
                dfs.append(df.rename(rename) if rename else df)
            if not dfs:
                return None
            df = (
                dfs[0]
                if len(dfs) == 1
                else dfs[0].join(
                    dfs[1], on=[entity_col, idx], how="full", coalesce=True
                )
            )
            if idx == time_col:
                df = df.with_columns(
                    pl.col(idx)
                    .str.to_datetime(
                        format="%Y-%m-%dT%H:%M:%SZ",
                        time_unit="us",
                        strict=False,
                    )
                    .dt.replace_time_zone(None)
                )
            return df

        def _pivot_static(num: List[Dict], str_: List[Dict]) -> Optional[Any]:
            dfs: List[Any] = []
            for items, val_fn, val_type in [
                (num, float, pl.Float64),
                (str_, str, pl.String),
            ]:
                if not items:
                    continue
                rows = [
                    {
                        entity_col: item[response_entity_key],
                        "__sig__": item[signal_col],
                        "Data": val_fn(item["Data"])
                        if item.get("Data") is not None
                        else None,
                    }
                    for item in items
                ]
                if not rows:
                    continue
                df = pl.DataFrame(
                    rows,
                    schema={
                        entity_col: pl.String,
                        "__sig__": pl.String,
                        "Data": val_type,
                    },
                ).pivot(values="Data", index=entity_col, on="__sig__")
                rename = {
                    k: v for k, v in signals_with_units_map.items() if k in df.columns
                }
                dfs.append(df.rename(rename) if rename else df)
            if not dfs:
                return None
            return (
                dfs[0]
                if len(dfs) == 1
                else dfs[0].join(dfs[1], on=entity_col, how="full", coalesce=True)
            )

        frames = [
            f
            for f in [
                _pivot_indexed(data_time_num, data_time_str, time_col),
                _pivot_indexed(data_depth_num, data_depth_str, depth_col),
                _pivot_static(data_static_num, data_static_str),
            ]
            if f is not None
        ]
        if not frames:
            return None
        if len(frames) == 1:
            return frames[0]
        df = frames[0]
        for right in frames[1:]:
            df = df.join(right, on=entity_col, how="full", coalesce=True)
        return df

    @staticmethod
    def _build_combined_df_narwhals(
        data_time_num: List[Dict],
        data_time_str: List[Dict],
        data_depth_num: List[Dict],
        data_depth_str: List[Dict],
        data_static_num: List[Dict],
        data_static_str: List[Dict],
        entity_col: str,
        time_col: str,
        depth_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
        backend: str = DataFrameBackend.PANDAS,
    ) -> Optional[Any]:
        """Build combined DataFrame using narwhals (unified pandas+polars code path).

        Identical logic to the pandas/polars variants but expressed in narwhals
        expressions, so one code path handles both backends.
        Requires narwhals >= 1.0 to be installed.

        For pyarrow and duckdb backends, narwhals pivot is not implemented —
        we use a polars bridge (build as polars, then convert to the target native type).
        """
        import narwhals as nw

        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        # pyarrow and duckdb can't pivot natively — build as polars, then convert
        _bridge_backends = (DataFrameBackend.PYARROW, DataFrameBackend.DUCKDB)
        if backend in _bridge_backends:
            result_pl = DataFrameMixinHelper._build_combined_df_narwhals(
                data_time_num,
                data_time_str,
                data_depth_num,
                data_depth_str,
                data_static_num,
                data_static_str,
                entity_col,
                time_col,
                depth_col,
                signal_col,
                signals_with_units_map,
                backend=DataFrameBackend.POLARS,
            )
            if result_pl is None:
                return None
            pd_result = result_pl.to_pandas()
            if backend == DataFrameBackend.PYARROW:
                import pyarrow as pa  # type: ignore[import-untyped]

                return pa.Table.from_pandas(pd_result)
            if backend == DataFrameBackend.DUCKDB:
                import duckdb  # type: ignore[import-untyped]

                return duckdb.from_df(pd_result)
            return result_pl

        nw_backend = (
            "polars" if DataFrameMixinHelper.is_polars_backend(backend) else "pandas"
        )

        def _full_join_coalesce(left: Any, right: Any, on: List[str]) -> Any:
            result = left.join(right, on=on if len(on) > 1 else on[0], how="full")
            for key in on:
                right_key = f"{key}_right"
                if right_key in result.columns:
                    result = result.with_columns(
                        nw.col(key).fill_null(nw.col(right_key))
                    ).drop(right_key)
            return result

        def _pivot_indexed(
            num: List[Dict], str_: List[Dict], idx: str
        ) -> Optional[Any]:
            all_rows: List[Dict] = []
            val_types: Dict[str, Any] = {}
            for items, val_fn, nw_type in [
                (num, float, nw.Float64),
                (str_, str, nw.String),
            ]:
                if not items:
                    continue
                rows = [
                    {
                        entity_col: item[response_entity_key],
                        "__sig__": item[signal_col],
                        idx: point.get(idx),
                        "Value": val_fn(point["Value"])
                        if point.get("Value") is not None
                        else None,
                    }
                    for item in items
                    for point in item.get("Data", [])
                    if idx in point
                ]
                if not rows:
                    continue
                all_rows.extend(rows)
                val_types["Value"] = nw.String if val_fn is str else nw.Float64
            if not all_rows:
                return None
            schema: Dict[str, Any] = {
                entity_col: nw.String,
                "__sig__": nw.String,
                idx: nw.String,
                "Value": val_types.get("Value", nw.Float64),
            }
            df = nw.from_dict(
                {
                    entity_col: [r[entity_col] for r in all_rows],
                    "__sig__": [r["__sig__"] for r in all_rows],
                    idx: [r[idx] for r in all_rows],
                    "Value": [r["Value"] for r in all_rows],
                },
                schema=schema,
                backend=nw_backend,
            )
            df = df.pivot(values="Value", index=[entity_col, idx], on="__sig__")
            rename = {
                k: v for k, v in signals_with_units_map.items() if k in df.columns
            }
            if rename:
                df = df.rename(rename)
            if idx == time_col:
                df = df.with_columns(
                    nw.col(idx).str.to_datetime(format="%Y-%m-%dT%H:%M:%S")
                )
            return df

        def _pivot_static(num: List[Dict], str_: List[Dict]) -> Optional[Any]:
            all_rows: List[Dict] = []
            val_type: Any = nw.Float64
            for items, val_fn, nw_type in [
                (num, float, nw.Float64),
                (str_, str, nw.String),
            ]:
                if not items:
                    continue
                rows = [
                    {
                        entity_col: item[response_entity_key],
                        "__sig__": item[signal_col],
                        "Data": val_fn(item["Data"])
                        if item.get("Data") is not None
                        else None,
                    }
                    for item in items
                ]
                if not rows:
                    continue
                all_rows.extend(rows)
                val_type = nw.String if val_fn is str else nw.Float64
            if not all_rows:
                return None
            df = nw.from_dict(
                {
                    entity_col: [r[entity_col] for r in all_rows],
                    "__sig__": [r["__sig__"] for r in all_rows],
                    "Data": [r["Data"] for r in all_rows],
                },
                schema=cast(
                    Dict[str, Any],
                    {entity_col: nw.String, "__sig__": nw.String, "Data": val_type},
                ),
                backend=nw_backend,
            )
            df = df.pivot(values="Data", index=entity_col, on="__sig__")
            rename = {
                k: v for k, v in signals_with_units_map.items() if k in df.columns
            }
            return df.rename(rename) if rename else df

        frames = [
            f
            for f in [
                _pivot_indexed(data_time_num, data_time_str, time_col),
                _pivot_indexed(data_depth_num, data_depth_str, depth_col),
                _pivot_static(data_static_num, data_static_str),
            ]
            if f is not None
        ]
        if not frames:
            return None
        if len(frames) == 1:
            return nw.to_native(frames[0])
        df = frames[0]
        for right in frames[1:]:
            df = _full_join_coalesce(df, right, [entity_col])
        return nw.to_native(df)

    @staticmethod
    def _build_multi_index_df(
        data_records: List[Dict],
        entity_col: str,
        index_cols: List[str],
        col_unit_labels: List[str],
        signals_with_units_map: Dict[str, str],
        backend: str = "pandas",
    ) -> Optional[Any]:
        """Build a wide DataFrame from records that have multiple numeric index axes.

        Generic version of the PVT builder: instead of a single Date/Depth index,
        each row is keyed by ``(entity, *index_values)``.  For PVT signals the
        caller passes ``index_cols=["Pressure", "Temperature"]`` and
        ``col_unit_labels=["Pa", "K"]`` so column headers become
        ``"Pressure [Pa]"`` and ``"Temperature [K]"``.

        Each input record has the shape::

            {"Entity": ..., "Signal": ..., "Unit": ...,
             "Data": [{"Pressure": float, "Temperature": float, "Value": float}, ...]}

        where the keys inside ``Data`` match ``index_cols`` plus ``"Value"``.

        The output is pivoted wide: rows are
        ``(entity_col, col_unit_labels[0], col_unit_labels[1], ...)``,
        columns are signal names with unit suffix from *signals_with_units_map*.
        Backend conversion mirrors ``_build_combined_df``.
        """
        if not data_records:
            return None

        # Build labelled output column names for the index axes
        out_index_cols = [
            f"{ic} [{ul}]" if ul else ic for ic, ul in zip(index_cols, col_unit_labels)
        ]

        # (entity, idx0, idx1, ...) -> {sig_col: value}
        rows_map: Dict[tuple, Dict[str, Any]] = {}
        response_entity_key = entity_col  # PVT response always uses "Entity"
        for item in data_records:
            ent = item.get(response_entity_key) or item.get("EntityName", "")
            sig_raw = item.get("Signal", "")
            sig_out = signals_with_units_map.get(sig_raw, sig_raw)
            for pt in item.get("Data") or []:
                idx_vals = tuple(pt.get(ic) for ic in index_cols)
                if any(v is None for v in idx_vals):
                    continue
                key = (ent,) + idx_vals
                if key not in rows_map:
                    row: Dict[str, Any] = {entity_col: ent}
                    for out_col, v in zip(out_index_cols, idx_vals):
                        row[out_col] = float(v)
                    rows_map[key] = row
                v = pt.get("Value")
                rows_map[key][sig_out] = float(v) if v is not None else None

        if not rows_map:
            return None

        import pandas as _pd

        df_pd = _pd.DataFrame(list(rows_map.values()))
        sort_keys = [entity_col] + out_index_cols
        df_pd = df_pd.sort_values(sort_keys).reset_index(drop=True)

        if backend == DataFrameBackend.PANDAS:
            return df_pd

        if DataFrameMixinHelper.is_polars_backend(backend):
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl  # type: ignore[import-untyped]

                return pl.from_pandas(df_pd)
            return df_pd

        if backend == DataFrameBackend.PYARROW:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.PYARROW):
                import pyarrow as pa  # type: ignore[import-untyped]

                return pa.Table.from_pandas(df_pd)
            return df_pd

        if backend == DataFrameBackend.DUCKDB:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.DUCKDB):
                import duckdb  # type: ignore[import-untyped]

                return duckdb.from_df(df_pd)
            return df_pd

        return df_pd

    @staticmethod
    def _build_combined_df_no_pivot(
        data_time_num: List[Dict],
        data_time_str: List[Dict],
        data_depth_num: List[Dict],
        data_depth_str: List[Dict],
        data_static_num: List[Dict],
        data_static_str: List[Dict],
        entity_col: str,
        time_col: str,
        depth_col: str,
        signal_col: str,
        signals_with_units_map: Dict[str, str],
    ) -> Optional[Any]:
        """Build a pandas DataFrame without pivot — constructs columns directly from dicts.

        Pandas-only path called exclusively from _build_combined_df when backend="pandas".
        Instead of flatten-all-rows → pivot, this approach:
        1. Builds a (entity, index) → {signal: value} mapping per signal type
        2. Constructs the output DataFrame column-by-column from those mappings

        ~70% faster than the pandas json_normalize+pivot path at 200×200.
        """
        response_entity_key = "EntityName" if entity_col != "Entity" else entity_col

        def _collect_indexed(
            items_list: List[tuple],
            idx_key: str,
        ) -> Dict[str, Dict[str, Any]]:
            """Walk items and build (entity\x00index) → {col: val} mapping."""
            rows_map: Dict[str, Dict[str, Any]] = {}
            for items, is_numeric in items_list:
                if not items:
                    continue
                for item in items:
                    ent = item[response_entity_key]
                    sig_raw = item[signal_col]
                    sig_out = signals_with_units_map.get(sig_raw, sig_raw)
                    for pt in item.get("Data") or []:
                        if idx_key not in pt:
                            continue
                        idx_val = str(pt[idx_key])
                        key = f"{ent}\x00{idx_val}"
                        if key not in rows_map:
                            rows_map[key] = {entity_col: ent, idx_key: idx_val}
                        v = pt.get("Value")
                        rows_map[key][sig_out] = (
                            (float(v) if is_numeric else str(v))
                            if v is not None
                            else None
                        )
            return rows_map

        # ── collect time and depth signals separately ─────────────────────────
        time_rows = _collect_indexed(
            [(data_time_num, True), (data_time_str, False)], time_col
        )
        depth_rows = _collect_indexed(
            [(data_depth_num, True), (data_depth_str, False)], depth_col
        )

        # ── collect static signals ────────────────────────────────────────────
        static_rows: Dict[str, Dict[str, Any]] = {}
        for items, is_numeric in [(data_static_num, True), (data_static_str, False)]:
            if not items:
                continue
            for item in items:
                ent = item[response_entity_key]
                sig_raw = item[signal_col]
                sig_out = signals_with_units_map.get(sig_raw, sig_raw)
                v = item.get("Data")
                if ent not in static_rows:
                    static_rows[ent] = {entity_col: ent}
                static_rows[ent][sig_out] = (
                    (float(v) if is_numeric else str(v)) if v is not None else None
                )

        def _merge_static(indexed: Dict[str, Dict[str, Any]]) -> None:
            for row in indexed.values():
                ent = row[entity_col]
                if ent in static_rows:
                    for k, v in static_rows[ent].items():
                        if k != entity_col:
                            row.setdefault(k, v)

        if time_rows:
            _merge_static(time_rows)
        if depth_rows:
            _merge_static(depth_rows)

        # ── build one or two pandas frames then combine ───────────────────────
        def _to_frame(
            rows: Dict[str, Dict[str, Any]], idx_key: str, parse_time: bool
        ) -> Any:
            if not rows:
                return None
            row_list = list(rows.values())
            all_keys = list(row_list[0].keys())
            col_order = [entity_col, idx_key] + [
                k for k in all_keys if k not in (entity_col, idx_key)
            ]
            col_data: Dict[str, List] = {
                k: [r.get(k) for r in row_list] for k in col_order
            }
            df = pd.DataFrame(col_data)
            if parse_time and idx_key in df.columns:
                _ts = cast(pd.Series, pd.to_datetime(df[idx_key], utc=True))
                df[idx_key] = _ts.dt.tz_localize(None)
            return df

        time_frame = _to_frame(time_rows, time_col, parse_time=True)
        depth_frame = _to_frame(depth_rows, depth_col, parse_time=False)

        # static-only case (no indexed signals at all)
        if time_frame is None and depth_frame is None:
            if not static_rows:
                return None
            row_list = list(static_rows.values())
            col_data = {k: [r.get(k) for r in row_list] for k in row_list[0]}
            result_frame: Any = pd.DataFrame(col_data)
        elif time_frame is not None and depth_frame is not None:
            result_frame = pd.merge(time_frame, depth_frame, on=entity_col, how="outer")
        else:
            result_frame = time_frame if time_frame is not None else depth_frame

        return result_frame


# DataFrames utilities
class DataFrameMixin(
    SupportsDataFrames,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
    SupportsRequests,
):
    """
    DataFrames Utilities
    """

    # read dataframe from file
    def read_dataframe_from_file(
        self,
        filepath: str,
        backend: str = DataFrameBackend.PANDAS,
        delimiter: str = ",",
        engine: Optional[str] = None,
        **kwargs,
    ) -> Union[pd.DataFrame, Any]:
        """
        Read DataFrame from file with backend selection.

        Parameters
        ----------
        filepath : str
            Path to file
        backend : str, default 'pandas'
            DataFrame backend ('pandas', 'polars')
        delimiter : str, default ','
            Delimiter for CSV/TSV files
        engine : str, optional
            Engine for pandas readers (e.g., 'openpyxl', 'pyarrow', 'c')

        Returns
        -------
        DataFrame
            DataFrame of specified backend type

        Raises
        ------
        ValueError
            If file extension is not supported

        Examples
        --------
        >>> df = api.read_dataframe_from_file("data.csv")
        >>> df = api.read_dataframe_from_file("data.xlsx", engine="openpyxl")
        >>> df = api.read_dataframe_from_file("data.parquet", backend="polars")
        """
        ext = ApiHelper.get_file_extension(filepath).lower()

        if backend == DataFrameBackend.PANDAS:
            if ext in (".xlsx", ".xls"):
                return pd.read_excel(filepath, engine=cast(Any, engine or "openpyxl"))
            elif ext == ".csv":
                return pd.read_csv(filepath, delimiter=delimiter, engine=engine)
            elif ext in (".tsv", ".txt"):
                return pd.read_table(filepath, sep=delimiter, engine=engine)
            elif ext == ".parquet":
                return pd.read_parquet(filepath, engine=engine or "auto")
            elif ext in (".feather", ".arrow"):
                return pd.read_feather(filepath)
            else:
                raise ValueError(
                    f"PetroVisor::read_dataframe_from_file(): "
                    f"Unsupported file extension: '{ext}'. "
                    f"Supported formats: .csv, .tsv, .txt, .xlsx, .xls, .parquet, .feather, .arrow"
                )

        elif backend == DataFrameBackend.POLARS:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl  # type: ignore[import-untyped]

                if ext in (".xlsx", ".xls"):
                    return pl.read_excel(filepath)
                elif ext == ".csv":
                    return pl.read_csv(filepath, separator=delimiter)
                elif ext in (".tsv", ".txt"):
                    return pl.read_csv(filepath, separator=delimiter)
                elif ext == ".parquet":
                    return pl.read_parquet(filepath)
                elif ext in (".feather", ".arrow"):
                    return pl.read_ipc(filepath)
                else:
                    raise ValueError(
                        f"PetroVisor::read_dataframe_from_file(): "
                        f"Unsupported file extension for polars: '{ext}'"
                    )
            else:
                # Fallback to pandas if polars not available
                return self.read_dataframe_from_file(
                    filepath,
                    backend=DataFrameBackend.PANDAS,
                    delimiter=delimiter,
                    engine=engine,
                    **kwargs,
                )

        else:
            raise ValueError(f"Unsupported backend: '{backend}'")

    # read dataframe from bytes
    def read_dataframe_from_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        backend: str = DataFrameBackend.PANDAS,
        **kwargs,
    ) -> Union[pd.DataFrame, Any]:
        """
        Read DataFrame from bytes using file extension.

        Parameters
        ----------
        file_bytes : bytes
            File content as bytes
        filename : str
            Filename (used to determine format from extension)
        backend : str, default 'pandas'
            DataFrame backend ('pandas', 'polars')

        Returns
        -------
        DataFrame
            DataFrame of specified backend type

        Raises
        ------
        ValueError
            If file extension is not supported

        Examples
        --------
        >>> file_bytes = api.get_file("data.csv")
        >>> df = api.read_dataframe_from_bytes(file_bytes, "data.csv")
        >>> df = api.read_dataframe_from_bytes(file_bytes, "data.parquet", backend="polars")
        """
        ext = ApiHelper.get_file_extension(filename).lower()

        if backend == DataFrameBackend.PANDAS:
            if ext == ".csv":
                return pd.read_csv(io.BytesIO(file_bytes))
            elif ext in (".xlsx", ".xls"):
                return pd.read_excel(io.BytesIO(file_bytes))
            elif ext == ".parquet":
                return pd.read_parquet(io.BytesIO(file_bytes))
            elif ext in (".feather", ".arrow"):
                return pd.read_feather(io.BytesIO(file_bytes))
            else:
                raise ValueError(
                    f"PetroVisor::read_dataframe_from_bytes(): "
                    f"Unsupported file extension: '{ext}'. "
                    f"Supported formats: .csv, .xlsx, .xls, .parquet, .feather, .arrow"
                )

        elif backend == DataFrameBackend.POLARS:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl  # type: ignore[import-untyped]

                if ext == ".csv":
                    return pl.read_csv(file_bytes)
                elif ext in (".xlsx", ".xls"):
                    return pl.read_excel(file_bytes)
                elif ext == ".parquet":
                    return pl.read_parquet(file_bytes)
                elif ext in (".feather", ".arrow"):
                    return pl.read_ipc(file_bytes)
                else:
                    raise ValueError(
                        f"PetroVisor::read_dataframe_from_bytes(): "
                        f"Unsupported file extension for polars: '{ext}'"
                    )
            else:
                # Fallback to pandas if polars not available
                return self.read_dataframe_from_bytes(
                    file_bytes, filename, backend=DataFrameBackend.PANDAS, **kwargs
                )

        else:
            raise ValueError(f"Unsupported backend: '{backend}'")

    # convert dataframe to file-like object
    def convert_dataframe_to_file_object(
        self,
        df: Any,
        file_name: str,
        date_format: Optional[str] = None,
        backend: Optional[str] = None,
        **kwargs,
    ) -> io.BytesIO:
        """
        Convert dataframe to file-like object

        Parameters
        ----------
        df : DataFrame
            DataFrame (pandas, polars, or other backend)
        file_name : str
            File name
        date_format : str, default None
            Date format
        backend : str, default None
            DataFrame backend. If None, auto-detected from df type
        """
        # Unwrap narwhals wrappers to their native type first
        if DataFrameMixinHelper.is_narwhals_available() and hasattr(
            df, "__narwhals_dataframe__"
        ):
            import narwhals as nw

            df = nw.to_native(df, pass_through=True)

        # Auto-detect backend if not specified
        if backend is None:
            backend = DataFrameMixinHelper.detect_backend(df)

        # Check if it's a DataFrame type we recognize
        if backend == "unknown":
            return df

        # Convert non-pandas DataFrames to pandas for serialization
        df_pandas = df
        if backend == DataFrameBackend.POLARS:
            if DataFrameMixinHelper.is_backend_available(DataFrameBackend.POLARS):
                import polars as pl

                if isinstance(df, (pl.DataFrame, pl.Series)):
                    df_pandas = df.to_pandas()

        # Serialize to file format
        if file_name.lower().endswith(".csv"):
            file_obj = io.BytesIO()
            if date_format:
                df_pandas.to_csv(
                    file_obj,
                    header=True,
                    index=False,
                    encoding="utf-8",
                    mode="wb",
                    date_format="%Y-%m-%dT%H:%M:%S.%fZ",
                )
            else:
                df_pandas.to_csv(
                    file_obj, header=True, index=False, encoding="utf-8", mode="wb"
                )
            file_obj.seek(0)
        elif file_name.lower().endswith(".xlsx"):
            file_obj = io.BytesIO()
            with pd.ExcelWriter(cast(Any, file_obj), engine="xlsxwriter") as writer:
                df_pandas.to_excel(writer, index=False)
            file_obj.seek(0)
        else:
            try:
                file_obj = io.BytesIO()
                df_pandas.to_pickle(file_obj, compression="gzip")
                file_obj.seek(0)
            except Exception:
                file_obj = io.BytesIO(pickle.dumps(df_pandas))
        file_obj.name = file_name
        return file_obj

    # convert PivotTable to DataFrame
    def convert_pivot_table_to_dataframe(
        self,
        data: List,
        schema: Optional[List[str]] = None,
        groupby_entity: bool = False,
        **kwargs,
    ):
        """
        Convert PivotTable to DataFrame

        Parameters
        ----------
        data : list
            PivotTable data
        schema : list[str], default None
            PivotTable schema
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        try:
            if data:
                # get columns
                cols = data[0]
                if len(data) > 1:
                    df = pd.DataFrame(data=data[1:], columns=cols)
                else:
                    df = pd.DataFrame(columns=cols)
            else:
                df = pd.DataFrame()

            # assign column types
            columns = df.columns
            if schema:
                columns_dtype = {col: ctype for col, ctype in zip(columns, schema)}
            else:
                columns_dtype = {}
                entity_col = self.get_entity_column_name(**kwargs)
                entity_type_col = self.get_entity_type_column_name(**kwargs)
                alias_col = self.get_alias_column_name(**kwargs)
                is_opportunity_col = self.get_opportunity_column_name(**kwargs)
                date_col = self.get_date_column_name(**kwargs)
                time_col = self.get_time_column_name(**kwargs)
                for col in [date_col, time_col]:
                    columns_dtype[col] = "Time"
                for col in [entity_col, alias_col, entity_type_col]:
                    columns_dtype[col] = "String"
                columns_dtype[is_opportunity_col] = "Bool"
            df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

            # group by entity
            if groupby_entity:
                df = {e: df_group for e, df_group in df.groupby(entity_col)}
        except BaseException:
            raise RuntimeError(
                "PetroVisor::convert_pivot_table_to_dataframe(): "
                "couldn't convert PivotTable to DataFrame"
            )
        return df

    # convert P# table to DataFrame
    def convert_psharp_table_to_dataframe(
        self,
        psharp_table: Union[Dict, List],
        dropna: bool = True,
        with_entity_column: bool = True,
        groupby_entity: bool = False,
        **kwargs,
    ) -> Optional[Union[pd.DataFrame, Dict[str, pd.DataFrame]]]:
        """
        Convert P# table to DataFrame

        Parameters
        ----------
        psharp_table : dict, list
            P# table data
        dropna : bool, default True
            Whether rows filled with NaNs should be dropped
        with_entity_column : bool, default True
            Load table with 'Entity' column, otherwise columns will be named as "EntityName : ColumnName"
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        if psharp_table is None:
            return None

        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()
        # known column types
        columns_dtype = {
            entity_col: "String",
            alias_col: "String",
            date_col: "Time",
            depth_col: "Numeric",
        }

        # read P# table from list
        if isinstance(psharp_table, list):
            if len(psharp_table) < 2:
                return None

            columns = psharp_table[0].split("\t") if len(psharp_table) > 0 else []

            # define type of table
            has_entity_col = entity_col in columns

            # create DataFrame
            if has_entity_col or not groupby_entity:
                # create DataFrame
                df = DataFrameMixinHelper.create_dataframe_from_list(psharp_table)
                # assign column types
                if df is not None:
                    df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)
                    # group by entity
                    if groupby_entity:
                        df = {
                            str(e): df_group for e, df_group in df.groupby(entity_col)
                        }
                    # convert to wide format with columns format "{entity_name} : {column_name}"
                    elif has_entity_col and not with_entity_column:
                        df = self.convert_dataframe_from_long_to_wide(df)
                    # convert to long format with 'Entity' column
                    elif not has_entity_col and with_entity_column:
                        df = self.convert_dataframe_from_wide_to_long(df)

            # special case when columns have format "{entity_name} : {column_name}"
            # and group by entity is required
            else:
                # remove entity name from column names
                col_names = DataFrameMixinHelper.remove_entities_from_columns(columns)
                # extract entity name from column names
                col_entities = DataFrameMixinHelper.get_entities_from_columns(columns)
                # list of all entities
                entities = DataFrameMixinHelper.get_unique_non_empty_names(col_entities)
                # create DataFrame
                df = {}
                for e in entities:
                    e_columns = [
                        cname
                        for ce, cname in zip(col_entities, col_names)
                        if not ce or ce == e
                    ]
                    df[e] = pd.DataFrame(
                        [
                            cv
                            for row in psharp_table[1:]
                            for cv, ce in zip(row.split("\t"), col_entities)
                            if not ce or ce == e
                        ],
                        columns=cast(Any, e_columns),
                    )

                # assign column types
                for e in entities:
                    df[e] = self.assign_dataframe_column_types(
                        df[e], columns_dtype, **kwargs
                    )

        elif (
            psharp_table is not None
            and "TableName" in psharp_table
            and "ResultsOrder" in psharp_table
        ):
            # results order
            columns_short = psharp_table["ResultsOrder"]
            # create column names map from short to full name with unit
            columns_short_to_long = {col: None for col in columns_short}

            # get column specs
            def get_column_specs(
                col: Dict[str, Any], is_not_full_spec: bool
            ) -> Tuple[str, str, str]:
                if is_not_full_spec:
                    centity = col["EntityName"]
                    cname = col["ResultName"]
                    cunit = col["UnitName"]
                else:
                    centity = col["Entity"]
                    result = col["Result"]
                    cname = result["Name"]
                    cunit = col["Unit"]
                    # cunit = result['Unit']['Name']
                return centity, cname, cunit

            # get full column name
            def get_full_column_name(col_name: str, unit_name: str):
                return f"{col_name} [{unit_name}]"

            # create DataFrame
            data_field = "Data"
            value_field = "Value"
            # result_field = ''
            fields = []
            for i, table_fields in enumerate(
                [
                    [
                        "Columns",
                        "ColumnsDepth",
                        "ColumnsString",
                        "ColumnsTime",
                        "ColumnsBool",
                    ],
                    ["Data", "DataDepth", "DataString", "DataTime", "DataBool"],
                ]
            ):
                is_not_full_spec = i == 0
                entity_field = "EntityName" if is_not_full_spec else "Entity"
                # non-empty fields
                fields = [
                    field
                    for field in table_fields
                    if field in psharp_table and psharp_table[field]
                ]
                for col_type in fields:
                    # column type
                    col_dtype = "Numeric"
                    for suffix in ["String", "Time", "Bool"]:
                        if suffix in col_type:
                            col_dtype = suffix
                            break
                    for col in psharp_table[col_type]:
                        # get column info
                        col_entity_name, col_name, col_unit_name = get_column_specs(
                            col, is_not_full_spec
                        )
                        # assign column data type
                        if columns_short_to_long[col_name] is None:
                            full_column_name = get_full_column_name(
                                col_name, col_unit_name
                            )
                            columns_short_to_long[col_name] = full_column_name
                            columns_dtype[full_column_name] = col_dtype
                        else:
                            full_column_name = columns_short_to_long[col_name]
                        # change entity field to 'Entity'
                        if entity_field != entity_col:
                            col[entity_col] = col.pop(entity_field)
                        # change value field to column name
                        for d in col[data_field]:
                            d[full_column_name] = d.pop(value_field)
                if fields:
                    break
            if not fields:
                return None

            # create DataFrame
            df = pd.json_normalize(
                (
                    [values for field in fields for values in psharp_table[field]]
                    if len(fields) > 1
                    else psharp_table[fields[0]]
                ),
                record_path=data_field,
                meta=[entity_col],
                errors="ignore",
            )

            # reorder columns
            offset = 0
            reordered_columns = list(df.columns)
            # first columns 'Date', 'Depth', 'Entity'
            for col in [entity_col, depth_col, date_col]:
                if col in reordered_columns:
                    reordered_columns.remove(col)
                    reordered_columns.insert(0, col)
                    offset += 1
            # arrange other columns according to results order
            for idx, col in enumerate(columns_short):
                full_column_name = columns_short_to_long[col]
                if full_column_name in reordered_columns:
                    reordered_columns.remove(full_column_name)
                    reordered_columns.insert(offset + idx, full_column_name)
                else:
                    offset -= 1

            # arrange columns according to results order
            df = df[reordered_columns]

            # assign column types
            df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

            # drop NaNs
            if dropna:
                # df = df.dropna(axis=0, how='all', inplace=False)
                df.dropna(axis=0, how="all", inplace=True)

            # group by entity
            if groupby_entity:
                df = {str(e): df_group for e, df_group in df.groupby(entity_col)}
            # convert to wide format with columns format "{entity_name} : {column_name"
            elif not with_entity_column:
                df = self.convert_dataframe_from_long_to_wide(df)
        else:
            raise ValueError(
                "PetroVisor::convert_psharp_table_to_dataframe(): "
                "unknown P# table type!"
            )

        return df

    # Get signal data from DataFrame

    def get_signal_data_from_dataframe(
        self,
        df: pd.DataFrame,
        signals: Optional[Dict] = None,
        only_existing_entities: bool = True,
        entity_type: str = "",
        entities: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get signal data from DataFrame

        Parameters
        ----------
        df : DataFrame
            Table
        signals : dict, default None
            Dictionary map from 'table column name' to 'workspace signal name'
        entities : dict, default None
            Dictionary map from 'table entity name' to 'workspace entity name'
        only_existing_entities : bool, default True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        """
        # get columns
        columns = df.columns
        # num_cols = len(columns)

        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()

        # entities map
        entities_map = copy.deepcopy(entities) if entities else {}

        # filter out undefined entities
        select_entities = (
            self.get_entity_names(entity_type=entity_type, **kwargs)
            if only_existing_entities
            else None
        )
        if select_entities and entities_map:
            entities_map_rev = {v: k for k, v in entities_map.items()}
            select_entities = [
                entities_map_rev[e] if (e in entities_map_rev) else e
                for e in select_entities
            ]

        # data containers keyed by Data/Save endpoint field names
        data_to_save = {
            "StaticNumericData": [],
            "StaticStringData": [],
            "TimeNumericData": [],
            "TimeStringData": [],
            "DepthNumericData": [],
            "DepthStringData": [],
            "PVTNumericData": [],
        }

        # collect data info
        with_entity_col = entity_col in columns
        if not with_entity_col:
            # remove entity name from column names
            col_names = DataFrameMixinHelper.remove_entities_from_columns(columns)
            # extract entity name from column names
            col_entities = DataFrameMixinHelper.get_entities_from_columns(columns)
            # list of all entities
            entity_list: List[str] = DataFrameMixinHelper.get_unique_non_empty_names(
                col_entities
            )
            # get column data info
            col_data = {
                e: [
                    (cname, cidx)
                    for cidx, (centity, cname) in enumerate(
                        zip(col_entities, col_names)
                    )
                    if centity == e
                ]
                for e in entity_list
                if (select_entities is None) or (e in select_entities)
            }
        else:
            # get column names
            col_names = columns
            # get list of entities
            entity_list: List[str] = (
                list(set(df[entity_col].tolist())) if (entity_col in columns) else []
            )
            # get column data info
            col_data = {
                e: [(cname, cidx) for cidx, cname in enumerate(columns)]
                for e in entity_list
                if (select_entities is None) or (e in select_entities)
            }

        # remap entities data
        if entities_map:
            col_data = {
                entities_map[e] if (e in entities_map) else e: d
                for e, d in col_data.items()
            }

        # 'Date' column
        date_index = None
        for i, column_name in enumerate(col_names):
            if column_name == date_col:
                date_index = i
                break

        # 'Depth' column
        depth_index = None
        for i, column_name in enumerate(col_names):
            if (
                column_name == depth_col
                or self.get_column_name_without_unit(column_name) == depth_col
            ):
                depth_index = i
                break

        # Multi-axis index specs for signal types that require more than one index column.
        # Each entry: signal_type_name → ordered list of (axis_key, axis_dtype) pairs.
        # axis_key  — field name expected by the Data/Save endpoint ("Pressure", "Temperature").
        # axis_dtype — passed to get_json_valid_value.
        # To support a new multi-index signal type add one entry to each dict.
        _MULTI_AXIS_SPECS: Dict[str, List[Tuple[str, str]]] = {
            SignalType.PVT.name: [
                ("Pressure", "Numeric"),
                ("Temperature", "Numeric"),
            ],
        }
        _MULTI_AXIS_BUCKET: Dict[str, str] = {
            SignalType.PVT.name: "PVTNumericData",
        }

        # For each multi-axis type, locate the column indices of its axes in col_names.
        # Result: {signal_type_name: {axis_key: column_index}}
        # Only populated when ALL axes for a type are found; a partial match is ignored so
        # a lone "Pressure" column in a non-PVT DataFrame is never treated as an index axis.
        _multi_axis_index: Dict[str, Dict[str, int]] = {}
        for _sig_type_name, _axes in _MULTI_AXIS_SPECS.items():
            _found: Dict[str, int] = {}
            for _axis_key, _axis_dtype in _axes:
                for i, column_name in enumerate(col_names):
                    if self.get_column_name_without_unit(column_name) == _axis_key:
                        _found[_axis_key] = i
                        break
            if len(_found) == len(_axes):
                _multi_axis_index[_sig_type_name] = _found

        # flat set of all axis base names that are confirmed index columns
        _multi_axis_bases: Set[str] = {
            axis_key for axes in _multi_axis_index.values() for axis_key in axes
        }

        # get signal info
        def _get_signal_info(
            column_name: str, signal_names: List[str], signals: Optional[Dict] = None
        ):
            column_name_without_unit = self.get_column_name_without_unit(column_name)
            column_unit_name = self.get_column_unit(column_name)
            if signals:
                signal = (
                    signals[column_name]
                    if (column_name in signals)
                    else (
                        signals[column_name_without_unit]
                        if (column_name_without_unit in signals)
                        else None
                    )
                )
            else:
                signal = None
            if not signal:
                signal_name = column_name_without_unit
                signal_unit = column_unit_name
            elif isinstance(signal, str):
                signal_name_without_unit = self.get_column_name_without_unit(signal)
                signal_unit_name = self.get_column_unit(signal)
                signal_name = signal_name_without_unit
                signal_unit = signal_unit_name if signal_unit_name else column_unit_name
            elif (
                isinstance(signal, tuple)
                or isinstance(signal, list)
                and len(signal) > 0
            ):
                signal_name = signal[0]
                signal_unit = signal[1] if (len(signal) > 1) else column_unit_name
            else:
                signal_name = self.get_column_name_without_unit(column_name)
                signal_unit = self.get_column_unit(column_name)
                for fname in ["Signal", "Name", "SignalName"]:
                    if fname in signal:
                        signal_name = signal[fname]
                        break
                    elif fname.lower() in signal:
                        signal_name = signal[fname.lower()]
                        break
                for fname in ["Unit", "UnitName", "SignalUnit"]:
                    if fname in signal:
                        signal_unit = signal[fname]
                        break
                    elif fname.lower() in signal:
                        signal_unit = signal[fname.lower()]
                        break
            # get signal
            if signal_name in signal_names:
                signal_obj = self.get_signal(signal_name, **kwargs)
                if signal_obj:
                    if not signal_unit and "StorageUnitName" in signal_obj:
                        signal_unit = signal_obj["StorageUnitName"]
                    signal_type = (
                        signal_obj["SignalType"]
                        if ("SignalType" in signal_obj)
                        else None
                    )
                    return {
                        "Signal": signal_name,
                        "Unit": signal_unit,
                        "SignalType": signal_type,
                    }
            return None

        # check whether non index column
        def _is_index_column(column_name: str) -> bool:
            base = self.get_column_name_without_unit(column_name)
            return column_name in {date_col, depth_col, entity_col, alias_col} or (
                base in _multi_axis_bases
            )

        # get signals
        col_names = list(set(col_names))
        existing_signal_names = self.get_signal_names(**kwargs)
        column_signals = {
            cname: _get_signal_info(cname, existing_signal_names, signals=signals)
            for cname in col_names
            if not _is_index_column(cname)
        }

        # pre-group by entity for long format to avoid repeated DataFrame filtering
        entity_groups: Dict[str, pd.DataFrame] = (
            {str(e): g for e, g in df.groupby(entity_col, sort=False)}
            if with_entity_col
            else {}
        )

        def _val_series(
            entity_df: pd.DataFrame, col_name: str, col_idx: int
        ) -> pd.Series:
            if with_entity_col:
                return entity_df[col_name]
            return df.iloc[:, col_idx]

        def _index_series(
            entity_df: pd.DataFrame, idx: Optional[int], idx_col: str
        ) -> pd.Series:
            if idx is None:
                return pd.Series(dtype=object)
            if with_entity_col:
                # Use positional index — handles "Depth [m]" vs "Depth" mismatch
                return entity_df.iloc[:, idx]
            return df.iloc[:, idx]

        def _build_records(
            idx_s: pd.Series,
            val_s: pd.Series,
            idx_key: str,
            idx_dtype: str,
            val_dtype: str,
        ) -> List[Dict[str, Any]]:
            sub = pd.DataFrame({idx_key: idx_s.values, "Value": val_s.values})
            return [
                {
                    idx_key: self.get_json_valid_value(
                        r[idx_key], dtype=idx_dtype, **kwargs
                    ),
                    "Value": self.get_json_valid_value(
                        r["Value"], dtype=val_dtype, **kwargs
                    ),
                }
                for r in sub.to_dict("records")
            ]

        def _build_multi_index_records(
            axis_series: List[Tuple[str, str, pd.Series]],
            val_s: pd.Series,
        ) -> List[Dict[str, Any]]:
            """Build [{axis0: v, axis1: v, ..., Value: v}] for multi-index signals.

            axis_series: [(axis_key, axis_dtype, series), ...]
            """
            frame: Dict[str, Any] = {
                axis_key: axis_s.values for axis_key, _, axis_s in axis_series
            }
            frame["Value"] = val_s.values
            sub = pd.DataFrame(frame)
            return [
                {
                    **{
                        axis_key: self.get_json_valid_value(
                            r[axis_key], dtype=axis_dtype, **kwargs
                        )
                        for axis_key, axis_dtype, _ in axis_series
                    },
                    "Value": self.get_json_valid_value(
                        r["Value"], dtype="Numeric", **kwargs
                    ),
                }
                for r in sub.to_dict("records")
            ]

        # collect signals data
        for _entity_name, d in col_data.items():
            # make sure that entity column is string
            entity_name = str(_entity_name)
            entity_df = entity_groups.get(entity_name, pd.DataFrame())
            # collect signals data
            for col in d:
                # column name
                column_name = col[0]
                # column index
                column_index = col[1]
                if column_name in column_signals and column_signals[column_name]:
                    signal = column_signals[column_name]
                    signal_name = signal["Signal"]
                    signal_unit_name = signal["Unit"]
                    signal_type = signal["SignalType"]

                    # static signal
                    if signal_type == SignalType.Static.name:
                        vals = _val_series(
                            entity_df, column_name, column_index
                        ).tolist()
                        if vals:
                            data_to_save["StaticNumericData"].append(
                                {
                                    "Entity": entity_name,
                                    "Signal": signal_name,
                                    "Unit": signal_unit_name,
                                    "Data": self.get_json_valid_value(
                                        vals[0], dtype="Numeric", **kwargs
                                    ),
                                }
                            )
                    elif signal_type == SignalType.String.name:
                        vals = _val_series(
                            entity_df, column_name, column_index
                        ).tolist()
                        if vals:
                            data_to_save["StaticStringData"].append(
                                {
                                    "Entity": entity_name,
                                    "Signal": signal_name,
                                    "Unit": signal_unit_name,
                                    "Data": self.get_json_valid_value(
                                        vals[0], dtype="String", **kwargs
                                    ),
                                }
                            )
                    # time signal
                    elif signal_type == SignalType.TimeDependent.name:
                        data_to_save["TimeNumericData"].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": _build_records(
                                    _index_series(entity_df, date_index, date_col),
                                    _val_series(entity_df, column_name, column_index),
                                    "Date",
                                    "Time",
                                    "Numeric",
                                ),
                            }
                        )
                    elif signal_type == SignalType.StringTimeDependent.name:
                        data_to_save["TimeStringData"].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": _build_records(
                                    _index_series(entity_df, date_index, date_col),
                                    _val_series(entity_df, column_name, column_index),
                                    "Date",
                                    "Time",
                                    "String",
                                ),
                            }
                        )
                    # depth signal
                    elif signal_type == SignalType.DepthDependent.name:
                        data_to_save["DepthNumericData"].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": _build_records(
                                    _index_series(entity_df, depth_index, depth_col),
                                    _val_series(entity_df, column_name, column_index),
                                    "Depth",
                                    "Numeric",
                                    "Numeric",
                                ),
                            }
                        )
                    elif signal_type == SignalType.StringDepthDependent.name:
                        data_to_save["DepthStringData"].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": _build_records(
                                    _index_series(entity_df, depth_index, depth_col),
                                    _val_series(entity_df, column_name, column_index),
                                    "Depth",
                                    "Numeric",
                                    "String",
                                ),
                            }
                        )
                    # multi-axis signal (e.g. PVT: Pressure + Temperature)
                    elif signal_type in _multi_axis_index:
                        _axes_spec = _MULTI_AXIS_SPECS[signal_type]
                        _axes_idx = _multi_axis_index[signal_type]
                        _axis_series = [
                            (
                                axis_key,
                                axis_dtype,
                                _index_series(entity_df, _axes_idx[axis_key], axis_key),
                            )
                            for axis_key, axis_dtype in _axes_spec
                        ]
                        if all(not s.empty for _, _, s in _axis_series):
                            data_to_save[_MULTI_AXIS_BUCKET[signal_type]].append(
                                {
                                    "Entity": entity_name,
                                    "Signal": signal_name,
                                    "Unit": signal_unit_name,
                                    "Data": _build_multi_index_records(
                                        _axis_series,
                                        _val_series(
                                            entity_df, column_name, column_index
                                        ),
                                    ),
                                }
                            )
                    else:
                        raise ValueError(
                            f"PetroVisor::get_signal_data_from_dataframe(): "
                            f"signal type: '{signal_type}' is not supported yet."
                        )
        return data_to_save

    # convert dataframe from wide to long format
    def convert_dataframe_from_wide_to_long(
        self, df: pd.DataFrame, inplace: bool = False, **kwargs
    ):
        """
        Convert DataFrame from wide to long format.
        Wide format assumes column names as '{entity_name} : {column_name}'
        Long format assumes that DataFrame has 'Entity' column.

        Parameters
        ----------
        df : DataFrame
            DataFrame
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        """

        # standard columns
        entity_col = self.get_entity_column_name()

        # define column indices and entities
        column_indices = []
        entity_columns = []
        for col in df.columns:
            c = col.split(" : ")
            if len(c) > 1:
                entity_columns.append((c[0], c[1]))
            else:
                column_indices.append(col)
        if not entity_columns:
            return df

        # set indices
        df_long, default_index_col = DataFrameMixinHelper.set_dataframe_index(
            df, column_indices, inplace=inplace, add_default_index=True, **kwargs
        )
        # assign new column names
        df_long.columns = pd.MultiIndex.from_tuples(
            entity_columns, names=[entity_col, None]
        )
        # stack entity column and reset index
        return df_long.stack(0).reset_index().drop(columns=default_index_col)

    # convert dataframe from long to wide format
    def convert_dataframe_from_long_to_wide(
        self,
        df: pd.DataFrame,
        indices: Optional[Union[str, List[str]]] = None,
        inplace: bool = False,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Convert DataFrame from long to wide format.
        Wide format assumes column names as '{entity_name} : {column_name}'
        Long format assumes that DataFrame has 'Entity' column.

        Parameters
        ----------
        df : DataFrame
            DataFrame
        indices : str | list, default None
            Indices columns
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        """

        # check whether entity column is present
        entity_col = self.get_entity_column_name()
        if entity_col not in df.columns:
            return df

        # define column indices
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()
        alias_col = self.get_alias_column_name()
        _raw_indices = (
            copy.deepcopy(indices)
            if indices
            else [date_col, depth_col, alias_col, entity_col]
        )
        column_indices: List[str] = (
            [_raw_indices] if isinstance(_raw_indices, str) else _raw_indices
        )
        if entity_col not in column_indices:
            column_indices.append(entity_col)

        # set indices
        df_wide, default_index_col = DataFrameMixinHelper.set_dataframe_index(
            df, column_indices, inplace=inplace, add_default_index=True, **kwargs
        )
        # unstack 'Entity' column
        df_wide = (
            df_wide.unstack(entity_col)
            .reset_index()
            .sort_index(axis=1)
            .drop(columns=default_index_col)
        )
        # rename column as '{entity_name} : {column_name}'
        df_wide.columns = [
            f"{c[1]} : {c[0]}" if c[1] else c[0] for c in df_wide.columns
        ]
        return df_wide

    # get valid json value
    def get_json_valid_value(
        self, value: Any, dtype: Union[str, SignalType] = "unknown", **kwargs
    ) -> Any:
        """
        Convert value to json accepted format

        Parameters
        ----------
        value : Any
            Value
        dtype : str | SignalType, default 'unknown'
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        is_null = pd.isnull(value)
        if not isinstance(dtype, str):
            dtype = self.get_signal_data_type_name(dtype, **kwargs)
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            # nan_value = pd.NA
            # nan_value = np.nan
            # nan_value = float('NaN')
            nan_value = "NaN"
            return (
                nan_value
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        elif dtype in {"time", "datetime", "datetime64[ns]"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else self.datetime_to_string(value, **kwargs)
            )
        elif dtype in {"string", "str"}:
            return "" if is_null else value
        elif dtype in {"bool", "boolean"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        elif dtype in {"unknown", "object"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        return None if is_null else value

    # assign DataFrame column to corresponding types
    def assign_dataframe_column_types(
        self,
        df: pd.DataFrame,
        columns_dtype: Dict,
        default_dtype: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Convert DataFrame columns to column types

        Parameters
        ----------
        df : DataFrame
            Table
        columns_dtype : dict
            Dictionary {"column name" : "type"}
        default_dtype : str, default None
            Default type to use: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        columns = df.columns
        for c in columns:
            if c in columns_dtype:
                df[c] = self.column_to_dtype(df, c, columns_dtype[c], **kwargs)
            elif default_dtype:
                df[c] = self.column_to_dtype(df, c, default_dtype, **kwargs)
        return df

    # get DataFrame data type name
    def convert_to_dtype_name(self, dtype: str, **kwargs) -> str:
        """
        Convert type name to DataFrame accepted type name

        Parameters
        ----------
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            return "float64"
        elif dtype in {"time", "datetime", "datetime64[ns]"}:
            return "datetime64[ns]"
        elif dtype in {"string"}:
            return "string"
        elif dtype in {"boolean", "bool"}:
            return "bool"
        elif dtype in {"unknown", "object"}:
            return "object"
        return "object"

    # convert DataFrame column to bool
    def column_to_dtype(
        self, df: pd.DataFrame, column: str, dtype: str, **kwargs
    ) -> pd.DataFrame:
        """
        Convert DataFrame column to specified type

        Parameters
        ----------
        df : DataFrame
            Table
        column: str
            Column name
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        if not dtype:
            return df[column]
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            df[column] = self.column_to_numeric(df, column, **kwargs)
        elif dtype in {"time", "datetime", "datetime64[ns]"}:
            df[column] = self.column_to_datetime(df, column, **kwargs)
        elif dtype in {"string", "str"}:
            df[column] = self.column_to_string(df, column, **kwargs)
        elif dtype in {"bool", "boolean"}:
            df[column] = self.column_to_bool(df, column, **kwargs)
        elif dtype in {"unknown", "object"}:
            df[column] = self.column_to_object(df, column, **kwargs)
        return df[column]

    # convert DataFrame column to 'object'
    def column_to_object(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'object' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("object")

    # convert DataFrame column to 'bool'
    def column_to_bool(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'bool' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("bool")

    # convert DataFrame column to 'string'
    def column_to_string(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'string' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("string")

    # convert DataFrame column to 'numeric'
    def column_to_numeric(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'numeric' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('float64')
        return pd.to_numeric(df[column])

    # convert DataFrame column to 'datetime'
    def column_to_datetime(self, df: pd.DataFrame, column, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'datetime' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('datetime64[ns]')
        # return pd.to_datetime(df[column], infer_datetime_format=False)
        # return pd.to_datetime(df[column], infer_datetime_format=True)
        # return pd.to_datetime(df[column], format=format)
        # return pd.to_datetime(df[column])
        datetime_args = {
            arg: kwargs[arg]
            for arg in [
                "errors",
                "dayfirst",
                "yearfirst",
                "utc",
                "format",
                "exact",
                "unit",
                "infer_datetime_format",
                "origin",
                "cache",
            ]
            if (arg in kwargs)
        }
        if datetime_args:
            return cast(pd.Series, pd.to_datetime(df[column], **datetime_args))
        return cast(pd.Series, pd.to_datetime(df[column]))

    # convert datetime to string
    def datetime_to_string(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%dT%H:%M:%S.%f",
        **kwargs,
    ) -> str:
        """
        Convert datetime object to string representation

        Parameters
        ----------
        d : datetime
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """

        def parse_date(date_string: str, desired_format: str) -> str:
            formats_to_try = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                # other formats might be added
            ]
            for format_str in formats_to_try:
                try:
                    date_object = datetime.strptime(date_string, format_str)
                    return date_object.strftime(desired_format)
                except ValueError:
                    pass
            return str(date_string).strip()

        return (
            ""
            if pd.isnull(d)
            else (
                d.strftime(format or "%Y-%m-%dT%H:%M:%S.%f")
                if isinstance(d, datetime)
                else parse_date(d, format or "%Y-%m-%dT%H:%M:%S.%f")
            )
        )

    # convert string to datetime
    def string_to_datetime(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%d %H:%M:%S",
        **kwargs,
    ) -> datetime:
        """
        Convert date from string representation to datetime object

        Parameters
        ----------
        d : str
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """
        return datetime.strptime(str(d), format or "%Y-%m-%d %H:%M:%S")

    # get column name without unit
    def get_column_name_without_unit(self, column_name: str, **kwargs) -> str:
        """
        Get column name without unit from column name

        Parameters
        ----------
        column_name : str | int
            Column name
        """
        if not isinstance(column_name, str):
            return column_name
        cname = column_name.split("[")[0].strip()
        return cname

    # get column unit
    def get_column_unit(self, column_name: str, **kwargs) -> str:
        """
        Get column unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        if not isinstance(column_name, str):
            return ""
        column_name = column_name.strip()
        cunit = re.findall(r"\[(.*?)\]", column_name)
        if cunit and len(cunit) > 0:
            return cunit[0]
        return ""

    # get column name and unit
    def get_column_name_and_unit(self, column_name: Any, **kwargs) -> Tuple[Any, str]:
        """
        Get column name and unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        if not isinstance(column_name, str):
            return column_name, ""
        column_name = column_name.strip()
        cname = self.get_column_name_without_unit(column_name, **kwargs)
        cunit = self.get_column_unit(column_name, **kwargs)
        return cname, cunit

    # get 'Entity' column name
    def get_entity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Entity' column name used in return tables from api calls
        """
        return DataFrameMixinHelper.COLUMN_ENTITY

    # get 'Alias' column name
    def get_alias_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Alias' column name used in return tables from api calls
        """
        return DataFrameMixinHelper.COLUMN_ALIAS

    # get 'EntityType' column name
    def get_entity_type_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Type' column name used in return tables from api calls
        """
        return "Type"

    # get 'Opportunity' column name
    def get_opportunity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'IsOpportunity' column name used in return tables from api calls
        """
        return "IsOpportunity"

    # get 'Date' column name
    def get_date_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Date' column name used in return tables from api calls
        """
        return DataFrameMixinHelper.COLUMN_DATE

    # get 'Time' column name
    def get_time_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Time' column name used in return tables from api calls
        """
        return "Time"

    # get 'Depth' column name
    def get_depth_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Depth' column name used in return tables from api calls
        """
        return DataFrameMixinHelper.COLUMN_DEPTH

    # get signal data type name
    def get_signal_data_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str:
        """
        Get data type name for corresponding signal type

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, str):
            signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        elif not isinstance(signal_type, SignalType):
            raise ValueError(
                f"PetroVisor::get_signal_data_type_name(): "
                f"unknown 'signal_type'! "
                f"Should be one of {[t.name for t in SignalType]} or {SignalType.__name__} enum."
            )
        if signal_type in {
            SignalType.Static,
            SignalType.TimeDependent,
            SignalType.DepthDependent,
            SignalType.PVT,
        }:
            return "numeric"
        elif signal_type in {
            SignalType.String,
            SignalType.StringTimeDependent,
            SignalType.StringDepthDependent,
        }:
            return "string"
        raise ValueError(
            f"PetroVisor::get_signal_data_type_name(): "
            f"'{signal_type}' is not supported yet."
        )

    # get signal range name
    def get_signal_range_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str:
        """
        Get data range type name for corresponding signal type

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, str):
            signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        elif not isinstance(signal_type, SignalType):
            raise ValueError(
                f"PetroVisor::get_signal_range_type_name(): "
                f"unknown 'signal_type'! "
                f"Should be one of {[t.name for t in SignalType]} or {SignalType.__name__} enum."
            )
        if signal_type in {SignalType.TimeDependent, SignalType.StringTimeDependent}:
            return "time"
        elif signal_type in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            return "numeric"
        elif signal_type in {SignalType.Static, SignalType.String, SignalType.PVT}:
            return ""
        raise ValueError(
            f"PetroVisor::get_signal_range_type_name(): "
            f"'{signal_type}' is not supported yet."
        )

    # convert list to dictionary
    def list_to_dict(self, x, num_cols, **kwargs):
        if num_cols == 0:
            return {
                self.get_json_valid_value(
                    idx, "numeric", **kwargs
                ): self.get_json_valid_value(row, "numeric", **kwargs)
                for idx, row in enumerate(x)
            }
        elif num_cols == 1:
            return {
                self.get_json_valid_value(
                    idx, "numeric", **kwargs
                ): self.get_json_valid_value(row[0], "numeric", **kwargs)
                for idx, row in enumerate(x)
            }
        elif num_cols > 1:
            return {
                self.get_json_valid_value(
                    row[0], "numeric", **kwargs
                ): self.get_json_valid_value(row[1], "numeric", **kwargs)
                for row in x
            }
