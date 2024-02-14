from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

from datetime import datetime
import time
import pandas as pd
import numpy as np
from pandas.api.types import is_bool_dtype, is_numeric_dtype, is_string_dtype, is_datetime64_dtype

from petrovisor.api.dtypes.internal_dtypes import RefTableColumnType
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.dtypes.items import ItemType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsSignalsRequests,
    SupportsDataFrames,
)


# Reference Table API calls
class RefTableMixin(SupportsDataFrames, SupportsSignalsRequests, SupportsItemRequests, SupportsRequests):
    """
    Reference Table API calls
    """

    # get reference table names
    def get_ref_table_names(self, **kwargs) -> Any:
        """
        Get reference table names
        """
        return self.get_item_names(ItemType.RefTable, **kwargs)

    # get reference table info
    def get_ref_table_data_info(self, name: str, **kwargs) -> Any:
        """
        Get reference table data info

        Parameters
        ----------
        name : str
            Reference table name
        """
        return self.get_item(ItemType.RefTable, name, **kwargs)

    # add reference table
    def add_ref_table(self, name: str,
                      df: Union[pd.DataFrame, Dict],
                      description: Optional[str] = None,
                      key_col: Optional[str] = 'Key',
                      date_col: Optional[str] = None,
                      entity_col: Optional[str] = 'Entity',
                      skip_existing_data=False,
                      chunksize=None,
                      **kwargs) -> Any:
        """
        Add reference table from provided DataFrame.
        If reference table already exists the provided DataFrame should follow the exact same schema.

        Parameters
        ----------
        name : str
            Reference table name
        df : DataFrame, dict
            DataFrame or dictionary, where keys are column names and values are column values or predefined types, such as 'str', 'float', 'bool', 'datetime64[s]'.
        description : str, default None
            Reference table description
        key_col : str, default 'Key'
            Key column name
        date_col : str, default None
            Date column name. Default names 'Date' (compatible with date column in P# table), 'Timestamp' (compatible with the internal time column name in RefTable), 'Time' (typically used as displayed name)
        entity_col : str, default 'Entity'
            Entity column name
        skip_existing_data : bool, default False
            Whether to skip or overwrite existing data that has same combination of 'Entity', 'Timestamp', 'Key'
        chunksize : int, default None
            Chunk size for splitting request into multiple smaller requests.
        """
        if isinstance(df, dict):
            df = RefTableMixinHelper.create_dataframe(df)

        # add definition if it doesn't exists
        is_empty = df.empty
        if not self.item_exists(ItemType.RefTable, name):

            # date column
            df_date_cols = set()
            for col in RefTableMixinHelper.get_set(date_col, default={'Date', 'Timestamp', 'Time'}):
                if col in df.columns:
                    df_date_cols.add(col)
            if 'Timestamp' in df_date_cols:
                df_date_col = 'Timestamp'
            elif 'Date' in df_date_cols:
                df_date_col = 'Date'
            elif 'Time' in df_date_cols:
                df_date_col = 'Time'
            else:
                df_date_col = df_date_cols.pop() if df_date_cols else None

            # entity column
            df_entity_cols = set()
            for col in RefTableMixinHelper.get_set(entity_col, default='Entity'):
                if col in df.columns:
                    df_entity_cols.add(col)
            if 'Entity' in df_entity_cols:
                df_entity_col = 'Entity'
            else:
                df_entity_col = df_entity_cols.pop() if df_entity_cols else None

            # key column
            df_key_cols = set()
            for col in RefTableMixinHelper.get_set(key_col, default='Key'):
                if col in df.columns:
                    df_key_cols.add(col)
            if 'Key' in df_key_cols:
                df_key_col = 'Key'
            elif df_key_cols:
                df_key_col = df_key_cols.pop()
            else:
                raise ValueError("PetroVisor::add_ref_table(): "
                                 "'Key' column is not specified")

            # reserved column names: "ID", "Timestamp", "Entity"
            reserved_columns = {'ID', 'Entity', 'Timestamp'}
            if df_date_col:
                reserved_columns = reserved_columns.union({df_date_col})
            if df_entity_col:
                reserved_columns = reserved_columns.union({df_entity_col})
            reserved_columns = reserved_columns.union({df_key_col})
            value_columns = [col for col in df.columns if col not in reserved_columns]
            column_types = df.dtypes
            options = {
                'Name': name,
                'Description': description or "",
                'Key': {
                    'Name': df_key_col,
                    'UnitName': self.get_column_unit(df_key_col) or ' ',
                    'ColumnType': RefTableMixinHelper.get_ref_table_column_type(column_types[df_key_col]),
                },
                'Values': [{'Name': col,
                            'UnitName': self.get_column_unit(col) or ' ',
                            'ColumnType': RefTableMixinHelper.get_ref_table_column_type(column_types[col]),
                            } for col in value_columns],
            }
            options = ApiHelper.update_dict(options, **kwargs)
            result = self.add_item(ItemType.RefTable, options, **kwargs)
            if is_empty:
                return result
        if is_empty:
            return ApiRequests.success()
        # save data to already exists RefTable
        waiting_time = 3  # in seconds
        while not self.item_exists(ItemType.RefTable, name):
            time.sleep(waiting_time)
        return self.save_ref_table_data(name,
                                        df,
                                        skip_existing_data=skip_existing_data,
                                        chunksize=chunksize,
                                        **kwargs)

    # load reference table data
    def load_ref_table_data(self,
                            name: str,
                            entity: Optional[Union[str, Dict, List[str], List[Dict]]] = None,
                            date_start: Optional[Union[datetime, str]] = None,
                            date_end: Optional[Union[datetime, str]] = None,
                            where_expression: Optional[str] = None,
                            date_col: Optional[str] = 'Timestamp',
                            entity_col: Optional[str] = 'Entity',
                            options: Optional[Dict] = None,
                            **kwargs) -> pd.DataFrame:
        """
        Load reference table data

        Parameters
        ----------
        name : str
            Reference table name
        entity : str, dict or list[str], list[dict]
            Entity object(s) or Entity name(s)
        date_start : str, datetime, None
            Start Date or None
        date_end : str, datetime, None
            End Date or None
        where_expression : str, default None
            SQL like WHERE expression
        date_col : str, default 'Date'
            Date column name. Default names 'Date' (compatible with date column in P# table), 'Timestamp' (compatible with the internal time column name in RefTable), 'Time' (typically used as displayed name)
        entity_col : str, default 'Entity'
            Entity column name
        options : dict, None, default Noe
            Options to retrieve data
        """
        route = 'RefTables'
        filter_options = options if options else {}
        if entity:
            if isinstance(entity, (list, tuple, set, )):
                filter_options['Entities'] = [ApiHelper.get_object_name(entity) for e in entity]
            else:
                filter_options['Entity'] = ApiHelper.get_object_name(entity)
        if date_start and date_end:
            date_start = self.get_json_valid_value(date_start, 'time', **kwargs) or ''
            date_end = self.get_json_valid_value(date_start, 'time', **kwargs) or ''
            if date_start and not date_end:
                filter_options['Timestamp'] = date_end
            elif not date_start and date_end:
                filter_options['Timestamp'] = date_end
            elif date_start and date_end:
                filter_options['StartTimestamp'] = date_start
                filter_options['EndTimestamp'] = date_end
        if where_expression:
            filter_options['WhereExpression'] = where_expression
        filter_options = ApiHelper.update_dict(filter_options, **kwargs)

        # get filtered data
        data = self.post(f'{route}/{self.encode(name)}/Data', data=filter_options, **kwargs)
        ref_table_info = self.get_ref_table_data_info(name)
        columns = [f"{d['Name']} [{d['UnitName']}]" for d in ref_table_info['Values']]
        key_column = f"{ref_table_info['Key']['Name']} [{ref_table_info['Key']['UnitName']}]"
        columns = [entity_col or 'Entity', date_col or 'Date', key_column, *columns]
        df = pd.DataFrame(data=data, columns=columns)
        return df

    # save data to reference table
    def save_ref_table_data(self,
                            name: str,
                            df: pd.DataFrame,
                            skip_existing_data: Optional[bool] = False,
                            chunksize: Optional[int] = None,
                            **kwargs):
        """
        Save reference table data

        Parameters
        ----------
        name : str
            Reference table name
        df : DataFrame, dict
            DataFrame or dictionary, where keys are column names and values are column values or predefined types, such as 'str', 'float', 'bool', 'datetime64[s]'.
        skip_existing_data : bool, default False
            Whether to skip or overwrite existing data that has same combination of 'Entity', 'Timestamp', 'Key'
        chunksize : int, default None
            Chunk size for splitting request into multiple smaller requests.
        """
        route = 'RefTables'

        # create DataFrame in case if it is passed as dictionary
        def create_dataframe(d: Dict):
            df = pd.DataFrame()
            for c, d in d.items():
                if isinstance(d, (str, type)):
                    df[c] = pd.Series(dtype=d)
                else:
                    df[c] = d
            return df

        if isinstance(df, dict):
            df = create_dataframe(df)

        if df is not None and not df.empty:
            if chunksize and (df.shape[0] > chunksize):
                # num_chunks = int(math.ceil(df.shape[0] / chunksize))
                # step = max(1, int(math.floor(0.1 * df.shape[0] / chunksize)))
                i = 0

                for start in range(0, df.shape[0], chunksize):
                    end = min(start + chunksize, df.shape[0])

                    self.save_ref_table_data(name,
                                             df[start:end],
                                             skip_existing_data=skip_existing_data,
                                             chunksize=chunksize,
                                             **kwargs)
                    i += 1
                return ApiRequests.success()
            # save data
            data = df.astype('string').to_json(orient='values')
            return self.put(f"{route}/{self.encode(name)}/Data/String",
                            query={'skipExistingData': skip_existing_data},
                            data=data)
        return ApiRequests.success()

    # delete reference table data
    def delete_ref_table_data(self,
                              name: str,
                              date_start: Optional[Union[datetime, float]] = None,
                              date_end: Optional[Union[datetime, float]] = None,
                              **kwargs) -> Any:
        """
        Delete reference table data

        Parameters
        ----------
        name : str
            Reference table name
        date_start : str, datetime, None
            Start Date or None
        date_end : str, datetime, None
            End Date or None
        """
        route = 'RefTables'
        if date_start or date_end:
            date_start = self.get_json_valid_value(date_start, 'time', **kwargs) or ''
            date_end = self.get_json_valid_value(date_start, 'time', **kwargs) or ''
            if date_start and not date_end:
                date_end = date_start
            elif not date_start and date_end:
                date_start = date_end
            if date_start and date_end:
                options = {
                    'TimestampStart': date_start,
                    'TimestampEnd': date_end,
                    'IncludeWithNoTimestamp': False,  # Whether rows without timestamps should be deleted
                }
                options = ApiHelper.update_dict(options, **kwargs)
                return self.delete(f'{route}/{self.encode(name)}/Data/Timestamp', query=options, **kwargs)
        return self.delete(f'{route}/{self.encode(name)}/Data', **kwargs)

    # delete reference table
    def delete_ref_table(self,
                         name: str,
                         **kwargs) -> Any:
        """
        Delete reference table

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = 'RefTables'
        if not self.item_exists(ItemType.RefTable, name):
            return ApiRequests.success()
        return self.delete(f'{route}/{self.encode(name)}', **kwargs)


# Reference table mixin helper
class RefTableMixinHelper:

    # create DataFrame in case if it is passed as dictionary
    @staticmethod
    def create_dataframe(d: Dict):
        df = pd.DataFrame()
        for c, d in d.items():
            if isinstance(d, (str, type)):
                df[c] = pd.Series(dtype=d)
            else:
                df[c] = d
        return df

    # get set given a value and default
    @staticmethod
    def get_set(col, default=None):
        """
        Get set given a value and default
        """
        if isinstance(col, (set, tuple, list)):
            return set(col)
        return {col} if col else RefTableMixinHelper.get_set(default) if default else {}

    # get reference column type
    @staticmethod
    def get_ref_table_column_type(dtype):
        """
        Get reference column type
        """
        if dtype == bool or is_bool_dtype(dtype):
            return RefTableColumnType.Bool.name
        elif dtype == np.int64 or dtype == np.float64 or is_numeric_dtype(dtype):
            return RefTableColumnType.Numeric.name
        elif dtype == datetime.date or is_datetime64_dtype(dtype):
            return RefTableColumnType.DateTime.name
        elif dtype == object or is_string_dtype(dtype):
            return RefTableColumnType.String.name
        else:
            return RefTableColumnType.Numeric.name
