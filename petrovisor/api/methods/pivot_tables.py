from typing import (
    Any,
    Optional,
    Union,
    Dict,
)
import warnings

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.enums.items import ItemType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsSignalsRequests,
    SupportsDataFrames,
)


# Pivot tables mixin helper
class PivotTablesMixinHelper:
    """
    Pivot tables mixin helper — endpoint constants.
    """

    ENDPOINT = "PivotTables"


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
        backend: str = "pandas",
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
        backend : str, default 'pandas'
            DataFrame backend ('pandas', 'polars'). Output DataFrame(s) will be in the specified backend format.
        """
        route = PivotTablesMixinHelper.ENDPOINT
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
            # get pivot table schema
            schema = self.get(f"{route}/{self.encode(name)}/Schema")
            df = self.convert_pivot_table_to_dataframe(
                pivot_table_data, schema=schema, groupby_entity=groupby_entity, **kwargs
            )
            # Convert to requested backend
            if df is not None and backend != "pandas":
                from petrovisor.api.methods.dataframes import DataFrameMixinHelper

                def convert_single(d):
                    if d is None:
                        return d
                    if (
                        backend == "polars"
                        and DataFrameMixinHelper.is_backend_available("polars")
                    ):
                        import polars as pl

                        return pl.from_pandas(d)
                    elif (
                        backend == "narwhals"
                        and DataFrameMixinHelper.is_backend_available("narwhals")
                    ):
                        import narwhals as nw

                        return nw.from_native(d)
                    return d

                # Handle Dict[str, DataFrame] (groupby_entity=True case)
                if isinstance(df, dict):
                    df = {k: convert_single(v) for k, v in df.items()}
                else:
                    df = convert_single(df)
            return df

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
        route = PivotTablesMixinHelper.ENDPOINT
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
            return self.post(
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
        route = PivotTablesMixinHelper.ENDPOINT
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
        if not self.item_exists(ItemType.PivotTable, name):
            return ApiRequests.success()
        # delete data first, then the item definition
        self.delete_pivot_table_data(name)
        return self.delete_item(ItemType.PivotTable, name, **kwargs)
