from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

import time
import warnings

from petrovisor.api.enums.items import ItemType
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.protocols.protocols import SupportsRequests


# Items mixin helper
class ItemsMixinHelper:
    # get item types
    @staticmethod
    def get_item_types() -> List:
        """
        Get all item types
        """
        return list(ItemsMixinHelper.get_item_routes().keys())

    # get item routes
    @staticmethod
    def get_item_routes() -> Dict:
        """
        Get all item routes
        """
        return dict(
            **ItemsMixinHelper.get_named_item_routes(),
            **ItemsMixinHelper.get_petrovisor_item_routes(),
        )

    # get 'NamedItem' routes
    @staticmethod
    def get_named_item_routes() -> Dict:
        """
        Get routes of NamedItems
        """
        return {
            ItemType.Unit: "Units",
            ItemType.UnitMeasurement: "UnitMeasurements",
            ItemType.Entity: "Entities",
            ItemType.EntityType: "EntityTypes",
            ItemType.Tag: "Tags",
            ItemType.Label: "Labels",
            ItemType.MessageEntry: "MessageEntries",
            ItemType.Ticket: "Tickets",
            ItemType.ProcessTemplate: "ProcessTemplates",
            ItemType.UserSetting: "UserSettings",
            ItemType.EventSubscription: "EventSubscriptions",
        }

    # get 'PetroVisorItem' routes
    @staticmethod
    def get_info_item_routes() -> Dict:
        """
        Get routes of InfoItems
        """
        return dict(
            **{
                ItemType.MLModel: "MLModels",
                ItemType.DataGrid: "DataGrids",
                ItemType.DataConnection: "DataConnections",
                ItemType.DataSourceMapping: "DataSourceMappings",
                ItemType.DataIntegrationSession: "DataIntegrationSessions",
                ItemType.Scenario: "Scenarios",
            },
            **{  # alias
                ItemType.MachineLearningModel: "MLModels",  # alias MLModel
            },
        )

    # get 'PetroVisorItem' routes
    @staticmethod
    def get_petrovisor_item_routes() -> Dict:
        """
        Get routes of PetroVisorItems
        """
        return dict(
            **{
                ItemType.Signal: "Signals",
                ItemType.ConfigurationSettings: "ConfigurationSettings",
                ItemType.RefTable: "RefTables",
                ItemType.PivotTable: "PivotTables",
                ItemType.Hierarchy: "Hierarchies",
                ItemType.Scope: "Scopes",
                ItemType.EntitySet: "EntitySets",
                ItemType.Context: "Contexts",
                ItemType.TableCalculation: "TableCalculations",
                ItemType.EventCalculation: "EventCalculations",
                ItemType.CleansingCalculation: "CleansingCalculations",
                ItemType.PSharpScript: "PSharpScripts",
                ItemType.CleansingScript: "CleansingScripts",
                ItemType.Plot: "Plots",
                ItemType.Chart: "Charts",
                ItemType.Filter: "Filters",
                ItemType.Workflow: "Workflows",
                ItemType.WorkflowSchedule: "WorkflowSchedules",
                ItemType.CustomWorkflowActivity: "CustomWorkflowActivities",
                ItemType.RWorkflowActivity: "RWorkflowActivities",
                ItemType.PythonWorkflowActivity: "PythonWorkflowActivities",
                ItemType.WebWorkflowActivity: "WebWorkflowActivities",
                ItemType.DataIntegrationSet: "DataIntegrationSets",
                ItemType.WorkspacePackage: "WorkspacePackages",
                ItemType.DCA: "DCA",
                ItemType.PowerBIItem: "PowerBIItems",
                ItemType.Dashboard: "Dashboards",
            },
            **{  # alias
                ItemType.ConfigurationSettingValue: "ConfigurationSettings",  # alias ConfigurationSettings
                ItemType.PivotTableDefinition: "PivotTables",  # alias PivotTable
                ItemType.ChartDefinition: "Charts",  # alias Chart
                ItemType.FilterDefinition: "Filters",  # alias Filter
            },
            **ItemsMixinHelper.get_info_item_routes(),
        )


