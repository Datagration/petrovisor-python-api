from typing import (
    Any,
    Optional,
    Union,
    Dict,
)

from petrovisor.api.utils.helper import ApiHelper

from petrovisor.api.protocols.protocols import SupportsRequests
from petrovisor.api.protocols.protocols import SupportsItemRequests
from petrovisor.api.protocols.protocols import SupportsSignalsRequests
from petrovisor.api.protocols.protocols import SupportsDataFrames


# Pivot Table API calls
class PivotTableMixin(SupportsDataFrames, SupportsSignalsRequests, SupportsItemRequests, SupportsRequests):
    """
    Pivot Table API calls
    """

    # load pivot table data
    def load_pivot_table_data(self,
                              name: str,
                              entity_set: Optional[Union[str, Dict]] = None,
                              scope: Optional[Union[str, Dict]] = None,
                              num_rows: Optional[int] = 0,
                              generate: bool = False,
                              groupby_entity: bool = False,
                              **kwargs) -> Any:
        """
        Load PivotTable and return DataFrame

        Parameters
        ----------
        name : str
            Reference table name
        entity_set : str, dict
            EntitySet object or EntitySet name
        scope : str, dict
            Scope object or Scope name
        num_rows : int, default 0
            Number of rows to load
        generate : bool, default False
            Generate pivot table, otherwise load saved
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        route = 'PivotTables'
        if entity_set or scope:
            options = {}
            if entity_set:
                options['OverrideEntitySet'] = ApiHelper.get_object_name(entity_set, **kwargs)
            if scope:
                options['OverrideScope'] = ApiHelper.get_object_name(scope, **kwargs)
            pivot_table_data = self.get(f'{route}/{name}/Generated/Options', data=options, **kwargs)
        elif generate:
            pivot_table_data = self.get(f'{route}/{name}/Generated', **kwargs)
        else:
            pivot_table_data = self.get(f'{route}/{name}/Saved',
                                        query={
                                            'RowCount': self.get_json_valid_value(num_rows, 'numeric')
                                        },
                                        **kwargs)
        if pivot_table_data:
            return self.convert_pivot_table_to_dataframe(pivot_table_data, groupby_entity=groupby_entity, **kwargs)
        return None

    # save pivot table data
    def save_pivot_table_data(self,
                              name: str,
                              entity_set: Optional[str] = None,
                              scope: Optional[str] = None,
                              **kwargs) -> Any:
        """
        Save PivotTable data

        Parameters
        ----------
        name : str
            Reference table name
        entity_set : str, dict
            EntitySet object or EntitySet name
        scope : str, dict
            Scope object or Scope name
        """
        route = 'PivotTables'
        if entity_set or scope:
            options = {}
            if entity_set:
                options['OverrideEntitySet'] = ApiHelper.get_object_name(entity_set, **kwargs)
            if scope:
                options['OverrideScope'] = ApiHelper.get_object_name(scope, **kwargs)
            self.post(f'{route}/{name}/Save/Options', data=options, **kwargs)
        return self.get(f'{route}/{name}/Save', **kwargs)

    # delete pivot table data
    def delete_pivot_table_data(self, name: str, **kwargs) -> Any:
        """
        Delete PivotTable data

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = 'PivotTables'
        return self.get(f'{route}/{name}/Delete', **kwargs)
