from typing import Union
from pydantic import Field
from petrovisor.api.models.base_model import BaseConfigModel


class Entity(BaseConfigModel):
    name: str = Field(..., alias="Name")
    type: str = Field(..., alias="EntityTypeName")
    alias: Union[str, None] = Field(None, alias="Alias")
    is_opportunity: bool = Field(False, alias="IsOpportunity")

    def __str__(self):
        return self.name
