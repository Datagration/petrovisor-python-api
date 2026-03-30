from typing import (
    Any,
    Optional,
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
from petrovisor.api.enums.increments import (
    TimeIncrement,
    DepthIncrement,
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
    Signals mixin helper — endpoint constants and pure data-conversion utilities.
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
    ENDPOINT_FILTERS_DATA = "Filters/Data"

    @staticmethod
    def to_data_list(
        data: Union[List[Dict], "pd.DataFrame", "pd.Series"],
    ) -> List[Dict]:
        """
        Convert data input to a list of dicts.

        Parameters
        ----------
        data : list[dict], DataFrame, Series
            Input data
        """
        if isinstance(data, pd.DataFrame):
            return cast(List[Dict], data.to_dict("records"))
        elif isinstance(data, pd.Series):
            return [data.to_dict()]
        return list(data)


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
        signal_type: Optional[str] = "",
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
        self, signals: List[Union[Signal, Dict[str, Any]]], **kwargs
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
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        if isinstance(signal, Signal):
            name = signal.name
        else:
            name = ApiHelper.get_object_name(signal)
        if not name:
            return ApiRequests.success()
        return self.delete(f"{route}/{self.encode(name)}", **kwargs)

    # delete signals
    def delete_signals(
        self, signals: List[Union[Signal, Dict[str, Any], str]], **kwargs
    ) -> Any:
        """
        Delete multiple signals

        Parameters
        ----------
        signals : list[Signal | dict | str]
            List of signals
        """
        route = SignalsMixinHelper.ENDPOINT_SIGNALS
        names = [
            s.name if isinstance(s, Signal) else ApiHelper.get_object_name(s)
            for s in signals
            if s
        ]
        names = [name for name in names if name]
        for name in names:
            self.delete(f"{route}/{self.encode(name)}", **kwargs)
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
        signals: Union[str, List[Union[str, Dict, Tuple[Any, str]]]],
        scenario: Optional[str] = None,
        context: Optional[Union[str, Dict[str, Any], Context]] = None,
        scope: Optional[Union[str, Dict[str, Any], Scope]] = None,
        entity_set: Optional[Union[str, Dict[str, Any], EntitySet]] = None,
        hierarchy: Optional[Union[str, Dict[str, Any], Hierarchy]] = None,
        entities: Optional[
            Union[
                Union[str, Dict[str, Any], Entity],
                List[Union[str, Dict[str, Any], Entity]],
            ]
        ] = None,
        entity_type: Optional[Union[str, List[str]]] = None,
        time_start: Optional[Union[str, datetime]] = None,
        time_end: Optional[Union[str, datetime]] = None,
        time_step: Optional[Union[str, TimeIncrement]] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Union[str, DepthIncrement]] = None,
        depth_unit: Optional[float] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        method: Optional[str] = None,
        **kwargs,
    ) -> Optional[pd.DataFrame]:
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
        method : str, optional, default None
            Data retrieval method (case-insensitive):
            - None (default): Uses Data/Retrieve endpoint with IsNumeric parameter
            - "dataview": Uses Filters/Data endpoint (frontend DataView compatibility)
        """
        # get signals
        if isinstance(signals, (list, set, tuple)):
            signal_names = signals
        else:
            signal_names = [signals]

        def get_signal_and_unit(signal):
            if isinstance(signal, (list, set, tuple)):
                signal_name = signal[0]
                unit_name = signal[1] if len(signal) > 1 else None
            else:
                signal_name, unit_name = self.get_column_name_and_unit(signal)
            signal_name = ApiHelper.get_object_name(signal_name)

            # Retry logic to handle eventual consistency issues
            # Backend may temporarily return 404 even for existing signals
            import time

            max_retries = 3
            retry_delay = 1.0
            s = None

            for attempt in range(max_retries):
                s = self.get_signal(signal_name)
                if s is not None:
                    break
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

            if s is None:
                raise ValueError(
                    f"PetroVisor::load_signals_data(): "
                    f"Signal '{signal_name}' not found after {max_retries} attempts. "
                    f"This may be due to: (1) signal does not exist, (2) backend eventual consistency issues. "
                    f"Please verify the signal exists using api.item_exists(ItemType.Signal, '{signal_name}') "
                    f"or api.get_signal('{signal_name}') before loading data."
                )

            s["UnitName"] = (
                ApiHelper.get_object_name(unit_name or "") or s["StorageUnitName"]
            )
            return s

        signals: List[Dict] = [get_signal_and_unit(s) for s in signal_names]
        signal_names = [s["Name"] for s in signals]
        if not signals:
            if not signal_names:
                warnings.warn(
                    "PetroVisor::load_signals_data():: No signals were provided.",
                    RuntimeWarning,
                )
            else:
                warnings.warn(
                    f"PetroVisor::load_signals_data():: Couldn't find signals {signal_names}.",
                    RuntimeWarning,
                )
            return None

        # get context
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
        entity_set = context.get("EntitySet", None) or {}
        scope = context.get("Scope", None) or {}
        hierarchy = ApiHelper.get_object_name(context.get("Hierarchy", None) or "")

        # get entity set
        entities = entity_set.get("Entities", None) or []
        if not entities:
            raise ValueError(
                "load_signals_data():: "
                "entity set is empty! Please provide non empty entity_set, or list of entities, or define entity_type."
            )
        entity_names = [ApiHelper.get_object_name(e) for e in entities]

        # define signal types
        signal_types = {
            "static": [s for s in signals if s["SignalType"] in {"Static", "String"}],
            "time": [
                s
                for s in signals
                if s["SignalType"] in {"TimeDependent", "StringTimeDependent"}
            ],
            "depth": [
                s
                for s in signals
                if s["SignalType"] in {"DepthDependent", "StringDepthDependent"}
            ],
        }
        signal_types = {k: v for k, v in signal_types.items() if v}
        has_time_signals = signal_types.get("time", None) is not None
        # has_depth_signals = signal_types.get("depth", None) is not None
        # has_static_signals = signal_types.get("static", None) is not None

        # get scope range
        time_start = None
        time_end = None
        time_step = None
        depth_start = None
        depth_end = None
        depth_step = None
        time_signals = signal_types.get("time", None)
        if time_signals:
            time_start = scope.get("Start", None)
            time_end = scope.get("End", None)
            time_step = scope.get("TimeIncrement", None)
            if time_step:
                time_step = str(self.get_time_increment_enum(time_step).name)
            else:
                time_step = str(TimeIncrement.EverySecond.name)
            if not time_start or pd.isnull(time_start):
                # may use later in case there will evidence that it is faster
                # time_starts: List[Any] = [
                #     pd.to_datetime(
                #         (self.get_data_range(s["SignalType"]) or {}).get("Start", "")
                #     )
                #     for s in ["TimeDependent", "StringTimeDependent"]
                # ]
                time_starts: List[Any] = [
                    pd.to_datetime(
                        (
                            self.get_data_range(
                                s["SignalType"],
                                signal=s["Name"],
                                entity=entity_names,
                            )
                            or {}
                        ).get("Start", "")
                    )
                    for s in time_signals
                ]
                time_start = np.min(time_starts)
            if not time_end or pd.isnull(time_end):
                # may use later in case there will be evidence that it is faster
                # time_end: List[Any] = [
                #     pd.to_datetime(
                #         (self.get_data_range(s["SignalType"]) or {}).get("End", "")
                #     )
                #     for s in ["TimeDependent", "StringTimeDependent"]
                # ]
                time_ends: List[Any] = [
                    pd.to_datetime(
                        (
                            self.get_data_range(
                                s["SignalType"],
                                signal=s["Name"],
                                entity=entity_names,
                            )
                            or {}
                        ).get("End", "")
                    )
                    for s in time_signals
                ]
                time_end = np.max(time_ends)

            # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
            time_start = self.datetime_to_string(pd.to_datetime(time_start))
            time_end = self.datetime_to_string(pd.to_datetime(time_end))

        depth_signals = signal_types.get("depth", None)
        if depth_signals:
            depth_start = scope.get("StartDepth", None)
            depth_end = scope.get("EndDepth", None)
            depth_step = scope.get("DepthIncrement", None)
            if depth_step:
                depth_step = str(self.get_depth_increment_enum(depth_step).name)
            else:
                depth_step = str(DepthIncrement.Meter.name)

            if depth_start is None or pd.isnull(depth_start):
                depth_starts = [
                    (
                        self.get_data_range(
                            s["SignalType"], signal=s["Name"], entity=entity_names
                        )
                        or {}
                    ).get("Start", None)
                    for s in depth_signals
                ]
                _depth_start_np = np.min(
                    [v for v in depth_starts if v is not None] or None
                )
                depth_start = float(
                    _depth_start_np
                    if _depth_start_np is not None
                    else np.finfo(np.float64).min
                )
            if depth_end is None or pd.isnull(depth_end):
                depth_ends = [
                    (
                        self.get_data_range(
                            s["SignalType"], signal=s["Name"], entity=entity_names
                        )
                        or {}
                    ).get("End", None)
                    for s in depth_signals
                ]
                _depth_end_np = np.max([v for v in depth_ends if v is not None] or None)
                depth_end = float(
                    _depth_end_np
                    if _depth_end_np is not None
                    else np.finfo(np.float64).max
                )

            # convert to float
            depth_start = float(depth_start)
            depth_end = float(depth_end)

        df_time = None
        df_depth = None
        df_static = None

        # Prepare common data needed for both methods
        unit_names = [s["UnitName"] for s in signals]
        signals_with_units_map = {
            s["Name"]: f"{s['Name']} [{s['UnitName']}]" for s in signals
        }

        # Normalize method parameter (case-insensitive)
        if method is not None:
            method = method.lower()

        if method == "dataview":
            # Use Filters/Data endpoint (for frontend DataView compatibility)
            data_rqst: Dict[str, Any] = {
                "CheckedEntities": entity_names,
                "CheckedSignals": signal_names,
                "CheckedUnits": unit_names,
            }
            if scenario:
                if not isinstance(scenario, (list, tuple, set)):
                    scenarios = [scenario]
                else:
                    scenarios = list(scenario)
                data_rqst["ScenarioNames"] = scenarios
            if hierarchy:
                data_rqst["HierarchyName"] = hierarchy
            if time_start is not None:
                data_rqst["TimeStart"] = time_start
            if time_end is not None:
                data_rqst["TimeEnd"] = time_end
            if time_step is not None:
                data_rqst["TimeStep"] = time_step
            if depth_start is not None:
                data_rqst["DepthStart"] = depth_start
            if depth_end is not None:
                data_rqst["DepthEnd"] = depth_end
            if depth_step is not None:
                data_rqst["DepthStep"] = depth_step
            if depth_unit is not None:
                data_rqst["DepthUnit"] = depth_unit
            if pressure_unit:
                data_rqst["PressureUnit"] = pressure_unit
            if temperature_unit:
                data_rqst["TemperatureUnit"] = temperature_unit

            table_data = (
                self.post(SignalsMixinHelper.ENDPOINT_FILTERS_DATA, data=data_rqst)
                or {}
            )
            data_time_num = table_data.get("DataNumeric", [])
            data_time_str = table_data.get("DataString", [])
            data_depth_num = table_data.get("DataDepth", [])
            data_depth_str = table_data.get("DataDepthString", [])

            if data_time_num and data_time_str:
                data_time = [*data_time_num, *data_time_str]
            elif data_time_num:
                data_time = data_time_num
            elif data_time_str:
                data_time = data_time_str
            else:
                data_time = []

            if data_depth_num and data_depth_str:
                data_depth = [*data_depth_num, *data_depth_str]
            elif data_depth_num:
                data_depth = data_depth_num
            elif data_depth_str:
                data_depth = data_depth_str
            else:
                data_depth = []

            if data_time:
                # create DataFrame by normalizing JSON
                df_normalized = pd.json_normalize(
                    data_time,
                    meta=["EntityName", "ResultName", "UnitName"],
                    record_path=["Data"],
                )

                # generate PivotTable
                if "Date" not in df_normalized.columns:
                    warnings.warn(
                        "PetroVisor::load_signals_data():: Couldn't retrieve any 'time' data.",
                        RuntimeWarning,
                    )
                else:
                    df = df_normalized.pivot(
                        index=["EntityName", "Date"],
                        columns="ResultName",
                        values="Value",
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df = df.rename(columns={"EntityName": "Entity"})
                    df["Date"] = pd.to_datetime(df["Date"])
                    if has_time_signals:
                        df_time = df
                    else:
                        df_static = df.drop(columns=["Date"])

            if data_depth:
                # create DataFrame by normalizing JSON
                df_normalized = pd.json_normalize(
                    data_depth,
                    meta=["EntityName", "ResultName", "UnitName"],
                    record_path=["Data"],
                )

                # generate PivotTable
                if "Depth" not in df_normalized.columns:
                    warnings.warn(
                        "PetroVisor::load_signals_data():: Couldn't retrieve any 'depth' data.",
                        RuntimeWarning,
                    )
                else:
                    df = df_normalized.pivot(
                        index=["EntityName", "Depth"],
                        columns="ResultName",
                        values="Value",
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df = df.rename(columns={"EntityName": "Entity"})
                    df_depth = df
        else:
            # Use Data/Retrieve endpoint (default, unified API)
            # Separate signals by type for proper request construction
            signals_with_units_num = [
                {"Signal": s["Name"], "Unit": s["UnitName"]}
                for s in signals
                if s["SignalType"]
                in {"TimeDependent", "DepthDependent", "Static", "PVT"}
            ]
            signals_with_units_str = [
                {"Signal": s["Name"], "Unit": s["UnitName"]}
                for s in signals
                if s["SignalType"]
                in {"StringTimeDependent", "StringDepthDependent", "String"}
            ]

            # Determine if we have time, depth, or static signals
            has_time_signals = any(
                s["SignalType"] in {"TimeDependent", "StringTimeDependent"}
                for s in signals
            )
            has_depth_signals = any(
                s["SignalType"] in {"DepthDependent", "StringDepthDependent"}
                for s in signals
            )
            # has_static_signals = any(
            #     s["SignalType"] in {"Static", "String"} for s in signals
            # )
            has_pvt_signals = any(s["SignalType"] == "PVT" for s in signals)

            # Retrieve numeric data
            if signals_with_units_num:
                data_rqst: Dict[str, Any] = {
                    "Combinations": {
                        "Entities": entity_names,
                        "Signals": signals_with_units_num,
                    }
                }

                # Add time/depth range parameters
                if has_time_signals and time_start is not None:
                    data_rqst["TimeStart"] = time_start
                if has_time_signals and time_end is not None:
                    data_rqst["TimeEnd"] = time_end
                if has_time_signals and time_step is not None:
                    data_rqst["TimeIncrement"] = time_step
                if has_depth_signals and depth_start is not None:
                    data_rqst["DepthStart"] = depth_start
                if has_depth_signals and depth_end is not None:
                    data_rqst["DepthEnd"] = depth_end
                if has_depth_signals and depth_step is not None:
                    data_rqst["DepthIncrement"] = depth_step
                if depth_unit:
                    data_rqst["DepthUnit"] = depth_unit

                # Add hierarchy and scenario
                if hierarchy:
                    data_rqst["Hierarchy"] = hierarchy
                if scenario:
                    if not isinstance(scenario, (list, tuple, set)):
                        data_rqst["Scenarios"] = [scenario]
                    else:
                        data_rqst["Scenarios"] = list(scenario)

                # Add PVT parameters
                if has_pvt_signals:
                    if pressure_unit:
                        data_rqst["PressureUnit"] = pressure_unit
                    if temperature_unit:
                        data_rqst["TemperatureUnit"] = temperature_unit

                # Call Data/Retrieve (backend determines numeric/string from signal name)
                response = (
                    self.post(SignalsMixinHelper.ENDPOINT_RETRIEVE, data=data_rqst)
                    or {}
                )

                # Extract data by type
                data_time_num = response.get("TimeNumericData", [])
                data_depth_num = response.get("DepthNumericData", [])
                data_static_num = response.get("StaticNumericData", [])
                data_pvt_num = response.get("PVTNumericData", [])
            else:
                data_time_num = []
                data_depth_num = []
                data_static_num = []
                data_pvt_num = []

            # Retrieve string data
            if signals_with_units_str:
                data_rqst: Dict[str, Any] = {
                    "Combinations": {
                        "Entities": entity_names,
                        "Signals": signals_with_units_str,
                    }
                }

                # Add time/depth range parameters
                if has_time_signals and time_start is not None:
                    data_rqst["TimeStart"] = time_start
                if has_time_signals and time_end is not None:
                    data_rqst["TimeEnd"] = time_end
                if has_time_signals and time_step is not None:
                    data_rqst["TimeIncrement"] = time_step
                if has_depth_signals and depth_start is not None:
                    data_rqst["DepthStart"] = depth_start
                if has_depth_signals and depth_end is not None:
                    data_rqst["DepthEnd"] = depth_end
                if has_depth_signals and depth_step is not None:
                    data_rqst["DepthIncrement"] = depth_step
                if depth_unit:
                    data_rqst["DepthUnit"] = depth_unit

                # Add hierarchy and scenario
                if hierarchy:
                    data_rqst["Hierarchy"] = hierarchy
                if scenario:
                    if not isinstance(scenario, (list, tuple, set)):
                        data_rqst["Scenarios"] = [scenario]
                    else:
                        data_rqst["Scenarios"] = list(scenario)

                # Call Data/Retrieve (backend determines numeric/string from signal name)
                response = (
                    self.post(SignalsMixinHelper.ENDPOINT_RETRIEVE, data=data_rqst)
                    or {}
                )

                # Extract data by type
                data_time_str = response.get("TimeStringData", [])
                data_depth_str = response.get("DepthStringData", [])
                data_static_str = response.get("StaticStringData", [])
            else:
                data_time_str = []
                data_depth_str = []
                data_static_str = []

            # Merge numeric and string data by type
            if data_time_num or data_time_str:
                data_time = [*(data_time_num or []), *(data_time_str or [])]

                # Create DataFrame by normalizing JSON
                df_normalized = pd.json_normalize(
                    data_time,
                    meta=["Entity", "Signal", "Unit", "Scenario"],
                    record_path=["Data"],
                )

                if "Date" in df_normalized.columns:
                    df = df_normalized.pivot(
                        index=["Entity", "Date"],
                        columns="Signal",
                        values="Value",
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df["Date"] = pd.to_datetime(df["Date"])
                    if has_time_signals:
                        df_time = df
                    else:
                        df_static = df.drop(columns=["Date"])

            if data_depth_num or data_depth_str:
                data_depth = [*(data_depth_num or []), *(data_depth_str or [])]

                # Create DataFrame by normalizing JSON
                df_normalized = pd.json_normalize(
                    data_depth,
                    meta=["Entity", "Signal", "Unit", "Scenario"],
                    record_path=["Data"],
                )

                if "Depth" in df_normalized.columns:
                    df = df_normalized.pivot(
                        index=["Entity", "Depth"],
                        columns="Signal",
                        values="Value",
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df_depth = df

            if data_static_num or data_static_str:
                data_static = [*(data_static_num or []), *(data_static_str or [])]

                # Create DataFrame by normalizing JSON
                df_normalized = pd.json_normalize(data_static)

                if (
                    "Entity" in df_normalized.columns
                    and "Signal" in df_normalized.columns
                ):
                    df = df_normalized.pivot(
                        index="Entity",
                        columns="Signal",
                        values="Data",
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df_static = df

            # Handle PVT data if present
            if data_pvt_num:
                # PVT data has structure: Entity, Signal, Unit, Data[{Pressure, Temperature, Value}], Scenario
                # For now, we'll add this to the processing but it needs special handling
                # TODO: Implement PVT-specific DataFrame construction
                pass

        def reorder_columns(df, signal_names):
            non_signal_columns = [
                col
                for col in df.columns
                if self.get_column_name_without_unit(col) not in signal_names
            ]
            return df[
                [
                    *non_signal_columns,
                    *[col for col in df.columns if col not in non_signal_columns],
                ]
            ]

        # merge all tables
        df = None
        if df_time is not None:
            df = df_time
        if df_depth is not None:
            if df is not None:
                df = pd.merge(df, df_depth, on="Entity")
                columns = df.columns.tolist()
                columns.remove("Depth")
                columns.insert(2, "Depth")
                df = df[columns]
            else:
                df = df_depth
            if depth_unit:
                df = df.rename(columns={"Depth": f"Depth [{depth_unit}]"})
        if df_static is not None:
            if df is not None:
                df = pd.merge(df, df_static, on="Entity")
            else:
                df = df_static
        if df is None:
            warnings.warn(
                "PetroVisor::load_signals_data():: Couldn't retrieve any data.",
                RuntimeWarning,
            )
            return df
        return reorder_columns(df, signal_names)

    # load data
    def load_data(
        self,
        data: Union[List[Dict], "pd.DataFrame", "pd.Series"],
        start: Optional[Union[datetime, float]] = None,
        end: Optional[Union[datetime, float]] = None,
        step: Optional[Union[str, TimeIncrement, DepthIncrement]] = None,
        hierarchy: Optional[str] = None,
        num_values: Optional[int] = None,
        gap_value: Optional[float] = None,
        interpolated: Optional[bool] = False,
        with_logs: bool = False,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        **kwargs,
    ) -> Any:
        """
        Load data

        Parameters
        ----------
        data : list[dict] | DataFrame | Series
            Request specs as a list of dicts (Entity, Signal, Unit) or a
            DataFrame/Series with those columns. Unit is optional and
            defaults to the signal's storage unit when omitted.
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        step : str, TimeIncrement, DepthIncrement, None, default None
            Step of time/depth range
        hierarchy : str, None, default None
            Hierarchy name
        num_values : int, None, default None
            Number of values to load
        gap_value : float, None, default None
            Gap filling value to use
        interpolated : bool, default False
            Whether to get interpolated value (depth dependent data)
        with_logs : bool, default False
            Load data and return logs
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        """
        data = self._as_data_list(data, fill_unit=True, **kwargs)
        data_type = None
        if "data_type" in kwargs:
            warnings.warn(
                "PetroVisor::load_data():: "
                "'data_type' is deprecated and will be removed in a future version.",
                DeprecationWarning,
            )
            data_type = self.get_signal_type_enum(kwargs.pop("data_type"), **kwargs)
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
        data: Union[List[Dict], "pd.DataFrame", "pd.Series"],
        with_logs: bool = False,
        logs_source: Optional[str] = None,
        no_range_delete: bool = False,
        values_time_increment: Optional[str] = None,
        values_depth_increment: Optional[str] = None,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        **kwargs,
    ) -> Any:
        """
        Save Signals data

        Parameters
        ----------
        data : list[dict] | DataFrame | Series
            Data records with Entity, Signal, Unit (optional) and Data fields.
            DataFrame/Series are converted to a list of dicts automatically.
            Unit defaults to the signal's storage unit when omitted.
        with_logs : bool, default False
            Generate logs (uses GenerateLogs field in request body)
        logs_source : str, optional
            Source for logs
        no_range_delete : bool, default False
            Don't delete existing data in range
        values_time_increment : str, optional
            Time increment for aggregation (e.g., 'EverySecond', 'Daily')
        values_depth_increment : str, optional
            Depth increment for aggregation (e.g., 'TenthMeter', 'Meter')
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        """
        data = self._as_data_list(data, fill_unit=True, **kwargs)
        data_type = None
        if "data_type" in kwargs:
            warnings.warn(
                "PetroVisor::save_data():: "
                "'data_type' is deprecated and will be removed in a future version.",
                DeprecationWarning,
            )
            data_type = self.get_signal_type_enum(kwargs.pop("data_type"), **kwargs)

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
        if data_type == SignalType.TimeDependent:
            request_body["TimeNumericData"] = data
        elif data_type == SignalType.Static:
            request_body["StaticNumericData"] = data
        elif data_type == SignalType.StringTimeDependent:
            request_body["TimeStringData"] = data
        elif data_type == SignalType.String:
            request_body["StaticStringData"] = data
        elif data_type == SignalType.DepthDependent:
            request_body["DepthNumericData"] = data
        elif data_type == SignalType.StringDepthDependent:
            request_body["DepthStringData"] = data
        elif data_type == SignalType.PVT:
            request_body["PVTNumericData"] = data

        # Add optional fields
        if logs_source:
            request_body["LogsSource"] = logs_source
        if values_time_increment:
            request_body["ValuesTimeIncrement"] = values_time_increment
        if values_depth_increment:
            request_body["ValuesDepthIncrement"] = values_depth_increment

        # Add PVT unit parameters
        if data_type == SignalType.PVT:
            request_body["PressureUnit"] = pressure_unit
            request_body["TemperatureUnit"] = temperature_unit

        # Always use Data/Save endpoint (GenerateLogs flag controls log generation)
        return self.post(SignalsMixinHelper.ENDPOINT_SAVE, data=request_body, **kwargs)

    # delete data
    def delete_data(
        self,
        data: Union[List[Dict], "pd.DataFrame", "pd.Series"],
        start: Optional[Union[datetime, float]] = None,
        end: Optional[Union[datetime, float]] = None,
        **kwargs,
    ) -> Any:
        """
        Delete data using Data/Delete endpoint

        Parameters
        ----------
        data : list[dict] | DataFrame | Series
            Request specs as a list of dicts (Entity, Signal) or a
            DataFrame/Series with those columns.
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        """
        data = self._as_data_list(data, fill_unit=False, **kwargs)
        data_type = None
        if "data_type" in kwargs:
            warnings.warn(
                "PetroVisor::delete_data():: "
                "'data_type' is deprecated and will be removed in a future version.",
                DeprecationWarning,
            )
            data_type = self.get_signal_type_enum(kwargs.pop("data_type"), **kwargs)

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
        value: float,
        timestamp: Optional[Union[datetime, str]],
        signal: Union[Dict, str],
        entity: Union[Dict, str],
        cleansing_script: str,
        unit: Optional[Union[Dict, str]] = None,
        **kwargs,
    ) -> Any:
        """
        Cleanse data

        Parameters
        ----------
        value : float
            Value
        timestamp : datetime,str
            Date
        signal : str, dict
            Signal object or Signal name
        entity : str, dict
            Entity object or Entity name
        cleansing_script : str
            Cleansing script
        unit : str, dict, optional
            Unit object or Unit name. Defaults to the signal's storage unit.
        """
        data_type = None
        if "data_type" in kwargs:
            warnings.warn(
                "PetroVisor::cleanse_data():: "
                "'data_type' is deprecated and will be removed in a future version.",
                DeprecationWarning,
            )
            data_type = self.get_signal_type_enum(kwargs.pop("data_type"), **kwargs)
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
        items: List[Dict] = SignalsMixinHelper.to_data_list(data)

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
