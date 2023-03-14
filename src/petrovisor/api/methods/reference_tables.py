from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

import pandas as pd
import numpy as np
from datetime import datetime

from petrovisor.api.utils.helper import ApiHelper

from petrovisor.api.protocols.protocols import SupportsRequests
from petrovisor.api.protocols.protocols import SupportsItemRequests
from petrovisor.api.protocols.protocols import SupportsSignalsRequests
from petrovisor.api.protocols.protocols import SupportsDataFrames


# Reference Table API calls
class RefTableMixin(SupportsDataFrames, SupportsSignalsRequests, SupportsItemRequests, SupportsRequests):
    """
    Reference Table API calls
    """

    # load reference table info
    def get_ref_table_data_info(self, name: str, **kwargs) -> Any:
        """
        Get reference table data info

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = 'ReferenceTables'
        return self.get(f'{route}/{name}/ExistingData', **kwargs)

    # load reference table data
    def load_ref_table_data(self,
                            name: str,
                            entity: Union[str, Dict],
                            date: Optional[Union[datetime, str]],
                            **kwargs) -> Any:
        """
        Load reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        """
        route = 'ReferenceTables'
        entity_name = ApiHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date, 'time', **kwargs)
        if date_str is None:
            date_str = ''
        return self.get(f'{route}/{name}/Data/{entity_name}/{date_str}', **kwargs)

    # save reference table data
    def save_ref_table_data(self,
                            name: str,
                            entity: Union[str, Dict],
                            date: Optional[Union[datetime, float]],
                            data: Union[Dict[float, float], List, pd.DataFrame],
                            **kwargs) -> Any:
        """
        Save reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        data : dict, list, DataFrame
            Reference Table Data
        """
        route = 'ReferenceTables'
        entity_name = ApiHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date, 'time', **kwargs)
        if date_str is None:
            date_str = ''
        # prepare data
        if isinstance(data, dict):
            return self.put(f'{route}/{name}/Data/{entity_name}/{date_str}', data=data, **kwargs)
        else:
            # convert list to dictionary
            def __list_to_dict(x, num_cols, **kwargs):
                if num_cols == 0:
                    return {
                        self.get_json_valid_value(idx, 'numeric', **kwargs):
                            self.get_json_valid_value(row, 'numeric', **kwargs) for idx, row in enumerate(x)}
                elif num_cols == 1:
                    return {
                        self.get_json_valid_value(idx, 'numeric', **kwargs):
                            self.get_json_valid_value(row[0], 'numeric', **kwargs) for idx, row in enumerate(x)}
                elif num_cols > 1:
                    return {
                        self.get_json_valid_value(row[0], 'numeric', **kwargs):
                            self.get_json_valid_value(row[1], 'numeric', **kwargs) for row in x}
                return {}
            if isinstance(data, (list, np.ndarray, pd.DataFrame, pd.Series)):
                num_cols = ApiHelper.get_num_cols(data)
                if num_cols is None:
                    raise ValueError(f"PetroVisor::save_ref_table_data(): "
                                     f"number of columns in the list should be either 2 or 1.")
                ref_table = __list_to_dict(ApiHelper.to_list(data, **kwargs), num_cols, **kwargs)
            else:
                raise ValueError(f"PetroVisor::save_ref_table_data(): invalid data format '{type(data)}'. "
                                 f"Should be either dict[float,float], list of iterables, DataFrame, Series or array.")
            return self.put(f'{route}/{name}/Data/{entity_name}/{date_str}', data=ref_table, **kwargs)

    # delete reference table data
    def delete_ref_table_data(self,
                              name: str,
                              entity: Union[str, Dict],
                              date: Optional[Union[datetime, float]],
                              **kwargs) -> Any:
        """
        Delete reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict
            Entity object or Entity name
        date : str, datetime, None
            Date or None
        """
        route = 'ReferenceTables'
        entity_name = ApiHelper.get_object_name(entity)
        date_str = self.get_json_valid_value(date, 'time', **kwargs)
        if date_str is None:
            date_str = ''
        return self.delete(f'{route}/{name}/Data/{entity_name}/{date_str}', **kwargs)
    