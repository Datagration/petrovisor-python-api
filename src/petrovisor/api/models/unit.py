from pydantic import (
    Field,
    field_validator,
)

from petrovisor.api.models.base_model import BaseConfigModel


class Unit(BaseConfigModel):
    name: str = Field(..., alias="Name")
    unit_measurement: str = Field(..., alias="MeasurementName")
    factor: float = Field(1, alias="Factor")
    summand: float = Field(0, alias="Summand")

    @field_validator("name")
    @classmethod
    def name_validator(cls, v: str) -> str:
        if not v:
            raise ValueError("Unit name cannot be empty.")
        return str(v)

    @field_validator("unit_measurement")
    @classmethod
    def unit_measurement_validator(cls, v: str) -> str:
        if not v:
            raise ValueError("Unit measurement name cannot be empty.")
        return v
