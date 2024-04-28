from typing import (
    Any,
    Optional,
    Union,
    Tuple,
    List,
    Set,
    Dict,
)

try:
    from typing import Protocol
except BaseException:
    from typing_extensions import Protocol

import numpy as np
import pandas as pd
from datetime import datetime

from petrovisor.api.enums.internal_dtypes import SignalType
from petrovisor.api.enums.increments import (
    TimeIncrement,
    DepthIncrement,
)


# PetroVisor requests protocol
class SupportsRequests(Protocol):
    @property
    def Api(self) -> str: ...

    @property
    def Workspace(self) -> str: ...

    @property
    def Key(self) -> str: ...

    @property
    def Token(self) -> str: ...

    @property
    def RefreshToken(self) -> str: ...

    @property
    def TokenEndpoint(self) -> str: ...

    @property
    def DiscoveryUrl(self) -> str: ...

    @property
    def Route(self) -> str: ...

    # 'NamedItem' routes
    @property
    def ItemRoutes(self): ...

    # 'PetroVisorItem' routes
    @property
    def PetroVisorItemRoutes(self): ...

    # 'InfoItem' routes
    @property
    def InfoItemRoutes(self): ...

    # get method
    def get(self, rqst: str, **kwargs) -> Any: ...

    # post method
    def post(self, rqst: str, **kwargs) -> Any: ...

    # put method
    def put(self, rqst: str, **kwargs) -> Any: ...

    # delete method
    def delete(self, rqst: str, **kwargs) -> Any: ...

    # encode url component
    @staticmethod
    def encode(
        url_component: str, safe: Optional[Union[str, bytes]] = "~", **kwargs
    ) -> str: ...


# PetroVisor Items requests protocol
class SupportsItemRequests(Protocol):
    # get item types
    def get_item_types(self, **kwargs): ...

    # get item
    def get_item(self, item_type: str, name: str, **kwargs) -> Any: ...

    # delete item
    def delete_item(self, item_type: str, item: Union[str, Dict], **kwargs) -> Any: ...

    # add or edit item
    def add_item(self, item_type: str, item: Dict, **kwargs) -> Any: ...

    # update item metadata
    def update_item_metadata(self, item_type: str, item: Dict, **kwargs) -> Any: ...

    # get items
    def get_items(self, item_type: str, **kwargs) -> List: ...

    # get item names
    def get_item_names(self, item_type: str, **kwargs) -> List[str]: ...

    # get item paged
    def get_items_paged(
        self, item_type: str, page: int = 1, page_size: int = 10, **kwargs
    ) -> List: ...

    # get item labels
    def get_item_labels(self, item_type: str, **kwargs) -> List[str]: ...

    # get item infos
    def get_item_infos(self, item_type: str, **kwargs) -> List: ...

    # get item name
    def get_item_name(self, item: Union[str, Dict], **kwargs) -> str: ...

    # get item field
    def get_item_field(
        self,
        item_type: Optional[str],
        item: Union[str, Dict],
        field_name: str,
        **kwargs,
    ) -> Any: ...

    # get 'NamedItem' route
    def get_item_route(self, data_type: str, **kwargs) -> str: ...

    # get 'PetroVisorItems' route
    def get_petrovisor_item_route(self, data_type: str, **kwargs) -> str: ...

    # get 'InfoItems' route
    def get_info_item_route(self, data_type: str, **kwargs) -> str: ...

    # is 'NamedItem'
    def is_named_item(self, data_type: str, **kwargs) -> bool: ...

    # is 'PetroVisorItem'
    def is_petrovisor_item(self, data_type: str, **kwargs) -> bool: ...

    # is 'InfoItem'
    def is_info_item(self, data_type: str, **kwargs) -> bool: ...

    # items exists
    def item_exists(self, item_type: str, item: Union[str, Dict], **kwargs) -> bool: ...


# PetroVisor Entities requests protocol
class SupportsEntitiesRequests(Protocol):
    # get entity
    def get_entity(self, name: str, alias: Optional[str] = "", **kwargs) -> Dict: ...

    # get entities
    def get_entities(
        self, entity_type: Optional[str] = "", signal: Optional[str] = "", **kwargs
    ) -> List[Dict]: ...

    # get entity names
    def get_entity_names(
        self, entity_type: Optional[str] = "", signal: Optional[str] = "", **kwargs
    ) -> List[str]: ...

    # add entities
    def add_entities(self, entities: List, **kwargs) -> Any: ...

    # rename entity type
    def rename_entity_type(self, old_name: str, new_name: str, **kwargs) -> Any: ...

    # rename entity
    def rename_entity(self, old_name: str, new_name: str, **kwargs) -> Any: ...


