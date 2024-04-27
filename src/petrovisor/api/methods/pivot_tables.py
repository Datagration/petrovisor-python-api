from typing import (
    Any,
    Optional,
    Union,
    Dict,
)
import warnings
import time

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.enums.items import ItemType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsSignalsRequests,
    SupportsDataFrames,
)


# Pivot Table API calls
class PivotTableMixin(
    SupportsDataFrames, SupportsSignalsRequests, SupportsItemRequests, SupportsRequests
):
    """
    Pivot Table API calls
    """

    # get pivot table names
    def get_pivot_table_names(self, **kwargs) -> Any:
        """
        Get pivot table names
        """
        return self.get_item_names(ItemType.PivotTable, **kwargs)

    # get pivot table info
    def get_pivot_table_data_info(self, name: str, **kwargs) -> Any:
        """
        Get pivot table data info

        Parameters
        ----------
        name : str
            Pivot table name
        """
        return self.get_item(ItemType.PivotTable, name, **kwargs)

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
    ) -> Any:
        """
        Load pivot table and return DataFrame

        Parameters
        ----------
        name : str
            Pivot table name
        entity_set : str, dict, default None
            EntitySet object or EntitySet name. If None, the EntitySet from PivotTable definition is used.
        scope : str, dict, default None
            Scope object or Scope name. If None, the Scope from PivotTable definition is used.
        num_rows : int, default 0
            Number of rows to load
        generate : bool, default False
            Generate pivot table, otherwise load saved
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        route = "PivotTables"
        if generate or entity_set or scope:
            options = {}
            if entity_set:
                entity_set_name = ApiHelper.get_object_name(entity_set, **kwargs)
                options["OverrideEntitySet"] = self.get_item(
                    ItemType.EntitySet, entity_set_name, **kwargs
                )
            if scope:
                scope_name = ApiHelper.get_object_name(scope, **kwargs)
                options["OverrideScope"] = self.get_item(
                    ItemType.Scope, scope_name, **kwargs
                )
            if options:
                pivot_table_data = self.get(
                    f"{route}/{self.encode(name)}/Generated/Options",
                    data=options,
                    **kwargs,
                )
            else:
                pivot_table_data = self.get(
                    f"{route}/{self.encode(name)}/Generated", **kwargs
                )
        else:
            pivot_table_data = self.get(
                f"{route}/{self.encode(name)}/Saved",
                query={"RowCount": self.get_json_valid_value(num_rows, "numeric")},
                **kwargs,
            )
        if pivot_table_data:
            return self.convert_pivot_table_to_dataframe(
                pivot_table_data, groupby_entity=groupby_entity, **kwargs
            )

        warnings.warn(
            f"PetroVisor::load_pivot_table_data(): "
            f"Pivot table '{name}' might be not saved, please try to generate data instead.",
            RuntimeWarning,
            stacklevel=1,
        )

        return None

    # save pivot table data
    def save_pivot_table_data(
        self,
        name: str,
        entity_set: Optional[str] = None,
        scope: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Save pivot table data

        Parameters
        ----------
        name : str
            Pivot table name
        entity_set : str, dict, default None
            EntitySet object or EntitySet name. If None, the EntitySet from PivotTable definition is used.
        scope : str, dict, default None
            Scope object or Scope name. If None, the Scope from PivotTable definition is used.
        """
        route = "PivotTables"
        options = {}
        if entity_set:
            entity_set_name = ApiHelper.get_object_name(entity_set, **kwargs)
            options["OverrideEntitySet"] = self.get_item(
                ItemType.EntitySet, entity_set_name, **kwargs
            )
        if scope:
            scope_name = ApiHelper.get_object_name(scope, **kwargs)
            options["OverrideScope"] = self.get_item(
                ItemType.Scope, scope_name, **kwargs
            )
        if options:
            self.post(
                f"{route}/{self.encode(name)}/Save/Options", data=options, **kwargs
            )
        return self.get(f"{route}/{self.encode(name)}/Save", **kwargs)

    # delete pivot table data
    def delete_pivot_table_data(self, name: str, **kwargs) -> Any:
        """
        Delete pivot table data

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = "PivotTables"
        if not self.item_exists(ItemType.PivotTable, name):
            return ApiRequests.success()
        return self.get(f"{route}/{self.encode(name)}/Delete", **kwargs)

    # delete pivot table
    def delete_pivot_table(self, name: str, **kwargs) -> Any:
        """
        Delete pivot table

        Parameters
        ----------
        name : str
            Pivot table name
        """
        route = "PivotTables"
        if not self.item_exists(ItemType.PivotTable, name):
            return ApiRequests.success()
        # delete data
        self.delete_pivot_table_data(name)
        # delete item
        self.delete(f"{route}/{self.encode(name)}", **kwargs)
        return ApiRequests.success()
