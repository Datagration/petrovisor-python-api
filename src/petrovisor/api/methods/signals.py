from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

from datetime import datetime

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.dtypes.signals import SignalType
from petrovisor.api.dtypes.increments import (
    TimeIncrement,
    DepthIncrement,
)

from petrovisor.api.protocols.protocols import SupportsRequests
from petrovisor.api.protocols.protocols import SupportsItemRequests
from petrovisor.api.protocols.protocols import SupportsDataFrames
from petrovisor.api.protocols.protocols import SupportsSignalsRequests


# Signals API calls
class SignalsMixin(SupportsDataFrames, SupportsSignalsRequests, SupportsItemRequests, SupportsRequests):
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
        return self.get_item_field('Signal', signal, 'SignalType', **kwargs)

    # get signal 'MeasurementName'
    def get_signal_measurement_name(self, signal: Union[str, Dict], **kwargs) -> Any:
        """
        Get signal measurement name

        Parameters
        ----------
        signal : str, dict
            Signal object or Signal name
        """
        field_name = 'MeasurementName'
        if isinstance(signal, str):
            signal_name = ApiHelper.get_object_name(signal)
            signal = self.get_item('Signal', signal_name, **kwargs)
        if not signal:
            raise ValueError(f"PetroVisor::get_signal_measurement_name(): "
                             f"signal '{signal}' cannot be found!")
        elif not ApiHelper.has_field(signal, field_name):
            raise ValueError(f"PetroVisor::get_signal_measurement_name(): "
                             f"signal '{signal}' doesn't have '{field_name}' field!")
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
        return self.get_item_field('Signal', signal, 'StorageUnitName', **kwargs)

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
        route = self.get_item_route('Unit')
        return self.get(f'{route}/{measurement}/Units', **kwargs)

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
        return [unit['Name'] for unit in units]

    # get 'Signal'
    def get_signal(self, name: str, short_name: Optional[str] = '', **kwargs) -> Optional[Dict]:
        """
        Get signal by name or short name

        Parameters
        ----------
        name : str
            Signal name
        short_name : str
            Signal short name
        """
        route = self.get_item_route('Signal')
        if short_name:
            signal = self.get(f'{route}/{short_name}/Signal', **kwargs)
        else:
            signal = None
        if signal is None:
            return self.get(f'{route}/{name}', **kwargs)
        return None

    # get 'Signals'
    def get_signals(self,
                    signal_type: Optional[str] = '',
                    entity: Optional[Union[Any, str]] = None,
                    **kwargs) -> List[Dict]:
        """
        Get signals. Filter optionally by signal type and entity

        Parameters
        ----------
        signal_type : str
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = self.get_item_route('Signal')
        # get signals by signal type
        if signal_type:
            signal_type = self.get_signal_type_enum(signal_type, **kwargs).name
            signals = self.get(f'{route}/{signal_type}/Signals', **kwargs)
        # get all signals
        else:
            signals = self.get(f'{route}/All', **kwargs)
        # get signals by 'Entity' name
        if entity:
            signal_names = self.get_signal_names(signal_type=None, entity=entity, **kwargs)
            if signal_names:
                return [s for s in signals if(s['Name'] in signal_names)]
        return signals if(signals is not None) else []

    # get 'Signal' names
    def get_signal_names(self,
                         signal_type: Optional[str] = '',
                         entity: Optional[Union[Any, str]] = None,
                         **kwargs) -> List[str]:
        """
        Get signal names. Filter optionally by signal type and entity

        Parameters
        ----------
        signal_type : str
            Signal type
        entity : str
            Entity object or Entity name
        """
        route = self.get_item_route('Signal')
        # get signals by 'Entity' name
        if entity:
            entities_route = self.get_item_route('Entity')
            entity_name = ApiHelper.get_object_name(entity)
            signal_names = self.get(f'{entities_route}/{entity_name}/Signals', **kwargs)
            if signal_type and signal_names is not None:
                signal_type_names = self.get_signal_names(signal_type=signal_type, entity=None, **kwargs)
                if signal_type_names:
                    return [s for s in signal_names if(s in signal_type_names)]
        # get signals by 'Signal' type
        elif signal_type:
            signals = self.get_signals(signal_type=signal_type, entity=None, **kwargs)
            return [e['Name'] for e in signals]
        # get all signals
        else:
            signal_names = self.get(f'{route}', **kwargs)
        return signal_names if(signal_names is not None) else []

    # add 'Signals'
    def add_signals(self, signals: List, **kwargs) -> Any:
        """
        Add multiple signals

        Parameters
        ----------
        signals : list
            List of entities
        """
        route = self.get_item_route('Signal')
        return self.post(f'{route}/Add', data=signals, **kwargs)

    # delete 'Signals'
    def delete_signals(self, signals: List, **kwargs) -> Any:
        """
        Delete multiple signals

        Parameters
        ----------
        signals : list
            List of entities
        """
        route = self.get_item_route('Signal')
        for signal_name in signals:
            self.delete(f'{route}/{signal_name}', **kwargs)

    # get data range
    def get_data_range(self,
                       signal_type: str,
                       signal: Optional[str] = None,
                       entity: Optional[str] = None,
                       **kwargs) -> Any:
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
            return self.get(f'{route}/Range/{signal_name}/{entity_name}', **kwargs)
        elif signal:
            signal_name = ApiHelper.get_object_name(signal)
            return self.get(f'{route}/Range/{signal_name}', **kwargs)
        return self.get(f'{route}/Range', **kwargs)

    # cleanse data
    def cleanse_data(self,
                     data_type: Union[str, SignalType],
                     value: float, timestamp: Optional[Union[datetime, str]],
                     signal: Union[Dict, str],
                     unit: Union[Dict, str],
                     entity: Union[Dict, str],
                     cleansing_script: str,
                     **kwargs) -> Any:
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
            raise Warning("PetroVisor::cleanse_data(): "
                          "cleansing is only supported for 'Static' and 'TimeNumeric' data.")
        options = {
            'UseDefaultCleansingScripts': True,
            'CleansingScript': cleansing_script,
            'TreatCleansingScriptAsCleansingScriptName': True,
            'IsPreview': True
        }
        options = ApiHelper.update_dict(options, **kwargs)
        entity_name = ApiHelper.get_object_name(entity, **kwargs)
        signal_name = ApiHelper.get_object_name(signal, **kwargs)
        unit_name = ApiHelper.get_object_name(unit, **kwargs)
        data_with_options = {
            'Entity': entity_name,
            'Signal': signal_name,
            'Unit': unit_name,
            'Value': value,
            'Options': options
        }
        if data_type == SignalType.TimeDependent:
            data_with_options['Timestamp'] = self.get_json_valid_value(timestamp, 'time', **kwargs)
        return self.post(f'{route}/Cleanse', data=data_with_options, **kwargs)

    # load data
    def load_data(self,
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
                  pressure_unit: str = 'Pa',
                  temperature_unit: str = 'K',
                  **kwargs) -> Any:
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
        if data_type in (SignalType.TimeDependent, SignalType.StringTimeDependent, SignalType.DepthDependent):
            # first/last values only
            if num_values is not None:
                # first values only
                if num_values > 0:
                    return self.post(f'{route}/First', data=data, query={'NumberOfValues': num_values}, **kwargs)
                # last  values only
                elif num_values < 0:
                    return self.post(f'{route}/Last', data=data, query={'NumberOfValues': abs(num_values)}, **kwargs)
            # get data defined on range
            if start is not None and end is not None:
                if step is not None or (start == end and data_type == SignalType.StringTimeDependent):
                    if step is not None:
                        range_step = self.get_increment_enum(step, data_type)
                    else:
                        range_step = TimeIncrement.EverySecond
                    if not ApiHelper.has_field(range_step, 'name'):
                        raise ValueError(f"PetroVisor::load_data(): "
                                         f"invalid increment value: '{step}'")
                    range_step = str(range_step.name)
                    is_time_dependent = (data_type == SignalType.TimeDependent or
                                         data_type == SignalType.StringTimeDependent)
                    range_type = 'time' if is_time_dependent else 'numeric'
                    data_range = {
                        'Start': self.get_json_valid_value(start, range_type, **kwargs),
                        'End': self.get_json_valid_value(end, range_type, **kwargs),
                        'Increment': range_step}
                    if hierarchy is not None and hierarchy and \
                            (data_type == SignalType.TimeDependent or
                             data_type == SignalType.StringTimeDependent):
                        data_range['Hierarchy'] = hierarchy
                    # load with filling gaps
                    if gap_value is not None:
                        gap_value = self.get_json_valid_value(gap_value, data_type, **kwargs)
                        return self.post(f'{route}/Load/{gap_value}', data=data, query=data_range, **kwargs)
                    # load data in specified range
                    if with_logs and ApiHelper.has_field(data, 'Data'):
                        return self.post(f'{route}/AquireWithLogs', data=data, query=data_range, **kwargs)
                    elif ApiHelper.has_field(data, 'Requests'):
                        return self.post(f'{route}/Retrieve', data=data, query=data_range, **kwargs)
                    return self.post(f'{route}/Load', data=data, query=data_range, **kwargs)
                elif start == end:
                    load_point = self.get_json_valid_value(start, data_type, **kwargs)
                    # get data at single point
                    if data_type == SignalType.TimeDependent:
                        return self.post(f'{route}/Saved', data=data, query={'Date': load_point}, **kwargs)
                    elif data_type == SignalType.DepthDependent:
                        # load interpolated data
                        if interpolated and data_type == SignalType.DepthDependent:
                            return self.post(f'{route}/Interpolated', data=data, query={'Depth': load_point}, **kwargs)
                        return self.post(f'{route}/Saved', data=data, query={'Depth': load_point}, **kwargs)
            else:
                raise ValueError(f"PetroVisor::load_data(): "
                                 f"'start', 'end' and 'step' should be provided! "
                                 f"'step' can be avoided if 'start' == 'end'.")
        # load 'Static' and 'PVT' data
        if with_logs and ApiHelper.has_field(data, 'Data') and data_type == SignalType.Static:
            return self.post(f'{route}/AquireWithLogs', data=data, **kwargs)
        elif ApiHelper.has_field(data, 'Requests'):
            return self.post(f'{route}/Retrieve', data=data, **kwargs)
        if data_type == SignalType.PVT:
            return self.post(f'{route}/Load',
                             data=data,
                             query={
                                 'PressureUnit': pressure_unit,
                                 'TemperatureUnit': temperature_unit
                             }, **kwargs)
        return self.post(f'{route}/Load', data=data, **kwargs)

    # save data
    def save_data(self,
                  data_type: Union[str, SignalType],
                  data: List,
                  with_logs: bool = False,
                  pressure_unit: str = 'Pa',
                  temperature_unit: str = 'K',
                  **kwargs) -> Any:
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
                return self.post(f'{route}/SaveWithLogs',
                                 data=data,
                                 query={
                                     'PressureUnit': pressure_unit,
                                     'TemperatureUnit': temperature_unit
                                 }, **kwargs)
            return self.post(f'{route}/Save',
                             data=data,
                             query={
                                 'PressureUnit': pressure_unit,
                                 'TemperatureUnit': temperature_unit
                             }, **kwargs)
        if with_logs:
            return self.post(f'{route}/SaveWithLogs', data=data, **kwargs)
        return self.post(f'{route}/Save', data=data, **kwargs)

    # delete data
    def delete_data(self,
                    data_type: Union[str, SignalType],
                    data: List,
                    start: Optional[Union[datetime, float]] = None,
                    end: Optional[Union[datetime, float]] = None,
                    **kwargs) -> Any:
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
        if data_type in (SignalType.TimeDependent, SignalType.StringTimeDependent, SignalType.DepthDependent):
            is_time_dependent = (data_type == SignalType.TimeDependent or data_type == SignalType.StringTimeDependent)
            range_type = 'time' if is_time_dependent else 'numeric'
            data_range = {
                'Start': self.get_json_valid_value(start, range_type, **kwargs),
                'End': self.get_json_valid_value(end, range_type, **kwargs)
            }
            self.post(f'{route}/Delete', data=data, query=data_range, **kwargs)
        return self.post(f'{route}/Delete', data=data, **kwargs)

    # get signal type route
    def get_signal_type_route(self, signal_type: Union[str, SignalType], **kwargs) -> str:
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
            raise ValueError(f"PetroVisor::get_data_type_route(): "
                             f"unknown SignalType! "
                             f"Should be either one of {[t.name for t in SignalType]} or {SignalType.__name__} enum.")
        if signal_type == SignalType.Static:
            return 'Data/Static'
        elif signal_type == SignalType.DepthDependent:
            return 'Data/Depth'
        elif signal_type == SignalType.TimeDependent:
            return 'Data/Time'
        elif signal_type == SignalType.String:
            return 'Data/String'
        elif signal_type == SignalType.StringTimeDependent:
            return 'Data/StringTime'
        elif signal_type == SignalType.PVT:
            return 'Data/PVT'
        raise ValueError(f"PetroVisor::get_signal_type_route(): "
                         f"'{signal_type}' is not supported yet.")

    # get valid signal type name
    def get_signal_type_enum(self, signal_type: Union[str, SignalType], **kwargs) -> SignalType:
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
        if signal_type in ('static', 'staticnumeric'):
            return SignalType.Static
        elif signal_type in ('time', 'timenumeric', 'timedependent'):
            return SignalType.TimeDependent
        elif signal_type in ('depth', 'depthnumeric', 'depthdependent'):
            return SignalType.DepthDependent
        elif signal_type in ('string', 'staticstring'):
            return SignalType.String
        elif signal_type in ('stringtime', 'timestring', 'stringtimedependent'):
            return SignalType.StringTimeDependent
        elif signal_type in ('pvt', 'pvtnumeric'):
            return SignalType.PVT
        raise ValueError(f"PetroVisor::get_signal_type_name(): "
                         f"unknown data type: '{signal_type}'! "
                         f"Should be one of: {[t.name for t in SignalType]}")

    # get time or depth increment name
    def get_increment_enum(self,
                           increment: Union[str, TimeIncrement, DepthIncrement],
                           signal_type: Union[str, SignalType],
                           **kwargs) -> Optional[Union[TimeIncrement, DepthIncrement]]:
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
        if signal_type == SignalType.TimeDependent or signal_type == SignalType.StringTimeDependent:
            return self.get_time_increment_enum(increment, **kwargs)
        elif signal_type == SignalType.DepthDependent:
            return self.get_depth_increment_enum(increment, **kwargs)
        return None

    # get time increment name
    def get_time_increment_enum(self, increment_type: Union[str, TimeIncrement], **kwargs) -> TimeIncrement:
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
        if increment_type in ('hourly', 'h', 'hr', 'hour', '1h', '1hr', '1hour'):
            return TimeIncrement.Hourly
        elif increment_type in ('daily', 'd', 'day', '1d', '1day'):
            return TimeIncrement.Daily
        elif increment_type in ('monthly', 'm', 'month', '1m', '1month'):
            return TimeIncrement.Monthly
        elif increment_type in ('yearly', 'y', 'year', '1y', '1year'):
            return TimeIncrement.Yearly
        elif increment_type in ('quarterly', 'q', '3m', '3month', 'quarter'):
            return TimeIncrement.Quarterly
        elif increment_type in ('everyminute', 'min', 'minute', '1min', '1minute'):
            return TimeIncrement.EveryMinute
        elif increment_type in ('everysecond', 's', 'sec', 'second', '1s', '1sec', '1second'):
            return TimeIncrement.EverySecond
        elif increment_type in ('everyfiveminute', '5min', '5minutes'):
            return TimeIncrement.EveryFiveMinutes
        elif increment_type in ('everyfifteenminutes', '15min', '15minutes'):
            return TimeIncrement.EveryFifteenMinutes
        raise ValueError(f"PetroVisor::get_time_increment_enum(): "
                         f"unknown time increment: '{increment_type}'! "
                         f"Should be one of: {[inc.name for inc in TimeIncrement]}")

    # get depth increment name
    def get_depth_increment_enum(self, increment_type: Union[str, DepthIncrement], **kwargs) -> DepthIncrement:
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
        if increment_type in ('meter', 'm', '1meter', '1m'):
            return DepthIncrement.Meter
        elif increment_type in ('halfmeter', 'halfm', '.5meter', '.5m', '0.5meter', '0.5m'):
            return DepthIncrement.HalfMeter
        elif increment_type in ('tenthmeter', '.1meter', '.1m', '0.1meter', '0.1m'):
            return DepthIncrement.TenthMeter
        elif increment_type in ('eightmeter', '.125meter', '.125m', '0.125meter', '0.125m'):
            return DepthIncrement.EighthMeter
        elif increment_type in ('foot', 'ft', '1foot', '1ft'):
            return DepthIncrement.Foot
        elif increment_type in ('halffoot', 'halfft', '.5foot', '.5feet', '.5ft', '0.5foot', '0.5feet', '0.5ft'):
            return DepthIncrement.HalfFoot
        raise ValueError(f"PetroVisor::get_depth_increment_enum(): "
                         f"unknown depth increment: '{increment_type}'! "
                         f"Should be one of: {[inc.name for inc in DepthIncrement]}")
