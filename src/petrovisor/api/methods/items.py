from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

from petrovisor.api.utils.helper import ApiHelper

from petrovisor.api.protocols.protocols import SupportsRequests


# Items API calls
class ItemsMixin(SupportsRequests):
    """
    Items API calls
    """

    # # 'NamedItem' routes
    # @property
    # def ItemRoutes(self):
    #     """
    #     Routes to items
    #     """
    #     return self.__item_routes
    #
    # # 'PetroVisorItem' routes
    # @property
    # def PetroVisorItemRoutes(self):
    #     """
    #     Routes to items with PetroVisor item info
    #     """
    #     return self.__petrovisor_item_routes
    #
    # # 'InfoItem' routes
    # @property
    # def InfoItemRoutes(self):
    #     """
    #     Routes to items with custom info
    #     """
    #     return self.__info_item_routes

    # def __init__(self, **kwargs):
    #     # 'NamedItem' routes
    #     self.__item_routes = ItemsMixinHelper.get_item_routes()
    #     # 'PetroVisorItem' routes
    #     self.__petrovisor_item_routes = ItemsMixinHelper.get_petrovisor_item_routes()
    #     # 'InfoItem' routes
    #     self.__info_item_routes = ItemsMixinHelper.get_info_item_routes()
    #
    #     super().__init__(**kwargs)

    # get item types
    def get_item_types(self, **kwargs):
        """
        Get all known item types

        Returns
        -------
        All know item types
        """
        return ItemsMixinHelper.get_item_types()

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
            raise NameError(f"PetroVisor::get_item(): unknown item type: '{item_type}'. "
                            f"Known item types: {list(self.ItemRoutes.keys())}")
        if route == 'Units' and name == ' ':
            name = '_'
        return self.get(f'{route}/{name}', **kwargs)

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
            raise NameError(f"PetroVisor::delete_item(): unknown item type: '{item_type}'. "
                            f"Known item types: {list(self.ItemRoutes.keys())}")
        name = self.get_item_name(item, **kwargs)
        return self.delete(f'{route}/{name}', **kwargs)

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
            raise NameError(f"PetroVisor::add_item(): unknown item type: '{item_type}'. "
                            f"Known item types: {list(self.ItemRoutes.keys())}")
        name = self.get_item_name(item, **kwargs)
        return self.put(f'{route}/{name}', data=item, **kwargs)

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
            raise NameError(f"PetroVisor::update_item_metadata(): unknown 'PetroVisor' item type: '{item_type}'. "
                            f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}")
        name = self.get_item_name(item, **kwargs)
        return self.put(f'{route}/{name}/Metadata', data=item, **kwargs)

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
            raise NameError(f"PetroVisor::get_items(): unknown item type: '{item_type}'. "
                            f"Known item types: {list(self.ItemRoutes.keys())}")
        return self.get(f'{route}/All', **kwargs)

    # get item paged
    def get_items_paged(self, item_type: str, page: int = 1, page_size: int = 10, **kwargs) -> List:
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
            raise NameError(f"PetroVisor::get_items_paged(): unknown 'PetroVisor' item type: '{item_type}'. "
                            f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}")
        return self.get(f'{route}/Paged', query={'Page': page, 'PageSize': page_size}, **kwargs)

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
            raise NameError(f"PetroVisor::get_item_names(): unknown item type: '{item_type}'. "
                            f"Known item types: {list(self.ItemRoutes.keys())}")
        return self.get(f'{route}', **kwargs)

    # get item labels
    def get_item_labels(self, item_type: str, **kwargs) -> List[str]:
        """
        Get item labels of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_petrovisor_item_route(item_type, **kwargs)
        if not route:
            raise NameError(f"PetroVisor::get_item_labels(): unknown 'PetroVisor' item type: '{item_type}'. "
                            f"Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}")
        return self.get(f'{route}/Labels', **kwargs)

    # get item infos
    def get_item_infos(self, item_type: str, **kwargs) -> List:
        """
        Get item infos of given type

        Parameters
        ----------
        item_type : str
            Item type
        """
        route = self.get_info_item_route(item_type, **kwargs)
        if not route:
            raise NameError(f"PetroVisor::get_item_infos(): unknown 'PetroVisor' item type: '{item_type}'. "
                            "Known 'PetroVisor' item types: {list(self.PetroVisorItemRoutes.keys())}")
        if self.is_info_item(item_type, **kwargs):
            return self.get(f'{route}/Info', **kwargs)
        return self.get(f'{route}/PetroVisorItems', **kwargs)

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
    def get_item_field(self, item_type: Optional[str], item: Union[str, Dict], field_name: str, **kwargs) -> Any:
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
            raise RuntimeError(f"PetroVisor::get_item_field(): Item '{item}' cannot be found!")
        elif not ApiHelper.has_field(item, field_name):
            raise RuntimeError(f"PetroVisor::get_item_field(): Item '{item}' doesn't not have '{field_name}' field!")
        return item[field_name]

    # get 'NamedItem' route
    def get_item_route(self, data_type: str, **kwargs) -> str:
        """
        Get route for corresponding NamedItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.get_dict_value(self.ItemRoutes, data_type, **kwargs)

    # get 'PetroVisorItems' route
    def get_petrovisor_item_route(self, data_type: str, **kwargs) -> str:
        """
        Get route for corresponding PetroVisorItem type

        Parameters
        ----------
        data_type : str
            Item type
        """
        return ApiHelper.get_dict_value(self.PetroVisorItemRoutes, data_type, **kwargs)

    # get 'InfoItems' route
    def get_info_item_route(self, data_type: str, **kwargs) -> str:
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
        return dict(**ItemsMixinHelper.get_named_item_routes(), **ItemsMixinHelper.get_petrovisor_item_routes())

    # get 'NamedItem' routes
    @staticmethod
    def get_named_item_routes() -> Dict:
        """
        Get routes of NamedItems
        """
        return {
            'Unit': 'Units',
            'UnitMeasurement': 'UnitMeasurements',
            'Entity': 'Entities',
            'EntityType': 'EntityTypes',
            'Signal': 'Signals',
            'ConfigurationSettingValue': 'ConfigurationSettings',
            'ConfigurationSettings': 'ConfigurationSettings',
            'Tag': 'Tags',
            'ProcessTemplate': 'ProcessTemplates',
            'MessageEntry': 'MessageEntries',
            'Ticket': 'Tickets',
            'UserSetting': 'UserSettings',
            'CustomWorkflowActivity': 'CustomWorkflowActivities',
            'WebWorkflowActivity': 'WebWorkflowActivities',
            'EventSubscription': 'EventSubscriptions',
            'WorkspacePackage': 'WorkspacePackages',
        }

    # get 'PetroVisorItem' routes
    @staticmethod
    def get_petrovisor_item_routes() -> Dict:
        """
        Get routes of PetroVisorItems
        """
        return dict(**{
            'Hierarchy': 'Hierarchies',
            'Scope': 'Scopes',
            'EntitySet': 'EntitySets',
            'Context': 'Contexts',
            'TableCalculation': 'TableCalculations',
            'EventCalculation': 'EventCalculations',
            'CleansingCalculation': 'CleansingCalculations',
            'Plot': 'Plots',
            'PSharpScript': 'PSharpScripts',
            'CleansingScript': 'CleansingScripts',
            'WorkflowSchedule': 'WorkflowSchedules',
            'RWorkflowActivity': 'RWorkflowActivities',
            'Workflow': 'Workflows',
            'FilterDefinition': 'Filters',
            'Filter': 'Filters',
            'DCA': 'DCA',
            'ChartDefinition': 'Charts',
            'Chart': 'Charts',
            'VoronoiGrid': 'VoronoiGrids',
            'GeoDataGrid': 'GeoDataGrids',
            'Polygon': 'Polygons',
            'PivotTableDefinition': 'PivotTables',
            'PivotTable': 'PivotTables',
            'DataIntegrationSet': 'DataIntegrationSets',
            'ReferenceTableDefinition': 'ReferenceTables',
            'ReferenceTable': 'ReferenceTables',
            'PowerBIItem': 'PowerBIItems',
        }, **ItemsMixinHelper.get_info_item_routes())

    # get 'PetroVisorItem' routes
    @staticmethod
    def get_info_item_routes() -> Dict:
        """
        Get routes of InfoItems
        """
        return {
            'MachineLearningModel': 'MLModels',
            'MLModel': 'MLModels',
            'DataGrid': 'DataGrids',
            'DataGridSet': 'DataGridSets',
            'DataConnection': 'DataConnections',
            'DataSource': 'DataSources',
            'Scenario': 'Scenarios',
            'DataIntegrationSession': 'DataIntegrationSessions',
        }
