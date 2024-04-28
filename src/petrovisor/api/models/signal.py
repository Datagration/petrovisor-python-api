from typing import Union
from pydantic import (
    Field,
    field_validator,
)

from petrovisor.api.enums.internal_dtypes import AggregationType, SignalType
from petrovisor.api.models.base_model import BaseConfigModel
from petrovisor.api.utils.validators import Validator


class Signal(BaseConfigModel):
    name: str = Field(..., alias="Name")
    short_name: str = Field("", alias="ShortName", validate_default=True)
    type: Union[str, None] = Field(SignalType.Static.name, alias="SignalType")
    unit: Union[str, None] = Field(" ", alias="StorageUnitName")
    unit_measurement: Union[str, None] = Field("Dimensionless", alias="MeasurementName")
    hierarchy_aggregation: Union[str, None] = Field(
        AggregationType.Sum.name, alias="AggregationType"
    )
    interval_aggregation: Union[str, None] = Field(
        AggregationType.Sum.name, alias="ContainerAggregationType"
    )

    @field_validator("type")
    @classmethod
    def signal_type_validator(cls, v: str) -> str:
        if not v:
            return str(SignalType.Static)
        return str(Validator.get_signal_type_enum(v).name)

    @field_validator("hierarchy_aggregation", "interval_aggregation")
    @classmethod
    def aggregation_validator(cls, v: str) -> Union[str, None]:
        if not v:
            return str(AggregationType.Sum.name)
        try:
            return str(Validator.get_aggregation_type_enum(v).name)
        except Exception:
            return str(AggregationType.Sum.name)

    @field_validator("name")
    @classmethod
    def name_validator(cls, v: str) -> str:
        if not v:
            raise ValueError("Signal name cannot be empty.")
        return str(v)

    @field_validator("short_name")
    @classmethod
    def short_name_validator(cls, v: str, values) -> str:
        if not v:
            v = values.data.get("name")
        return v[:29] if len(v) > 29 else v

    @field_validator("unit")
    @classmethod
    def unit_name_validator(cls, v: str) -> str:
        if not v:
            return " "
        return str(v)

    @field_validator("unit_measurement")
    @classmethod
    def unit_measurement_validator(cls, v: str) -> str:
        if not v:
            return "Dimensionless"
        return v

    def __str__(self):
        return self.name
