from typing import (
    Union,
    List,
)
from pydantic import Field
from petrovisor.api.models.base_model import BaseConfigModel
from petrovisor.api.models.entity import Entity


class EntitySet(BaseConfigModel):
    name: str = Field(..., alias="Name")
    entities: Union[List[Entity], None] = Field(None, alias="Entities")

    def __str__(self):
        return self.name
