from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
    Set,
)

from datetime import datetime
import pandas as pd
import numpy as np

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.dtypes.items import ItemType
from petrovisor.api.dtypes.increments import (
    TimeIncrement,
    DepthIncrement,
)
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsDataFrames,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
)
from petrovisor.models.contexts import (
    ContextsManager,
    Context,
    Scope,
    EntitySet,
    Hierarchy,
)


# Context API calls
class ContextMixin(
    SupportsDataFrames,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
    SupportsItemRequests,
    SupportsRequests,
):
    """
    Context API calls
    """

    # get 'Context'
    def get_context(
        self,
        name: Union[str, Dict],
        entity_set: Union[str, Dict] = None,
        scope: Union[str, Dict] = None,
        hierarchy: Union[str, Dict] = None,
        relationship: Dict[str, str] = None,
        entity_type: Union[str, List[str]] = None,
        entities: Union[Union[str, Dict], List[Union[str, Dict]]] = None,
        time_start: Union[str, datetime] = None,
        time_end: Union[str, datetime] = None,
        time_step: Union[str, TimeIncrement] = None,
        depth_start: float = None,
        depth_end: float = None,
        depth_step: Union[str, DepthIncrement] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Get Context by name or construct using given parameters

        Parameters
        ----------
        name : str | dict
            Context name
        entity_set : str, default None
            Entity set name
        scope : str, default None
            Scope name
        hierarchy : str, default None
            Hierarchy name
        relationship: dict, default None
            Hierarchy relationship as dictionary in form of 'Child': 'Parent'
        entity_type : str, default None
            Entity type. Used when entity_set, entities or context is not provided.
            If not None, will filter out entities defined in entity_set.
        entities : str | list[str], default None
            Entity or list of Entities
        time_start : datetime, str, default None
            Start of time range
        time_end : datetime, str, default None
            End of time range
        time_step : str, TimeIncrement, default None
            Step of time range, e.g. 'Daily', 'Hourly'
        depth_start : datetime, float, None, default None
            Start of depth range
        depth_end : datetime, float, default None
            End of depth range
        depth_step : str, DepthIncrement, default None
            Step of depth range, e.g. 'Meter', 'Foot'
        """
        route = "Contexts"

        def is_context(obj):
            if not isinstance(obj, dict):
                return False
            if "Name" in obj and "Scope" in obj and "EntitySet" in obj:
                return True
            return False

        default_context = {
            "Name": "",
            "Scope": None,
            "EntitySet": None,
            "Hierarchy": None,
            "Formula": "",
            "Labels": [],
        }

        if is_context(name):
            default_context.update(name)
            return name

        context_name = ApiHelper.get_object_name(name) or ""
        default_context.update({"Name": context_name})

        if context_name and self.item_exists("Context", context_name):
            context = (
                self.get(f"{route}/{self.encode(context_name)}", **kwargs)
                or default_context
            )
        else:
            context = default_context

        if (
            context.get("Scope", None) is None
            or scope is not None
            or time_start is not None
            or time_end is not None
            or time_step is not None
            or depth_start is not None
            or depth_end is not None
            or depth_step is not None
        ):
            context["Scope"] = self.get_scope(
                scope,
                time_start=time_start,
                time_end=time_end,
                time_step=time_step,
                depth_start=depth_start,
                depth_end=depth_end,
                depth_step=depth_step,
                **kwargs,
            )
        if (
            context.get("EntitySet", None) is None
            or entity_set is not None
            or entities is not None
            or entity_type is not None
        ):
            context["EntitySet"] = self.get_entity_set(
                entity_set, entities=entities, entity_type=entity_type, **kwargs
            )
        if (
            context.get("Hierarchy", None) is None
            or hierarchy is not None
            or relationship is not None
        ):
            context["Hierarchy"] = self.get_hierarchy(
                hierarchy, relationship=relationship, **kwargs
            )
            if context["Hierarchy"] is None or not context["Hierarchy"].get(
                "Relationship", None
            ):
                context.pop("Hierarchy")
        return context

    # get 'Scope'
    def get_scope(
        self,
        name: Union[str, Dict],
        time_start: Union[str, datetime] = None,
        time_end: Union[str, datetime] = None,
        time_step: Union[str, TimeIncrement] = None,
        depth_start: float = None,
        depth_end: float = None,
        depth_step: Union[str, DepthIncrement] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Get Scope by name or construct using given parameters

        Parameters
        ----------
        name : str | dict
            Scope name
        time_start : datetime, str, default None
            Start of time range
        time_end : datetime, str, default None
            End of time range
        time_step : str, TimeIncrement, default None
            Step of time range, e.g. 'Daily', 'Hourly'
        depth_start : datetime, float, None, default None
            Start of depth range
        depth_end : datetime, float, default None
            End of depth range
        depth_step : str, DepthIncrement, default None
            Step of depth range, e.g. 'Meter', 'Foot'
        """
        route = "Scopes"

        default_scope = {
            "Name": "",
            "Start": None,
            "End": None,
            "TimeIncrement": None,
            "StartDepth": None,
            "EndDepth": None,
            "DepthIncrement": None,
            "Formula": "",
            "Labels": [],
        }

        def is_scope(obj):
            if not isinstance(obj, dict):
                return False
            if "Name" in obj and (
                ("Start" in obj and "End" in obj and "TimeIncrement" in obj)
                or (
                    "StartDepth" in obj
                    and "EndDepth" in obj
                    and "DepthIncrement" in obj
                )
            ):
                return True
            return False

        if is_scope(name):
            scope = default_scope
            scope.update(name)
            return scope

        scope_name = ApiHelper.get_object_name(name) or ""
        default_scope.update({"Name": scope_name})

        if scope_name and self.item_exists("Scope", scope_name):
            scope = (
                self.get(f"{route}/{self.encode(scope_name)}", **kwargs)
                or default_scope
            )
        else:
            scope = default_scope

        if time_start is not None and not pd.isnull(time_start):
            # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
            scope["Start"] = self.datetime_to_string(pd.to_datetime(time_start))
        elif scope.get("Start", None) is None:
            scope["Start"] = None
        if time_end is not None and not pd.isnull(time_end):
            # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
            scope["End"] = self.datetime_to_string(pd.to_datetime(time_end))
        elif scope.get("End", None) is None:
            scope["End"] = None
        if time_step:
            scope["TimeIncrement"] = str(self.get_time_increment_enum(time_step).name)
        elif scope.get("TimeIncrement", None) is None:
            scope["TimeIncrement"] = None
        if depth_start is not None and not pd.isnull(depth_start):
            scope["StartDepth"] = float(depth_start)
        elif scope.get("StartDepth", None) is None:
            scope["StartDepth"] = None
        if depth_end is not None and not pd.isnull(depth_end):
            scope["EndDepth"] = float(depth_end)
        elif scope.get("EndDepth", None) is None:
            scope["EndDepth"] = None
        if depth_step:
            scope["DepthIncrement"] = str(
                self.get_depth_increment_enum(depth_step).name
            )
        elif scope.get("DepthIncrementh", None) is None:
            scope["DepthIncrement"] = None
        return scope

    # get 'EntitySet'
    def get_entity_set(
        self,
        name: Union[str, Dict],
        entities: List[str] = None,
        entity_type: Union[str, List[str]] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Get EntitySet by name or construct using given parameters

        Parameters
        ----------
        name : str | dict
            Scope name
        entities : list[str], default None
            Entity names or Entity objects
        entity_type : str | list[str], default None
            Entity type. Used when entity_set or entities is not provided.
            If not None, will filter out entities defined in entity_set.
        """
        route = "EntitySets"

        default_entity_set = {
            "Name": "",
            "Entities": None,
            "Formula": "",
            "Labels": [],
        }

        def is_entity_set(obj):
            if not isinstance(obj, dict):
                return False
            if "Name" in obj and "Entities" in obj:
                return True
            return False

        if is_entity_set(name):
            entity_set = default_entity_set
            entity_set.update(name)
            return entity_set

        entity_set_name = ApiHelper.get_object_name(name) or ""
        default_entity_set.update({"Name": entity_set_name})

        if entity_set_name and self.item_exists("EntitySet", entity_set_name):
            entity_set = (
                self.get(f"{route}/{self.encode(entity_set_name)}", **kwargs)
            ) or default_entity_set
        else:
            entity_set = default_entity_set

        if (
            entity_set.get("Entities", None) is None
            or entities is not None
            or entity_type is not None
        ):
            if entities is not None:
                if not isinstance(
                    entities,
                    (
                        list,
                        tuple,
                        set,
                    ),
                ):
                    eset_entities = [
                        self.get_entity(ApiHelper.get_object_name(entities))
                    ]
                else:
                    eset_entities = [
                        self.get_entity(ApiHelper.get_object_name(e)) for e in entities
                    ]
            else:
                eset_entities = []
            if entity_type is not None:
                if not isinstance(entity_type, (list, tuple, set)):
                    entity_type = [entity_type]
                if eset_entities:
                    entity_types = [et.casefold() for et in entity_type]
                    eset_entities = [
                        e
                        for e in eset_entities
                        if e["EntityTypeName"].casefold() in entity_types
                    ]
                else:
                    eset_entities = []
                    for et in entity_type:
                        eset_entities.extend(self.get_entities(entity_type=et))
            entity_set["Entities"] = eset_entities or []
        return entity_set

    # get 'Hierarchy'
    def get_hierarchy(
        self,
        name: Union[str, Dict],
        relationship: Dict[str, Union[str, None]] = None,
        **kwargs,
    ) -> Optional[Dict]:
        """
        Get Hierarchy by name or construct using given parameters

        Parameters
        ----------
        name : str | dict
            Hierarchy name
        relationship: dict, default None
            Hierarchy relationship as dictionary in form of 'Child': 'Parent'
        """
        route = "Hierarchies"

        default_hierarchy = {
            "Name": "",
            "Relationship": None,
            "Formula": "",
            "Labels": [],
        }

        def is_hierarchy(obj):
            if not isinstance(obj, dict):
                return False
            if "Name" in obj and "Relationship" in obj:
                return True
            return False

        if is_hierarchy(name):
            hierarchy = default_hierarchy
            hierarchy.update(name)
            return hierarchy

        hierarchy_name = ApiHelper.get_object_name(name) or ""
        default_hierarchy.update({"Name": hierarchy_name})

        if hierarchy_name and self.item_exists("Hierarchy", hierarchy_name):
            hierarchy = (
                self.get(f"{route}/{self.encode(hierarchy_name)}", **kwargs)
            ) or default_hierarchy
        else:
            hierarchy = default_hierarchy

        if hierarchy.get("Relationship", None) is None or relationship is not None:
            hierarchy["Relationship"] = relationship or {}
        return hierarchy

    # create Context
    def create_context(
        self,
        context: Context | dict[str, Any] | str | None,
        scope: Union[Scope, Dict[str, Any], str, None] = None,
        entity_set: Union[EntitySet, Dict[str, Any], str, None] = None,
        hierarchy: Union[Hierarchy, Dict[str, Any], str, None] = None,
        **kwargs,
    ) -> Union[Context, None]:
        """
        Create Context by given parameters

        Parameters
        ----------
        context : Context | dict | str | None
            Context object or name
        scope : Scope | dict | str | None, default None
            Scope object or name
        entity_set : EntitySet | dict | str | None, default None
            Entity Set object or name
        hierarchy : Hierarchy | dict | str | None, default None
            Hierarchy object or name
        """
        if not context and not scope and not entity_set and not hierarchy:
            return None
        if context and isinstance(context, Context):
            context_obj = context
        elif context and isinstance(context, dict):
            context_obj = Context.parse_obj(context)
        else:
            context_obj = Context(name=context or "Context")
        # overriding context
        if entity_set:
            context_obj.entity_set = self.create_entity_set(entity_set)
        if scope:
            context_obj.scope = self.create_scope(scope)
        if hierarchy:
            context_obj.hierarchy = self.create_hierarchy(hierarchy)
        return context_obj

    # create Scope
    def create_scope(
        self, scope: Union[Scope, Dict[str, Any], str, None], **kwargs
    ) -> Union[Scope, None]:
        """
        Create Scope by given parameters

        Parameters
        ----------
        scope : Scope | dict | str | None
            Scope object or name
        """
        if not scope:
            return None
        if isinstance(scope, Scope):
            return scope
        if isinstance(scope, dict):
            return Scope.parse_obj(scope)
        return Scope(name=scope)

    # create EntitySet
    def create_entity_set(
        self, entity_set: Union[EntitySet, Dict[str, Any], str, None], **kwargs
    ) -> Union[EntitySet, None]:
        """
        Create EntitySet by given parameters

        Parameters
        ----------
        entity_set : EntitySet | dict | str | None, default None
            Entity Set object or name
        """
        if not entity_set:
            return None
        if isinstance(entity_set, EntitySet):
            return entity_set
        if isinstance(entity_set, dict):
            return EntitySet.parse_obj(entity_set)
        return EntitySet(name=entity_set)

    # create Hierarchy
    def create_hierarchy(
        self, hierarchy: Union[Hierarchy, Dict[str, Any], str, None], **kwargs
    ) -> Union[Hierarchy, None]:
        """
        Create Hierarchy by given parameters

        Parameters
        ----------
        hierarchy : Hierarchy | dict | str | None, default None
            Hierarchy object or name
        """
        if not hierarchy:
            return None
        if isinstance(hierarchy, Hierarchy):
            return hierarchy
        if isinstance(hierarchy, dict):
            return Hierarchy.parse_obj(hierarchy)
        return Hierarchy(name=hierarchy)

    # merge Contexts
    def merge_contexts(
        self,
        *args: Union[List[Union[Context, Dict[str, Any], str, None]], None],
        **kwargs,
    ) -> Union[Context, None]:
        """
        Merge Contexts by given parameters

        Parameters
        ----------
        args: list[Context] | list[dict] | list[str] | None, default None
            Context objects or names
        """
        contexts = []
        for arg in args:
            if not arg:
                continue
            if isinstance(arg, list):
                contexts.extend(arg)
            else:
                contexts.append(arg)
        if not contexts:
            return None
        for i, context in enumerate(contexts):
            if isinstance(context, str) and self.item_exists(ItemType.Context, context):
                contexts[i] = self.create_context(self.get_context(context))

        # single context
        if len(contexts) == 1:
            return self.create_context(contexts[0])

        # merge all contexts
        context = Context(name="Merged Context")
        context.scope = self.merge_scopes(
            [getattr(ctx, "scope", None) for ctx in contexts]
        )
        context.entity_set = self.merge_entity_sets(
            [getattr(ctx, "entity_set", None) for ctx in contexts]
        )
        context.hierarchy = self.merge_hierarchies(
            [getattr(ctx, "hierarchy", None) for ctx in contexts]
        )
        return context

    # merge Scopes
    def merge_scopes(
        self,
        *args: Union[List[Union[Scope, Dict[str, Any], str, None]], None],
        **kwargs,
    ) -> Union[Scope, None]:
        """
        Merge Scopes by given parameters

        Parameters
        ----------
        *args: list[Scope] | list[dict] | list[str] | None, default None
            Scope objects or names
        """
        scopes = []
        for arg in args:
            if not arg:
                continue
            if isinstance(arg, list):
                scopes.extend(arg)
            else:
                scopes.append(arg)
        if not scopes:
            return None
        for i, scope in enumerate(scopes):
            if isinstance(scope, str) and self.item_exists(ItemType.Scope, scope):
                scopes[i] = self.create_scope(self.get_scope(scope))

        # single scope
        if len(scopes) == 1:
            return self.create_scope(scopes[0])

        # merge all scopes
        scope = Scope(name="Merged Scope")
        scope.time_start = None
        scope.time_end = None
        scope.time_step = None
        scope.depth_start = None
        scope.depth_end = None
        scope.depth_step = None

        try:
            time_starts: List[Any] = []
            for s in scopes:
                time_start = getattr(s, "time_start", "")
                if time_start and not pd.isnull(time_start):
                    time_starts.append(pd.to_datetime(time_start))
            if time_starts:
                time_start = np.min(time_starts)
                # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
                scope.time_start = self.datetime_to_string(pd.to_datetime(time_start))
        except Exception:
            pass

        try:
            time_ends: List[Any] = []
            for s in scopes:
                time_end = getattr(s, "time_end", "")
                if time_end and not pd.isnull(time_end):
                    time_ends.append(pd.to_datetime(time_end))
            if time_ends:
                time_end = np.max(time_ends)
                # convert to ISO time format '%Y-%m-%dT%H:%M:%S.%f'
                scope.time_end = self.datetime_to_string(pd.to_datetime(time_end))
        except Exception:
            pass

        try:
            time_steps: Set[TimeIncrement] = set()
            for s in scopes:
                time_step = getattr(s, "time_step", "")
                if time_step:
                    time_steps.add(self.get_time_increment_enum(time_step))
            if time_steps:
                time_step = self.get_time_increments_min(time_steps)
                if time_step is not None:
                    scope.time_step = str(time_step.name)
        except Exception:
            pass

        try:
            depth_starts: List[Any] = []
            for s in scopes:
                depth_start = getattr(s, "depth_start", None)
                if depth_start and not pd.isnull(depth_start):
                    depth_starts.append(depth_start)
            if depth_starts:
                depth_start = np.min([v for v in depth_starts if v is not None] or None)
                # convert to float
                if depth_start is not None:
                    scope.depth_start = float(depth_start)
        except Exception:
            pass

        try:
            depth_ends: List[Any] = []
            for s in scopes:
                depth_end = getattr(s, "depth_end", None)
                if depth_end and not pd.isnull(depth_end):
                    depth_ends.append(depth_end)
            if depth_ends:
                depth_end = np.max([v for v in depth_ends if v is not None] or None)
                # convert to float
                if depth_end is not None:
                    scope.depth_end = float(depth_end)
        except Exception:
            pass

        try:
            depth_steps: Set[DepthIncrement] = set()
            for s in scopes:
                depth_step = getattr(s, "depth_step", None)
                if depth_step:
                    depth_steps.add(self.get_depth_increment_enum(depth_step))
            if depth_steps:
                depth_step = self.get_depth_increments_min(depth_steps)
                if depth_step is not None:
                    scope.depth_step = str(depth_step.name)
        except Exception:
            pass

        return scope

    # merge EntitySets
    def merge_entity_sets(
        self,
        *args: Union[List[Union[EntitySet, Dict[str, Any], str, None]], None],
        **kwargs,
    ) -> Union[EntitySet, None]:
        """
        Merge EntitySets by given parameters

        Parameters
        ----------
        args: list[EntitySet] | list[dict] | list[str] | None, default None
            Entity Set objects or names
        """
        entity_sets = []
        for arg in args:
            if not arg:
                continue
            if isinstance(arg, list):
                entity_sets.extend(arg)
            else:
                entity_sets.append(arg)
        if not entity_sets:
            return None
        for i, entity_set in enumerate(entity_sets):
            if isinstance(entity_set, str) and self.item_exists(
                ItemType.EntitySet, entity_set
            ):
                entity_sets[i] = self.create_entity_set(self.get_entity_set(entity_set))

        # single entity set
        if len(entity_sets) == 1:
            return self.create_entity_set(entity_sets[0])

        # merge all entity sets
        entity_set = EntitySet(name="Merged EntitySet")
        entity_set.entities = []
        for eset in entity_sets:
            entities = getattr(eset, "entities", None)
            if entities and isinstance(entities, list):
                entity_set.entities.extend(entities)
        return entity_set

    # merge Hierarchies
    def merge_hierarchies(
        self,
        *args: Union[List[Union[Hierarchy, Dict[str, Any], str, None]], None],
        **kwargs,
    ) -> Union[Hierarchy, None]:
        """
        Merge Hierarchies by given parameters

        Parameters
        ----------
        args: list[Hierarchy] | list[dict] | list[str] | None, default None
            Hierarchy objects or names
        """
        hierarchies = []
        for arg in args:
            if not arg:
                continue
            if isinstance(arg, list):
                hierarchies.extend(arg)
            else:
                hierarchies.append(arg)
        if not hierarchies:
            return None
        for i, hierarchy in enumerate(hierarchies):
            if isinstance(hierarchy, str) and self.item_exists(
                ItemType.Hierarchy, hierarchy
            ):
                hierarchies[i] = self.create_hierarchy(self.get_hierarchy(hierarchy))

        # single hierarchy
        if len(hierarchies) == 1:
            return self.create_hierarchy(hierarchies[0])

        # merge all hierarchies
        hierarchy = Hierarchy(name="Merged Hierarchy")
        hierarchy.relationship = {}
        for h in hierarchies:
            relationship = getattr(h, "relationship", None)
            if relationship and isinstance(relationship, dict):
                hierarchy.relationship.update(relationship)
        return hierarchy

    # create contexts manager
    def create_contexts_manager(
        self,
        contexts: Union[List[Context], List[Dict[str, Any]], List[str]] = None,
        scope: Union[Scope, Dict[str, Any], str, None] = None,
        entity_set: Union[EntitySet, Dict[str, Any], str, None] = None,
        hierarchy: Union[Hierarchy, Dict[str, Any], str, None] = None,
        primary_context: str = "first",
        default_name: Union[str, None] = None,
        **kwargs,
    ) -> Union[ContextsManager, None]:
        """
        Create Context Manager which is a context itself and a list of contexts, i.e.
        when user uses it as a single object it returns attributes of primary context
        (either first context or merged contexts).

        Parameters
        ----------
        name : Union[str, None], default None
            Name of the context manager
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
        return ContextsManager(
            self,
            contexts=contexts,
            scope=scope,
            entity_set=entity_set,
            hierarchy=hierarchy,
            default_name=default_name,
            primary_context=primary_context,
            **kwargs,
        )
