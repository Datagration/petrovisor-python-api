from typing import (
    Any,
    Optional,
    Union,
    List,
    Dict,
    Tuple,
    Iterable,
)

import io
import re
import copy
from datetime import datetime
import pandas as pd

from petrovisor.api.enums.internal_dtypes import SignalType
from petrovisor.api.protocols.protocols import (
    SupportsRequests,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
    SupportsDataFrames,
)


# DataFrames utilities
class DataFrameMixin(
    SupportsDataFrames,
    SupportsSignalsRequests,
    SupportsEntitiesRequests,
    SupportsRequests,
):
    """
    DataFrames Utilities
    """

    # convert dataframe to file-like object
    def convert_dataframe_to_file_object(
        self,
        df: pd.DataFrame,
        file_name: str,
        date_format: Optional[str] = None,
        **kwargs,
    ) -> io.BytesIO:
        """
        Convert dataframe to file-like object

        Parameters
        ----------
        df : DataFrame
            DataFrame
        file_name : str
            File name
        date_format : str, default None
            Date format
        """
        with io.BytesIO() as file_obj:
            file_obj.name = file_name
            if file_name.lower().endswith(".csv"):
                if date_format:
                    df.to_csv(
                        file_obj,
                        header=True,
                        index=False,
                        encoding="utf-8",
                        mode="wb",
                        date_format="%Y-%m-%dT%H:%M:%S.%fZ",
                    )
                else:
                    df.to_csv(
                        file_obj, header=True, index=True, encoding="utf-8", mode="wb"
                    )
                file_obj.seek(0)
            elif file_name.lower().endswith(".xlsx"):
                excel_writer = pd.ExcelWriter(file_obj, engine="openpyxl")
                df.to_excel(excel_writer, header=True, index=True, encoding="utf-8")
                excel_writer.save()
                file_obj.seek(0)
            else:
                file_obj.close()
            return file_obj

    # convert PivotTable to DataFrame
    def convert_pivot_table_to_dataframe(
        self, data: List, groupby_entity: bool = False, **kwargs
    ):
        """
        Convert PivotTable to DataFrame

        Parameters
        ----------
        data : list
            PivotTable data
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        try:
            if data:
                # get columns
                cols = data[0]
                if len(data) > 1:
                    df = pd.DataFrame(data=data[1:], columns=cols)
                else:
                    df = pd.DataFrame(columns=cols)
            else:
                df = pd.DataFrame()

            # assign column types
            columns = df.columns
            columns_dtype = {col: "Numeric" for col in columns}
            entity_col = self.get_entity_column_name(**kwargs)
            entity_type_col = self.get_entity_type_column_name(**kwargs)
            alias_col = self.get_alias_column_name(**kwargs)
            is_opportunity_col = self.get_opportunity_column_name(**kwargs)
            date_col = self.get_date_column_name(**kwargs)
            time_col = self.get_time_column_name(**kwargs)
            for col in [date_col, time_col]:
                columns_dtype[col] = "Time"
            for col in [entity_col, alias_col, entity_type_col]:
                columns_dtype[col] = "String"
            columns_dtype[is_opportunity_col] = "Bool"
            df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

            # group by entity
            if groupby_entity:
                df = {e: df_group for e, df_group in df.groupby(entity_col)}
        except BaseException:
            raise RuntimeError(
                "PetroVisor::convert_pivot_table_to_dataframe(): "
                "couldn't convert PivotTable to DataFrame"
            )
        return df

    # convert P# table to DataFrame
    def convert_psharp_table_to_dataframe(
        self,
        psharp_table: Union[Dict, List],
        dropna: bool = True,
        with_entity_column: bool = True,
        groupby_entity: bool = False,
        **kwargs,
    ) -> Optional[Union[pd.DataFrame, Dict[str, pd.DataFrame]]]:
        """
        Convert P# table to DataFrame

        Parameters
        ----------
        psharp_table : dict, list
            P# table data
        dropna : bool, default True
            Whether rows filled with NaNs should be dropped
        with_entity_column : bool, default True
            Load table with 'Entity' column, otherwise columns will be named as "EntityName : ColumnName"
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        """
        if psharp_table is None:
            return None

        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()
        # known column types
        columns_dtype = {
            entity_col: "String",
            alias_col: "String",
            date_col: "Time",
            depth_col: "Numeric",
        }

        # read P# table from list
        if isinstance(psharp_table, list):
            if len(psharp_table) < 2:
                return None

            columns = psharp_table[0].split("\t") if len(psharp_table) > 0 else []

            # define type of table
            has_entity_col = entity_col in columns

            # create DataFrame
            if has_entity_col or not groupby_entity:
                # create DataFrame
                df = DataFrameMixinHelper.create_dataframe_from_list(psharp_table)
                # assign column types
                df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)
                # group by entity
                if groupby_entity:
                    df = {e: df_group for e, df_group in df.groupby(entity_col)}
                # convert to wide format with columns format "{entity_name} : {column_name}"
                elif has_entity_col and not with_entity_column:
                    df = self.convert_dataframe_from_long_to_wide(df)
                # convert to long format with 'Entity' column
                elif not has_entity_col and with_entity_column:
                    df = self.convert_dataframe_from_wide_to_long(df)

            # special case when columns have format "{entity_name} : {column_name}"
            # and group by entity is required
            else:
                # remove entity name from column names
                col_names = DataFrameMixinHelper.remove_entities_from_columns(columns)
                # extract entity name from column names
                col_entities = DataFrameMixinHelper.get_entities_from_columns(columns)
                # list of all entities
                entities = DataFrameMixinHelper.get_unique_non_empty_names(col_entities)
                # create DataFrame
                df = {}
                for e in entities:
                    e_columns = [
                        cname
                        for ce, cname in zip(col_entities, col_names)
                        if not ce or ce == e
                    ]
                    df[e] = pd.DataFrame(
                        [
                            cv
                            for row in psharp_table[1:]
                            for cv, ce in zip(row.split("\t"), col_entities)
                            if not ce or ce == e
                        ],
                        columns=e_columns,
                    )

                # assign column types
                for e in entities:
                    df[e] = self.assign_dataframe_column_types(
                        df[e], columns_dtype, **kwargs
                    )

        elif (
            psharp_table is not None
            and "TableName" in psharp_table
            and "ResultsOrder" in psharp_table
        ):
            # results order
            columns_short = psharp_table["ResultsOrder"]
            # create column names map from short to full name with unit
            columns_short_to_long = {col: None for col in columns_short}

            # get column specs
            def get_column_specs(
                col: Dict[str, Any], is_not_full_spec: bool
            ) -> Tuple[str, str, str]:
                if is_not_full_spec:
                    centity = col["EntityName"]
                    cname = col["ResultName"]
                    cunit = col["UnitName"]
                else:
                    centity = col["Entity"]
                    result = col["Result"]
                    cname = result["Name"]
                    cunit = col["Unit"]
                    # cunit = result['Unit']['Name']
                return centity, cname, cunit

            # get full column name
            def get_full_column_name(col_name: str, unit_name: str):
                return f"{col_name} [{unit_name}]"

            # create DataFrame
            data_field = "Data"
            value_field = "Value"
            # result_field = ''
            fields = []
            for i, table_fields in enumerate(
                [
                    [
                        "Columns",
                        "ColumnsDepth",
                        "ColumnsString",
                        "ColumnsTime",
                        "ColumnsBool",
                    ],
                    ["Data", "DataDepth", "DataString", "DataTime", "DataBool"],
                ]
            ):
                is_not_full_spec = i == 0
                entity_field = "EntityName" if is_not_full_spec else "Entity"
                # non-empty fields
                fields = [
                    field
                    for field in table_fields
                    if field in psharp_table and psharp_table[field]
                ]
                for col_type in fields:
                    # column type
                    col_dtype = "Numeric"
                    for suffix in ["String", "Time", "Bool"]:
                        if suffix in col_type:
                            col_dtype = suffix
                            break
                    for col in psharp_table[col_type]:
                        # get column info
                        col_entity_name, col_name, col_unit_name = get_column_specs(
                            col, is_not_full_spec
                        )
                        # assign column data type
                        if columns_short_to_long[col_name] is None:
                            full_column_name = get_full_column_name(
                                col_name, col_unit_name
                            )
                            columns_short_to_long[col_name] = full_column_name
                            columns_dtype[columns_short_to_long[col_name]] = col_dtype
                        else:
                            full_column_name = columns_short_to_long[col_name]
                        # change entity field to 'Entity'
                        if entity_field != entity_col:
                            col[entity_col] = col.pop(entity_field)
                        # change value field to column name
                        for d in col[data_field]:
                            d[full_column_name] = d.pop(value_field)
                if fields:
                    break
            if not fields:
                return None

            # create DataFrame
            df = pd.json_normalize(
                (
                    [values for field in fields for values in psharp_table[field]]
                    if len(fields) > 1
                    else psharp_table[fields[0]]
                ),
                record_path=data_field,
                meta=[entity_col],
                errors="ignore",
            )

            # reorder columns
            offset = 0
            reordered_columns = list(df.columns)
            # first columns 'Date', 'Depth', 'Entity'
            for col in [entity_col, depth_col, date_col]:
                if col in reordered_columns:
                    reordered_columns.remove(col)
                    reordered_columns.insert(0, col)
                    offset += 1
            # arrange other columns according to results order
            for idx, col in enumerate(columns_short):
                full_column_name = columns_short_to_long[col]
                if full_column_name in reordered_columns:
                    reordered_columns.remove(full_column_name)
                    reordered_columns.insert(offset + idx, full_column_name)
                else:
                    offset -= 1

            # arrange columns according to results order
            df = df[reordered_columns]

            # assign column types
            df = self.assign_dataframe_column_types(df, columns_dtype, **kwargs)

            # drop NaNs
            if dropna:
                # df = df.dropna(axis=0, how='all', inplace=False)
                df.dropna(axis=0, how="all", inplace=True)

            # group by entity
            if groupby_entity:
                df = {e: df_group for e, df_group in df.groupby(entity_col)}
            # convert to wide format with columns format "{entity_name} : {column_name"
            elif not with_entity_column:
                df = self.convert_dataframe_from_long_to_wide(df)
        else:
            raise ValueError(
                "PetroVisor::convert_psharp_table_to_dataframe(): "
                "unknown P# table type!"
            )

        return df

    # Get signal data from DataFrame

    def get_signal_data_from_dataframe(
        self,
        df: pd.DataFrame,
        signals: Optional[Dict] = None,
        only_existing_entities: bool = True,
        entity_type: str = "",
        entities: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get signal data from DataFrame

        Parameters
        ----------
        df : DataFrame
            Table
        signals : dict, default None
            Dictionary map from 'table column name' to 'workspace signal name'
        entities : dict, default None
            Dictionary map from 'table entity name' to 'workspace entity name'
        only_existing_entities : bool, default True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        """
        # get columns
        columns = df.columns
        # num_cols = len(columns)

        # standard columns
        entity_col = self.get_entity_column_name()
        alias_col = self.get_alias_column_name()
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()

        # entities map
        entities_map = copy.deepcopy(entities) if entities else {}

        # filter out undefined entities
        select_entities = (
            self.get_entity_names(entity_type=entity_type, **kwargs)
            if only_existing_entities
            else None
        )
        if select_entities and entities_map:
            entities_map_rev = {v: k for k, v in entities_map.items()}
            select_entities = [
                entities_map_rev[e] if (e in entities_map_rev) else e
                for e in select_entities
            ]

        # data containers
        data_to_save = {s.name: [] for s in SignalType}

        # collect data info
        with_entity_col = entity_col in columns
        if not with_entity_col:
            # remove entity name from column names
            col_names = DataFrameMixinHelper.remove_entities_from_columns(columns)
            # extract entity name from column names
            col_entities = DataFrameMixinHelper.get_entities_from_columns(columns)
            # list of all entities
            entities = DataFrameMixinHelper.get_unique_non_empty_names(col_entities)
            # get column data info
            col_data = {
                e: [
                    (cname, cidx)
                    for cidx, (centity, cname) in enumerate(
                        zip(col_entities, col_names)
                    )
                    if centity == e
                ]
                for e in entities
                if (select_entities is None) or (e in select_entities)
            }
        else:
            # get column names
            col_names = columns
            # get list of entities
            entities = (
                list(set(df[entity_col].tolist())) if (entity_col in columns) else []
            )
            # get column data info
            col_data = {
                e: [(cname, cidx) for cidx, cname in enumerate(columns)]
                for e in entities
                if (select_entities is None) or (e in select_entities)
            }

        # remap entities data
        if entities_map:
            col_data = {
                entities_map[e] if (e in entities_map) else e: d
                for e, d in col_data.items()
            }

        # 'Date' column
        date_index = None
        for i, column_name in enumerate(col_names):
            if column_name == date_col:
                date_index = i
                break

        # 'Depth' column
        depth_index = None
        for i, column_name in enumerate(col_names):
            if (
                column_name == depth_col
                or self.get_column_name_without_unit(column_name) == depth_col
            ):
                depth_index = i
                break

        # get signal info
        def _get_signal_info(
            column_name: str, signal_names: List[str], signals: Optional[Dict] = None
        ):
            column_name_without_unit = self.get_column_name_without_unit(column_name)
            column_unit_name = self.get_column_unit(column_name)
            if signals:
                signal = (
                    signals[column_name]
                    if (column_name in signals)
                    else (
                        signals[column_name_without_unit]
                        if (column_name_without_unit in signals)
                        else None
                    )
                )
            else:
                signal = None
            if not signal:
                signal_name = column_name_without_unit
                signal_unit = column_unit_name
            elif isinstance(signal, str):
                signal_name_without_unit = self.get_column_name_without_unit(signal)
                signal_unit_name = self.get_column_unit(signal)
                signal_name = signal_name_without_unit
                signal_unit = signal_unit_name if signal_unit_name else column_unit_name
            elif (
                isinstance(signal, tuple)
                or isinstance(signal, list)
                and len(signal) > 0
            ):
                signal_name = signal[0]
                signal_unit = signal[1] if (len(signal) > 1) else column_unit_name
            else:
                signal_name = self.get_column_name_without_unit(column_name)
                signal_unit = self.get_column_unit(column_name)
                for fname in ["Signal", "Name", "SignalName"]:
                    if fname in signal:
                        signal_name = signal[fname]
                        break
                    elif fname.lower() in signal:
                        signal_name = signal[fname.lower()]
                        break
                for fname in ["Unit", "UnitName", "SignalUnit"]:
                    if fname in signal:
                        signal_unit = signal[fname]
                        break
                    elif fname.lower() in signal:
                        signal_unit = signal[fname.lower()]
                        break
            # get signal
            if signal_name in signal_names:
                signal_obj = self.get_signal(signal_name, **kwargs)
                if signal_obj:
                    if not signal_unit and "StorageUnitName" in signal_obj:
                        signal_unit = signal_obj["StorageUnitName"]
                    signal_type = (
                        signal_obj["SignalType"]
                        if ("SignalType" in signal_obj)
                        else None
                    )
                    return {
                        "Signal": signal_name,
                        "Unit": signal_unit,
                        "SignalType": signal_type,
                    }
            return None

        # check whether non index column
        def _is_index_column(column_name: str) -> bool:
            return column_name in {date_col, depth_col, entity_col, alias_col}

        # get column data
        def _get_column_data(column_index: int, entity_name: str) -> List:
            if not with_entity_col:
                return df.iloc[:, column_index].to_list()
            return df[df[entity_col] == entity_name].iloc[:, column_index].to_list()

        # get signals
        col_names = list(set(col_names))
        existing_signal_names = self.get_signal_names(**kwargs)
        column_signals = {
            cname: _get_signal_info(cname, existing_signal_names, signals=signals)
            for cname in col_names
            if not _is_index_column(cname)
        }

        # collect signals data
        for _entity_name, d in col_data.items():
            # make sure that entity column is string
            entity_name = str(_entity_name)
            # collect signals data
            for col in d:
                # column name
                column_name = col[0]
                # column index
                column_index = col[1]
                if column_name in column_signals and column_signals[column_name]:

                    signal = column_signals[column_name]
                    signal_name = signal["Signal"]
                    signal_unit_name = signal["Unit"]
                    signal_type = signal["SignalType"]

                    # static signal
                    if signal_type in {SignalType.Static.name, SignalType.String.name}:
                        dtype = "Numeric" if (signal_type == "Static") else "String"
                        static_data = _get_column_data(column_index, entity_name)
                        if static_data and len(static_data) > 0:
                            value = (
                                static_data[0]
                                if (signal_type == "Static")
                                else static_data[0]
                            )
                            data_to_save[signal_type].append(
                                {
                                    "Entity": entity_name,
                                    "Signal": signal_name,
                                    "Unit": signal_unit_name,
                                    "Data": self.get_json_valid_value(
                                        value, dtype=dtype, **kwargs
                                    ),
                                }
                            )
                    # time signal
                    elif signal_type in (
                        SignalType.TimeDependent.name,
                        SignalType.StringTimeDependent.name,
                    ):
                        dtype = (
                            "Numeric" if (signal_type == "TimeDependent") else "String"
                        )
                        data_to_save[signal_type].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": [
                                    {
                                        "Date": self.get_json_valid_value(
                                            dvalue, dtype="Time", **kwargs
                                        ),
                                        "Value": self.get_json_valid_value(
                                            value, dtype=dtype, **kwargs
                                        ),
                                    }
                                    for dvalue, value in zip(
                                        _get_column_data(date_index, entity_name),
                                        _get_column_data(column_index, entity_name),
                                    )
                                ],
                            }
                        )
                    # depth signal
                    elif signal_type in (
                        SignalType.DepthDependent.name,
                        SignalType.StringDepthDependent.name,
                    ):
                        dtype = (
                            "Numeric" if (signal_type == "DepthDependent") else "String"
                        )
                        data_to_save[signal_type].append(
                            {
                                "Entity": entity_name,
                                "Signal": signal_name,
                                "Unit": signal_unit_name,
                                "Data": [
                                    {
                                        "Depth": self.get_json_valid_value(
                                            dvalue, dtype="Numeric", **kwargs
                                        ),
                                        "Value": self.get_json_valid_value(
                                            value, dtype=dtype, **kwargs
                                        ),
                                    }
                                    for dvalue, value in zip(
                                        _get_column_data(depth_index, entity_name),
                                        _get_column_data(column_index, entity_name),
                                    )
                                ],
                            }
                        )
                    else:
                        raise ValueError(
                            f"PetroVisor::get_signal_data_from_dataframe(): "
                            f"signal type: '{signal_type}' is not supported yet."
                        )
        return data_to_save

    # convert dataframe from wide to long format
    def convert_dataframe_from_wide_to_long(
        self, df: pd.DataFrame, inplace: bool = False, **kwargs
    ):
        """
        Convert DataFrame from wide to long format.
        Wide format assumes column names as '{entity_name} : {column_name}'
        Long format assumes that DataFrame has 'Entity' column.

        Parameters
        ----------
        df : DataFrame
            DataFrame
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        """

        # standard columns
        entity_col = self.get_entity_column_name()

        # define column indices and entities
        column_indices = []
        entity_columns = []
        for col in df.columns:
            c = col.split(" : ")
            if len(c) > 1:
                entity_columns.append((c[0], c[1]))
            else:
                column_indices.append(col)
        if not entity_columns:
            return df

        # set indices
        df_long, default_index_col = DataFrameMixinHelper.set_dataframe_index(
            df, column_indices, inplace=inplace, add_default_index=True, **kwargs
        )
        # assign new column names
        df_long.columns = pd.MultiIndex.from_tuples(
            entity_columns, names=[entity_col, None]
        )
        # stack entity column and reset index
        return df_long.stack(0).reset_index().drop(columns=default_index_col)

    # convert dataframe from long to wide format
    def convert_dataframe_from_long_to_wide(
        self,
        df: pd.DataFrame,
        indices: Optional[Union[str, List[str]]] = None,
        inplace: bool = False,
        **kwargs,
    ):
        """
        Convert DataFrame from long to wide format.
        Wide format assumes column names as '{entity_name} : {column_name}'
        Long format assumes that DataFrame has 'Entity' column.

        Parameters
        ----------
        df : DataFrame
            DataFrame
        indices : str | list, default None
            Indices columns
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        """

        # check whether entity column is present
        entity_col = self.get_entity_column_name()
        if entity_col not in df.columns:
            return df

        # define column indices
        date_col = self.get_date_column_name()
        depth_col = self.get_depth_column_name()
        alias_col = self.get_alias_column_name()
        column_indices = (
            copy.deepcopy(indices)
            if indices
            else [date_col, depth_col, alias_col, entity_col]
        )
        if entity_col not in column_indices:
            column_indices.append(entity_col)

        # set indices
        df_wide, default_index_col = DataFrameMixinHelper.set_dataframe_index(
            df, column_indices, inplace=inplace, add_default_index=True, **kwargs
        )
        # unstack 'Entity' column
        df_wide = (
            df_wide.unstack(entity_col)
            .reset_index()
            .sort_index(axis=1)
            .drop(columns=default_index_col)
        )
        # rename column as '{entity_name} : {column_name}'
        df_wide.columns = [
            f"{c[1]} : {c[0]}" if c[1] else c[0] for c in df_wide.columns
        ]
        return df_wide

    # get valid json value
    def get_json_valid_value(
        self, value: Any, dtype: Union[str, SignalType] = "unknown", **kwargs
    ) -> Any:
        """
        Convert value to json accepted format

        Parameters
        ----------
        value : Any
            Value
        dtype : str | SignalType, default 'unknown'
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        is_null = pd.isnull(value)
        if not isinstance(dtype, str):
            dtype = self.get_signal_data_type_name(dtype, **kwargs)
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            # nan_value = pd.NA
            # nan_value = np.nan
            # nan_value = float('NaN')
            nan_value = "NaN"
            return (
                nan_value
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        elif dtype in {"time", "datetime64[ns]"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else self.datetime_to_string(value, **kwargs)
            )
        elif dtype in {"string", "str"}:
            return "" if is_null else value
        elif dtype in {"bool", "boolean"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        elif dtype in {"unknown", "object"}:
            return (
                None
                if is_null or (isinstance(value, str) and not value.strip())
                else value
            )
        return None if is_null else value

    # assign DataFrame column to corresponding types
    def assign_dataframe_column_types(
        self,
        df: pd.DataFrame,
        columns_dtype: Dict,
        default_dtype: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Convert DataFrame columns to column types

        Parameters
        ----------
        df : DataFrame
            Table
        columns_dtype : dict
            Dictionary {"column name" : "type"}
        default_dtype : str, default None
            Default type to use: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        columns = df.columns
        for c in columns:
            if c in columns_dtype:
                df[c] = self.column_to_dtype(df, c, columns_dtype[c], **kwargs)
            elif default_dtype:
                df[c] = self.column_to_dtype(df, c, default_dtype, **kwargs)
        return df

    # get DataFrame data type name
    def convert_to_dtype_name(self, dtype: str, **kwargs) -> str:
        """
        Convert type name to DataFrame accepted type name

        Parameters
        ----------
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            return "float64"
        elif dtype in {"time", "datetime64[ns]"}:
            return "datetime64[ns]"
        elif dtype in {"string"}:
            return "string"
        elif dtype in {"boolean", "bool"}:
            return "bool"
        elif dtype in {"unknown", "object"}:
            return "object"
        return "object"

    # convert DataFrame column to bool
    def column_to_dtype(
        self, df: pd.DataFrame, column: str, dtype: str, **kwargs
    ) -> pd.DataFrame:
        """
        Convert DataFrame column to specified type

        Parameters
        ----------
        df : DataFrame
            Table
        column: str
            Column name
        dtype : str
            data type: 'numeric' or 'float64', 'time', 'bool' or 'boolean', 'unknown' or 'object'
        """
        dtype = dtype.lower()
        if dtype in {"numeric", "float64"}:
            df[column] = self.column_to_numeric(df, column, **kwargs)
        elif dtype in {"time", "datetime64[ns]"}:
            df[column] = self.column_to_datetime(df, column, **kwargs)
        elif dtype in {"string", "str"}:
            df[column] = self.column_to_string(df, column, **kwargs)
        elif dtype in {"bool", "boolean"}:
            df[column] = self.column_to_bool(df, column, **kwargs)
        elif dtype in {"unknown", "object"}:
            df[column] = self.column_to_object(df, column, **kwargs)
        return df[column]

    # convert DataFrame column to 'object'
    def column_to_object(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'object' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("object")

    # convert DataFrame column to 'bool'
    def column_to_bool(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'bool' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("bool")

    # convert DataFrame column to 'string'
    def column_to_string(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'string' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        return df[column].astype("string")

    # convert DataFrame column to 'numeric'
    def column_to_numeric(self, df: pd.DataFrame, column: str, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'numeric' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('float64')
        return pd.to_numeric(df[column])

    # convert DataFrame column to 'datetime'
    def column_to_datetime(self, df: pd.DataFrame, column, **kwargs) -> pd.Series:
        """
        Convert DataFrame column to 'datetime' type

        Parameters
        ----------
        df : DataFrame
            Table
        column : str
            Column name
        """
        # return df[column].astype('datetime64[ns]')
        # return pd.to_datetime(df[column], infer_datetime_format=False)
        # return pd.to_datetime(df[column], infer_datetime_format=True)
        # return pd.to_datetime(df[column], format=format)
        # return pd.to_datetime(df[column])
        datetime_args = {
            arg: kwargs[arg]
            for arg in [
                "errors",
                "dayfirst",
                "yearfirst",
                "utc",
                "format",
                "exact",
                "unit",
                "infer_datetime_format",
                "origin",
                "cache",
            ]
            if (arg in kwargs)
        }
        if datetime_args:
            return pd.to_datetime(df[column], **datetime_args)
        return pd.to_datetime(df[column])

    # convert datetime to string
    def datetime_to_string(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%dT%H:%M:%S.%f",
        **kwargs,
    ) -> str:
        """
        Convert datetime object to string representation

        Parameters
        ----------
        d : datetime
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """

        def parse_date(date_string: str, desired_format: str) -> str:
            formats_to_try = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                # other formats might be added
            ]
            for format_str in formats_to_try:
                try:
                    date_object = datetime.strptime(date_string, format_str)
                    return date_object.strftime(desired_format)
                except ValueError:
                    pass
            return str(date_string).strip()

        return (
            ""
            if pd.isnull(d)
            else (
                d.strftime(format) if isinstance(d, datetime) else parse_date(d, format)
            )
        )

    # convert string to datetime
    def string_to_datetime(
        self,
        d: Union[datetime, str],
        format: Optional[str] = "%Y-%m-%d %H:%M:%S",
        **kwargs,
    ) -> datetime:
        """
        Convert date from string representation to datetime object

        Parameters
        ----------
        d : str
            Date
        format : str, default '%Y-%m-%dT%H:%M:%S.%f'
            Time format
        """
        return datetime.strptime(d, format)

    # get column name without unit
    def get_column_name_without_unit(self, column_name: str, **kwargs) -> str:
        """
        Get column name without unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        cname = column_name.split("[")[0].strip()
        return cname

    # get column unit
    def get_column_unit(self, column_name: str, **kwargs) -> str:
        """
        Get column unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        column_name = column_name.strip()
        cunit = re.findall(r"\[(.*?)\]", column_name)
        if cunit and len(cunit) > 0:
            return cunit[0]
        return ""

    # get column name and unit
    def get_column_name_and_unit(self, column_name: str, **kwargs) -> Tuple[str, str]:
        """
        Get column name and unit from column name

        Parameters
        ----------
        column_name : str
            Column name
        """
        column_name = column_name.strip()
        cname = self.get_column_name_without_unit(column_name, **kwargs)
        cunit = self.get_column_unit(column_name, **kwargs)
        return cname, cunit

    # get 'Entity' column name
    def get_entity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Entity' column name used in return tables from api calls
        """
        return "Entity"

    # get 'Alias' column name
    def get_alias_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Alias' column name used in return tables from api calls
        """
        return "Alias"

    # get 'EntityType' column name
    def get_entity_type_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Type' column name used in return tables from api calls
        """
        return "Type"

    # get 'Opportunity' column name
    def get_opportunity_column_name(self, **kwargs) -> str:
        """
        Get predefined 'IsOpportunity' column name used in return tables from api calls
        """
        return "IsOpportunity"

    # get 'Date' column name
    def get_date_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Date' column name used in return tables from api calls
        """
        return "Date"

    # get 'Time' column name
    def get_time_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Time' column name used in return tables from api calls
        """
        return "Time"

    # get 'Depth' column name
    def get_depth_column_name(self, **kwargs) -> str:
        """
        Get predefined 'Depth' column name used in return tables from api calls
        """
        return "Depth"

    # get signal data type name
    def get_signal_data_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str:
        """
        Get data type name for corresponding signal type

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, str):
            signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        elif not isinstance(signal_type, SignalType):
            raise ValueError(
                f"PetroVisor::get_signal_data_type_name(): "
                f"unknown 'signal_type'! "
                f"Should be one of {[t.name for t in SignalType]} or {SignalType.__name__} enum."
            )
        if signal_type in {
            SignalType.Static,
            SignalType.TimeDependent,
            SignalType.DepthDependent,
            SignalType.PVT,
        }:
            return "numeric"
        elif signal_type in {
            SignalType.String,
            SignalType.StringTimeDependent,
            SignalType.StringDepthDependent,
        }:
            return "string"
        raise ValueError(
            f"PetroVisor::get_signal_data_type_name(): "
            f"'{signal_type}' is not supported yet."
        )

    # get signal range name
    def get_signal_range_type_name(
        self, signal_type: Union[str, SignalType], **kwargs
    ) -> str:
        """
        Get data range type name for corresponding signal type

        Parameters
        ----------
        signal_type : str, SignalType
            Signal type
        """
        if isinstance(signal_type, str):
            signal_type = self.get_signal_type_enum(signal_type, **kwargs)
        elif not isinstance(signal_type, SignalType):
            raise ValueError(
                f"PetroVisor::get_signal_range_type_name(): "
                f"unknown 'signal_type'! "
                f"Should be one of {[t.name for t in SignalType]} or {SignalType.__name__} enum."
            )
        if signal_type in {SignalType.TimeDependent, SignalType.StringTimeDependent}:
            return "time"
        elif signal_type in {
            SignalType.DepthDependent,
            SignalType.StringDepthDependent,
        }:
            return "numeric"
        elif signal_type in {SignalType.Static, SignalType.String, SignalType.PVT}:
            return ""
        raise ValueError(
            f"PetroVisor::get_signal_range_type_name(): "
            f"'{signal_type}' is not supported yet."
        )

    # convert list to dictionary
    def list_to_dict(self, x, num_cols, **kwargs):
        if num_cols == 0:
            return {
                self.get_json_valid_value(
                    idx, "numeric", **kwargs
                ): self.get_json_valid_value(row, "numeric", **kwargs)
                for idx, row in enumerate(x)
            }
        elif num_cols == 1:
            return {
                self.get_json_valid_value(
                    idx, "numeric", **kwargs
                ): self.get_json_valid_value(row[0], "numeric", **kwargs)
                for idx, row in enumerate(x)
            }
        elif num_cols > 1:
            return {
                self.get_json_valid_value(
                    row[0], "numeric", **kwargs
                ): self.get_json_valid_value(row[1], "numeric", **kwargs)
                for row in x
            }


# DataFrame mixin helper
class DataFrameMixinHelper:

    # set DataFrame indices
    @staticmethod
    def set_dataframe_index(
        df: pd.DataFrame,
        indices: List[str],
        inplace: bool = False,
        add_default_index: bool = False,
        default_index_name: str = "index",
        **kwargs,
    ):
        """
        Set DataFrame index

        Parameters
        ----------
        df : DataFrame
            DataFrame
        indices : list
            Columns to use as indices
        inplace : bool, default False
            Whether to modify DataFrame or to work with a copy
        add_default_index : bool, default False
            Whether to add default index column
        default_index_name : str, default 'index'
            Default index name

        Returns
        -------
        Tuple (DataFrame, default_index_column)
        """
        # define working DataFrame
        df_with_index = df if inplace else df.copy()
        # get column indices
        idx = [item for item in indices if item in df.columns]
        # add default index
        index_col = ""
        if add_default_index:
            # get index name which does not match any column name
            def get_default_index_name(df: pd.DataFrame):
                index_name = default_index_name
                i = 0
                while index_name in df.columns:
                    index_name = f"{default_index_name}_{i}"
                    i += 1
                return index_name

            index_col = get_default_index_name(df)
            df_with_index[index_col] = df_with_index.index
            idx.insert(0, index_col)
        # set indices
        df_with_index = df_with_index.set_index(idx)
        return df_with_index, index_col

    # create DataFrame from list
    @staticmethod
    def create_dataframe_from_list(data: List[str], **kwargs) -> Optional[pd.DataFrame]:
        """
        Create DataFrame from list of tabulated string

        Parameters
        ----------
        data : list
            List of tabulated strings
        """
        if len(data) < 1:
            return None
        return pd.read_csv(io.StringIO("\n".join(data)), delimiter="\t")

    # remove entity name from column names
    @staticmethod
    def remove_entities_from_columns(columns: Iterable[str]) -> List[str]:
        """
        Remove entity name from column names

        Parameters
        ----------
        columns : list
            Column names
        """
        return [
            c[1] if len(c) > 1 else c[0] for c in (col.split(" : ") for col in columns)
        ]

    # extract entity name from column names
    @staticmethod
    def get_entities_from_columns(columns: Iterable[str]) -> List[str]:
        """
        Extract entity name from column names

        Parameters
        ----------
        columns : list
            Column names
        """
        return [
            c[0] if len(c) > 1 else "" for c in (col.split(" : ") for col in columns)
        ]

    # get list of unique non-empty names
    @staticmethod
    def get_unique_non_empty_names(x: List[str]) -> List[str]:
        """
        get list of unique non-empty names

        Parameters
        ----------
        x : list
            List of names
        """
        return list(set([e for e in x if e]))
