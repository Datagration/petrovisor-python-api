from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    Union,
    Tuple,
    List,
    Set,
    Dict,
    TYPE_CHECKING,
)

from uuid import UUID

try:
    from typing import Protocol
except BaseException:
    from typing_extensions import Protocol

if TYPE_CHECKING:
    from petrovisor.api.models.context import Context
    from petrovisor.api.models.scope import Scope
    from petrovisor.api.models.entity_set import EntitySet
    from petrovisor.api.models.hierarchy import Hierarchy
    from petrovisor.api.models.entity import Entity
    from petrovisor.models.contexts_manager import ContextsManager

import io
import numpy as np
import pandas as pd
from datetime import datetime

from petrovisor.api.enums.internal_dtypes import SignalType
from petrovisor.api.enums.increments import (
    TimeIncrement,
    DepthIncrement,
)
from petrovisor.api.enums.ml import (
    MLModelType,
    MLNormalizationType,
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

    # resolve item (returns full dict, or None)
    def resolve_item(self, item_type: str, name: str, **kwargs) -> Optional[Any]: ...


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

    # add entity
    def add_entity(self, entity: Union[Any, Dict[str, Any]], **kwargs) -> Any: ...

    # add entities
    def add_entities(self, entities: Sequence, **kwargs) -> Any: ...

    # delete entity
    def delete_entity(
        self, entity: Union[Any, Dict[str, Any], str], **kwargs
    ) -> Any: ...

    # delete entities
    def delete_entities(
        self, entities: Sequence[Union[Any, Dict[str, Any], str]], **kwargs
    ) -> Any: ...

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

    # get 'Signal' objects
    def get_signals(
        self,
        signal_type: Union[str, SignalType] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[Dict]: ...

    # get 'Signal' names
    def get_signal_names(
        self,
        signal_type: Optional[Union[str, SignalType]] = "",
        entity: Optional[Union[Any, str]] = None,
        **kwargs,
    ) -> List[str]: ...

    # get signal type string
    def get_signal_type(self, signal: Union[str, Dict], **kwargs) -> str: ...

    # get signal measurement name
    def get_signal_measurement_name(
        self, signal: Union[str, Dict], **kwargs
    ) -> Any: ...

    # get signal storage unit
    def get_signal_unit(self, signal: Union[str, Dict], **kwargs) -> Any: ...

    # get all units of signal measurement
    def get_signal_units(self, signal: Union[str, Dict], **kwargs) -> Any: ...

    # get all unit names of signal measurement
    def get_signal_unit_names(self, signal: Union[str, Dict], **kwargs) -> Any: ...

    # add signal
    def add_signal(self, signal: Union[Any, Dict[str, Any]], **kwargs) -> Any: ...

    # add signals
    def add_signals(
        self, signals: Sequence[Union[Any, Dict[str, Any]]], **kwargs
    ) -> Any: ...

    # delete signal
    def delete_signal(
        self, signal: Union[Any, Dict[str, Any], str], **kwargs
    ) -> Any: ...

    # delete signals
    def delete_signals(
        self, signals: Sequence[Union[Any, Dict[str, Any], str]], **kwargs
    ) -> Any: ...

    # get data range
    def get_data_range(
        self,
        signal_type: Optional[str] = None,
        signal: Optional[str] = None,
        entity: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Any: ...

    # load signals data as DataFrame
    def load_signals_data(
        self,
        signals: Union[str, Sequence[Union[str, Dict, Tuple[Any, str]]]],
        **kwargs,
    ) -> Optional[pd.DataFrame]: ...

    # load data (raw API)
    def load_data(
        self,
        data: Union[List[Dict], pd.DataFrame, pd.Series],
        **kwargs,
    ) -> Any: ...

    # save data
    def save_data(
        self,
        data: Union[str, List[Dict], pd.DataFrame, pd.Series],
        **kwargs,
    ) -> Any: ...

    # delete data
    def delete_data(
        self,
        data: Union[List[Dict], pd.DataFrame, pd.Series],
        **kwargs,
    ) -> Any: ...

    # cleanse data
    def cleanse_data(
        self,
        value: float,
        timestamp: Optional[Union[datetime, str]],
        signal: Union[Dict, str],
        entity: Union[Dict, str],
        cleansing_script: str,
        unit: Optional[Union[Dict, str]] = None,
        **kwargs,
    ) -> Any: ...

    # get valid signal type name
    def get_signal_type_enum(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> SignalType: ...

    # get time or depth increment enum
    def get_increment_enum(
        self,
        increment: Union[str, TimeIncrement, DepthIncrement],
        signal_type: Union[str, SignalType],
        **kwargs,
    ) -> Optional[Union[TimeIncrement, DepthIncrement]]: ...

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
    # get unit by name
    def get_unit(self, name: str, **kwargs) -> Optional[Dict]: ...

    # get measurement 'Units'
    def get_measurement_units(self, measurement: str, **kwargs) -> Any: ...

    # get measurement 'Unit' names
    def get_measurement_unit_names(self, measurement: str, **kwargs) -> Any: ...

    # get measurements
    def get_measurements(self, **kwargs) -> Any: ...

    # add unit
    def add_unit(self, unit: Union[Any, Dict[str, Any]], **kwargs) -> Any: ...

    # add units
    def add_units(
        self, units: Sequence[Union[Any, Dict[str, Any]]], **kwargs
    ) -> Any: ...

    # convert values from one unit to another
    def convert_units(
        self,
        values: Union[float, List[float], np.ndarray, pd.Series, None] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs,
    ) -> Union[float, List[float], None]: ...


# PetroVisor Context requests protocol
class SupportsContextRequests(Protocol):
    # get 'Context'
    def get_context(
        self,
        name: Optional[Union[str, Dict, "Context"]],
        entity_set: Optional[Union[str, Dict, "EntitySet"]] = None,
        scope: Optional[Union[str, Dict, "Scope"]] = None,
        hierarchy: Optional[Union[str, Dict, "Hierarchy"]] = None,
        relationship: Optional[Dict[str, str]] = None,
        entity_type: Optional[Union[str, List[str]]] = None,
        entities: Optional[
            Union[str, Dict, "Entity", Sequence[Union[str, Dict, "Entity"]]]
        ] = None,
        time_start: Optional[Union[str, datetime]] = None,
        time_end: Optional[Union[str, datetime]] = None,
        time_step: Optional[Union[str, TimeIncrement]] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Union[str, DepthIncrement]] = None,
        **kwargs,
    ) -> Optional[Dict]: ...

    # get 'Scope'
    def get_scope(
        self,
        name: Optional[Union[str, Dict, "Scope"]],
        time_start: Optional[Union[str, datetime]] = None,
        time_end: Optional[Union[str, datetime]] = None,
        time_step: Optional[Union[str, TimeIncrement]] = None,
        depth_start: Optional[float] = None,
        depth_end: Optional[float] = None,
        depth_step: Optional[Union[str, DepthIncrement]] = None,
        **kwargs,
    ) -> Optional[Dict]: ...

    # get 'EntitySet'
    def get_entity_set(
        self,
        name: Optional[Union[str, Dict, "EntitySet"]],
        entities: Optional[Sequence[str]] = None,
        entity_type: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> Optional[Dict]: ...

    # get 'Hierarchy'
    def get_hierarchy(
        self,
        name: Optional[Union[str, Dict, "Hierarchy"]],
        relationship: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Optional[Dict]: ...

    # create Context
    def create_context(
        self,
        context: Optional[Union[str, Dict, "Context"]],
        scope: Optional[Union[str, Dict, "Scope"]] = None,
        entity_set: Optional[Union[str, Dict, "EntitySet"]] = None,
        hierarchy: Optional[Union[str, Dict, "Hierarchy"]] = None,
        **kwargs,
    ) -> Optional["Context"]: ...

    # create Scope
    def create_scope(
        self,
        scope: Optional[Union[str, Dict, "Scope"]],
        **kwargs,
    ) -> Optional["Scope"]: ...

    # create EntitySet
    def create_entity_set(
        self,
        entity_set: Optional[Union[str, Dict, "EntitySet"]],
        **kwargs,
    ) -> Optional["EntitySet"]: ...

    # create Hierarchy
    def create_hierarchy(
        self,
        hierarchy: Optional[Union[str, Dict, "Hierarchy"]],
        **kwargs,
    ) -> Optional["Hierarchy"]: ...

    # merge Contexts
    def merge_contexts(
        self,
        *args: Optional[List[Optional[Union[str, Dict, "Context"]]]],
        **kwargs,
    ) -> Optional["Context"]: ...

    # merge Scopes
    def merge_scopes(
        self,
        *args: Optional[List[Optional[Union[str, Dict, "Scope"]]]],
        **kwargs,
    ) -> Optional["Scope"]: ...

    # merge EntitySets
    def merge_entity_sets(
        self,
        *args: Optional[List[Optional[Union[str, Dict, "EntitySet"]]]],
        **kwargs,
    ) -> Optional["EntitySet"]: ...

    # merge Hierarchies
    def merge_hierarchies(
        self,
        *args: Optional[List[Optional[Union[str, Dict, "Hierarchy"]]]],
        **kwargs,
    ) -> Optional["Hierarchy"]: ...

    # create contexts manager
    def create_contexts_manager(
        self,
        contexts: Optional[List[Union[str, Dict, "Context"]]] = None,
        scope: Optional[Union[str, Dict, "Scope"]] = None,
        entity_set: Optional[Union[str, Dict, "EntitySet"]] = None,
        hierarchy: Optional[Union[str, Dict, "Hierarchy"]] = None,
        primary_context: str = "first",
        default_name: Optional[str] = None,
        **kwargs,
    ) -> Optional["ContextsManager"]: ...


# P# requests protocol
class SupportsPsharpRequests(Protocol):
    # get P# script names
    def get_psharp_script_names(self, **kwargs) -> List[str]: ...

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

    # load P# table as DataFrame
    def load_psharp_table(
        self,
        script_name: str,
        table: Optional[str] = None,
        dropna: bool = True,
        with_entity_column: bool = True,
        groupby_entity: bool = False,
        load_full_table_info: bool = False,
        **kwargs,
    ) -> Optional[Union[pd.DataFrame, Dict[str, Any]]]: ...

    # save DataFrame data to PetroVisor signals
    def save_table_data(
        self,
        df: pd.DataFrame,
        **kwargs,
    ) -> None: ...


# DataFrames handling protocol
class SupportsDataFrames(Protocol):
    # get valid json value
    def get_json_valid_value(
        self, value: Any, dtype: Union[str, SignalType] = "unknown", **kwargs
    ) -> Any: ...

    # convert dataframe to file-like object
    def convert_dataframe_to_file_object(
        self,
        df: pd.DataFrame,
        file_name: str,
        date_format: Optional[str] = None,
        **kwargs,
    ) -> io.BytesIO: ...

    # convert PivotTable to DataFrame
    def convert_pivot_table_to_dataframe(
        self,
        data: List,
        schema: Optional[List[str]] = None,
        groupby_entity: bool = False,
        **kwargs,
    ): ...

    # get signal data from DataFrame
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

    # convert dataframe from wide to long format
    def convert_dataframe_from_wide_to_long(
        self, df: pd.DataFrame, inplace: bool = False, **kwargs
    ): ...

    # convert dataframe from long to wide format
    def convert_dataframe_from_long_to_wide(
        self,
        df: pd.DataFrame,
        indices: Optional[Union[str, List[str]]] = None,
        inplace: bool = False,
        **kwargs,
    ) -> pd.DataFrame: ...

    # assign DataFrame column types
    def assign_dataframe_column_types(
        self,
        df: pd.DataFrame,
        columns_dtype: Dict,
        default_dtype: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame: ...

    # convert type name to DataFrame accepted type name
    def convert_to_dtype_name(self, dtype: str, **kwargs) -> str: ...

    # convert DataFrame column to specified type
    def column_to_dtype(
        self, df: pd.DataFrame, column: str, dtype: str, **kwargs
    ) -> pd.DataFrame: ...

    # convert DataFrame column to 'object'
    def column_to_object(
        self, df: pd.DataFrame, column: str, **kwargs
    ) -> pd.Series: ...

    # convert DataFrame column to 'bool'
    def column_to_bool(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series: ...

    # convert DataFrame column to 'string'
    def column_to_string(
        self, df: pd.DataFrame, column: str, **kwargs
    ) -> pd.Series: ...

    # convert DataFrame column to 'numeric'
    def column_to_numeric(
        self, df: pd.DataFrame, column: str, **kwargs
    ) -> pd.Series: ...

    # convert DataFrame column to 'datetime'
    def column_to_datetime(
        self, df: pd.DataFrame, column: Any, **kwargs
    ) -> pd.Series: ...

    # convert datetime to string
    def datetime_to_string(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%dT%H:%M:%S.%f",
        **kwargs,
    ) -> str: ...

    # convert string to datetime
    def string_to_datetime(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%d %H:%M:%S",
        **kwargs,
    ) -> datetime: ...

    # get column name without unit
    def get_column_name_without_unit(self, column_name: str, **kwargs) -> str: ...

    # get column unit
    def get_column_unit(self, column_name: str, **kwargs) -> str: ...

    # get column name and unit
    def get_column_name_and_unit(
        self, column_name: str, **kwargs
    ) -> Tuple[str, str]: ...

    # get 'Entity' column name
    def get_entity_column_name(self, **kwargs) -> str: ...

    # get 'Alias' column name
    def get_alias_column_name(self, **kwargs) -> str: ...

    # get 'EntityType' column name
    def get_entity_type_column_name(self, **kwargs) -> str: ...

    # get 'Opportunity' column name
    def get_opportunity_column_name(self, **kwargs) -> str: ...

    # get 'Date' column name
    def get_date_column_name(self, **kwargs) -> str: ...

    # get 'Time' column name
    def get_time_column_name(self, **kwargs) -> str: ...

    # get 'Depth' column name
    def get_depth_column_name(self, **kwargs) -> str: ...

    # get signal data type name
    def get_signal_data_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str: ...

    # get signal range type name
    def get_signal_range_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str: ...

    # convert list to dict
    def list_to_dict(self, x: Any, num_cols: int, **kwargs) -> Dict: ...


# Logs requests protocol
class SupportsLogsRequests(Protocol):
    # add log entry
    def add_log_entry(self, message: str, **kwargs) -> Any: ...

    # add workflow log entry
    def add_workflow_log_entry(self, message: str, workflow: str, **kwargs) -> Any: ...


# Files requests protocol
class SupportsFilesRequests(Protocol):
    # get file names
    def get_file_names(self, **kwargs) -> List[str]: ...

    # get file by name
    def get_file(self, filename: str, format: str = "bytes", **kwargs) -> Any: ...

    # delete file
    def delete_file(self, filename: str, **kwargs) -> Any: ...

    # upload file
    def upload_file(self, file: Any, name: str = "", **kwargs) -> Any: ...

    # upload folder
    def upload_folder(self, folder: str, name: str = "", **kwargs) -> Any: ...

    # delete folder
    def delete_folder(self, folder: str, **kwargs) -> Any: ...

    # load object from blob storage
    def get_object(
        self,
        name: str,
        func: Optional[Callable] = None,
        binary: bool = True,
        **kwargs,
    ) -> Any: ...

    # upload object to blob storage
    def upload_object(
        self,
        obj: Any,
        name: str,
        func: Optional[Callable] = None,
        binary: bool = True,
        **kwargs,
    ) -> Any: ...


# DataGrids requests protocol
class SupportsDataGridsRequests(Protocol):
    # import data grids
    def import_data_grids(
        self,
        file_filter: Optional[str] = "",
        file_extension: Optional[str] = "",
        default_crs: Optional[str] = "EPSG:3857",
        **kwargs,
    ) -> List[str]: ...

    # update DataGrid CRS
    def update_data_grid_crs(self, name: str, crs: str, **kwargs) -> Any: ...

    # project DataGrid to CRS
    def project_data_grid_to_crs(
        self, name: str, crs: str = "+proj=longlat +datum=WGS84 +no_defs", **kwargs
    ) -> Any: ...


# Pivot table requests protocol
class SupportsPivotTableRequests(Protocol):
    # get pivot table names
    def get_pivot_table_names(self, **kwargs) -> Any: ...

    # get pivot table data info
    def get_pivot_table_data_info(self, name: str, **kwargs) -> Any: ...

    # load pivot table data
    def load_pivot_table_data(
        self,
        name: str,
        entity_set: Optional[Union[str, Dict]] = None,
        scope: Optional[Union[str, Dict]] = None,
        num_rows: Optional[int] = 0,
        generate: bool = False,
        groupby_entity: bool = False,
        **kwargs,
    ) -> Any: ...

    # save pivot table data
    def save_pivot_table_data(
        self,
        name: str,
        entity_set: Optional[str] = None,
        scope: Optional[str] = None,
        **kwargs,
    ) -> Any: ...

    # delete pivot table data
    def delete_pivot_table_data(self, name: str, **kwargs) -> Any: ...

    # delete pivot table
    def delete_pivot_table(self, name: str, **kwargs) -> Any: ...


# Reference table requests protocol
class SupportsRefTableRequests(Protocol):
    # get reference table names
    def get_ref_table_names(self, **kwargs) -> Any: ...

    # get reference table data info
    def get_ref_table_data_info(self, name: str, **kwargs) -> Any: ...

    # add reference table
    def add_ref_table(
        self,
        name: str,
        df: Union[pd.DataFrame, Dict],
        description: Optional[str] = None,
        key_col: Optional[str] = "Key",
        date_col: Optional[str] = None,
        entity_col: Optional[str] = "Entity",
        skip_existing_data: bool = False,
        chunksize: Optional[int] = None,
        **kwargs,
    ) -> Any: ...

    # load reference table data
    def load_ref_table_data(
        self,
        name: str,
        entities: Optional[Union[str, Dict, List[str], List[Dict]]] = None,
        date_start: Optional[Union[datetime, str]] = None,
        date_end: Optional[Union[datetime, str]] = None,
        columns: Optional[Union[str, List[str]]] = None,
        top: Optional[int] = None,
        all_cols: Optional[bool] = False,
        where: Optional[str] = None,
        options: Optional[Dict] = None,
        date_col: Optional[str] = "Timestamp",
        entity_col: Optional[str] = "Entity",
        **kwargs,
    ) -> pd.DataFrame: ...

    # save reference table data
    def save_ref_table_data(
        self,
        name: str,
        df: pd.DataFrame,
        skip_existing_data: Optional[bool] = False,
        chunksize: Optional[int] = None,
        date_col: Optional[str] = "Timestamp",
        entity_col: Optional[str] = "Entity",
        **kwargs,
    ) -> Any: ...

    # delete reference table data
    def delete_ref_table_data(
        self,
        name: str,
        entities: Optional[Union[str, List[str]]] = None,
        date_start: Optional[Union[datetime, float]] = None,
        date_end: Optional[Union[datetime, float]] = None,
        drop_null_dates: Optional[bool] = False,
        keys: Optional[Union[str, List[str]]] = None,
        where: Optional[str] = None,
        options: Optional[Dict] = None,
        **kwargs,
    ) -> Any: ...

    # delete reference table
    def delete_ref_table(self, name: str, **kwargs) -> Any: ...


# Workspace values requests protocol
class SupportsWorkspaceValuesRequests(Protocol):
    # get workspace value names
    def get_workspace_value_names(self, **kwargs) -> List[str]: ...

    # get workspace values
    def get_workspace_values(
        self, value_type: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]: ...

    # get workspace value
    def get_workspace_value(self, name: str, **kwargs) -> Tuple[Any, str]: ...

    # add or edit workspace value
    def add_workspace_value(
        self,
        name: str,
        value: Union[str, List[Any], Dict[str, Any], Tuple, float, int],
        unit: Union[Dict, str] = "",
        description: Optional[str] = "",
        **kwargs,
    ) -> Any: ...

    # rename workspace value
    def rename_workspace_value(
        self, old_name: str, new_name: str, **kwargs
    ) -> Dict: ...

    # delete workspace value
    def delete_workspace_value(self, name: str, **kwargs) -> Dict: ...


# Workflows requests protocol
class SupportsWorkflowsRequests(Protocol):
    # run workflow
    def run_workflow(
        self,
        workflow: str,
        contexts: Optional[List[str]] = None,
        scope: Optional[str] = None,
        entity_set: Optional[str] = None,
        schedule_name: str = "Now",
        source: str = "by Activity service",
        **kwargs,
    ) -> Any: ...

    # get workflow execution state
    def get_workflow_execution_state(self, uid: UUID, **kwargs) -> Any: ...


# ML requests protocol
class SupportsMLRequests(Protocol):
    # get ML models
    def ml_models(self, **kwargs) -> Any: ...

    # get ML model names
    def ml_model_names(self, **kwargs) -> Any: ...

    # get ML model
    def ml_model(self, model_name: str, **kwargs) -> Any: ...

    # get ML model attribute
    def ml_model_attribute(self, model_name: str, attribute: str, **kwargs) -> Any: ...

    # get ML model type
    def ml_model_type(self, model_name: str, **kwargs) -> Any: ...

    # get ML model features and label
    def ml_model_features_and_label(self, model_name: str, **kwargs) -> Any: ...

    # get ML model features
    def ml_model_features(self, model_name: str, **kwargs) -> Any: ...

    # get ML model feature names
    def ml_model_feature_names(self, model_name: str, **kwargs) -> Any: ...

    # get ML model label
    def ml_model_label(self, model_name: str, **kwargs) -> Any: ...

    # get ML model label name
    def ml_model_label_name(self, model_name: str, **kwargs) -> Any: ...

    # get ML trainers and metrics
    def ml_trainers_and_metrics(
        self, model_type: Union[str, MLModelType], **kwargs
    ) -> Any: ...

    # get ML trainers
    def ml_trainers(self, model_type: Union[str, MLModelType], **kwargs) -> Any: ...

    # get ML metrics
    def ml_metrics(self, model_type: Union[str, MLModelType], **kwargs) -> Any: ...

    # get ML pre-training statistics
    def ml_pre_training_statistics(
        self, model_name: str, skip_pre_processing: bool = True, **kwargs
    ) -> Any: ...

    # get ML post-training statistics
    def ml_post_training_statistics(
        self, model_name: str, entity: Optional[Union[str, Dict]] = None, **kwargs
    ) -> Any: ...

    # predict using ML model
    def ml_predict(
        self, model_name: str, entity: Union[str, Dict], data: Dict, **kwargs
    ) -> Any: ...

    # train ML model
    def ml_train(
        self,
        model_name: str,
        time_to_train: int = 5,
        complete_case_only: bool = True,
        per_entity: bool = False,
        normalization: str = "Auto",
        trainers: Optional[Union[str, List[str]]] = None,
        optimization_metric: str = "",
        validation_fraction: float = 0.1,
        cross_folds: int = 0,
        clusters: int = 0,
        test_fraction: float = 0.0,
        test_latin_hypercube: bool = True,
        entity_set: Optional[Union[str, Dict]] = None,
        scope: Optional[Union[str, Dict]] = None,
        as_request: bool = False,
        request_source: Optional[str] = "manually by user",
        activity: Optional[str] = None,
        **kwargs,
    ) -> Any: ...

    # check whether ML service is idle
    def ml_is_service_idle(self, **kwargs) -> Any: ...

    # get ML model training states
    def ml_get_model_training_states(
        self, exclude_processed: bool = False, **kwargs
    ) -> Any: ...

    # get ML model training id
    def ml_get_model_training_id(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any: ...

    # get ML model training state
    def ml_get_model_training_state(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any: ...

    # get ML model training results
    def ml_get_model_training_results(
        self, model_name_or_id: Union[str, UUID], **kwargs
    ) -> Any: ...

    # get ML model type enum
    def get_ml_model_type_enum(
        self, type: Union[str, MLModelType], **kwargs
    ) -> MLModelType: ...

    # get ML normalization type enum
    def get_ml_normalization_type_enum(
        self, type: Union[str, MLNormalizationType], **kwargs
    ) -> MLNormalizationType: ...
