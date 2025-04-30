from typing import (
    Union,
    Dict,
)
from pydantic import Field
from petrovisor.api.models.base_model import BaseConfigModel


class Hierarchy(BaseConfigModel):
    name: str = Field(..., alias="Name")
    relationship: Union[Union[Dict[str, Union[str, None]], None]] = Field(
        None, alias="Relationship"
    )

    def __str__(self):
        return self.name
