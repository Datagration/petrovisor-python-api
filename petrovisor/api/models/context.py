from typing import Union

from pydantic import Field

from petrovisor.api.models.base_model import BaseConfigModel
from petrovisor.api.models.scope import Scope
from petrovisor.api.models.entity_set import EntitySet
from petrovisor.api.models.hierarchy import Hierarchy


class Context(BaseConfigModel):
    name: str = Field(..., alias="Name")
    scope: Union[Scope, None] = Field(None, alias="Scope")
    entity_set: Union[EntitySet, None] = Field(None, alias="EntitySet")
    hierarchy: Union[Hierarchy, None] = Field(None, alias="Hierarchy")

    def __str__(self):
        return self.name
