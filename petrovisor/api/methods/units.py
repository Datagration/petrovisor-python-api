from typing import (
    Any,
    Union,
    List,
    Dict,
    Optional,
)

import numpy as np
import pandas as pd

from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.models.unit import Unit
from petrovisor.api.protocols.protocols import SupportsRequests


# Units mixin helper
class UnitsMixinHelper:
    """
    Units mixin helper — endpoint constants.
    """

    ENDPOINT = "Units"
    ENDPOINT_ADD = "Units/Add"
    ENDPOINT_MEASUREMENTS = "UnitMeasurements"


# Units API calls
class UnitsMixin(SupportsRequests):
    # get unit
    def get_unit(self, name: str, **kwargs) -> Optional[Dict]:
        """
        Get unit by name

        Parameters
        ----------
        name : str
            Signal name
        """
        route = UnitsMixinHelper.ENDPOINT
        return self.get(f"{route}/{self.encode(name)}", **kwargs)

    # get measurement 'Units'
    def get_measurement_units(self, measurement: str, **kwargs) -> Any:
        """
        Get measurement units

        Parameters
        ----------
        measurement : str
            Measurement name
        """
        route = UnitsMixinHelper.ENDPOINT
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

    # get measurements
    def get_measurements(self, **kwargs) -> Any:
        """
        Get unit measurements
        """
        route = UnitsMixinHelper.ENDPOINT_MEASUREMENTS
        return self.get(f"{route}", **kwargs)

    # add unit
    def add_unit(self, unit: Union[Unit, Dict[str, Any]], **kwargs) -> Any:
        """
        Add unit

        Parameters
        ----------
        unit : Unit | dict
            Unit
        """
        route = UnitsMixinHelper.ENDPOINT
        if isinstance(unit, Unit):
            validated_unit = unit.model_dump(by_alias=True)
        elif isinstance(unit, dict):
            validated_unit = unit
        else:
            raise ValueError(
                "PetroVisor::add_unit(): "
                "Invalid type. Unit should be of type dict or Unit."
            )
        return self.post(f"{route}", data=validated_unit, **kwargs)

    # add units
    def add_units(self, units: List[Union[Unit, Dict[str, Any]]], **kwargs) -> Any:
        """
        Add multiple units

        Parameters
        ----------
        units : list[Unit | dict]
            List of units
        """
        validated_units = [
            e.model_dump(by_alias=True) if isinstance(e, Unit) else e
            for e in units
            if isinstance(e, dict) or isinstance(e, Unit)
        ]
        for validated_unit in validated_units:
            self.post(UnitsMixinHelper.ENDPOINT_ADD, data=validated_unit, **kwargs)
        return ApiRequests.success()

    # convert values from one unit to another
    def convert_units(
        self,
        values: Union[float, List[float], np.ndarray, pd.Series, None] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs,
    ) -> Union[float, List[float], np.ndarray, pd.Series, None]:
        """
        Convert values from one unit to another.
        Use '_' to get unit ' ' (dimensionless).
        Use '@' to get unit '%' (dimensionless).

        Parameters
        ----------
        values : float | List[float]
            Value(s)
        source: str
            Source unit
        target: str
            Target unit
        """
        route = UnitsMixinHelper.ENDPOINT
        if values is None or not source or not target or source == target:
            return values

        if not ApiHelper.is_iterable(values, exclude_str=True):
            return self.get(
                f"{route}/{self.encode(source)}/Convert/{self.encode(target)}/{values}",
                data=values,
                **kwargs,
            )

        values = ApiHelper.to_list(values)
        return self.post(
            f"{route}/{self.encode(source)}/Convert/{self.encode(target)}",
            data=values,
            **kwargs,
        )
