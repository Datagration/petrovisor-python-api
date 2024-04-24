from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
    Tuple,
)

from datetime import datetime
import pandas as pd
import numpy as np
import warnings
import sys

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.dtypes.items import ItemType
from petrovisor.api.dtypes.internal_dtypes import SignalType
from petrovisor.api.dtypes.increments import (
    TimeIncrement,
    DepthIncrement,
)
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsDataFrames,
    SupportsContextRequests,
    SupportsEntitiesRequests,
)


# Signals API calls
class SignalsMixin(
    SupportsDataFrames,
    SupportsContextRequests,
    SupportsEntitiesRequests,
    SupportsItemRequests,
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

    # get measurement 'Units'
    def get_measurement_units(self, measurement: str, **kwargs) -> Any:
        """
        Get measurement units

        Parameters
        ----------
        measurement : str
            Measurement name
        """
        route = "Units"
        return self.get(f"{route}/{self.encode(measurement)}/Units", **kwargs)

    # get measurement 'Unit' names
    def get_measurement_unit_names(self, measurement: str, **kwargs) -> Any:
        """
        Get measurement unit names

        Parameters
        ----------
        measurement : str
            Measurement name
        """
        units = self.get_measurement_units(measurement, **kwargs)
        return [unit["Name"] for unit in units]

    # get 'Signal'
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
        route = "Signals"
        if short_name:
            signal = self.get(f"{route}/{self.encode(short_name)}/Signal", **kwargs)
        else:
            signal = None
        if signal is None:
            return self.get(f"{route}/{self.encode(name)}", **kwargs)
        return None

    # get 'Signals'
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
        route = "Signals"
        # get signals by signal type
        if signal_type:
            signal_type = self.get_signal_type_enum(signal_type, **kwargs).name
            signals = self.get(f"{route}/{signal_type}/Signals", **kwargs)
        # get all signals
        else:
            signals = self.get(f"{route}/All", **kwargs)
        # get signals by 'Entity' name
        if entity:
            signal_names = self.get_signal_names(
                signal_type=None, entity=entity, **kwargs
            )
            if signal_names and signals:
                return [s for s in signals if s["Name"] in signal_names]
            return []
        return signals if signals is not None else []

    # get 'Signal' names
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
        route = "Signals"
        # get signals by 'Entity' name
        if entity:
            entities_route = "Entities"
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

    # add 'Signals'
    def add_signals(self, signals: List, **kwargs) -> Any:
        """
        Add multiple signals

        Parameters
        ----------
        signals : list
            List of signals
        """
        route = "Signals"
        return self.post(f"{route}/Add", data=signals, **kwargs)

    # delete 'Signals'
    def delete_signals(self, signals: List, **kwargs) -> Any:
        """
        Delete multiple signals

        Parameters
        ----------
        signals : list
            List of signals
        """
        route = "Signals"
        for signal_name in signals:
            self.delete(f"{route}/{self.encode(signal_name)}", **kwargs)

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
        signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        if signal_type in {SignalType.Static, SignalType.String}:
            return {"Start": None, "End": None}

        route = self.get_signal_type_route(signal_type=signal_type, **kwargs)
        if signal_type in {
            SignalType.TimeDependent,
            SignalType.StringTimeDependent,
        }:
            if signal and entity:
                signal_name = ApiHelper.get_object_name(signal)
                if not isinstance(entity, (list, tuple, set)):
                    entity_name = ApiHelper.get_object_name(entity)
                    return self.get(
                        f"{route}/Range/{self.encode(signal_name)}/{self.encode(entity_name)}",
                        **kwargs,
                    )
                else:
                    signal_name = ApiHelper.get_object_name(signal)
                    minmax = [
                        (
                            self.get(
                                f"{route}/Range/{self.encode(signal_name)}/{self.encode(ApiHelper.get_object_name(e))}",
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
                return self.get(f"{route}/Range/{signal_name}", **kwargs)
            return self.get(f"{route}/Range", **kwargs)
        elif signal_type in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            if signal and entity and not isinstance(entity, (list, tuple, set)):
                signal_name = ApiHelper.get_object_name(signal)
                entity_name = ApiHelper.get_object_name(entity)
                min_value = self.post(
                    f"{route}/DepthStepExtremum",
                    query={"IsMinimum": True},
                    data=[{"Entity": entity_name, "Signal": signal_name}],
                    **kwargs,
                )[0]
                max_value = self.post(
                    f"{route}/DepthStepExtremum",
                    query={"IsMinimum": False},
                    data=[{"Entity": entity_name, "Signal": signal_name}],
                    **kwargs,
                )[0]
                return {"Start": min_value, "End": max_value}
            else:
                if signal:
                    signal_name = ApiHelper.get_object_name(signal)
                    if entity and isinstance(entity, (list, tuple, set)):
                        entities = entity
                    else:
                        entities = self.get_entities(signal=signal_name)
                    data = [
                        {"Entity": ApiHelper.get_object_name(e), "Signal": signal_name}
                        for e in entities
                    ]
                else:
                    entities = self.get_entities()
                    signals = self.get_signals(signal_type=signal_type)
                    data = [
                        {
                            "Entity": ApiHelper.get_object_name(e),
                            "Signal": ApiHelper.get_object_name(s),
                        }
                        for e in entities
                        for s in signals
                    ]
                if not data:
                    return {"Start": None, "End": None}
                min_values = self.post(
                    f"{route}/DepthStepExtremum",
                    query={"IsMinimum": True},
                    data=data,
                    **kwargs,
                )
                max_values = self.post(
                    f"{route}/DepthStepExtremum",
                    query={"IsMinimum": False},
                    data=data,
                    **kwargs,
                )
                return {
                    "Start": np.min([v for v in min_values if v is not None] or None),
                    "End": np.max([v for v in max_values if v is not None] or None),
                }
        return {"Start": None, "End": None}

    # cleanse data
    def cleanse_data(
        self,
        data_type: Union[str, SignalType],
        value: float,
        timestamp: Optional[Union[datetime, str]],
        signal: Union[Dict, str],
        unit: Union[Dict, str],
        entity: Union[Dict, str],
        cleansing_script: str,
        **kwargs,
    ) -> Any:
        """
        Cleanse data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        value : float
            Value
        timestamp : datetime,str
            Date
        signal : str, dict
            Signal object or Signal name
        unit : str, dict
            Unit object or Unit name
        entity : str, dict
            Entity object or Entity name
        cleansing_script : str
            Cleansing script
        """
        data_type = self.get_signal_type_enum(data_type, **kwargs)
        route = self.get_signal_type_route(signal_type=data_type, **kwargs)
        if data_type != SignalType.TimeDependent and data_type != SignalType.Static:
            raise Warning(
                "PetroVisor::cleanse_data(): "
                "cleansing is only supported for 'Static' and 'TimeNumeric' data."
            )
        options = {
            "UseDefaultCleansingScripts": True,
            "CleansingScript": cleansing_script,
            "TreatCleansingScriptAsCleansingScriptName": True,
            "IsPreview": True,
        }
        options = ApiHelper.update_dict(options, **kwargs)
        entity_name = ApiHelper.get_object_name(entity, **kwargs)
        signal_name = ApiHelper.get_object_name(signal, **kwargs)
        unit_name = ApiHelper.get_object_name(unit, **kwargs)
        data_with_options = {
            "Entity": entity_name,
            "Signal": signal_name,
            "Unit": unit_name,
            "Value": value,
            "Options": options,
        }
        if data_type == SignalType.TimeDependent:
            data_with_options["Timestamp"] = self.get_json_valid_value(
                timestamp, "time", **kwargs
            )
        return self.post(f"{route}/Cleanse", data=data_with_options, **kwargs)

    # load signals data
    def load_signals_data(
        self,
        signals: Union[str, List[Union[str, Dict, Tuple[Any, str]]]],
        context: Union[str, Dict] = None,
        entity_set: Union[str, Dict, List[Union[str, Dict]]] = None,
        scope: Union[str, Dict] = None,
        hierarchy: Union[str, Dict] = None,
        scenario: Union[str, Dict] = None,
        entity_type: Union[str, List[str]] = None,
        entities: Union[Union[str, Dict], List[Union[str, Dict]]] = None,
        time_start: Union[str, datetime] = None,
        time_end: Union[str, datetime] = None,
        time_step: Union[str, TimeIncrement] = None,
        depth_start: float = None,
        depth_end: float = None,
        depth_step: Union[str, DepthIncrement] = None,
        depth_unit: float = None,
        **kwargs,
    ) -> Optional[pd.DataFrame]:
        """
        Load signals data

        Parameters
        ----------
        signals : str | list[str] | list[dict|object]
            Signal name(s) or Signal objects. Single signal or multiple signals
        context : Union[str, dict, object]
            Context name or object
        entity_set : str  | list[str], default None
            Entity set or list of Entities. If None, then all entities of requested entity type will be considered
        scope : str, default None
            Scope name
        hierarchy : str, default None
            Hierarchy name
        scenario : str, default None
            Scenario name
        entity_type : str | list[str], default None
            Entity type. Used when entity_set, entities or context is not provided.
            If not None, will filter out entities defined in entity_set.
        entities : str | list[str], default None
            Entity or list of Entities
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
                signal_name = signal
                unit_name = None
            signal_name = ApiHelper.get_object_name(signal_name)
            s = self.get_signal(signal_name)
            s["UnitName"] = (
                ApiHelper.get_object_name(unit_name or "") or s["StorageUnitName"]
            )
            return s

        signals = [get_signal_and_unit(s) for s in signal_names]
        signal_names = [s["Name"] for s in signals]
        if not signals:
            if not signal_names:
                warnings.warn(
                    "load_signals_data():: No signals were provided.",
                    RuntimeWarning,
                )
            else:
                warnings.warn(
                    f"load_signals_data():: Couldn't find signals {signal_names}.",
                    RuntimeWarning,
                )
            return None

        # get context
        context = (
            self.get_context(
                context,
                context=context,
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
                f"entity set is empty! Please provide non empty entity_set, or list of entities, or define entity_type."
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
        has_static_signals = signal_types.get("static", None) is not None
        has_time_signals = signal_types.get("time", None) is not None
        has_depth_signals = signal_types.get("depth", None) is not None

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
                # might use later in case there will evidence that it is faster
                # time_start = np.min(
                #     [
                #         pd.to_datetime(
                #             (self.get_data_range(s["SignalType"]) or {}).get(
                #                 "Start", ""
                #             )
                #         )
                #         for s in ["TimeDependent", "StringTimeDependent"]
                #     ]
                # )
                time_start = np.min(
                    [
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
                )
            if not time_end or pd.isnull(time_end):
                # might use later in case there will evidence that it is faster
                # time_end = np.max(
                #     [
                #         pd.to_datetime(
                #             (
                #                 self.get_data_range(s["SignalType"]) or {}
                #             ).get("End", "")
                #         )
                #         for s in ["TimeDependent", "StringTimeDependent"]
                #     ]
                # )
                time_end = np.max(
                    [
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
                )

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
                depth_start = np.min([v for v in depth_starts if v is not None] or None)
                depth_start = (
                    depth_start if depth_start is not None else np.finfo(np.float64).min
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
                depth_end = np.min([v for v in depth_ends if v is not None] or None)
                depth_end = (
                    depth_end if depth_end is not None else np.finfo(np.float64).max
                )

            # convert to float
            depth_start = float(depth_start)
            depth_end = float(depth_end)

        df_time = None
        df_depth = None
        df_static = None
        # use_filters = True  # use when is more reliable
        use_filters = False  # use when is more reliable
        if use_filters:
            unit_names = [s["UnitName"] for s in signals]
            signals_with_units_map = {
                s["Name"]: f"{s['Name']} [{s['UnitName']}]" for s in signals
            }
            data_rqst = {
                # "Name": "string",
                # "EntityNamePattern": "string",
                # "SignalNamePattern": "string",
                # "ShowEmptyRows": true,
                # "ShowEmptyColumns": true,
                # "HierarchyName": "string",
                # "EntityType": "string",
                # "DataTypes": [
                #  "None"
                # ],
                # "EntitySetName": "string",
                "CheckedEntities": entity_names,
                "CheckedSignals": signal_names,
                "CheckedUnits": unit_names,
                # "ScopeName": "string",
                # "ChartDefinitionName": "string",
                # "ScenarioNames": [
                #  "string"
                # ],
                # "IncludeWorkspaceData": true,
                # "TimeStart": "2024-04-12T20:42:22.961Z",
                # "TimeEnd": "2024-04-12T20:42:22.961Z",
                # "TimeStep": "EverySecond",
                # "DepthStart": 0,
                # "DepthEnd": 0,
                # "DepthStep": "TenthMeter"
            }
            if scenario:
                if not isinstance(scenario, (list, tuple, set)):
                    scenarios = list(scenario)
                else:
                    scenarios = [scenario]
                data_rqst["Scenario"] = scenarios
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

            table_data = self.post("Filters/Data", data=data_rqst) or {}
            data_time_num = table_data.get("DataNumeric", [])
            data_time_str = table_data.get("DataString", [])
            data_depth_num = table_data.get("DataDepth", [])
            data_depth_str = table_data.get("DataStringDepth", [])

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
                # create DataFrame by normalizing json
                df_normalized = pd.json_normalize(
                    data_time,
                    meta=["EntityName", "ResultName", "UnitName"],
                    record_path=["Data"],
                )

                # generate PivotTable
                df = df_normalized.pivot(
                    index=["EntityName", "Date"], columns="ResultName", values="Value"
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
                # create DataFrame by normalizing json
                df_normalized = pd.json_normalize(
                    data_depth,
                    meta=["EntityName", "ResultName", "UnitName"],
                    record_path=["Data"],
                )

                # generate PivotTable
                df = df_normalized.pivot(
                    index=["EntityName", "Depth"], columns="ResultName", values="Value"
                )
                df.columns.name = None
                df = df.rename(columns=signals_with_units_map)
                df = df.reset_index()
                df = df.rename(columns={"EntityName": "Entity"})
                df_depth = df
        else:
            for data_type, data_type_signals in signal_types.items():
                if data_type == "static":
                    num_signal_type = "Static"
                    str_signal_type = "String"
                elif data_type == "time":
                    num_signal_type = "TimeDependent"
                    str_signal_type = "StringTimeDependent"
                elif data_type == "depth":
                    num_signal_type = "DepthDependent"
                    str_signal_type = "StringDepthDependent"
                else:
                    continue

                # collect signal names with unit names for dats retrieval
                signals_with_units_num = [
                    {"Signal": s["Name"], "Unit": s["UnitName"]}
                    for s in data_type_signals
                    if s["SignalType"] == num_signal_type
                ]
                signals_with_units_str = [
                    {"Signal": s["Name"], "Unit": s["UnitName"]}
                    for s in data_type_signals
                    if s["SignalType"] == str_signal_type
                ]
                signals_with_units_map = {
                    s["Name"]: f"{s['Name']} [{s['UnitName']}]"
                    for s in data_type_signals
                }

                # retrieve numeric data
                if signals_with_units_num:
                    if data_type == "time":
                        data_rqst = {
                            # "Requests": [
                            #    {
                            #        "Entity": "string",
                            #        "Signal": "string",
                            #        "Unit": "string"
                            #    }
                            #  ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_num,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            # "Hierarchy": "string",
                            "TimeIncrement": time_step,
                            "Start": time_start,
                            "End": time_end,
                            # "Options": {
                            #     "WithGaps": true,
                            #     "GapValue": "NaN",
                            #     "GapStringValue": ""
                            # }
                        }
                        if hierarchy:
                            data_rqst["Hierarchy"] = hierarchy
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        # if num_gap_value is not None:
                        #     data_rqst["Options"] = {"WithGaps": True, "GapStringValue": num_gap_value}
                        data_num = self.post("Data/Time/Retrieve", data=data_rqst)
                    elif data_type == "depth":
                        data_rqst = {
                            # "Requests": [
                            #     {
                            #         "Entity": "string",
                            #         "Signal": "string",
                            #         "Unit": "string"
                            #     }
                            # ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_num,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            "DepthIncrement": depth_step,
                            "StartDepth": depth_start,
                            "EndDepth": depth_end,
                            # "Options": {
                            #     "WithGaps": true,
                            #     "GapValue": "NaN",
                            #     "GapStringValue": ""
                            # },
                            # "DepthUnit": depth_unit,
                        }
                        if depth_unit is not None:
                            data_rqst["DepthUnit"] = depth_unit
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        # if num_gap_value is not None:
                        #     data_rqst["Options"] = {"WithGaps": True, "GapStringValue": num_gap_value}
                        data_num = self.post("Data/Depth/Retrieve", data=data_rqst)
                    else:
                        data_rqst = {
                            # "Requests": [
                            #    {
                            #        "Entity": "string",
                            #        "Signal": "string",
                            #        "Unit": "string"
                            #    }
                            #  ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_num,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            # "Hierarchy": "string",
                        }
                        if hierarchy:
                            data_rqst["Hierarchy"] = hierarchy
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        data_num = self.post("Data/Static/Retrieve", data=data_rqst)
                else:
                    data_num = []

                # retrieve string data
                if signals_with_units_str:
                    if data_type == "time":
                        data_rqst = {
                            # "Requests": [
                            #    {
                            #        "Entity": "string",
                            #        "Signal": "string",
                            #        "Unit": "string"
                            #    }
                            #  ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_str,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            # "Hierarchy": "string",
                            "TimeIncrement": time_step,
                            "Start": time_start,
                            "End": time_end,
                            # "Options": {
                            #     "WithGaps": true,
                            #     "GapValue": "NaN",
                            #     "GapStringValue": ""
                            # }
                        }
                        if hierarchy:
                            data_rqst["Hierarchy"] = hierarchy
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        # if num_gap_value is not None:
                        #     data_rqst["Options"] = {"WithGaps": True, "GapStringValue": str_gap_value}
                        data_str = self.post("Data/StringTime/Retrieve", data=data_rqst)
                    elif data_type == "depth":
                        data_rqst = {
                            # "Requests": [
                            #     {
                            #         "Entity": "string",
                            #         "Signal": "string",
                            #         "Unit": "string"
                            #     }
                            # ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_str,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            "DepthIncrement": depth_step,
                            "StartDepth": depth_start,
                            "EndDepth": depth_end,
                            # "Options": {
                            #     "WithGaps": true,
                            #     "GapValue": "NaN",
                            #     "GapStringValue": ""
                            # },
                            # "DepthUnit": "string",
                        }
                        if depth_unit is not None:
                            data_rqst["DepthUnit"] = depth_unit
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        # if num_gap_value is not None:
                        #     data_rqst["Options"] = {"WithGaps": True, "GapStringValue": str_gap_value}
                        data_num = self.post(
                            "Data/StringDepth/Retrieve", data=data_rqst
                        )
                    else:
                        data_rqst = {
                            # "Requests": [
                            #    {
                            #        "Entity": "string",
                            #        "Signal": "string",
                            #        "Unit": "string"
                            #    }
                            #    ],
                            "Combinations": {
                                "Entities": entity_names,
                                "Signals": signals_with_units_str,
                            },
                            # "TopRecords": 0,
                            # "Scenario": "string",
                            # "Hierarchy": "string",
                        }
                        if hierarchy:
                            data_rqst["Hierarchy"] = hierarchy
                        if scenario:
                            data_rqst["Scenario"] = scenario
                        data_str = self.post("Data/String/Retrieve", data=data_rqst)
                else:
                    data_str = []

                # merge numeric and string data
                if data_num and data_str:
                    data = [*data_num, *data_str]
                elif data_num:
                    data = data_num
                elif data_str:
                    data = data_str
                else:
                    data = []

                if not data:
                    warnings.warn(
                        f"load_signals_data():: Couldn't retrieve any {data_type} data.",
                        RuntimeWarning,
                    )
                    continue

                if data_type == "time":
                    # create DataFrame by normalizing json
                    df_normalized = pd.json_normalize(
                        data, meta=["Entity", "Signal", "Unit"], record_path=["Data"]
                    )

                    # generate PivotTable
                    df = df_normalized.pivot(
                        index=["Entity", "Date"], columns="Signal", values="Value"
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df["Date"] = pd.to_datetime(df["Date"])
                    df_time = df
                elif data_type == "depth":
                    # create DataFrame by normalizing json
                    df_normalized = pd.json_normalize(
                        data, meta=["Entity", "Signal", "Unit"], record_path=["Data"]
                    )

                    # generate PivotTable
                    df = df_normalized.pivot(
                        index=["Entity", "Depth"], columns="Signal", values="Value"
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df_depth = df
                else:
                    # create DataFrame by normalizing json
                    df_normalized = pd.json_normalize(data)

                    # generate PivotTable
                    df = df_normalized.pivot(
                        index="Entity", columns="Signal", values="Data"
                    )
                    df.columns.name = None
                    df = df.rename(columns=signals_with_units_map)
                    df = df.reset_index()
                    df_static = df

        def reorder_columns(df, signals, signal_names):
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
        if df_static is not None:
            if df is not None:
                df = pd.merge(df, df_static, on="Entity")
            else:
                df = df_static
        if df is None:
            warnings.warn(
                f"load_signals_data():: Couldn't retrieve any data.",
                RuntimeWarning,
            )
            return df
        return reorder_columns(df, signals, signal_names)

    # load data
    def load_data(
        self,
        data_type: Union[str, SignalType],
        data: List,
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
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        step : str, TimeIncrement, DepthIncrement, None, default None
            Step of time/depth range
        hierarchy : str, None, default None
            Hierarchy name
        num_values : int, None, default None
            Number of values ot load
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
        data_type = self.get_signal_type_enum(data_type, **kwargs)
        route = self.get_signal_type_route(signal_type=data_type, **kwargs)
        # load 'Time' or 'Depth' data
        if data_type in {
            SignalType.TimeDependent,
            SignalType.StringTimeDependent,
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            # first/last values only
            if num_values is not None:
                # first values only
                if num_values > 0:
                    return self.post(
                        f"{route}/First",
                        data=data,
                        query={"NumberOfValues": num_values},
                        **kwargs,
                    )
                # last  values only
                elif num_values < 0:
                    return self.post(
                        f"{route}/Last",
                        data=data,
                        query={"NumberOfValues": abs(num_values)},
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
                    if not ApiHelper.has_field(range_step, "name"):
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
                    data_range = {
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
                    # load with filling gaps
                    if gap_value is not None:
                        gap_value = self.get_json_valid_value(
                            gap_value, data_type, **kwargs
                        )
                        return self.post(
                            f"{route}/Load/{gap_value}",
                            data=data,
                            query=data_range,
                            **kwargs,
                        )
                    # load data in specified range
                    if with_logs and ApiHelper.has_field(data, "Data"):
                        return self.post(
                            f"{route}/AquireWithLogs",
                            data=data,
                            query=data_range,
                            **kwargs,
                        )
                    elif ApiHelper.has_field(data, "Requests"):
                        return self.post(
                            f"{route}/Retrieve", data=data, query=data_range, **kwargs
                        )
                    return self.post(
                        f"{route}/Load", data=data, query=data_range, **kwargs
                    )
                elif start == end:
                    load_point = self.get_json_valid_value(start, data_type, **kwargs)
                    # get data at single point
                    if data_type == SignalType.TimeDependent:
                        return self.post(
                            f"{route}/Saved",
                            data=data,
                            query={"Date": load_point},
                            **kwargs,
                        )
                    elif data_type == SignalType.DepthDependent:
                        # load interpolated data
                        if interpolated and data_type == SignalType.DepthDependent:
                            return self.post(
                                f"{route}/Interpolated",
                                data=data,
                                query={"Depth": load_point},
                                **kwargs,
                            )
                        return self.post(
                            f"{route}/Saved",
                            data=data,
                            query={"Depth": load_point},
                            **kwargs,
                        )
            else:
                raise ValueError(
                    "PetroVisor::load_data(): "
                    "'start', 'end' and 'step' should be provided! "
                    "'step' can be avoided if 'start' == 'end'."
                )
        # load 'Static' and 'PVT' data
        if (
            with_logs
            and ApiHelper.has_field(data, "Data")
            and data_type == SignalType.Static
        ):
            return self.post(f"{route}/AquireWithLogs", data=data, **kwargs)
        elif ApiHelper.has_field(data, "Requests"):
            return self.post(f"{route}/Retrieve", data=data, **kwargs)
        if data_type == SignalType.PVT:
            return self.post(
                f"{route}/Load",
                data=data,
                query={
                    "PressureUnit": pressure_unit,
                    "TemperatureUnit": temperature_unit,
                },
                **kwargs,
            )
        return self.post(f"{route}/Load", data=data, **kwargs)

    # save data
    def save_data(
        self,
        data_type: Union[str, SignalType],
        data: List,
        with_logs: bool = False,
        pressure_unit: str = "Pa",
        temperature_unit: str = "K",
        **kwargs,
    ) -> Any:
        """
        Save data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        with_logs : bool, default False
            Load data and return logs
        pressure_unit : str, default 'Pa'
            Pressure unit (PVT data)
        temperature_unit : str, default 'K'
            Temperature unit (PVT data)
        """
        route = self.get_signal_type_route(signal_type=data_type, **kwargs)
        if data_type == SignalType.PVT:
            if with_logs:
                return self.post(
                    f"{route}/SaveWithLogs",
                    data=data,
                    query={
                        "PressureUnit": pressure_unit,
                        "TemperatureUnit": temperature_unit,
                    },
                    **kwargs,
                )
            return self.post(
                f"{route}/Save",
                data=data,
                query={
                    "PressureUnit": pressure_unit,
                    "TemperatureUnit": temperature_unit,
                },
                **kwargs,
            )
        if with_logs:
            return self.post(f"{route}/SaveWithLogs", data=data, **kwargs)
        return self.post(f"{route}/Save", data=data, **kwargs)

    # delete data
    def delete_data(
        self,
        data_type: Union[str, SignalType],
        data: List,
        start: Optional[Union[datetime, float]] = None,
        end: Optional[Union[datetime, float]] = None,
        **kwargs,
    ) -> Any:
        """
        Delete data

        Parameters
        ----------
        data_type : str, SignalType
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        data : list
            Data
        start : datetime, float, None, default None
            Start of time/depth range
        end : datetime, float, default None
            End of time/depth range
        """
        data_type = self.get_signal_type_enum(data_type, **kwargs)
        route = self.get_signal_type_route(signal_type=data_type, **kwargs)
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
            range_type = "time" if is_time_dependent else "numeric"
            data_range = {
                "Start": self.get_json_valid_value(start, range_type, **kwargs),
                "End": self.get_json_valid_value(end, range_type, **kwargs),
            }
            return self.post(f"{route}/Delete", data=data, query=data_range, **kwargs)
        return self.post(f"{route}/Delete", data=data, **kwargs)

    # get signal type route
    def get_signal_type_route(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str:
        """
        Get route of corresponding signal type

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, str):
            signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        elif not isinstance(signal_type, SignalType):
            raise ValueError(
                f"PetroVisor::get_data_type_route(): "
                f"unknown SignalType! "
                f"Should be either one of {[t.name for t in SignalType]} or {SignalType.__name__} enum."
            )
        if signal_type == SignalType.Static:
            return "Data/Static"
        elif signal_type == SignalType.DepthDependent:
            return "Data/Depth"
        elif signal_type == SignalType.TimeDependent:
            return "Data/Time"
        elif signal_type == SignalType.String:
            return "Data/String"
        elif signal_type == SignalType.StringTimeDependent:
            return "Data/StringTime"
        elif signal_type == SignalType.StringDepthDependent:
            return "Data/StringDepth"
        elif signal_type == SignalType.PVT:
            return "Data/PVT"
        raise ValueError(
            f"PetroVisor::get_signal_type_route(): "
            f"'{signal_type}' is not supported yet."
        )

    # get valid signal type name
    def get_signal_type_enum(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> SignalType:
        """
        Get SignalType enum

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, SignalType):
            return signal_type
        # prepare name for comparison
        signal_type = ApiHelper.get_comparison_string(signal_type, **kwargs)
        if signal_type in ("static", "staticnumeric"):
            return SignalType.Static
        elif signal_type in ("time", "timenumeric", "timedependent"):
            return SignalType.TimeDependent
        elif signal_type in ("depth", "depthnumeric", "depthdependent"):
            return SignalType.DepthDependent
        elif signal_type in ("string", "staticstring"):
            return SignalType.String
        elif signal_type in ("stringtime", "timestring", "stringtimedependent"):
            return SignalType.StringTimeDependent
        elif signal_type in ("stringdepth", "depthstring", "stringdepthdependent"):
            return SignalType.StringDepthDependent
        elif signal_type in ("pvt", "pvtnumeric"):
            return SignalType.PVT
        raise ValueError(
            f"PetroVisor::get_signal_type_name(): "
            f"unknown data type: '{signal_type}'! "
            f"Should be one of: {[t.name for t in SignalType]}"
        )

    # get time or depth increment name
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
            return self.get_time_increment_enum(increment, **kwargs)
        elif signal_type in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            return self.get_depth_increment_enum(increment, **kwargs)
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
        if isinstance(increment_type, TimeIncrement):
            return increment_type
        # prepare name for comparison
        increment_type = ApiHelper.get_comparison_string(increment_type, **kwargs)
        if increment_type in ("hourly", "h", "hr", "hour", "1h", "1hr", "1hour"):
            return TimeIncrement.Hourly
        elif increment_type in ("daily", "d", "day", "1d", "1day"):
            return TimeIncrement.Daily
        elif increment_type in ("monthly", "m", "month", "1m", "1month"):
            return TimeIncrement.Monthly
        elif increment_type in ("yearly", "y", "year", "1y", "1year"):
            return TimeIncrement.Yearly
        elif increment_type in ("quarterly", "q", "3m", "3month", "quarter"):
            return TimeIncrement.Quarterly
        elif increment_type in ("everyminute", "min", "minute", "1min", "1minute"):
            return TimeIncrement.EveryMinute
        elif increment_type in (
            "everysecond",
            "s",
            "sec",
            "second",
            "1s",
            "1sec",
            "1second",
        ):
            return TimeIncrement.EverySecond
        elif increment_type in ("everyfiveminute", "5min", "5minutes"):
            return TimeIncrement.EveryFiveMinutes
        elif increment_type in ("everyfifteenminutes", "15min", "15minutes"):
            return TimeIncrement.EveryFifteenMinutes
        raise ValueError(
            f"PetroVisor::get_time_increment_enum(): "
            f"unknown time increment: '{increment_type}'! "
            f"Should be one of: {[inc.name for inc in TimeIncrement]}"
        )

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
        if isinstance(increment_type, DepthIncrement):
            return increment_type
        # prepare name for comparison
        increment_type = ApiHelper.get_comparison_string(increment_type, **kwargs)
        if increment_type in ("meter", "m", "1meter", "1m"):
            return DepthIncrement.Meter
        elif increment_type in (
            "halfmeter",
            "halfm",
            ".5meter",
            ".5m",
            "0.5meter",
            "0.5m",
        ):
            return DepthIncrement.HalfMeter
        elif increment_type in ("tenthmeter", ".1meter", ".1m", "0.1meter", "0.1m"):
            return DepthIncrement.TenthMeter
        elif increment_type in (
            "eightmeter",
            ".125meter",
            ".125m",
            "0.125meter",
            "0.125m",
        ):
            return DepthIncrement.EighthMeter
        elif increment_type in ("foot", "ft", "1foot", "1ft"):
            return DepthIncrement.Foot
        elif increment_type in (
            "halffoot",
            "halfft",
            ".5foot",
            ".5feet",
            ".5ft",
            "0.5foot",
            "0.5feet",
            "0.5ft",
        ):
            return DepthIncrement.HalfFoot
        raise ValueError(
            f"PetroVisor::get_depth_increment_enum(): "
            f"unknown depth increment: '{increment_type}'! "
            f"Should be one of: {[inc.name for inc in DepthIncrement]}"
        )