# Signals requests protocol
class SupportsSignalsRequests(Protocol):

    # get 'Signal'
    def get_signal(
        self, name: str, short_name: Optional[str] = "", **kwargs
    ) -> Optional[Dict]: ...

    # get 'Signal' names
    def get_signal_names(
        self,
        signal_type: Optional[str] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[str]: ...

    # get valid signal type name
    def get_signal_type_enum(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> SignalType: ...

    # get signal type route
    def get_signal_type_route(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str: ...

    # get time increment name
    def get_time_increment_enum(
        self, increment_type: Union[str, TimeIncrement], **kwargs
    ) -> TimeIncrement: ...

    # get depth increment name
    def get_depth_increment_enum(
        self, increment_type: Union[str, DepthIncrement], **kwargs
    ) -> DepthIncrement: ...

    # get ordered time increments
    def get_time_increments_ordered(
        self, reverse: bool = False, **kwargs
    ) -> List[TimeIncrement]: ...

    # get smallest time increment
    def get_time_increments_min(
        self,
        increment_types: Union[
            List[Union[str, TimeIncrement]], Set[Union[str, TimeIncrement]]
        ],
        **kwargs,
    ) -> Optional[TimeIncrement]: ...

    # get largest time increment
    def get_time_increments_max(
        self,
        increment_types: Union[
            List[Union[str, TimeIncrement]], Set[Union[str, TimeIncrement]]
        ],
        **kwargs,
    ) -> Optional[TimeIncrement]: ...

    # get ordered depth increments
    def get_depth_increments_ordered(
        self, reverse: bool = False, **kwargs
    ) -> List[DepthIncrement]: ...

    # get smallest depth increment
    def get_depth_increments_min(
        self,
        increment_types: Union[
            List[Union[str, DepthIncrement]], Set[Union[str, DepthIncrement]]
        ],
        **kwargs,
    ) -> Optional[DepthIncrement]: ...

    # get largest depth increment
    def get_depth_increments_max(
        self,
        increment_types: Union[
            List[Union[str, DepthIncrement]], Set[Union[str, DepthIncrement]]
        ],
        **kwargs,
    ) -> Optional[DepthIncrement]: ...


# Units requests protocol
class SupportsUnitsRequests(Protocol):
    # get measurement 'Units'
    def get_measurement_units(self, measurement: str, **kwargs) -> Any: ...

    # get measurement 'Unit' names
    def get_measurement_unit_names(self, measurement: str, **kwargs) -> Any: ...

    # get measurements
    def get_measurements(self, **kwargs) -> Any: ...

    # convert values from one unit to another
    def convert_units(
        self,
        values: Union[float, List[float], np.ndarray, pd.Series, None] = None,
        source: str = None,
        target: str = None,
        **kwargs,
    ) -> Union[float, List[float], None]: ...


# PetroVisor Contex requests protocol
class SupportsContextRequests(Protocol):
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
    ) -> Optional[Dict]: ...

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
    ) -> Optional[Dict]: ...

    # get 'EntitySet'
    def get_entity_set(
        self,
        name: Union[str, Dict],
        entities: List[str] = None,
        entity_type: Union[str, List[str]] = None,
        **kwargs,
    ) -> Optional[Dict]: ...

    # get 'Hierarchy'
    def get_hierarchy(
        self, name: Union[str, Dict], relationship: Dict[str, str] = None, **kwargs
    ) -> Optional[Dict]: ...


# P# requests protocol
class SupportsPsharpRequests(Protocol):
    # get P# script
    def get_psharp_script(self, name: str, **kwargs) -> Dict: ...

    # parse P# script
    def parse_psharp_script(
        self, script: Union[str, Dict], options: Optional[Dict] = None, **kwargs
    ) -> Dict: ...

    # get P# script content
    def get_psharp_script_content(self, script: Union[str, Dict], **kwargs) -> str: ...

    # get P# script table names
    def get_psharp_script_table_names(
        self, script: Union[str, Dict], options: Optional[Dict] = None, **kwargs
    ) -> List[str]: ...

    # get P# script tables, columns and signals
    def get_psharp_script_columns_and_signals(
        self, script: Union[str, Dict], options: Optional[Dict] = None, **kwargs
    ) -> Dict: ...


# DataFrames handling protocol
class SupportsDataFrames(Protocol):
    # get valid json value
    def get_json_valid_value(
        self, value: Any, dtype: Union[str, SignalType] = "unknown", **kwargs
    ) -> Any: ...

    # convert PivotTable to DataFrame
    def convert_pivot_table_to_dataframe(
        self, data: List, groupby_entity: bool = False, **kwargs
    ): ...

    # Get signal data from DataFrame

    def get_signal_data_from_dataframe(
        self,
        df: pd.DataFrame,
        signals: Optional[Dict] = None,
        only_existing_entities: bool = True,
        entity_type: str = "",
        entities: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]: ...

    # convert P# table to DataFrame
    def convert_psharp_table_to_dataframe(
        self,
        psharp_table: Union[Dict, List],
        dropna: bool = True,
        with_entity_column: bool = True,
        groupby_entity: bool = False,
        **kwargs,
    ) -> Optional[Union[pd.DataFrame, Dict[str, pd.DataFrame]]]: ...

    # get column name without unit
    def get_column_name_without_unit(self, column_name: str, **kwargs) -> str: ...

    # get column unit
    def get_column_unit(self, column_name: str, **kwargs) -> str: ...

    # get column name and unit
    def get_column_name_and_unit(
        self, column_name: str, **kwargs
    ) -> Tuple[str, str]: ...

    # convert datetime to string
    def datetime_to_string(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%dT%H:%M:%S.%f",
        **kwargs,
    ) -> str: ...
