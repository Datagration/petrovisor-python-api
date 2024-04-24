from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

from datetime import datetime
import pandas as pd

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


# Context API calls
class ContextMixin(
    SupportsDataFrames, SupportsEntitiesRequests, SupportsItemRequests, SupportsRequests
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
        relationship: Dict[str, str | None] = None,
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
