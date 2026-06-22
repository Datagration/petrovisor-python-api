from typing import (
    Any,
    Optional,
    Sequence,
    Union,
    List,
    Set,
    Dict,
    Tuple,
    cast,
)

from datetime import datetime
import pandas as pd
import numpy as np
import warnings

from petrovisor.api.utils.validators import Validator
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.enums.items import ItemType
from petrovisor.api.enums.internal_dtypes import SignalType
from petrovisor.api.methods.dataframes import DataFrameMixinHelper
from petrovisor.api.methods.contexts import ContextsMixinHelper
from petrovisor.api.enums.increments import (
    TimeIncrement,
    DepthIncrement,
    AggregationFunction,
)
from petrovisor.api.models.signal import Signal
from petrovisor.api.models.entity import Entity
from petrovisor.api.models.entity_set import EntitySet
from petrovisor.api.models.hierarchy import Hierarchy
from petrovisor.api.models.scope import Scope
from petrovisor.api.models.context import Context
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsDataFrames,
    SupportsContextRequests,
    SupportsEntitiesRequests,
    SupportsUnitsRequests,
)


# Signals mixin helper
class SignalsMixinHelper:
    """
    Signals mixin helper — endpoint constants and DataFrame construction helpers.
    """

    # Endpoint routes — signals CRUD
    ENDPOINT_SIGNALS = "Signals"
    ENDPOINT_SIGNALS_ALL = "Signals/All"
    ENDPOINT_SIGNALS_ADD = "Signals/Add"
    ENDPOINT_ENTITIES = "Entities"

    # Endpoint routes — data operations
    ENDPOINT_TIME_RANGE = "Data/TimeRange"
    ENDPOINT_DEPTH_RANGE = "Data/DepthRange"
    ENDPOINT_RETRIEVE = "Data/Retrieve"
    ENDPOINT_TOP = "Data/Top"
    ENDPOINT_SAVE = "Data/Save"
    ENDPOINT_DELETE = "Data/Delete"
    ENDPOINT_ACQUIRE = "Data/Acquire"

    # -------------------------------------------------------------------------
    # Request-building helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_retrieve_rqst(
        entity_names: List[str],
        signals_with_units: List[Dict[str, str]],
        *,
        has_time: bool = False,
        has_depth: bool = False,
        has_pvt: bool = False,
        time_start: Optional[Any] = None,
        time_end: Optional[Any] = None,
        time_step: Optional[Any] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Any] = None,
        depth_unit: Optional[str] = None,
        hierarchy: Optional[Any] = None,
        scenario: Optional[Any] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        with_gaps: Optional[bool] = None,
        gap_value: Optional[float] = None,
        gap_string_value: Optional[str] = None,
        nrows: Optional[int] = None,
        aggfunc: Optional[Any] = None,
        with_workspace_values: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Build a Data/Retrieve request body dict."""
        rqst: Dict[str, Any] = {
            "Combinations": {
                "Entities": entity_names,
                "Signals": signals_with_units,
            }
        }
        if has_time:
            if time_start is not None:
                rqst["TimeStart"] = time_start
            if time_end is not None:
                rqst["TimeEnd"] = time_end
            if time_step is not None:
                rqst["TimeIncrement"] = time_step
        if has_depth:
            if depth_start is not None:
                rqst["DepthStart"] = depth_start
            if depth_end is not None:
                rqst["DepthEnd"] = depth_end
            if depth_step is not None:
                rqst["DepthIncrement"] = depth_step
        if depth_unit:
            rqst["DepthUnit"] = depth_unit
        if hierarchy:
            rqst["Hierarchy"] = hierarchy
        if scenario:
            rqst["Scenarios"] = (
                [scenario]
                if not isinstance(scenario, (list, tuple, set))
                else list(scenario)
            )
        if has_pvt:
            if pressure_unit:
                rqst["PressureUnit"] = pressure_unit
            if temperature_unit:
                rqst["TemperatureUnit"] = temperature_unit
        if (
            with_gaps is not None
            or gap_value is not None
            or gap_string_value is not None
        ):
            options: Dict[str, Any] = rqst.setdefault("Options", {})
            options["WithGaps"] = with_gaps if with_gaps is not None else True
            if gap_value is not None:
                options["GapValue"] = gap_value
            if gap_string_value is not None:
                options["GapStringValue"] = gap_string_value
        if nrows is not None:
            rqst["TopRecords"] = nrows
        if aggfunc is not None:
            rqst["Aggregation"] = (
                aggfunc.value if isinstance(aggfunc, AggregationFunction) else aggfunc
            )
        if with_workspace_values is not None:
            rqst["IncludeWorkspaceData"] = with_workspace_values
        return rqst

    # -------------------------------------------------------------------------
    # Resolve helpers  (accept api=self to avoid circular instance dependencies)
    # -------------------------------------------------------------------------

    @staticmethod
    def _resolve_signals(
        signals: Union[str, Sequence[Union[str, Dict, Tuple[Any, str]]]],
        api: Any,
    ) -> List[Dict]:
        """Resolve signal names / (name, unit) specs to fully-populated signal dicts.

        Each returned dict has a ``UnitName`` key set to the requested unit (or the
        signal's storage unit when none was requested).

        Uses ``resolve_item`` (list-endpoint pre-check) instead of ``get_signal``
        directly, avoiding the ~10 s per-attempt penalty that the individual GET
        endpoint incurs on a 404.

        Raises
        ------
        ValueError
            If any signal is not found after retries.
        """
        if isinstance(signals, (list, tuple)):
            signal_list = list(signals)
        else:
            signal_list = [signals]

        result: List[Dict] = []
        for signal in signal_list:
            if isinstance(signal, (list, tuple)):
                signal_name = signal[0]
                unit_name = signal[1] if len(signal) > 1 else None
            else:
                signal_name, unit_name = api.get_column_name_and_unit(signal)
            signal_name = ApiHelper.get_object_name(signal_name)

            # Single list-based lookup first (fast, no 404 penalty).
            # On miss, retry via individual GET which converges in ~0.5 s
            # once the item propagates (after="create" path).
            s = api.resolve_item(ItemType.Signal, signal_name)
            if s is None:
                s = api.resolve_item(
                    ItemType.Signal,
                    signal_name,
                    after="create",
                    max_retries=3,
                    retry_delay=1.0,
                )

            if s is None:
                raise ValueError(
                    f"PetroVisor::_resolve_signals(): "
                    f"Signal '{signal_name}' not found. "
                    f"This may be due to: (1) signal does not exist, "
                    f"(2) backend eventual consistency issues. "
                    f"Please verify the signal exists using "
                    f"api.item_exists(ItemType.Signal, '{signal_name}') "
                    f"or api.get_signal('{signal_name}') before loading data."
                )

            s["UnitName"] = (
                ApiHelper.get_object_name(unit_name or "") or s["StorageUnitName"]
            )
            result.append(s)
        return result

    @staticmethod
    def _build_pvt_df(
        data_pvt_num: List[Dict],
        entity_col: str,
        pressure_unit: str,
        temperature_unit: str,
        signals_with_units_map: Dict[str, str],
        backend: str,
    ) -> Optional[Any]:
        """Build a PVT DataFrame — thin wrapper around DataFrameMixinHelper._build_multi_index_df."""
        return DataFrameMixinHelper._build_multi_index_df(
            data_pvt_num,
            entity_col=entity_col,
            index_cols=["Pressure", "Temperature"],
            col_unit_labels=[pressure_unit, temperature_unit],
            signals_with_units_map=signals_with_units_map,
            backend=backend,
        )

    # Range-resolution helpers delegated to ContextsMixinHelper
    _resolve_time_range = ContextsMixinHelper._resolve_time_range
    _resolve_depth_range = ContextsMixinHelper._resolve_depth_range

    # DataFrame builder aliases (all live in DataFrameMixinHelper)
    _build_combined_df_narwhals = DataFrameMixinHelper._build_combined_df_narwhals

    # -------------------------------------------------------------------------
    # DataFrame construction helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _classify_signals(signals: List[Dict]) -> Dict[str, Any]:
        """Classify a resolved signal list by type.

        Returns a single dict that replaces the various inline ``any(...)``
        checks and list comprehensions scattered across ``load_signals_data``:

        ``has_time``      — any time-dependent signal (numeric or string)
        ``has_depth``     — any depth-dependent signal (numeric or string)
        ``has_static``    — any static / scalar signal
        ``has_pvt``       — any PVT signal
        ``time_signals``  — full signal dicts for time-type signals
        ``depth_signals`` — full signal dicts for depth-type signals
        ``signals_num``   — ``[{"Signal": ..., "Unit": ...}]`` for numeric types
        ``signals_str``   — ``[{"Signal": ..., "Unit": ...}]`` for string types
        """
        _TIME = {"TimeDependent", "StringTimeDependent"}
        _DEPTH = {"DepthDependent", "StringDepthDependent"}
        _NUMERIC = {"TimeDependent", "DepthDependent", "Static", "PVT"}
        _STRING = {"StringTimeDependent", "StringDepthDependent", "String"}
        _STATIC = {"Static", "String"}

        time_sigs = [s for s in signals if s["SignalType"] in _TIME]
        depth_sigs = [s for s in signals if s["SignalType"] in _DEPTH]

        return {
            "has_time": bool(time_sigs),
            "has_depth": bool(depth_sigs),
            "has_static": any(s["SignalType"] in _STATIC for s in signals),
            "has_pvt": any(s["SignalType"] == "PVT" for s in signals),
            "time_signals": time_sigs,
            "depth_signals": depth_sigs,
            "signals_num": [
                {"Signal": s["Name"], "Unit": s["UnitName"]}
                for s in signals
                if s["SignalType"] in _NUMERIC
            ],
            "signals_str": [
                {"Signal": s["Name"], "Unit": s["UnitName"]}
                for s in signals
                if s["SignalType"] in _STRING
            ],
        }


# Signals API calls
class SignalsMixin(
    SupportsDataFrames,
    SupportsContextRequests,
    SupportsEntitiesRequests,
    SupportsItemRequests,
    SupportsUnitsRequests,
    SupportsRequests,
):
    """
    Signals API calls
    """

    # get signal type
    def get_signal_type(self, signal: Union[str, Dict], **kwargs) -> str:
        """
        Get signal type

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        return self.get_item_field(ItemType.Signal, signal, "SignalType", **kwargs)

    # get signal 'MeasurementName'
    def get_signal_measurement_name(self, signal: Union[str, Dict], **kwargs) -> Any:
        """
        Get signal measurement name

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        field_name = "MeasurementName"
        if isinstance(signal, str):
            signal_name = ApiHelper.get_object_name(signal)
            signal = self.get_item(ItemType.Signal, signal_name, **kwargs)
        if not signal:
            raise ValueError(
                f"PetroVisor::get_signal_measurement_name(): "
                f"signal '{signal}' cannot be found!"
            )
        elif not ApiHelper.has_field(signal, field_name):
            raise ValueError(
                f"PetroVisor::get_signal_measurement_name(): "
                f"signal '{signal}' doesn't have '{field_name}' field!"
            )
        return signal[field_name]

    # get signal storage 'Unit'
    def get_signal_unit(self, signal: Union[str, Dict], **kwargs) -> Any:
        """
        Get signal unit

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        return self.get_item_field(ItemType.Signal, signal, "StorageUnitName", **kwargs)

    # get signal 'Units'
    def get_signal_units(self, signal: Union[str, Dict], **kwargs) -> Any:
        """
        Get all units of signal measurement

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        measurement_name = self.get_signal_measurement_name(signal, **kwargs)
        return self.get_measurement_units(measurement_name, **kwargs)

    # get signal 'Unit' names
    def get_signal_unit_names(self, signal: Union[str, Dict], **kwargs) -> Any:
        """
        Get all unit names of signal measurement

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        measurement_name = self.get_signal_measurement_name(signal, **kwargs)
        return self.get_measurement_unit_names(measurement_name, **kwargs)

    # get signal
    def get_signal(
        self, name: str, short_name: Optional[str] = "", **kwargs
    ) -> Optional[Dict]:
        """
        Get signal by name or short name

        Parameters
        ----------
        name : str
            Signal name
        short_name : str
            Signal short name
        """
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        if short_name:
            signal = self.get(f"{route}/{self.encode(short_name)}/Signal", **kwargs)
        else:
            signal = None
        if signal is None:
            return self.get(f"{route}/{self.encode(name)}", **kwargs)
        return None

    # get signals
    def get_signals(
        self,
        signal_type: Union[str, SignalType] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[Dict]:
        """
        Get signals. Filter optionally by signal type and entity

        Parameters
        ----------
        signal_type : str | SignalType
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        # get signals by signal type
        if signal_type:
            signal_type = self.get_signal_type_enum(signal_type, **kwargs).name
            signals = self.get(f"{route}/{signal_type}/Signals", **kwargs)
        # get all signals
        else:
            signals = self.get(SignalsMixinHelper.ENDPOINT_SIGNALS_ALL, **kwargs)
        # get signals by 'Entity' name
        if entity:
            signal_names = self.get_signal_names(
                signal_type=None, entity=entity, **kwargs
            )
            if signal_names and signals:
                return [s for s in signals if s["Name"] in signal_names]
            return []
        return signals if signals is not None else []

    # get signal names
    def get_signal_names(
        self,
        signal_type: Optional[Union[str, SignalType]] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[str]:
        """
        Get signal names. Filter optionally by signal type and entity

        Parameters
        ----------
        signal_type : str
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        # get signals by 'Entity' name
        if entity:
            entities_route = SignalsMixinHelper.ENDPOINT_ENTITIES
            entity_name = ApiHelper.get_object_name(entity)
            signal_names = self.get(
                f"{entities_route}/{self.encode(entity_name)}/Signals", **kwargs
            )
            if signal_type and signal_names is not None:
                signal_type_names = self.get_signal_names(
                    signal_type=signal_type, entity=None, **kwargs
                )
                if signal_type_names:
                    return [s for s in signal_names if s in signal_type_names]
        # get signals by 'Signal' type
        elif signal_type:
            signals = self.get_signals(signal_type=signal_type, entity=None, **kwargs)
            return [e["Name"] for e in signals]
        # get all signals
        else:
            signal_names = self.get(f"{route}", **kwargs)
        return signal_names if signal_names is not None else []

    # add signal
    def add_signal(self, signal: Union[Signal, Dict[str, Any]], **kwargs) -> Any:
        """
        Add signal

        Parameters
        ----------
        signal : Signal | dict
            Signal
        """
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        if isinstance(signal, Signal):
            validated_signal = signal.model_dump(by_alias=True)
        elif isinstance(signal, dict):
            validated_signal = signal
        else:
            raise ValueError(
                "PetroVisor::add_signal(): "
                "Invalid type. Signal should be of type dict or Signal."
            )
        return self.post(f"{route}", data=validated_signal, **kwargs)

    # add signals
    def add_signals(
        self, signals: Sequence[Union[Signal, Dict[str, Any]]], **kwargs
    ) -> Any:
        """
        Add multiple signals

        Parameters
        ----------
        signals : list[Signal | dict]
            List of signals
        """
        validated_signals = [
            e.model_dump(by_alias=True) if isinstance(e, Signal) else e
            for e in signals
            if isinstance(e, dict) or isinstance(e, Signal)
        ]
        return self.post(
            SignalsMixinHelper.ENDPOINT_SIGNALS_ADD, data=validated_signals, **kwargs
        )

    # delete signal
    def delete_signal(
        self, signal: Union[Signal, Dict[str, Any], str], **kwargs
    ) -> Any:
        """
        Delete signal

        Parameters
        ----------
        signal : Signal | dict | str
            Signal
        """
        if isinstance(signal, Signal):
            name = signal.name
        else:
            name = ApiHelper.get_object_name(signal)
        if not name:
            return ApiRequests.success()
        return self.delete_item(ItemType.Signal, name, **kwargs)

    # delete signals
    def delete_signals(
        self, signals: Sequence[Union[Signal, Dict[str, Any], str]], **kwargs
    ) -> Any:
        """
        Delete multiple signals

        Parameters
        ----------
        signals : list[Signal | dict | str]
            List of signals
        """
        for signal in signals:
            if signal:
                self.delete_signal(signal, **kwargs)
        return ApiRequests.success()

    # get data range
    def get_data_range(
        self,
        signal_type: Optional[str] = None,
        signal: Optional[str] = None,
        entity: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Any:
        """
        Upload object

        Parameters
        ----------
        signal_type : str, default None
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        signal : str
            Object name
        entity : str | list[str], default None
            Entity name or Entities
        """
        signal_type_enum = self.get_signal_type_enum(signal_type, **kwargs)
        if signal_type_enum in {SignalType.Static, SignalType.String}:
            return {"Start": None, "End": None}

        # Determine if numeric or string signal
        is_numeric = signal_type_enum in {
            SignalType.TimeDependent,
            SignalType.DepthDependent,
        }

        if signal_type_enum in {
            SignalType.TimeDependent,
            SignalType.StringTimeDependent,
        }:
            # Use a unified Data/TimeRange endpoint with IsNumeric query parameter (GET)
            if signal and entity:
                signal_name = ApiHelper.get_object_name(signal)
                if not isinstance(entity, (list, tuple, set)):
                    entity_name = ApiHelper.get_object_name(entity)
                    return self.get(
                        f"{SignalsMixinHelper.ENDPOINT_TIME_RANGE}/{self.encode(signal_name)}/{self.encode(entity_name)}",
                        query={"IsNumeric": is_numeric},
                        **kwargs,
                    )
                else:
                    signal_name = ApiHelper.get_object_name(signal)
                    minmax = [
                        (
                            self.get(
                                f"{SignalsMixinHelper.ENDPOINT_TIME_RANGE}/{self.encode(signal_name)}/{self.encode(ApiHelper.get_object_name(e))}",
                                query={"IsNumeric": is_numeric},
                                **kwargs,
                            )
                            or {}
                        )
                        for e in entity
                    ]
                    minmax = [v for v in minmax if isinstance(v, dict)]
                    if not minmax:
                        return {"Start": None, "End": None}
                    return {
                        "Start": np.min(
                            [pd.to_datetime(v.get("Start", "")) for v in minmax]
                        ),
                        "End": np.max(
                            [pd.to_datetime(v.get("End", "")) for v in minmax]
                        ),
                    }
            elif signal:
                signal_name = ApiHelper.get_object_name(signal)
                return self.get(
                    f"{SignalsMixinHelper.ENDPOINT_TIME_RANGE}/{signal_name}",
                    query={"IsNumeric": is_numeric},
                    **kwargs,
                )
            return self.get(
                SignalsMixinHelper.ENDPOINT_TIME_RANGE,
                query={"IsNumeric": is_numeric},
                **kwargs,
            )
        elif signal_type_enum in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            # Use unified Data/DepthRange endpoint with IsNumeric query parameter (GET)
            # This is symmetric with Data/TimeRange
            if signal and entity:
                signal_name = ApiHelper.get_object_name(signal)
                if not isinstance(entity, (list, tuple, set)):
                    entity_name = ApiHelper.get_object_name(entity)
                    return self.get(
                        f"{SignalsMixinHelper.ENDPOINT_DEPTH_RANGE}/{self.encode(signal_name)}/{self.encode(entity_name)}",
                        query={"IsNumeric": is_numeric},
                        **kwargs,
                    )
                else:
                    signal_name = ApiHelper.get_object_name(signal)
                    minmax = [
                        (
                            self.get(
                                f"{SignalsMixinHelper.ENDPOINT_DEPTH_RANGE}/{self.encode(signal_name)}/{self.encode(ApiHelper.get_object_name(e))}",
                                query={"IsNumeric": is_numeric},
                                **kwargs,
                            )
                            or {}
                        )
                        for e in entity
                    ]
                    minmax = [v for v in minmax if isinstance(v, dict)]
                    if not minmax:
                        return {"Start": None, "End": None}
                    return {
                        "Start": np.min([v for v in minmax if v is not None]),
                        "End": np.max([v for v in minmax if v is not None]),
                    }
            elif signal:
                signal_name = ApiHelper.get_object_name(signal)
                return self.get(
                    f"{SignalsMixinHelper.ENDPOINT_DEPTH_RANGE}/{signal_name}",
                    query={"IsNumeric": is_numeric},
                    **kwargs,
                )
            return self.get(
                SignalsMixinHelper.ENDPOINT_DEPTH_RANGE,
                query={"IsNumeric": is_numeric},
                **kwargs,
            )
        return {"Start": None, "End": None}

    # load signals data
    def load_signals_data(
        self,
        signals: Union[str, Sequence[Union[str, Dict, Tuple[Any, str]]]],
        scenario: Optional[str] = None,
        context: Optional[Union[str, Dict[str, Any], Context]] = None,
        scope: Optional[Union[str, Dict[str, Any], Scope]] = None,
        entity_set: Optional[Union[str, Dict[str, Any], EntitySet]] = None,
        hierarchy: Optional[Union[str, Dict[str, Any], Hierarchy]] = None,
        entities: Optional[
            Union[
                str,
                Dict[str, Any],
                Entity,
                Sequence[Union[str, Dict[str, Any], Entity]],
            ]
        ] = None,
        entity_type: Optional[Union[str, List[str]]] = None,
        time_start: Optional[Union[str, datetime]] = None,
        time_end: Optional[Union[str, datetime]] = None,
        time_step: Optional[Union[str, TimeIncrement]] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Union[str, DepthIncrement]] = None,
        depth_unit: Optional[str] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        with_gaps: Optional[bool] = None,
        gap_value: Optional[float] = None,
        gap_string_value: Optional[str] = None,
        nrows: Optional[int] = None,
        aggfunc: Optional[Union[str, AggregationFunction]] = None,
        with_workspace_values: Optional[bool] = None,
        backend: str = "pandas",
        **kwargs,
    ) -> Optional[Any]:
        """
        Load signals data

        Parameters
        ----------
        signals : str | list[str] | list[dict|object]
            Signal name(s) or Signal objects. Single signal or multiple signals
        scenario : str, default None
            Scenario name
        context : str | dict | Context
            Context or context name
        scope : str | dict | Scope, default None
            Scope or scope name
        entity_set : str | dict | EntitySet, default None
            Entity set or entity set name
        hierarchy : str | dict | Hierarchy, default None
            Hierarchy or hierarchy name
        entities : str | dict | Entity | list[str | dict | Entity], default None
            Entity or list of Entities
        entity_type : str | list[str], default None
            Entity type. Used when entity_set, entities or context is not provided.
            If not None, it will filter out entities defined in entity_set.
        time_start : datetime, str, default None
            Start of time range
        time_end : datetime, str, default None
            End of time range
        time_step : str, TimeIncrement, default None
            Step of time range, e.g. 'Daily', 'Hourly'
        depth_start : datetime, float, None, default None
            Start of depth range
        depth_end : datetime, float, default None
            End of depth range
        depth_step : str, DepthIncrement, default None
            Step of depth range, e.g. 'Meter', 'Foot'
        depth_unit : str, default None
            Depth unit, e.g. 'm', 'ft'. Only when retrieving depth signals
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        with_gaps : bool, default None
            Fill gaps in output with a gap value. True enables gap filling,
            False disables it. None uses server default (no gap filling).
            Automatically set to True when gap_value is provided.
        gap_value : float, default None
            Numeric gap fill value (implies with_gaps=True). Defaults to NaN on server.
        gap_string_value : str, default None
            String gap fill value for string signals (implies with_gaps=True).
        nrows : int, default None
            Maximum number of records to return (maps to TopRecords).
            Consistent with pandas.
        aggfunc : str | AggregationFunction, default None
            Aggregation function applied during retrieval.
            Accepts AggregationFunction enum or string (e.g. 'Sum', 'Average').
            Consistent with pandas pivot_table(aggfunc=...).
        with_workspace_values : bool, default None
            Include workspace data in the response (maps to IncludeWorkspaceData).
        backend : str, default 'pandas'
            DataFrame backend ('pandas', 'polars'). Output DataFrame will be in the specified backend format.
        """
        # Signal names/specs
        signals: List[Dict] = SignalsMixinHelper._resolve_signals(signals, self)
        signal_names = [s["Name"] for s in signals]
        if not signals:
            warnings.warn(
                "PetroVisor::load_signals_data():: No signals were provided.",
                RuntimeWarning,
            )
            return None
        signals_with_units_map = {
            s["Name"]: f"{s['Name']} [{s['UnitName']}]" for s in signals
        }

        # Context and its components ( EntitySet, Entities, Hierarchy, Scope, Time/Depth ranges)
        context = (
            self.get_context(
                context,
                entity_set=entity_set,
                scope=scope,
                hierarchy=hierarchy,
                entity_type=entity_type,
                entities=entities,
                time_start=time_start,
                time_end=time_end,
                time_step=time_step,
                depth_start=depth_start,
                depth_end=depth_end,
                depth_step=depth_step,
            )
            or {}
        )
        scope = context.get("Scope", None) or {}
        hierarchy = ApiHelper.get_object_name(context.get("Hierarchy", None) or "")
        entity_set = context.get("EntitySet", None) or {}
        entities = entity_set.get("Entities", None) or []
        if not entities:
            raise ValueError(
                "load_signals_data():: "
                "entity set is empty! Please provide non empty entity_set, or list of entities, or define entity_type."
            )
        entity_names = [ApiHelper.get_object_name(e) for e in entities]

        # Classify signals (static/time/depth/pvt)
        _cls = SignalsMixinHelper._classify_signals(signals)
        has_time_signals = _cls["has_time"]
        has_depth_signals = _cls["has_depth"]
        has_pvt_signals = _cls["has_pvt"]

        # Scope range
        time_start = time_end = time_step = None
        depth_start = depth_end = depth_step = None
        if _cls["time_signals"]:
            time_start, time_end, time_step = SignalsMixinHelper._resolve_time_range(
                scope, _cls["time_signals"], entity_names, self
            )
        if _cls["depth_signals"]:
            depth_start, depth_end, depth_step = (
                SignalsMixinHelper._resolve_depth_range(
                    scope, _cls["depth_signals"], entity_names, self
                )
            )

        # Use Data/Retrieve endpoint
        # Separate signals by type for proper request construction
        signals_with_units_num = _cls["signals_num"]
        signals_with_units_str = _cls["signals_str"]

        # Retrieve numeric data
        if signals_with_units_num:
            _rqst_num = SignalsMixinHelper._build_retrieve_rqst(
                entity_names,
                signals_with_units_num,
                has_time=has_time_signals,
                has_depth=has_depth_signals,
                has_pvt=has_pvt_signals,
                time_start=time_start,
                time_end=time_end,
                time_step=time_step,
                depth_start=depth_start,
                depth_end=depth_end,
                depth_step=depth_step,
                depth_unit=depth_unit,
                hierarchy=hierarchy,
                scenario=scenario,
                pressure_unit=pressure_unit,
                temperature_unit=temperature_unit,
                with_gaps=with_gaps,
                gap_value=gap_value,
                nrows=nrows,
                aggfunc=aggfunc,
                with_workspace_values=with_workspace_values,
            )
            _resp_num = (
                self.post(SignalsMixinHelper.ENDPOINT_RETRIEVE, data=_rqst_num) or {}
            )
            data_time_num = _resp_num.get("TimeNumericData", [])
            data_depth_num = _resp_num.get("DepthNumericData", [])
            data_static_num = _resp_num.get("StaticNumericData", [])
            data_pvt_num = _resp_num.get("PVTNumericData", [])
        else:
            data_time_num = []
            data_depth_num = []
            data_static_num = []
            data_pvt_num = []

        # Retrieve string data (gap_string_value only applies here)
        if signals_with_units_str:
            _rqst_str = SignalsMixinHelper._build_retrieve_rqst(
                entity_names,
                signals_with_units_str,
                has_time=has_time_signals,
                has_depth=has_depth_signals,
                has_pvt=False,
                time_start=time_start,
                time_end=time_end,
                time_step=time_step,
                depth_start=depth_start,
                depth_end=depth_end,
                depth_step=depth_step,
                depth_unit=depth_unit,
                hierarchy=hierarchy,
                scenario=scenario,
                with_gaps=with_gaps,
                gap_value=gap_value,
                gap_string_value=gap_string_value,
                nrows=nrows,
                aggfunc=aggfunc,
                with_workspace_values=with_workspace_values,
            )
            _resp_str = (
                self.post(SignalsMixinHelper.ENDPOINT_RETRIEVE, data=_rqst_str) or {}
            )
            data_time_str = _resp_str.get("TimeStringData", [])
            data_depth_str = _resp_str.get("DepthStringData", [])
            data_static_str = _resp_str.get("StaticStringData", [])
        else:
            data_time_str = []
            data_depth_str = []
            data_static_str = []

        # Columns
        _entity_col = "Entity"
        _time_col = "Date"
        _depth_col = "Depth"
        _signal_col = "Signal"

        # Build PVT DataFrame (separate from time/depth/static — different index axes)
        df_pvt = None
        if data_pvt_num:
            df_pvt = SignalsMixinHelper._build_pvt_df(
                data_pvt_num,
                _entity_col,
                pressure_unit,
                temperature_unit,
                signals_with_units_map,
                backend,
            )

        # Build all signal types in one pass and join on entity
        df = DataFrameMixinHelper._build_combined_df(
            data_time_num,
            data_time_str,
            data_depth_num,
            data_depth_str,
            data_static_num,
            data_static_str,
            _entity_col,
            _time_col,
            _depth_col,
            _signal_col,
            signals_with_units_map,
            backend,
        )

        # If time signals were requested as static (no time range), drop the Date column
        if (
            df is not None
            and not has_time_signals
            and _time_col in DataFrameMixinHelper.df_get_column_names(df)
        ):
            df = DataFrameMixinHelper.df_drop_column(df, _time_col, backend)

        # Reorder: move Depth column to position 2 (after Entity, Date) when both exist
        if (
            df is not None
            and _depth_col in DataFrameMixinHelper.df_get_column_names(df)
            and _time_col in DataFrameMixinHelper.df_get_column_names(df)
        ):
            cols = DataFrameMixinHelper.df_get_column_names(df)
            non_depth = [c for c in cols if c != _depth_col]
            df = DataFrameMixinHelper.df_select_columns(
                df, non_depth[:2] + [_depth_col] + non_depth[2:], backend
            )

        if df is not None and _depth_col in DataFrameMixinHelper.df_get_column_names(
            df
        ):
            _depth_label = depth_unit or "m"
            df = DataFrameMixinHelper.df_rename_column(
                df, _depth_col, f"{_depth_col} [{_depth_label}]", backend
            )

        # PVT-only result: return pvt df directly (already in the requested backend)
        if df is None and df_pvt is not None:
            return df_pvt

        if df is None:
            warnings.warn(
                "PetroVisor::load_signals_data():: Couldn't retrieve any data.",
                RuntimeWarning,
            )
            return df

        # ---- reorder: non-signal columns first, then signal columns ----
        _cols = DataFrameMixinHelper.df_get_column_names(df)
        _non_sig = [
            c for c in _cols if self.get_column_name_without_unit(c) not in signal_names
        ]
        _sig_cols = [c for c in _cols if c not in _non_sig]
        df = DataFrameMixinHelper.df_select_columns(
            df, [*_non_sig, *_sig_cols], backend
        )

        # ---- final backend conversion ----
        return DataFrameMixinHelper.df_to_backend(df, backend)

    # save data from table to PetroVisor
    def save_table_data(
        self,
        df: pd.DataFrame,
        delimiter: str = "\t",
        signals: Optional[Dict] = None,
        chunksize: int = 10000,
        only_existing_entities: bool = True,
        entity_type: str = "",
        entities: Optional[Dict] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        **kwargs,
    ) -> None:
        """
        Save DataFrame data to corresponding signals

        Parameters
        ----------
        df : DataFrame, str
            Table or filename. Table should contain necessary columns 'Entity', 'Date' or 'Depth',
            depending on the type of the present signals.
        delimiter : str, default '\t'
            Delimiter used when reading table from file
        signals : dict, default None
            Dictionary map from table 'column name' to workspace 'signal name'
        chunksize : int, default 10000
            Save data by splitting it into several chunks of specified size and performing separate requests
        entities : dict, default None
            Dictionary map from table 'entity name' to workspace 'entity name'
        only_existing_entities : bool, default True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        pressure_unit : str, default 'Pa'
            Unit for Pressure axis when saving PVT signals
        temperature_unit : str, default 'K'
            Unit for Temperature axis when saving PVT signals
        """
        # read table
        if isinstance(df, str):
            df = self.read_dataframe_from_file(
                filepath=df,
                backend="pandas",
                delimiter=delimiter,
            )
        if df is not None:
            df = DataFrameMixinHelper.normalize_depth_column(
                df, "Depth", self.convert_units
            )
            if chunksize and (df.shape[0] > chunksize):
                for start in range(0, df.shape[0], chunksize):
                    end = min(start + chunksize, df.shape[0])
                    self.save_table_data(
                        df[start:end],
                        delimiter=delimiter,
                        signals=signals,
                        chunksize=chunksize,
                        only_existing_entities=only_existing_entities,
                        entity_type=entity_type,
                        entities=entities,
                        pressure_unit=pressure_unit,
                        temperature_unit=temperature_unit,
                        **kwargs,
                    )
                return None
            # get PetroVisor data from DataFrame
            data_to_save = self.get_signal_data_from_dataframe(
                df,
                signals=signals,
                only_existing_entities=only_existing_entities,
                entity_type=entity_type,
                entities=entities,
                **kwargs,
            )
            # save all signal types in a single Data/Save request
            if any(data_to_save.values()):
                data_to_save["GenerateLogs"] = False
                if data_to_save.get("PVTNumericData"):
                    data_to_save["PressureUnit"] = pressure_unit
                    data_to_save["TemperatureUnit"] = temperature_unit
                self.post(SignalsMixinHelper.ENDPOINT_SAVE, data=data_to_save, **kwargs)
        return None

    # load data
    def load_data(
        self,
        data_type: Optional[Union[str, SignalType]] = None,
        data: Optional[
            Union[
                str,
                List[Union[str, Dict, Tuple[Any, str]]],
                List[Dict],
                "pd.DataFrame",
                "pd.Series",
            ]
        ] = None,
        start: Optional[Union[datetime, float]] = None,
        end: Optional[Union[datetime, float]] = None,
        step: Optional[Union[str, TimeIncrement, DepthIncrement]] = None,
        scenario: Optional[str] = None,
        context: Optional[Union[str, Dict[str, Any], Context]] = None,
        scope: Optional[Union[str, Dict[str, Any], Scope]] = None,
        entity_set: Optional[Union[str, Dict[str, Any], EntitySet]] = None,
        hierarchy: Optional[Union[str, Dict[str, Any], Hierarchy]] = None,
        entities: Optional[
            Union[
                str,
                Dict[str, Any],
                Entity,
                Sequence[Union[str, Dict[str, Any], Entity]],
            ]
        ] = None,
        entity_type: Optional[Union[str, List[str]]] = None,
        time_start: Optional[Union[str, datetime]] = None,
        time_end: Optional[Union[str, datetime]] = None,
        time_step: Optional[Union[str, TimeIncrement]] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Union[str, DepthIncrement]] = None,
        depth_unit: Optional[str] = None,
        num_values: Optional[int] = None,
        gap_value: Optional[float] = None,
        gap_string_value: Optional[str] = None,
        with_gaps: Optional[bool] = None,
        aggfunc: Optional[Union[str, AggregationFunction]] = None,
        nrows: Optional[int] = None,
        with_workspace_values: Optional[bool] = None,
        interpolated: Optional[bool] = False,
        with_logs: bool = False,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        backend: str = "pandas",
        **kwargs,
    ) -> Optional[Any]:
        """
        Load data.

        Parameters
        ----------
        data_type : str | SignalType, optional
            Signal type ('static', 'time', 'depth', 'string', 'timestring', 'stringdepth', 'pvt').
            When omitted (new-style calls), the format is inferred from ``data``.
        data : str | list | DataFrame | Series, optional
            Data to load. Accepts:
            - str: single signal name (new style)
            - list[str]: multiple signal names (new style)
            - list[(str, str)]: (signal, unit) tuples (new style)
            - list[dict]: [{Entity, Signal, Unit}, ...] (entity-based, requires data_type)
            - DataFrame/Series: entity-based format
        start : datetime | float, optional
            Start of time/depth range (entity-based path).
        end : datetime | float, optional
            End of time/depth range (entity-based path).
        step : str | TimeIncrement | DepthIncrement, optional
            Time or depth increment (entity-based path).
        scenario : str, optional
        context : str | dict | Context, optional
        scope : str | dict | Scope, optional
        entity_set : str | dict | EntitySet, optional
        hierarchy : str | dict | Hierarchy, optional
        entities : str | dict | Entity | list, optional
        entity_type : str | list[str], optional
        time_start : datetime | str, optional
        time_end : datetime | str, optional
        time_step : str | TimeIncrement, optional
        depth_start : float, optional
        depth_end : float, optional
        depth_step : str | DepthIncrement, optional
        depth_unit : str, optional
        num_values : int, optional
            Top/last N values (entity-based path, uses Data/Top).
        gap_value : float, optional
        gap_string_value : str, optional
        with_gaps : bool, optional
        aggfunc : str | AggregationFunction, optional
        nrows : int, optional
        with_workspace_values : bool, optional
        interpolated : bool, default False
        with_logs : bool, default False
        pressure_unit : str, default 'Pa'
        temperature_unit : str, default 'K'
        backend : str, default 'pandas'
        """
        _first: Any = data_type
        _data: Any = data
        # Backward compat: if first positional arg is not a valid signal type, it's data
        resolved_type: Optional[SignalType] = None
        if _first is not None:
            try:
                resolved_type = self.get_signal_type_enum(_first)
            except (ValueError, TypeError, AttributeError):
                if _data is None:
                    _data = _first
        else:
            resolved_type = None

        # Deprecated start/end/step: map to time_*/depth_* based on resolved_type
        _time_start: Any = time_start
        _time_end: Any = time_end
        _time_step: Any = time_step
        _depth_start: Any = depth_start
        _depth_end: Any = depth_end
        _depth_step: Any = depth_step
        if start is not None or end is not None or step is not None:
            _signal_types = {
                SignalType.TimeDependent,
                SignalType.StringTimeDependent,
                SignalType.DepthDependent,
                SignalType.StringDepthDependent,
                SignalType.Static,
                SignalType.String,
                SignalType.PVT,
            }
            if resolved_type not in _signal_types:
                deprecated = [
                    p
                    for p, v in [("start", start), ("end", end), ("step", step)]
                    if v is not None
                ]
                warnings.warn(
                    f"load_data() parameter(s) {deprecated} are deprecated. "
                    "Use time_start/time_end/time_step or depth_start/depth_end/depth_step instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            is_time_dependent = True
            if resolved_type is not None:
                is_time_dependent = resolved_type in {
                    SignalType.TimeDependent,
                    SignalType.StringTimeDependent,
                }
            if is_time_dependent:
                if _time_start is None and start is not None:
                    _time_start = start
                if _time_end is None and end is not None:
                    _time_end = end
                if _time_step is None and step is not None:
                    _time_step = step
            else:
                if _depth_start is None and start is not None:
                    _depth_start = start
                if _depth_end is None and end is not None:
                    _depth_end = end
                if _depth_step is None and step is not None:
                    _depth_step = step

        # When resolved_type is set, it's the entity-based format
        # When not set, detect from data content
        is_signal_name_format = False
        if resolved_type is None:
            if isinstance(_data, str):
                is_signal_name_format = True
            elif isinstance(_data, (list, tuple, set)) and _data:
                first_elem = next(iter(_data))
                if isinstance(first_elem, str):
                    is_signal_name_format = True
                elif isinstance(first_elem, (list, tuple)) and len(first_elem) >= 1:
                    is_signal_name_format = True

        if is_signal_name_format:
            return self.load_signals_data(
                signals=_data,
                scenario=scenario,
                context=context,
                scope=scope,
                entity_set=entity_set,
                hierarchy=hierarchy,
                entities=entities,
                entity_type=entity_type,
                time_start=_time_start,
                time_end=_time_end,
                time_step=_time_step,
                depth_start=_depth_start,
                depth_end=_depth_end,
                depth_step=_depth_step,
                depth_unit=depth_unit,
                with_gaps=with_gaps,
                gap_value=gap_value,
                gap_string_value=gap_string_value,
                nrows=nrows,
                aggfunc=aggfunc,
                with_workspace_values=with_workspace_values,
                pressure_unit=pressure_unit,
                temperature_unit=temperature_unit,
                backend=backend,
                **kwargs,
            )

        # Entity-based format
        data_type = resolved_type
        data = self._as_data_list(_data, fill_unit=True, **kwargs)
        # load 'Time' or 'Depth' data
        if data_type in {
            SignalType.TimeDependent,
            SignalType.StringTimeDependent,
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            # first/last values only
            if num_values is not None:
                # Determine if numeric or string signal
                # is_numeric = data_type in {
                #     SignalType.TimeDependent,
                #     SignalType.DepthDependent,
                # }
                # Build request body with Requests field
                # Backend determines numeric/string from signal name
                request_body: Dict[str, Any] = {
                    "Requests": data,
                    "TopRecords": abs(num_values),
                    "IsLastValues": num_values < 0,
                }
                return self.post(
                    SignalsMixinHelper.ENDPOINT_TOP,
                    data=request_body,
                    **kwargs,
                )
            # get data defined on range
            if start is not None and end is not None:
                if step is not None or (
                    start == end and data_type == SignalType.StringTimeDependent
                ):
                    if step is not None:
                        range_step = self.get_increment_enum(step, data_type)
                    else:
                        range_step = TimeIncrement.EverySecond
                    if range_step is None or not ApiHelper.has_field(
                        range_step, "name"
                    ):
                        raise ValueError(
                            f"PetroVisor::load_data(): "
                            f"invalid increment value: '{step}'"
                        )
                    range_step = str(range_step.name)
                    is_time_dependent = data_type in {
                        SignalType.TimeDependent,
                        SignalType.StringTimeDependent,
                    }
                    range_type = "time" if is_time_dependent else "numeric"
                    data_range: Dict[str, Any] = {
                        "Start": self.get_json_valid_value(start, range_type, **kwargs),
                        "End": self.get_json_valid_value(end, range_type, **kwargs),
                        "Increment": range_step,
                    }
                    if (
                        hierarchy is not None
                        and hierarchy
                        and data_type
                        in {SignalType.TimeDependent, SignalType.StringTimeDependent}
                    ):
                        data_range["Hierarchy"] = hierarchy
                    # Determine if a numeric or string signal
                    # is_numeric = data_type in {
                    #     SignalType.TimeDependent,
                    #     SignalType.DepthDependent,
                    # }

                    # Build request body with the Requests field
                    # Backend determines numeric/string from signal name
                    request_body: Dict[str, Any] = {
                        "Requests": data,
                    }

                    # Add time/depth range parameters to the body
                    if is_time_dependent:
                        request_body["TimeStart"] = data_range["Start"]
                        request_body["TimeEnd"] = data_range["End"]
                        request_body["TimeIncrement"] = data_range["Increment"]
                        if "Hierarchy" in data_range:
                            request_body["Hierarchy"] = data_range["Hierarchy"]
                    else:
                        request_body["DepthStart"] = data_range["Start"]
                        request_body["DepthEnd"] = data_range["End"]
                        request_body["DepthIncrement"] = data_range["Increment"]

                    # load with filling gaps
                    if gap_value is not None:
                        gap_value = self.get_json_valid_value(
                            gap_value, data_type, **kwargs
                        )
                        if not request_body.get("Options"):
                            request_body["Options"] = {}
                        request_body["Options"]["GapValue"] = gap_value
                        request_body["Options"]["WithGaps"] = True

                    # load data with logs
                    if with_logs and ApiHelper.has_field(data, "Data"):
                        if not request_body.get("Options"):
                            request_body["Options"] = {}
                        request_body["Options"]["WithLogs"] = True

                    # load data in specified range using unified endpoint
                    return self.post(
                        SignalsMixinHelper.ENDPOINT_RETRIEVE,
                        data=request_body,
                        **kwargs,
                    )
                elif start == end:
                    load_point = self.get_json_valid_value(start, data_type, **kwargs)
                    # Determine if a numeric or string signal
                    # is_numeric = data_type in {
                    #     SignalType.TimeDependent,
                    #     SignalType.DepthDependent,
                    # }

                    # Build request body with the Requests field
                    # Backend determines numeric/string from signal name
                    request_body: Dict[str, Any] = {
                        "Requests": data,
                    }

                    # get data at a single point using a unified endpoint
                    if data_type in {
                        SignalType.TimeDependent,
                        SignalType.StringTimeDependent,
                    }:
                        request_body["TimeStart"] = load_point
                        request_body["TimeEnd"] = load_point
                    elif data_type in {
                        SignalType.DepthDependent,
                        SignalType.StringDepthDependent,
                    }:
                        request_body["DepthStart"] = load_point
                        request_body["DepthEnd"] = load_point
                        if interpolated:
                            if not request_body.get("Options"):
                                request_body["Options"] = {}
                            request_body["Options"]["Interpolated"] = True

                    return self.post(
                        SignalsMixinHelper.ENDPOINT_RETRIEVE,
                        data=request_body,
                        **kwargs,
                    )
            else:
                raise ValueError(
                    "PetroVisor::load_data(): "
                    "'start', 'end' and 'step' should be provided! "
                    "'step' can be avoided if 'start' == 'end'."
                )
        # load 'Static', 'String', and 'PVT' data using unified endpoint
        # Backend determines numeric/string from signal name
        request_body: Dict[str, Any] = {
            "Requests": data,
        }

        # Add with_logs for Static
        if (
            with_logs
            and ApiHelper.has_field(data, "Data")
            and data_type == SignalType.Static
        ):
            if not request_body.get("Options"):
                request_body["Options"] = {}
            request_body["Options"]["WithLogs"] = True

        # Add PVT unit parameters
        if data_type == SignalType.PVT:
            request_body["PressureUnit"] = pressure_unit
            request_body["TemperatureUnit"] = temperature_unit

        return self.post(
            SignalsMixinHelper.ENDPOINT_RETRIEVE, data=request_body, **kwargs
        )

    # save data
    def save_data(
        self,
        data_type: Optional[Union[str, SignalType]] = None,
        data: Optional[Union[str, List[Dict], "pd.DataFrame", "pd.Series"]] = None,
        signals: Optional[Dict] = None,
        entities: Optional[Dict] = None,
        with_logs: bool = False,
        logs_source: Optional[str] = None,
        no_range_delete: bool = False,
        time_step: Optional[str] = None,
        depth_step: Optional[str] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        chunksize: int = 10000,
        only_existing_entities: bool = False,
        entity_type: str = "",
        delimiter: str = "\t",
        engine: Optional[str] = None,
        date_col: str = "Date",
        depth_col: str = "Depth",
        **kwargs,
    ) -> Any:
        """
        Save Signals data

        Parameters
        ----------
        data_type : str | SignalType, optional
            Accepted for backward compatibility — ignored (signal type is auto-detected from data).
        data : str | list[dict] | DataFrame | Series
            Data to save. Accepts:
            - File path (.csv, .tsv, .txt, .xlsx, .xls, .parquet, .feather, .arrow)
            - DataFrame in long format  (Entity, Date/Depth, Signal [Unit] columns)
            - DataFrame in wide format  (Date/Depth, Entity : Signal [Unit] columns)
            - DataFrame in record format (Entity, Signal, Unit, Data columns)
            - Named Series (static multi-entity or time/depth single-entity)
            - List of dicts with Entity, Signal, Unit, Data keys
            Unit defaults to the signal's storage unit when omitted.
        signals : dict, optional
            Column-name → signal-name override map. Applied to DataFrame columns
            before conversion. Matches both "Col [unit]" and bare "Col" keys.
        entities : dict, optional
            Entity-name → workspace entity-name override map. Applied after
            DataFrame/Series conversion, before entity filtering.
        with_logs : bool, default False
            Generate logs (uses GenerateLogs field in request body)
        logs_source : str, optional
            Source for logs
        no_range_delete : bool, default False
            Don't delete existing data in range
        time_step : str, optional
            Time increment for aggregation (e.g., 'EverySecond', 'Daily')
        depth_step : str, optional
            Depth increment for aggregation (e.g., 'TenthMeter', 'Meter')
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        chunksize : int, default 0
            Split DataFrame into chunks of this many rows before saving.
            0 disables chunking.
        only_existing_entities : bool, default False
            Skip records whose Entity is not in the workspace.
        entity_type : str, default ''
            When only_existing_entities=True, restrict to entities of this type.
        delimiter : str, default '\t'
            Field delimiter used when reading .csv / .tsv / .txt files.
        engine : str, optional
            Passed to the underlying pandas reader when loading from a file path.
            Examples: 'openpyxl'/'xlrd' for Excel; 'pyarrow'/'fastparquet' for
            Parquet; 'c'/'python'/'pyarrow' for CSV/TSV. Ignored for .feather/.arrow.
        date_col : str, default 'Date'
            Column name for dates. Override for DataFrames that use 'Timestamp',
            'Time', or other column names instead of the default 'Date'.
        depth_col : str, default 'Depth'
            Base name for depth columns. Override if your data uses a different
            name. Actual columns may have unit suffixes (e.g., 'Depth [m]').
        """
        # Backward compat: if data_type is not a valid signal type string it's actually data
        _first: Any = data_type
        _data: Any = data
        resolved_type: Optional[SignalType] = None
        if _first is not None:
            try:
                resolved_type = self.get_signal_type_enum(_first)
            except (ValueError, TypeError, AttributeError):
                if _data is None:
                    _data = _first
        data_type = resolved_type
        data = _data

        # Read table from file if file path is provided
        if isinstance(data, str):
            data = self.read_dataframe_from_file(
                filepath=data,
                backend="pandas",
                delimiter=delimiter,
                engine=engine,
            )

        # signals remapping - column name to signal name
        if signals and isinstance(data, pd.DataFrame):
            rename_map: Dict[str, str] = {}
            for col in data.columns:
                if col in signals:
                    mapped = signals[col]
                    _, unit = DataFrameMixinHelper.parse_signal_column(col)
                    if isinstance(mapped, str):
                        rename_map[col] = f"{mapped} [{unit}]"
                else:
                    col_base, unit = DataFrameMixinHelper.parse_signal_column(col)
                    if col_base in signals:
                        mapped = signals[col_base]
                        if isinstance(mapped, str):
                            rename_map[col] = f"{mapped} [{unit}]"
            if rename_map:
                data = data.rename(columns=rename_map)

        # chunking — split large DataFrames before conversion
        if (
            chunksize
            and chunksize > 0
            and isinstance(data, pd.DataFrame)
            and len(data) > chunksize
        ):
            for start in range(0, len(data), chunksize):
                self.save_data(
                    data.iloc[start : start + chunksize],
                    signals=signals,
                    entities=entities,
                    with_logs=with_logs,
                    logs_source=logs_source,
                    no_range_delete=no_range_delete,
                    time_step=time_step,
                    depth_step=depth_step,
                    pressure_unit=pressure_unit,
                    temperature_unit=temperature_unit,
                    chunksize=chunksize,
                    only_existing_entities=only_existing_entities,
                    entity_type=entity_type,
                    date_col=date_col,
                    depth_col=depth_col,
                    **kwargs,
                )
            return None

        if isinstance(data, pd.DataFrame):
            data = DataFrameMixinHelper.normalize_depth_column(
                data, depth_col, self.convert_units
            )

        data_list: List[Dict] = DataFrameMixinHelper.to_data_list(
            data, date_col=date_col, depth_col=depth_col
        )

        # entity remapping - source entity name to target workspace entity name
        if entities:
            for record in data_list:
                if isinstance(record, dict) and record.get("Entity") in entities:
                    record["Entity"] = entities[record["Entity"]]

        # entity filtering — uses workspace names, so applied after entity remapping
        select_entities: Optional[Set[str]] = None
        if only_existing_entities:
            select_entities = set(
                self.get_entity_names(entity_type=entity_type, **kwargs)
            )

        # Build the request body with the appropriate data field based on signal type
        request_body: Dict[str, Any] = {
            "TimeNumericData": [],
            "StaticNumericData": [],
            "TimeStringData": [],
            "StaticStringData": [],
            "DepthNumericData": [],
            "DepthStringData": [],
            "PVTNumericData": [],
            "GenerateLogs": with_logs,
            "NoRangeDelete": no_range_delete,
        }

        # Populate the appropriate field based on data_type
        if data_type is not None:
            # deprecated path — fill unit the old way then route directly
            filled = self._as_data_list(data_list, fill_unit=True, **kwargs)
            if data_type == SignalType.Static:
                request_body["StaticNumericData"] = filled
            elif data_type == SignalType.String:
                request_body["StaticStringData"] = filled
            elif data_type == SignalType.TimeDependent:
                request_body["TimeNumericData"] = filled
            elif data_type == SignalType.StringTimeDependent:
                request_body["TimeStringData"] = filled
            elif data_type == SignalType.DepthDependent:
                request_body["DepthNumericData"] = filled
            elif data_type == SignalType.StringDepthDependent:
                request_body["DepthStringData"] = filled
            elif data_type == SignalType.PVT:
                request_body["PVTNumericData"] = filled
        else:
            # Step 1: auto-route each record; resolve signal type AND default unit in
            # one get_signal() call per unique signal name — no separate fill_unit pass.
            _type_unit_cache: Dict[str, Tuple[Optional[SignalType], str]] = {}
            _bucket_map = {
                SignalType.TimeDependent: "TimeNumericData",
                SignalType.Static: "StaticNumericData",
                SignalType.StringTimeDependent: "TimeStringData",
                SignalType.String: "StaticStringData",
                SignalType.DepthDependent: "DepthNumericData",
                SignalType.StringDepthDependent: "DepthStringData",
                SignalType.PVT: "PVTNumericData",
            }
            # (idx_key, idx_dtype, val_dtype) per signal type
            _dtypes: Dict[SignalType, Tuple[Optional[str], Optional[str], str]] = {
                SignalType.Static: (None, None, "Numeric"),
                SignalType.String: (None, None, "String"),
                SignalType.TimeDependent: ("Date", "Time", "Numeric"),
                SignalType.StringTimeDependent: ("Date", "Time", "String"),
                SignalType.DepthDependent: ("Depth", "Numeric", "Numeric"),
                SignalType.StringDepthDependent: ("Depth", "Numeric", "String"),
            }
            for record in data_list:
                if not isinstance(record, dict):
                    continue
                entity = str(record.get("Entity") or "")
                if select_entities is not None and entity not in select_entities:
                    continue
                signal_name = ApiHelper.get_object_name(record.get("Signal") or "")
                if not signal_name:
                    continue
                if signal_name not in _type_unit_cache:
                    sig_obj = self.get_signal(signal_name, **kwargs)
                    if sig_obj and "SignalType" in sig_obj:
                        try:
                            sig_type: Optional[SignalType] = SignalType[
                                sig_obj["SignalType"]
                            ]
                        except (KeyError, ValueError):
                            sig_type = None
                        default_unit = sig_obj.get("StorageUnitName", "")
                    else:
                        sig_type = None
                        default_unit = ""
                    _type_unit_cache[signal_name] = (sig_type, default_unit)
                sig_type, default_unit = _type_unit_cache[signal_name]
                # fill unit from signal definition if missing
                if not record.get("Unit") and default_unit:
                    record["Unit"] = default_unit
                bucket = _bucket_map.get(sig_type) if sig_type is not None else None
                if bucket is None:
                    continue
                # apply get_json_valid_value with correct dtypes
                raw_data = record.get("Data")
                if sig_type == SignalType.PVT:
                    # PVT Data: [{Pressure, Temperature, Value}] — two numeric axes
                    if isinstance(raw_data, list):
                        record["Data"] = [
                            {
                                "Pressure": self.get_json_valid_value(
                                    r.get("Pressure"), dtype="Numeric", **kwargs
                                ),
                                "Temperature": self.get_json_valid_value(
                                    r.get("Temperature"), dtype="Numeric", **kwargs
                                ),
                                "Value": self.get_json_valid_value(
                                    r.get("Value"), dtype="Numeric", **kwargs
                                ),
                            }
                            for r in raw_data
                            if isinstance(r, dict)
                        ]
                elif sig_type in _dtypes:
                    idx_key, idx_dtype, val_dtype = _dtypes[sig_type]
                    if (
                        idx_key is not None
                        and idx_dtype is not None
                        and isinstance(raw_data, list)
                    ):
                        record["Data"] = [
                            {
                                idx_key: self.get_json_valid_value(
                                    r.get(idx_key), dtype=idx_dtype, **kwargs
                                ),
                                "Value": self.get_json_valid_value(
                                    r.get("Value"), dtype=val_dtype, **kwargs
                                ),
                            }
                            for r in raw_data
                            if isinstance(r, dict)
                        ]
                    else:
                        record["Data"] = self.get_json_valid_value(
                            raw_data, dtype=val_dtype, **kwargs
                        )
                request_body[bucket].append(record)

        # Add optional fields
        if logs_source:
            request_body["LogsSource"] = logs_source
        if time_step:
            request_body["ValuesTimeIncrement"] = time_step
        if depth_step:
            request_body["ValuesDepthIncrement"] = depth_step

        # Add PVT unit parameters when PVT data is present (explicit or auto-detected)
        if data_type == SignalType.PVT or request_body.get("PVTNumericData"):
            if pressure_unit:
                request_body["PressureUnit"] = pressure_unit
            if temperature_unit:
                request_body["TemperatureUnit"] = temperature_unit

        # Skip the request if all data buckets are empty (avoids a server 500)
        _data_keys = [
            "TimeNumericData",
            "StaticNumericData",
            "TimeStringData",
            "StaticStringData",
            "DepthNumericData",
            "DepthStringData",
            "PVTNumericData",
        ]
        if not any(request_body.get(k) for k in _data_keys):
            return None

        # Always use Data/Save endpoint (GenerateLogs flag controls log generation)
        return self.post(SignalsMixinHelper.ENDPOINT_SAVE, data=request_body, **kwargs)

    # delete data
    def delete_data(
        self,
        data_type: Optional[Union[str, SignalType]] = None,
        data: Optional[Union[List[Dict], "pd.DataFrame", "pd.Series"]] = None,
        start: Optional[Union[datetime, float]] = None,
        end: Optional[Union[datetime, float]] = None,
        **kwargs,
    ) -> Any:
        """
        Delete data using Data/Delete endpoint

        Parameters
        ----------
        data_type : str | SignalType, optional
            Signal type ('static', 'time', 'depth', 'string', 'timestring', 'stringdepth').
            When provided, used to determine time vs depth range format for start/end.
        data : list[dict] | DataFrame | Series
            Request specs as a list of dicts (Entity, Signal) or a
            DataFrame/Series with those columns.
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        """
        # Backward compat: if data_type is not a valid signal type it's actually data
        _first: Any = data_type
        _data: Any = data
        resolved_type: Optional[SignalType] = None
        if _first is not None:
            try:
                resolved_type = self.get_signal_type_enum(_first)
            except (ValueError, TypeError, AttributeError):
                if _data is None:
                    _data = _first
        else:
            resolved_type = None
        data_type = resolved_type
        data = self._as_data_list(_data, fill_unit=False, **kwargs)

        # Build the request body with the Requests field
        request_body = {
            "Requests": data,
        }

        # Add time/depth range for time/depth dependent signals
        if data_type in {
            SignalType.TimeDependent,
            SignalType.StringTimeDependent,
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            is_time_dependent = data_type in {
                SignalType.TimeDependent,
                SignalType.StringTimeDependent,
            }

            if start is not None and end is not None:
                range_type = "time" if is_time_dependent else "numeric"
                start_value = self.get_json_valid_value(start, range_type, **kwargs)
                end_value = self.get_json_valid_value(end, range_type, **kwargs)

                if is_time_dependent:
                    request_body["TimeStart"] = start_value
                    request_body["TimeEnd"] = end_value
                else:
                    request_body["DepthStart"] = start_value
                    request_body["DepthEnd"] = end_value

        return self.post(
            SignalsMixinHelper.ENDPOINT_DELETE, data=request_body, **kwargs
        )

    # cleanse data
    def cleanse_data(
        self,
        data_type: Optional[Union[str, SignalType]] = None,
        value: Optional[float] = None,
        timestamp: Optional[Union[datetime, str]] = None,
        signal: Optional[Union[Dict, str]] = None,
        unit: Optional[Union[Dict, str]] = None,
        entity: Optional[Union[Dict, str]] = None,
        cleansing_script: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Cleanse data

        Parameters
        ----------
        data_type : str | SignalType, optional
            Signal type ('static', 'time'). Used to determine cleansing path.
            When omitted, inferred from timestamp (None → Static, set → TimeDependent).
        value : float
            Value
        timestamp : datetime, str, optional
            Date (required for TimeDependent; None for Static)
        signal : str, dict
            Signal object or Signal name
        unit : str, dict, optional
            Unit object or Unit name. Defaults to the signal's storage unit.
        entity : str, dict
            Entity object or Entity name
        cleansing_script : str
            Cleansing script
        """
        # Backward compat: if data_type is not a valid signal type it's actually value
        _first: Any = data_type
        _value: Any = value
        resolved_type: Optional[SignalType] = None
        if _first is not None:
            try:
                resolved_type = self.get_signal_type_enum(_first)
            except (ValueError, TypeError, AttributeError):
                if _value is None:
                    _value = _first
        value = _value

        # Infer data_type from timestamp when not provided
        data_type = (
            resolved_type
            if resolved_type is not None
            else (
                SignalType.TimeDependent if timestamp is not None else SignalType.Static
            )
        )

        if (
            data_type is not None
            and data_type != SignalType.TimeDependent
            and data_type != SignalType.Static
        ):
            raise Warning(
                "PetroVisor::cleanse_data(): "
                "cleansing is only supported for 'Static' and 'TimeNumeric' data."
            )

        entity_name = ApiHelper.get_object_name(entity, **kwargs)
        signal_name = ApiHelper.get_object_name(signal, **kwargs)
        unit_name = ApiHelper.get_object_name(unit, **kwargs)
        if not unit_name:
            unit_name = self.get_signal_unit(signal_name, **kwargs) or ""

        # Build cleansing options
        cleansing_options = {
            "UseDefaultCleansingScripts": True,
            "CleansingScript": cleansing_script,
            "TreatCleansingScriptAsCleansingScriptName": True,
        }

        # Build request body based on signal type
        request_body: Dict[str, Any] = {
            "IsPreview": True,
            "CleansingOptions": cleansing_options,
        }

        if data_type == SignalType.Static:
            # Static numeric data
            request_body["StaticNumericData"] = [
                {
                    "Entity": entity_name,
                    "Signal": signal_name,
                    "Unit": unit_name,
                    "Data": value,
                }
            ]
        elif data_type == SignalType.TimeDependent:
            # Time numeric data
            timestamp_str = self.get_json_valid_value(timestamp, "time", **kwargs)
            request_body["TimeNumericData"] = [
                {
                    "Entity": entity_name,
                    "Signal": signal_name,
                    "Unit": unit_name,
                    "Data": [
                        {
                            "Date": timestamp_str,
                            "Value": value,
                        }
                    ],
                }
            ]

        # Use Data/Acquire endpoint
        return self.post(
            SignalsMixinHelper.ENDPOINT_ACQUIRE,
            data=request_body,
            **kwargs,
        )

    # normalize data input to list of dicts
    def _as_data_list(
        self,
        data: Union[List[Dict], "pd.DataFrame", "pd.Series"],
        fill_unit: bool = True,
        **kwargs,
    ) -> List[Dict]:
        """
        Normalize data input to a list of dicts.

        Converts DataFrame or Series to a list of dicts. When fill_unit=True,
        any record missing a 'Unit' field has it filled from the signal's
        default storage unit (cached per unique signal name).

        Parameters
        ----------
        data : list[dict], DataFrame, Series
            Input data
        fill_unit : bool, default True
            Fill missing Unit from signal definition
        """
        items: List[Dict] = DataFrameMixinHelper.to_data_list(data)

        if fill_unit:
            unit_cache: Dict[str, str] = {}
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not item.get("Unit") and item.get("Signal"):
                    signal_name = ApiHelper.get_object_name(item["Signal"])
                    if signal_name not in unit_cache:
                        unit_cache[signal_name] = (
                            self.get_signal_unit(signal_name, **kwargs) or ""
                        )
                    item["Unit"] = unit_cache[signal_name]

        return items

    # get a valid signal type name
    def get_signal_type_enum(
        self, signal_type: Optional[Union[str, SignalType]], **kwargs
    ) -> SignalType:
        """
        Get SignalType enum

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        return Validator.get_signal_type_enum(signal_type or "", **kwargs)

    # get a time or depth increment name
    def get_increment_enum(
        self,
        increment: Union[str, TimeIncrement, DepthIncrement],
        signal_type: Union[str, SignalType],
        **kwargs,
    ) -> Optional[Union[TimeIncrement, DepthIncrement]]:
        """
        Get TimeIncrement or DepthIncrement enum

        Parameters
        ----------
        increment : str, TimeIncrement, DepthIncrement
            Increment
        signal_type : str, SignalType
            Signal type
        """
        signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        if signal_type in {SignalType.TimeDependent, SignalType.StringTimeDependent}:
            return self.get_time_increment_enum(
                cast(Union[str, TimeIncrement], increment), **kwargs
            )
        elif signal_type in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            return self.get_depth_increment_enum(
                cast(Union[str, DepthIncrement], increment), **kwargs
            )
        return None

    # get time increment name
    def get_time_increment_enum(
        self, increment_type: Union[str, TimeIncrement], **kwargs
    ) -> TimeIncrement:
        """
        Get TimeIncrement enum

        Parameters
        ----------
        increment_type : str, TimeIncrement
            Increment
        """
        return Validator.get_time_increment_enum(increment_type, **kwargs)

    # get depth increment name
    def get_depth_increment_enum(
        self, increment_type: Union[str, DepthIncrement], **kwargs
    ) -> DepthIncrement:
        """
        Get DepthIncrement enum

        Parameters
        ----------
        increment_type : str, DepthIncrement
            Increment
        """
        return Validator.get_depth_increment_enum(increment_type, **kwargs)

    # get ordered time increments
    def get_time_increments_ordered(
        self, reverse: bool = False, **kwargs
    ) -> List[TimeIncrement]:
        """
        Get TimeIncrement enums ordered

        Parameters
        ----------
        reverse : bool, default False
            If False - ascending order, if True - descending order
        """
        increments = [
            TimeIncrement.EverySecond,
            TimeIncrement.EveryMinute,
            TimeIncrement.EveryFiveMinutes,
            TimeIncrement.EveryFifteenMinutes,
            TimeIncrement.Hourly,
            TimeIncrement.Daily,
            TimeIncrement.Monthly,
            TimeIncrement.Quarterly,
            TimeIncrement.Yearly,
        ]
        if reverse:
            return increments[::-1]
        return increments

    # get the smallest time increment
    def get_time_increments_min(
        self,
        increment_types: Union[
            List[Union[str, TimeIncrement]], Set[Union[str, TimeIncrement]]
        ],
        **kwargs,
    ) -> Optional[TimeIncrement]:
        """
        Get smallest TimeIncrement

        Parameters
        ----------
        increment_types : list[str | TimeIncrement]
            Increments
        """
        increments = set(
            [self.get_time_increment_enum(increment) for increment in increment_types]
        )
        for increment in self.get_time_increments_ordered():
            if increment in increments:
                return increment
        return None

    # get the largest time increment
    def get_time_increments_max(
        self,
        increment_types: Union[
            List[Union[str, TimeIncrement]], Set[Union[str, TimeIncrement]]
        ],
        **kwargs,
    ) -> Optional[TimeIncrement]:
        """
        Get largest TimeIncrement enum

        Parameters
        ----------
        increment_types : list[str | TimeIncrement]
            Increments
        """
        increments = set(
            [self.get_time_increment_enum(increment) for increment in increment_types]
        )
        for increment in self.get_time_increments_ordered(reverse=True):
            if increment in increments:
                return increment
        return None

    # get ordered depth increments
    def get_depth_increments_ordered(
        self, reverse: bool = False, **kwargs
    ) -> List[DepthIncrement]:
        """
        Get DepthIncrement enums ordered

        Parameters
        ----------
        reverse : bool, default False
            If False - ascending order, if True - descending order
        """
        increments = [
            DepthIncrement.TenthMeter,
            DepthIncrement.EighthMeter,
            DepthIncrement.HalfFoot,
            DepthIncrement.Foot,
            DepthIncrement.HalfMeter,
            DepthIncrement.Meter,
        ]
        if reverse:
            return increments[::-1]
        return increments

    # get smallest depth increment
    def get_depth_increments_min(
        self,
        increment_types: Union[
            List[Union[str, DepthIncrement]], Set[Union[str, DepthIncrement]]
        ],
        **kwargs,
    ) -> Optional[DepthIncrement]:
        """
        Get smallest DepthIncrement

        Parameters
        ----------
        increment_types : list[str | DepthIncrement]
            Increments
        """
        increments = set(
            [self.get_depth_increment_enum(increment) for increment in increment_types]
        )
        for increment in self.get_depth_increments_ordered():
            if increment in increments:
                return increment
        return None

    # get largest depth increment
    def get_depth_increments_max(
        self,
        increment_types: Union[
            List[Union[str, DepthIncrement]], Set[Union[str, DepthIncrement]]
        ],
        **kwargs,
    ) -> Optional[DepthIncrement]:
        """
        Get largest DepthIncrement enum

        Parameters
        ----------
        increment_types : list[str | DepthIncrement]
            Increments
        """
        increments = set(
            [self.get_depth_increment_enum(increment) for increment in increment_types]
        )
        for increment in self.get_depth_increments_ordered(reverse=True):
            if increment in increments:
                return increment
        return None
