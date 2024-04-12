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
)


# Signals API calls
class SignalsMixin(
    SupportsDataFrames, SupportsContextRequests, SupportsItemRequests, SupportsRequests
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
        signal_type: Optional[str] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[Dict]:
        """
        Get signals. Filter optionally by signal type and entity

        Parameters
        ----------
        signal_type : str
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
        signal_type: str,
        signal: Optional[str] = None,
        entity: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Upload object

        Parameters
        ----------
        signal_type : str
            Data type: 'static', 'time', 'depth', 'string', 'timestring', 'pvt'
        signal : str
            Object name
        entity : str, default None
            Entity name
        """
        route = self.get_signal_type_route(signal_type=signal_type, **kwargs)
        if signal and entity:
            signal_name = ApiHelper.get_object_name(signal)
            entity_name = ApiHelper.get_object_name(entity)
            return self.get(
                f"{route}/Range/{self.encode(signal_name)}/{self.encode(entity_name)}",
                **kwargs,
            )
        elif signal:
            signal_name = ApiHelper.get_object_name(signal)
            return self.get(f"{route}/Range/{signal_name}", **kwargs)
        return self.get(f"{route}/Range", **kwargs)

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
        relationship: Dict[str, str] = None,
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
        relationship: dict, default None
            Hierarchy relationship as dictionary in form of 'Child': 'Parent'
        entity_type : str | list[str], default None
            Entity type. Used when entity_set, entities or context is not provided.
            If None, then all entities will be considered.
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
            s["UnitName"] = ApiHelper.get_object_name(unit_name) or s["StorageUnitName"]
            return s

        signals = [get_signal_and_unit(s) for s in signal_names]
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
        signal_types = {s["SignalType"] for s in signals}

        # define signal types
        if signal_types.issubset({"Static", "String"}):
            num_signal_type = "Static"
            str_signal_type = "String"
            data_type = "static"
        elif signal_types.issubset({"TimeDependent", "StringTimeDependent"}):
            num_signal_type = "TimeDependent"
            str_signal_type = "StringTimeDependent"
            data_type = "time"
        elif signal_types.issubset({"DepthDependent", "StringDepthDependent"}):
            num_signal_type = "DepthDependent"
            str_signal_type = "StringDepthDependent"
            data_type = "depth"
        else:
            static_signals = [
                s["Name"] for s in signals if s["SignalType"] in {"Static", "String"}
            ]
            time_signals = [
                s["Name"]
                for s in signals
                if s["SignalType"] in {"TimeDependent", "StringTimeDependent"}
            ]
            depth_signals = [
                s["Name"]
                for s in signals
                if s["SignalType"] in {"DepthDependent", "StringDepthDependent"}
            ]
            df = None
            if time_signals:
                df = self.load_signals_data(
                    time_signals,
                    context=context,
                    entity_set=entity_set,
                    scope=scope,
                    hierarchy=hierarchy,
                    scenario=scenario,
                    relationship=relationship,
                    entity_type=entity_type,
                    entities=entities,
                    time_start=time_start,
                    time_end=time_end,
                    time_step=time_step,
                    depth_start=depth_start,
                    depth_end=depth_end,
                    depth_step=depth_step,
                    depth_unit=depth_unit,
                )
            if depth_signals:
                df_depth = self.load_signals_data(
                    depth_signals,
                    context=context,
                    entity_set=entity_set,
                    scope=scope,
                    hierarchy=hierarchy,
                    scenario=scenario,
                    relationship=relationship,
                    entity_type=entity_type,
                    entities=entities,
                    time_start=time_start,
                    time_end=time_end,
                    time_step=time_step,
                    depth_start=depth_start,
                    depth_end=depth_end,
                    depth_step=depth_step,
                    depth_unit=depth_unit,
                )
                if df is not None:
                    df = pd.merge(df, df_depth, on="Entity")
                    columns = df.columns.tolist()
                    columns.remove("Depth")
                    position = 2 if time_signals else 1
                    columns.insert(position, "Depth")
                    df = df[columns]
                else:
                    df = df_depth
            if static_signals:
                df_static = self.load_signals_data(
                    static_signals,
                    context=context,
                    entity_set=entity_set,
                    scope=scope,
                    hierarchy=hierarchy,
                    scenario=scenario,
                    relationship=relationship,
                    entity_type=entity_type,
                    entities=entities,
                    time_start=time_start,
                    time_end=time_end,
                    time_step=time_step,
                    depth_start=depth_start,
                    depth_end=depth_end,
                    depth_step=depth_step,
                    depth_unit=depth_unit,
                )
                if df is not None:
                    df = pd.merge(df, df_static, on="Entity")
                else:
                    df = df_static
            return df

        # collect signal names with unit names fro dat retrieval
        signals_with_units_num = [
            {"Signal": s["Name"], "Unit": s["UnitName"]}
            for s in signals
            if s["SignalType"] == num_signal_type
        ]
        signals_with_units_str = [
            {"Signal": s["Name"], "Unit": s["UnitName"]}
            for s in signals
            if s["SignalType"] == str_signal_type
        ]
        signals_with_units_map = {
            s["Name"]: f"{s['Name']} [{s['UnitName']}]" for s in signals
        }

        # get context
        context = (
            self.get_context(
                context,
                context=context,
                entity_set=entity_set,
                scope=scope,
                hierarchy=hierarchy,
                relationship=relationship,
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
        hierarchy = context.get("Hierarchy", None)

        # get entity set
        entities = entity_set.get("Entities", None) or []
        if not entities:
            raise ValueError(
                "load_signals_data():: "
                f"entity set is empty! Please provide non empty entity_set, or list of entities, or define entity_type."
            )
        entity_names = [ApiHelper.get_object_name(e) for e in entities]

        # get scope range
        if data_type in {"time", "depth"}:
            if data_type == "time":
                range_start = scope.get("Start", "")
                range_end = scope.get("End", "")
                range_step = scope.get("TimeIncrement", None)
                if range_step:
                    range_step = str(self.get_time_increment_enum(range_step).name)

                if not range_start or pd.isnull(range_start):
                    range_start = np.min(
                        [
                            pd.to_datetime(
                                (
                                    self.get_data_range(
                                        s["SignalType"], signal=s["Name"]
                                    )
                                    or {}
                                ).get("Start", "")
                            )
                            for s in signals
                        ]
                    )
                if not range_end or pd.isnull(range_end):
                    range_end = np.min(
                        [
                            pd.to_datetime(
                                (
                                    self.get_data_range(
                                        s["SignalType"], signal=s["Name"]
                                    )
                                    or {}
                                ).get("End", "")
                            )
                            for s in signals
                        ]
                    )

                # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
                range_start = self.datetime_to_string(pd.to_datetime(range_start))
                range_end = self.datetime_to_string(pd.to_datetime(range_end))

            else:  # elif data_type == 'depth':
                range_start = scope.get("StartDepth", None)
                range_end = scope.get("EndDepth", None)
                range_step = scope.get("DepthIncrement", None)
                if range_step:
                    range_step = str(self.get_depth_increment_enum(range_step).name)

                if range_start is None or pd.isnull(range_start):
                    range_start = np.min(
                        [
                            (
                                self.get_data_range(s["SignalType"], signal=s["Name"])
                                or {}
                            ).get("Start", 0)
                            for s in signals
                        ]
                    )
                if range_end is None or pd.isnull(range_end):
                    range_end = np.min(
                        [
                            (
                                self.get_data_range(s["SignalType"], signal=s["Name"])
                                or {}
                            ).get("End", 0)
                            for s in signals
                        ]
                    )

                # convert to float
                range_start = float(range_start)
                range_end = float(range_end)
        else:
            range_start = None
            range_end = None
            range_step = None

        # fill gaps (not really needed, but if there will be demand, can be uncommented)
        # def get_gap_values(gval: Union[float, str, Tuple[Union[float,str]], List[Union[float,str]]]):
        #     """
        #     gap_value : float, str, tuple[float | str], list[float | str], default None
        #     Whether to fill gaps with specified value.
        #     If tuple/list is provided numeric value will be used for numeric data gaps, str for string data.
        #     """
        #     num_gap_value = None
        #     str_gap_value = None
        #     if isinstance(gval, (float, int)):
        #         num_gap_value = "NaN" if pd.isnull(gval) else str(gval)
        #     elif isinstance(gval, str):
        #         str_gap_value = gval
        #     elif isinstance(gval, (list, tuple, set)):
        #         for gv in gval:
        #             if isinstance(gv, (float, int)):
        #                 num_gap_value = "NaN" if pd.isnull(gv) else str(gv)
        #                 break
        #         for gv in gval:
        #             if isinstance(gv, str):
        #                 str_gap_value = gv
        #                 break
        #     return num_gap_value, str_gap_value
        # gap_value = None
        # num_gap_value, str_gap_value = get_gap_values(gap_value)

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
                    # "TimeIncrement": "EverySecond",
                    "Start": range_start,
                    "End": range_end,
                    # "Options": {
                    #     "WithGaps": true,
                    #     "GapValue": "NaN",
                    #     "GapStringValue": ""
                    # }
                }
                if range_step is not None:
                    data_rqst["TimeIncrement"] = range_step
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
                    # "DepthIncrement": "TenthMeter",
                    "StartDepth": range_start,
                    "EndDepth": range_end,
                    # "Options": {
                    #     "WithGaps": true,
                    #     "GapValue": "NaN",
                    #     "GapStringValue": ""
                    # },
                    # "DepthUnit": depth_unit,
                }
                if range_step is not None:
                    data_rqst["DepthIncrement"] = range_step
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
                    # "TimeIncrement": "EverySecond",
                    "Start": range_start,
                    "End": range_end,
                    # "Options": {
                    #     "WithGaps": true,
                    #     "GapValue": "NaN",
                    #     "GapStringValue": ""
                    # }
                }
                if range_step is not None:
                    data_rqst["TimeIncrement"] = range_step
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
                    # "DepthIncrement": "TenthMeter",,
                    "StartDepth": range_start,
                    "EndDepth": range_end,
                    # "Options": {
                    #     "WithGaps": true,
                    #     "GapValue": "NaN",
                    #     "GapStringValue": ""
                    # },
                    # "DepthUnit": "string",
                }
                if range_step is not None:
                    data_rqst["DepthIncrement"] = range_step
                if depth_unit is not None:
                    data_rqst["DepthUnit"] = depth_unit
                if scenario:
                    data_rqst["Scenario"] = scenario
                # if num_gap_value is not None:
                #     data_rqst["Options"] = {"WithGaps": True, "GapStringValue": str_gap_value}
                data_num = self.post("Data/StringDepth/Retrieve", data=data_rqst)
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

        # merge numeric and data
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
                "load_signals_data():: Couldn't retrieve any data.", RuntimeWarning
            )
            return None

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
            return df
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
            return df
        else:
            # create DataFrame by normalizing json
            df_normalized = pd.json_normalize(data)

            # generate PivotTable
            df = df_normalized.pivot(index="Entity", columns="Signal", values="Data")
            df.columns.name = None
            df = df.rename(columns=signals_with_units_map)
            df = df.reset_index()
            return df

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
