from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
)

import warnings
from datetime import datetime
import time
import pandas as pd
import numpy as np
from pandas.api.types import (
    is_bool_dtype,
    is_numeric_dtype,
    is_string_dtype,
    is_datetime64_dtype,
)

from petrovisor.api.enums.internal_dtypes import RefTableColumnType
from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.utils.requests import ApiRequests
from petrovisor.api.enums.items import ItemType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsItemRequests,
    SupportsSignalsRequests,
    SupportsUnitsRequests,
    SupportsDataFrames,
)


# Reference Table API calls
class RefTableMixin(
    SupportsDataFrames,
    SupportsSignalsRequests,
    SupportsItemRequests,
    SupportsUnitsRequests,
    SupportsRequests,
):
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            waiting_time = 3  # in seconds
            max_retries = 10
            i = 0
            item = self.get_item(ItemType.RefTable, name, **kwargs)
            while not item and i < max_retries:
                time.sleep(waiting_time)
                item = self.get_item(ItemType.RefTable, name, **kwargs)
                i += 1
        if item:
            return item
        return self.get_item(ItemType.RefTable, name, **kwargs)

    # add reference table
    def add_ref_table(
        self,
        name: str,
        df: Union[pd.DataFrame, Dict],
        description: Optional[str] = None,
        key_col: Optional[str] = "Key",
        date_col: Optional[str] = None,
        entity_col: Optional[str] = "Entity",
        skip_existing_data=False,
        chunksize=None,
        **kwargs,
    ) -> Any:
        """
        Add reference table from provided DataFrame.
        If reference table already exists the provided DataFrame should follow the exact same schema.

        Parameters
        ----------
        name : str
            Reference table name
        df : DataFrame, dict
            DataFrame or dictionary, where keys are column names and values are column values or predefined types,
            such as 'str', 'float', 'bool', 'datetime64[s]'.
        description : str, default None
            Reference table description
        key_col : str, default 'Key'
            Key column name
        date_col : str, default None
            Date column name. Default names
            'Date' (compatible with date column in P# table),
            'Timestamp' (compatible with the internal time column name in RefTable),
            'Time' (typically used as displayed name)
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

            df_columns = list(df.columns)
            df_columns_without_unit = [
                self.get_column_name_without_unit(col) for col in df.columns
            ]
            index_columns = []

            def get_column_by_name(name, columns):
                for idx, col in enumerate(columns):
                    if self.get_column_name_without_unit(col) == name:
                        return col
                return None

            # entity column
            df_entity_col = None
            for col in RefTableMixinHelper.get_list(entity_col, default="Entity"):
                if col in df_columns:
                    df_entity_col = col
                    index_columns.append(df_entity_col)
                    break
            if df_entity_col is None:
                if len(df_columns) <= len(index_columns):
                    raise ValueError(
                        "PetroVisor::add_ref_table(): 'Entity' column is not specified"
                    )
                df_entity_col = df_columns[len(index_columns)]
                index_columns.append(df_entity_col)
            else:
                # put index columns in front
                df_columns = [
                    *index_columns,
                    *[col for col in df_columns if col not in index_columns],
                ]

            # date column
            df_date_col = None
            for col in RefTableMixinHelper.get_list(
                date_col, default=["Timestamp", "Date", "Time"]
            ):
                if col in df_columns:
                    df_date_col = col
                    index_columns.append(df_date_col)
                    break
            if df_date_col is None:
                if len(df_columns) <= len(index_columns):
                    raise ValueError(
                        "PetroVisor::add_ref_table(): 'Timestamp' column is not specified"
                    )
                df_date_col = df_columns[len(index_columns)]
                index_columns.append(df_date_col)
            else:
                # put index columns in front
                df_columns = [
                    *index_columns,
                    *[col for col in df_columns if col not in index_columns],
                ]

            # check for columns with invalid name
            # reserved column names: "ID", "Entity", "Timestamp"
            reserved_columns = {"ID", "Entity", "Timestamp"}
            key_value_columns = [
                self.get_column_name_without_unit(col)
                for col in df_columns
                if col not in index_columns
            ]
            invalid_columns = reserved_columns.intersection(key_value_columns)
            if invalid_columns:
                raise ValueError(
                    f"PetroVisor::add_ref_table(): "
                    f"Column names {invalid_columns} are not allowed to be used as regular column names."
                )

            # key column
            df_key_col = None
            for col in RefTableMixinHelper.get_list(key_col, default="Key"):
                if col in df_columns:
                    df_key_col = col
                    index_columns.append(df_key_col)
                    break
                elif col in df_columns_without_unit:
                    df_key_col = get_column_by_name(col, df_columns)
                    index_columns.append(df_key_col)
                    break
            if df_key_col is None:
                if len(df_columns) <= len(index_columns):
                    raise ValueError(
                        "PetroVisor::add_ref_table(): 'Key' column is not specified"
                    )
                df_key_col = df_columns[len(index_columns)]
                index_columns.append(df_key_col)
            else:
                # put index columns in front
                df_columns = [
                    *index_columns,
                    *[col for col in df_columns if col not in index_columns],
                ]

            value_columns = [col for col in df_columns if col not in index_columns]

            # reorder columns
            if list(df.columns[: len(index_columns)]) != index_columns:
                df = df[[*index_columns, *value_columns]]

            column_types = df.dtypes
            options = {
                "Name": name,
                "Description": description or "",
                "Key": {
                    "Name": self.get_column_name_without_unit(df_key_col),
                    "UnitName": self.get_column_unit(df_key_col) or " ",
                    "ColumnType": RefTableMixinHelper.get_ref_table_column_type(
                        column_types[df_key_col]
                    ),
                },
                "Values": [
                    {
                        "Name": self.get_column_name_without_unit(col),
                        "UnitName": self.get_column_unit(col) or " ",
                        "ColumnType": RefTableMixinHelper.get_ref_table_column_type(
                            column_types[col]
                        ),
                    }
                    for col in value_columns
                ],
            }
            options = ApiHelper.update_dict(options, **kwargs)
            result = self.add_item(ItemType.RefTable, options, **kwargs)
            if is_empty:
                return result
        if is_empty:
            return ApiRequests.success()
        # check that RefTable was created
        waiting_time = 3  # in seconds
        while not self.item_exists(ItemType.RefTable, name):
            time.sleep(waiting_time)
        # save data to already exists RefTable
        return self.save_ref_table_data(
            name,
            df,
            skip_existing_data=skip_existing_data,
            chunksize=chunksize,
            **kwargs,
        )

    # load reference table data
    def load_ref_table_data(
        self,
        name: str,
        entity: Optional[Union[str, Dict, List[str], List[Dict]]] = None,
        date_start: Optional[Union[datetime, str]] = None,
        date_end: Optional[Union[datetime, str]] = None,
        where_expression: Optional[str] = None,
        options: Optional[Dict] = None,
        date_col: Optional[str] = "Timestamp",
        entity_col: Optional[str] = "Entity",
        **kwargs,
    ) -> pd.DataFrame:
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
        options : dict, None, default None
            Options to retrieve data
        date_col : str, default 'Timestamp'
            Date column name. Default names
            'Date' (compatible with date column in P# table),
            'Timestamp' (compatible with the internal time column name in RefTable),
            'Time' (typically used as displayed name)
        entity_col : str, default 'Entity'
            Entity column name
        """
        route = "RefTables"

        # get table columns specs
        ref_table_info = self.get_ref_table_data_info(name)
        if not ref_table_info:
            warnings.warn(
                "PetroVisor::load_ref_table_data():: "
                f"Couldn't retrieve ref table '{name}' columns information. Trying to retrieve data only.",
                RuntimeWarning,
            )

        # retrieve data
        filter_options = options if options else {}
        if entity:
            if isinstance(
                entity,
                (
                    list,
                    tuple,
                    set,
                ),
            ):
                filter_options["Entities"] = [
                    ApiHelper.get_object_name(entity) for e in entity
                ]
            else:
                filter_options["Entity"] = ApiHelper.get_object_name(entity)
        if date_start and date_end:
            date_start = self.get_json_valid_value(date_start, "time", **kwargs) or ""
            date_end = self.get_json_valid_value(date_start, "time", **kwargs) or ""
            if date_start and not date_end:
                filter_options["Timestamp"] = date_end
            elif not date_start and date_end:
                filter_options["Timestamp"] = date_end
            elif date_start and date_end:
                filter_options["StartTimestamp"] = date_start
                filter_options["EndTimestamp"] = date_end
        if where_expression:
            filter_options["WhereExpression"] = where_expression
        filter_options = ApiHelper.update_dict(filter_options, **kwargs)

        # get filtered data
        data = self.post(
            f"{route}/{self.encode(name)}/Data", data=filter_options, **kwargs
        )

        if not ref_table_info:
            # assign data without column names
            df = pd.DataFrame(data=data)
        else:
            columns = [
                f"{d['Name']} [{d['UnitName']}]" for d in ref_table_info["Values"]
            ]
            key_column = (
                f"{ref_table_info['Key']['Name']} [{ref_table_info['Key']['UnitName']}]"
            )
            columns = [
                entity_col or "Entity",
                date_col or "Timestamp",
                key_column,
                *columns,
            ]
            # assign data and column names
            df = pd.DataFrame(data=data, columns=columns)
        return df

    # save data to reference table
    def save_ref_table_data(
        self,
        name: str,
        df: pd.DataFrame,
        skip_existing_data: Optional[bool] = False,
        chunksize: Optional[int] = None,
        date_col: Optional[str] = "Timestamp",
        entity_col: Optional[str] = "Entity",
        **kwargs,
    ):
        """
        Save reference table data

        Parameters
        ----------
        name : str
            Reference table name
        df : DataFrame, dict
            DataFrame or dictionary, where keys are column names and values are column values or predefined types,
            such as 'str', 'float', 'bool', 'datetime64[s]'.
        skip_existing_data : bool, default False
            Whether to skip or overwrite existing data that has same combination of 'Entity', 'Timestamp', 'Key'
        chunksize : int, default None
            Chunk size for splitting request into multiple smaller requests.
        date_col : str, default 'Timestamp'
            Date column name. Default names
            'Date' (compatible with date column in P# table),
            'Timestamp' (compatible with the internal time column name in RefTable),
            'Time' (typically used as displayed name)
        entity_col : str, default 'Entity'
            Entity column name
        """
        route = "RefTables"

        # get table columns specs
        ref_table_info = self.get_ref_table_data_info(name)
        if not ref_table_info:
            warnings.warn(
                "PetroVisor::save_ref_table_data():: "
                f"Couldn't retrieve ref table '{name}' columns information. Trying to save data now.",
                RuntimeWarning,
            )

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

        if df is None or df.empty:
            return ApiRequests.success()

        # convert units if don't match with storage
        if ref_table_info:
            # ref table units
            columns = [(d["Name"], d["UnitName"]) for d in ref_table_info["Values"]]
            key_column = (
                ref_table_info["Key"]["Name"],
                ref_table_info["Key"]["UnitName"],
            )
            columns = [
                (entity_col or "Entity", ""),
                (date_col or "Timestamp", ""),
                key_column,
                *columns,
            ]
            df_columns = [self.get_column_name_and_unit(col) for col in df.columns]
            if len(df_columns) != len(columns):
                raise ValueError(
                    "PetroVisor::save_ref_table_data():: "
                    "Number of columns do not match. "
                    f"RefTable columns: {columns}, DataFrame columns: {df_columns}."
                )
            for idx, ((_, unit), (_, df_col_unit)) in enumerate(
                zip(columns, df_columns)
            ):
                df_col = df.columns[idx]
                if (
                    unit
                    and df_col_unit
                    and unit != df_col_unit
                    and unit not in (" ", "%")
                ):
                    dtype = df[df_col].dtype
                    df[df_col] = self.convert_units(
                        df[df_col].values,
                        source=df_col_unit,
                        target=unit,
                    )
                    df[df_col] = df[df_col].astype(dtype)

        if chunksize and (df.shape[0] > chunksize):
            # num_chunks = int(math.ceil(df.shape[0] / chunksize))
            # step = max(1, int(math.floor(0.1 * df.shape[0] / chunksize)))
            i = 0

            for start in range(0, df.shape[0], chunksize):
                end = min(start + chunksize, df.shape[0])
                self.save_ref_table_data(
                    name,
                    df[start:end],
                    skip_existing_data=skip_existing_data,
                    chunksize=chunksize,
                    **kwargs,
                )
                i += 1
            return ApiRequests.success()

        # save data
        data = df.astype("string").to_json(orient="values")
        return self.put(
            f"{route}/{self.encode(name)}/Data/String",
            query={"skipExistingData": skip_existing_data},
            data=data,
        )

    # delete reference table data
    def delete_ref_table_data(
        self,
        name: str,
        date_start: Optional[Union[datetime, float]] = None,
        date_end: Optional[Union[datetime, float]] = None,
        **kwargs,
    ) -> Any:
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
        route = "RefTables"
        if not self.item_exists(ItemType.RefTable, name):
            return ApiRequests.success()

        if date_start or date_end:
            date_start = self.get_json_valid_value(date_start, "time", **kwargs) or ""
            date_end = self.get_json_valid_value(date_start, "time", **kwargs) or ""
            if date_start and not date_end:
                date_end = date_start
            elif not date_start and date_end:
                date_start = date_end
            if date_start and date_end:
                options = {
                    "TimestampStart": date_start,
                    "TimestampEnd": date_end,
                    "IncludeWithNoTimestamp": False,  # Whether rows without timestamps should be deleted
                }
                options = ApiHelper.update_dict(options, **kwargs)
                return self.delete(
                    f"{route}/{self.encode(name)}/Data/Timestamp",
                    query=options,
                    **kwargs,
                )
        return self.delete(f"{route}/{self.encode(name)}/Data", **kwargs)

    # delete reference table
    def delete_ref_table(self, name: str, **kwargs) -> Any:
        """
        Delete reference table

        Parameters
        ----------
        name : str
            Reference table name
        """
        route = "RefTables"
        if not self.item_exists(ItemType.RefTable, name):
            return ApiRequests.success()
        # delete data
        self.delete_ref_table_data(name)
        # delete item
        self.delete(f"{route}/{self.encode(name)}", **kwargs)
        return ApiRequests.success()


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

    # get list given a value and default
    @staticmethod
    def get_list(col, default=None):
        """
        Get list given a value and default
        """
        if isinstance(col, (set, tuple, list)):
            return list(col)
        return (
            [col] if col else RefTableMixinHelper.get_list(default) if default else []
        )

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