# Items API calls
class ItemsMixin(SupportsRequests):
    """
    Items API calls
    """

    # get item types
    def get_item_types(self, **kwargs):
        """
        Get all known item types

        Returns
        -------
        All known item types
        """
        return ItemsMixinHelper.get_item_types()

    def item_exists(
        self,
        item_type: str,
        item: Union[str, Dict],
        after: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> bool:
        """Return whether an item of *item_type* named *item* exists.

        Uses the list endpoint as a fast pre-check, avoiding the ~10 s 404
        penalty the individual GET incurs on missing items.

        The ``after`` argument handles eventual consistency when the caller
        knows a mutation just occurred:

        ``after=None`` (default)
            Single list check, no retry.  Use for stable lookups.

        ``after="create"``
            Polls until the item appears in the individual GET (faster
            propagation path than the list after a creation).

        ``after="delete"``
            Polls until the item disappears from the list (avoids the slow
            404 path on the individual GET after a deletion).

        Parameters
        ----------
        item_type : str
            ``ItemType`` enum value (e.g. ``ItemType.Signal``).
        item : str or dict
            Item name or dict with a ``Name`` key.
        after : {"create", "delete", None}, default None
            Consistency hint — see above.
        max_retries : int, default 3
            Poll attempts before giving up.  Ignored when ``after=None``.
        retry_delay : float, default 1.0
            Seconds between polls.
        """
        item_name = self.get_item_name(item, **kwargs)

        if after == "create":
            # Individual GET converges fast (~0.5 s) once the item propagates.
            # 404 misses during polling are expected — suppress RuntimeWarnings.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                for attempt in range(max_retries):
                    if self.get_item(item_type, item_name, **kwargs) is not None:
                        return True
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            return False

        if after == "delete":
            for attempt in range(max_retries):
                names = self.get_item_names(item_type, **kwargs)
                if not names or item_name not in names:
                    return False
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            return True

        # after=None — single list check, no retries.
        names = self.get_item_names(item_type, **kwargs)
        return bool(names) and item_name in names

    def resolve_item(
        self,
        item_type: str,
        name: str,
        after: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> Optional[Any]:
        """Return the full item dict for *name* of *item_type*, or None if not found.

        Use this instead of ``item_exists`` when you need the item's data, not
        just a presence check.  Shares the same ``after`` polling strategies.

        ``after=None`` (default)
            Single list pre-check, then fetch.  Fast for stable lookups;
            avoids the ~10 s 404 on missing items.

        ``after="create"``
            Polls individual GET until the item is returned.  Converges
            faster than the list after a creation.

        ``after="delete"``
            Polls the list until the name is absent, then returns ``None``.

        Parameters
        ----------
        item_type : str
            ``ItemType`` enum value (e.g. ``ItemType.Signal``).
        name : str
            Item name to resolve.
        after : {"create", "delete", None}, default None
            Consistency hint — see above.
        max_retries : int, default 3
            Poll attempts before returning ``None``.  Ignored when ``after=None``.
        retry_delay : float, default 1.0
            Seconds between polls.
        """
        item_name = self.get_item_name(name, **kwargs)

        if after == "create":
            # Individual GET converges fast (~0.5 s) once the item propagates.
            # 404 misses during polling are expected — suppress RuntimeWarnings.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                for attempt in range(max_retries):
                    item = self.get_item(item_type, item_name, **kwargs)
                    if item is not None:
                        return item
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
            return None

        if after == "delete":
            for attempt in range(max_retries):
                names = self.get_item_names(item_type, **kwargs)
                if not names or item_name not in names:
                    return None
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            return None

        # after=None — single list pre-check, then fetch.
        names = self.get_item_names(item_type, **kwargs)
        if names and item_name in names:
            return self.get_item(item_type, item_name, **kwargs)
        return None

    # get item
    def get_item(self, item_type: str, name: str, **kwargs) -> Any:
        """
        Get item

        Parameters
        ----------
        item_type : str
            Item type
        name : str
            Item name
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_item(): "
                f"unknown item type: '{item_type}'. "
                f"Known item types: {list(self.ItemRoutes.keys())}"
            )
        if route == "Units" and name == " ":
            name = "_"
        return self.get(f"{route}/{self.encode(name)}", **kwargs)

    # delete item
    def delete_item(self, item_type: str, item: Union[str, Dict], **kwargs) -> Any:
        """
        Delete item

        Parameters
        ----------
        item_type : str
            Item type
        item : str, dict
            Item object or Item name
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::delete_item(): "
                f"unknown item type: '{item_type}'. "
                f"Known item types: {list(self.ItemRoutes.keys())}"
            )
        name = self.get_item_name(item, **kwargs)

        if not self.item_exists(item_type, name):
            return ApiRequests.success()

        self.delete(f"{route}/{self.encode(name)}", **kwargs)

        self.item_exists(
            item_type, name, after="delete", max_retries=3, retry_delay=0.5
        )
        return ApiRequests.success()

    # add or edit item
    def add_item(self, item_type: str, item: Dict, **kwargs) -> Any:
        """
        Add or edit item

        Parameters
        ----------
        item_type : str
            Item type
        item : dict
            Item object
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::add_item(): "
                f"unknown item type: '{item_type}'. "
                f"Known item types: {list(self.ItemRoutes.keys())}"
            )
        name = self.get_item_name(item, **kwargs)
        return self.put(f"{route}/{self.encode(name)}", data=item, **kwargs)

    # update item metadata
    def update_item_metadata(self, item_type: str, item: Dict, **kwargs) -> Any:
        """
        Update item metadata

        Parameters
        ----------
        item_type : str
            Item type
        item : dict
            Item object
        """
        route = self.get_petrovisor_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::update_item_metadata(): "
                f"unknown 'PetroVisor' item type: '{item_type}'. "
                f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}"
            )
        name = self.get_item_name(item, **kwargs)
        return self.put(f"{route}/{self.encode(name)}/Metadata", data=item, **kwargs)

    # get items
    def get_items(self, item_type: str, **kwargs) -> List:
        """
        Get items of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_items(): "
                f"unknown item type: '{item_type}'. "
                f"Known item types: {list(self.ItemRoutes.keys())}"
            )
        return self.get(f"{route}/All", **kwargs)

    # get item paged
    def get_items_paged(
        self, item_type: str, page: int = 1, page_size: int = 10, **kwargs
    ) -> List:
        """
        Get items of given type in paged format

        Parameters
        ----------
        item_type : str
            Item type
        page : int, default 1
            Page number
        page_size : int, default 10
            Page size
        """
        route = self.get_petrovisor_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_items_paged(): "
                f"unknown 'PetroVisor' item type: '{item_type}'. "
                f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}"
            )
        return self.get(
            f"{route}/Paged", query={"Page": page, "PageSize": page_size}, **kwargs
        )

    # get item names
    def get_item_names(self, item_type: str, **kwargs) -> List[str]:
        """
        Get item names of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_item_names(): "
                f"unknown item type: '{item_type}'. "
                f"Known item types: {list(self.ItemRoutes.keys())}"
            )
        return self.get(f"{route}", **kwargs)

    # get item labels
    def get_item_labels(
        self, item_type: str, name: Optional[str] = None, **kwargs
    ) -> List:
        """
        Get item labels of given type

        Parameters
        ----------
        item_type : str
            Item type
        name : str
            Item name
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_item_labels(): "
                f"unknown 'PetroVisor' item type: '{item_type}'. "
                f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}"
            )
        if self.is_petrovisor_item(item_type, **kwargs):
            if name:
                item = self.get_item(item_type, name, **kwargs)
                return item["Labels"]
            items = self.get(f"{route}/PetroVisorItems", **kwargs)
            return [{item["Name"]: item["Labels"]} for item in items]
        return []

    # get item infos
    def get_item_infos(
        self, item_type: str, name: Optional[str] = None, **kwargs
    ) -> Union[List, Dict, None]:
        """
        Get item infos of given type

        Parameters
        ----------
        item_type : str
            Item type
        name : str
            Item name
        """
        route = self.get_item_route(item_type, **kwargs)
        if not route:
            raise ValueError(
                f"PetroVisor::get_item_infos(): "
                f"unknown 'PetroVisor' item type: '{item_type}'. "
                f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}"
            )
        if self.is_info_item(item_type, **kwargs):
            if name:
                return self.get(f"{route}/{self.encode(name)}/Info", **kwargs)
            return self.get(f"{route}/Info", **kwargs)
        elif self.is_petrovisor_item(item_type, **kwargs):
            if name:
                return self.get(f"{route}/{self.encode(name)}/PetroVisorItem", **kwargs)
            return self.get(f"{route}/PetroVisorItems", **kwargs)
        return None if name else []

    # get item name
    def get_item_name(self, item: Union[str, Dict], **kwargs) -> str:
        """
        Get item name

        Parameters
        ----------
        item : dict
            Item object
        """
        return ApiHelper.get_object_name(item)

    # get item field
    def get_item_field(
        self,
        item_type: Optional[str],
        item: Union[str, Dict],
        field_name: str,
        **kwargs,
    ) -> Any:
        """
        Get item field value

        Parameters
        ----------
        item_type : str
            Item type
        item : str, dict
            Item object or Item name
        field_name : str
            Field name
        """
        if isinstance(item, str) and item_type:
            item_name = ApiHelper.get_object_name(item)
            item = self.get_item(item_type, item_name, **kwargs)
        if not item:
            raise ValueError(
                f"PetroVisor::get_item_field(): item '{item}' cannot be found!"
            )
        elif not ApiHelper.has_field(item, field_name):
            raise ValueError(
                f"PetroVisor::get_item_field(): "
                f"item '{item}' doesn't not have '{field_name}' field!"
            )
        elif not isinstance(item, dict):
            raise ValueError(
                f"PetroVisor::get_item_field(): "
                f"item '{item}' is not a dict-like object!"
            )
        return item[field_name]

    # get 'NamedItem' route
    def get_item_route(self, data_type: str, **kwargs) -> Optional[str]:
        """
        Get route for corresponding NamedItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.get_dict_value(self.ItemRoutes, data_type, **kwargs)

    # get 'PetroVisorItems' route
    def get_petrovisor_item_route(self, data_type: str, **kwargs) -> Optional[str]:
        """
        Get route for corresponding PetroVisorItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.get_dict_value(self.PetroVisorItemRoutes, data_type, **kwargs)

    # get 'InfoItems' route
    def get_info_item_route(self, data_type: str, **kwargs) -> Optional[str]:
        """
        Get route for corresponding InfoItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.get_dict_value(self.InfoItemRoutes, data_type, **kwargs)

    # is 'NamedItem'
    def is_named_item(self, data_type: str, **kwargs) -> bool:
        """
        Check whether provided item is NamedItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.contains(self.ItemRoutes, data_type, **kwargs)

    # is 'PetroVisorItem'
    def is_petrovisor_item(self, data_type: str, **kwargs) -> bool:
        """
        Check whether provided item is PetroVisorItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.contains(self.PetroVisorItemRoutes, data_type, **kwargs)

    # is 'InfoItem'
    def is_info_item(self, data_type: str, **kwargs) -> bool:
        """
        Check whether provided item is InfoItem

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.contains(self.InfoItemRoutes, data_type, **kwargs)
