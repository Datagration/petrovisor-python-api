from typing import Union
from pydantic import (
    Field,
    field_validator,
)

import pandas as pd

from petrovisor.api.models.base_model import BaseConfigModel
from petrovisor.api.utils.validators import Validator


class Scope(BaseConfigModel):
    name: str = Field(..., alias="Name")
    time_start: Union[str, None] = Field(None, alias="Start")
    time_end: Union[str, None] = Field(None, alias="End")
    time_step: Union[str, None] = Field(None, alias="TimeIncrement")
    depth_start: Union[float, None] = Field(None, alias="StartDepth")
    depth_end: Union[float, None] = Field(None, alias="EndDepth")
    depth_step: Union[str, None] = Field(None, alias="DepthIncrement")

    @field_validator("time_start", "time_end")
    @classmethod
    def time_validator(cls, v: str) -> Union[str, None]:
        if not v:
            return None
        try:
            return pd.to_datetime(v).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            return None

    @field_validator("time_step")
    @classmethod
    def time_step_validator(cls, v: str) -> Union[str, None]:
        if not v:
            return None
        try:
            return str(Validator.get_time_increment_enum(v).name)
        except Exception:
            return None

    @field_validator("depth_step")
    @classmethod
    def depth_step_validator(cls, v: str) -> Union[str, None]:
        if not v:
            return None
        try:
            return str(Validator.get_depth_increment_enum(v).name)
        except Exception:
            return None

    def __str__(self):
        return self.name
