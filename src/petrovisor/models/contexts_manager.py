from typing import (
    Any,
    Union,
    List,
    Dict,
)

from petrovisor.api.enums.items import ItemType
from petrovisor.api.models.context import Context
from petrovisor.api.models.scope import Scope
from petrovisor.api.models.entity_set import EntitySet
from petrovisor.api.models.hierarchy import Hierarchy


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
