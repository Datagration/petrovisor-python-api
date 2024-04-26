from typing import (
    Any,
    Union,
    List,
    Dict,
)

import pandas as pd

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
)
from petrovisor.api.utils.validators import Validator
from petrovisor.api.dtypes.items import ItemType


class BaseModelConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Scope(BaseModelConfig):
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


class Entity(BaseModelConfig):
    name: str = Field(..., alias="Name")
    entity_type_name: str = Field(..., alias="EntityTypeName")
    alias: Union[str, None] = Field(None, alias="Alias")
    is_opportunity: Union[bool, None] = Field(None, alias="IsOpportunity")

    def __str__(self):
        return self.name


class EntitySet(BaseModelConfig):
    name: str = Field(..., alias="Name")
    entities: Union[List[Entity], None] = Field(None, alias="Entities")

    def __str__(self):
        return self.name


class Hierarchy(BaseModelConfig):
    name: str = Field(..., alias="Name")
    relationship: Union[Union[Dict[str, Union[str, None]], None]] = Field(
        None, alias="Relationship"
    )

    def __str__(self):
        return self.name


class Context(BaseModelConfig):
    name: str = Field(..., alias="Name")
    scope: Union[Scope, None] = Field(None, alias="Scope")
    entity_set: Union[EntitySet, None] = Field(None, alias="EntitySet")
    hierarchy: Union[Hierarchy, None] = Field(None, alias="Hierarchy")

    def __str__(self):
        return self.name


class ContextsManager(list):
    api: Any
    name: Union[str, None]
    scope: Union[Scope, None]
    entity_set: Union[EntitySet, None]
    hierarchy: Union[Hierarchy, None]

    def __init__(
        self,
        api,
        contexts: Union[List[Context], List[Dict], List[str], None] = None,
        scope: Union[Scope, Dict[str, Any], str, None] = None,
        entity_set: Union[EntitySet, Dict[str, Any], str, None] = None,
        hierarchy: Union[Hierarchy, Dict[str, Any], str, None] = None,
        default_name: Union[str, None] = None,
        primary_context: str = "first",
        **kwargs,
    ):
        """
        Create Context Manager which is a context itself and a list of contexts, i.e.
        when user uses it as a single object it returns attributes of primary context
        (either first context or merged contexts).

        Parameters
        ----------
        api : PetroVisor
            PetroVisor API
        contexts: list[Context] | list[dict] | list[str] | None, default None
            Context objects or names
        scope : Scope | dict | str | None, default None
            Scope object or name
        entity_set : EntitySet | dict | str | None, default None
            Entity Set object or name
        hierarchy : Hierarchy | dict | str | None, default None
            Hierarchy object or name
        default_name : str, default None
            Default primary context name, in case if no contexts were provided
        primary_context : str, options {'first', 'merged'}, default 'first'
            'first' - first context will be used as a primary context
            'merged' - all contexts will be merged to be used as a primary context
        """
        self.api = api

        # get EntitySet
        if entity_set:
            if isinstance(entity_set, str) and api.item_exists(
                ItemType.EntitySet, entity_set
            ):
                entity_set = api.get_entity(entity_set)
            entity_set = api.create_entity_set(entity_set)

        # get Scope
        if scope:
            if isinstance(scope, str) and api.item_exists(ItemType.Scope, scope):
                scope = api.get_scope(scope)
            scope = api.create_scope(scope)

        # get Hierarchy
        if hierarchy:
            if isinstance(hierarchy, str) and api.item_exists(
                ItemType.Hierarchy, hierarchy
            ):
                hierarchy = api.get_hierarchy(hierarchy)
            hierarchy = api.create_hierarchy(hierarchy)

        # merge contexts
        if contexts:
            all_contexts = [
                api.create_context(
                    (
                        api.get_context(context)
                        if context
                        and isinstance(context, str)
                        and api.item_exists(ItemType.Context, context)
                        else context
                    ),
                    entity_set=entity_set,
                    scope=scope,
                    hierarchy=hierarchy,
                )
                for context in contexts
            ]
            all_contexts = [context for context in all_contexts if context]
        else:
            all_contexts = []

        # initialize list of contexts
        super().__init__(all_contexts)

        if len(all_contexts) == 0:
            context = Context(name=default_name or "")
        elif len(all_contexts) == 1 or primary_context.casefold() == "first":
            context = all_contexts[0]
        else:
            context = api.merge_contexts(all_contexts)
        self.name = context.name
        self.entity_set = context.entity_set
        self.scope = context.scope
        self.hierarchy = context.hierarchy
