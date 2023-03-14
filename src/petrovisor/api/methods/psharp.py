from typing import (
    Optional,
    Union,
    List,
    Dict,
)

import pandas as pd

from petrovisor.api.utils.helper import ApiHelper

from petrovisor.api.protocols.protocols import SupportsRequests
from petrovisor.api.protocols.protocols import SupportsSignalsRequests
from petrovisor.api.protocols.protocols import SupportsDataFrames
from petrovisor.api.protocols.protocols import SupportsPsharpRequests


# P# API class
class PsharpMixin(SupportsDataFrames, SupportsPsharpRequests, SupportsSignalsRequests, SupportsRequests):
    """
    P# API class
    """

    # get P# script names
    def get_psharp_script_names(self, **kwargs) -> List[str]:
        """
        Get P# script names
        """
        return self.get(f'Configuration/PSharpFunctions', **kwargs)

    # get P# script
    def get_psharp_script(self, name: str, **kwargs) -> Dict:
        """
        Get P# script

        Parameters
        ----------
        name : str
            P# script name
        """
        return self.get(f'PSharpScripts/{name}', **kwargs)

    # get P# script content
    def get_psharp_script_content(self, script: Union[str, Dict], **kwargs) -> str:
        """
        Get P# script content

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        """
        # get P# script content
        if isinstance(script, str):
            script_content = script
            script = self.get_psharp_script(script, **kwargs)
        else:
            script_content = None
        if script is None and script_content:
            pass
        elif 'Content' in script:
            script_content = script['Content']
        else:
            raise RuntimeError(
                f"PetroVisor::get_psharp_script_content(): Couldn't get content of P# script '{script}'.")
        return script_content

    # parse P# script
    def parse_psharp_script(self,
                            script: Union[str, Dict],
                            options: Optional[Dict] = None,
                            **kwargs) -> Dict:
        """
        Parse P# script

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        # get P# script content
        script_content = self.get_psharp_script_content(script, **kwargs)
        # define options
        if not options:
            options = {
                'TreatScriptContentAsScriptName': False,
                'NoMissedObjects': True
            }
            options = ApiHelper.update_dict(options, **kwargs)
        return self.post(f'Parsing/Parsed', data={'ScriptContent': script_content, 'Options': options}, **kwargs)

    # get P# script table names
    def get_psharp_script_table_names(self,
                                      script: Union[str, Dict],
                                      options: Optional[Dict] = None,
                                      **kwargs) -> List[str]:
        """
        Get P# script table names

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        if isinstance(script, str) or 'TableCalculations' not in script:
            psharp_script_parsed = self.parse_psharp_script(script, options=options, **kwargs)
        else:
            psharp_script_parsed = script
        if 'TableCalculations' in psharp_script_parsed:
            table_names = [t['Name'] for t in psharp_script_parsed['TableCalculations']]
        else:
            table_names = []
        return table_names

    # get P# script tables, columns and signals
    def get_psharp_script_columns_and_signals(self,
                                              script: Union[str, Dict],
                                              options: Optional[Dict] = None,
                                              **kwargs) -> Dict:
        """
        Get P# script columns and signals

        Parameters
        ----------
        script : str, dict
            P# script object or P# script name
        options : dict, default None
            P# script parse options
        """
        if isinstance(script, str) or 'TableCalculations' not in script:
            psharp_script_parsed = self.parse_psharp_script(script, options=options, **kwargs)
        else:
            psharp_script_parsed = script
        # get psharp script signals
        table_signals = {}
        if 'TableCalculations' in psharp_script_parsed:
            for t in psharp_script_parsed['TableCalculations']:
                table_name = t['Name']
                table_columns = t['Columns']
                table_signals[table_name] = {}
                for col in table_columns:
                    col_name = col['Name']
                    unit_name = col['Unit']['Name']
                    full_column_name = col_name + ' ' + '[' + unit_name + ']'
                    col_formula = col['Formula']
                    col_signal = col_formula.split('"')
                    signal_name = col_signal[1] if len(col_signal) > 1 else ''
                    signal_unit_name = col_signal[3] if len(col_signal) > 3 else ' '
                    # table_signals[table_name][full_column_name] = {'Signal': signal_name, 'Unit': signal_unit_name}
                    table_signals[table_name][col_name] = {
                        'Unit': unit_name,
                        'Signal': signal_name,
                        'SignalUnit': signal_unit_name
                    }
        return table_signals

    # load P# table
    def load_psharp_table(self,
                          script_name: str,
                          table: Optional[str] = None,
                          with_entity_column: bool = True,
                          groupby_entity: bool = False,
                          load_full_table_info: bool = False,
                          **kwargs) -> Optional[Union[pd.DataFrame, List[pd.DataFrame], Dict[str, pd.DataFrame]]]:
        """
        Load P# table and return DataFrame

        Parameters
        ----------
        script_name : str
            P# script name
        table : str, default None
            Table name or id. 0 is first table, -1 is last table.
            If None, all tables will be loaded and dictionary with table name as key will be returned
        with_entity_column : bool, default True
            Load table with 'Entity' column, otherwise columns will be named as "EntityName : ColumnName"
        groupby_entity : bool, default False
            Return dictionary of DataFrames grouped by entity name
        load_full_table_info : bool, default False
            Load table using api call with full table content
        """

        # get table id, table name, and existing table names
        if table is None or not isinstance(table, str):
            # get table id
            table_id = None
            if table is not None:
                try:
                    table_id = int(table)
                except BaseException:
                    raise RuntimeError(
                        f"PetroVisor::load_table_from_psharp(): "
                        f"{table} should be either 'string'(table name), 'integer'(table id) or 'None'(all tables) !")
            # get table name
            if with_entity_column or table_id != 0:
                # get table names
                table_names = self.get_psharp_script_table_names(script_name, **kwargs)
                # get table name
                if table_id is not None:
                    num_tables = len(table_names)
                    # if( table_id >= num_tables ):
                    #     table_id = num_tables - 1
                    # elif( table_id < 0 and (num_tables + table_id) < 0 ):
                    #     table_id = 0
                    if table_id >= num_tables or (num_tables + table_id) < 0:
                        return None
                    table_name = table_names[table_id]
                else:
                    table_name = None
            else:
                table_name = ''
                table_names = []
        else:
            table_id = None
            table_name = table if isinstance(table, str) else ''
            table_names = []

        # read single table from P# script
        if table_name or table_id == 0:
            psharp_table = None
            if with_entity_column and table_name:
                psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsBITable',
                                        query={'Table': table_name}, **kwargs)
            elif not with_entity_column and (table_name or table_id == 0):
                if table_id == 0:
                    psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsTable', **kwargs)
                else:
                    psharp_table = self.get(f'PSharpScripts/{script_name}/ExecuteAsTable',
                                            query={'Table': table_name}, **kwargs)
            if psharp_table is not None:
                return self.convert_psharp_table_to_dataframe(psharp_table,
                                                              with_entity_column=with_entity_column,
                                                              groupby_entity=groupby_entity,
                                                              **kwargs)
        # read multiple tables from P# script
        else:
            # if with_entity_column:
            #     psharp_tables = [self.get(f'PSharpScripts/{script_name}/ExecuteAsBITable',
            #                               query={'Table': table_name}, **kwargs)
            #                      for table_name in table_names]
            # else:
            #     psharp_tables = [self.get(f'PSharpScripts/{script_name}/ExecuteAsTable',
            #                               query={'Table': table_name}, **kwargs)
            #                      for table_name in table_names]
            script_content = self.get_psharp_script_content(script_name, **kwargs)
            if load_full_table_info:
                psharp_tables = self.post(f'PSharpScripts/ExecuteScript',
                                          data={'ScriptContent': script_content}, **kwargs)
            else:
                psharp_tables = self.post(f'PSharpScripts/Execute',
                                          data={'ScriptContent': script_content}, **kwargs)
            # convert tables
            if psharp_tables is not None:
                return {
                    table_name: self.convert_psharp_table_to_dataframe(t,
                                                                       groupby_entity=groupby_entity,
                                                                       **kwargs)
                    for table_name, t in zip(table_names, psharp_tables)
                }
        return None

    # save data from table to PetroVisor
    def save_table_data(self,
                        df: pd.DataFrame,
                        delimiter: str = '\t',
                        signals: Optional[Dict] = None,
                        chunksize: int = 10000,
                        only_existing_entities: bool = True,
                        entity_type: str = '',
                        entities: Optional[Dict] = None,
                        **kwargs) -> None:
        """
        Save DataFrame data to corresponding signals

        Parameters
        ----------
        df : DataFrame, str
            Table or filename
        delimiter : str, default '\t'
            Delimiter used while reading table from file
        signals : dict, default None
            Dictionary map from 'table column name' to 'workspace signal name'
        chunksize : int, default 10000
            Save data by splitting it into several chunks of specified size and performing separate requests
        entities : dict, default None
            Dictionary map from 'table entity name' to 'workspace entity name'
        only_existing_entities : bool, default True
            Save data only if entity exist in workspace
        entity_type : str, default None
            Save data only for specified entity type
        """
        # read table
        if isinstance(df, str):
            ext = ApiHelper.get_file_extension(df, **kwargs)
            if ext.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(df)
            else:  # elif(ext.lower() in ['.csv']):
                df = pd.read_csv(df, delimiter=delimiter)
        if df is not None:
            if chunksize and (df.shape[0] > chunksize):
                for start in range(0, df.shape[0], chunksize):
                    end = min(start + chunksize, df.shape[0])
                    self.save_table_data(df[start:end], delimiter=delimiter, signals=signals, chunksize=chunksize,
                                         only_existing_entities=only_existing_entities, entity_type=entity_type,
                                         entities=entities, **kwargs)
                return None
            # get PetroVisor data from DataFrame
            data_to_save = self.get_signal_data_from_dataframe(df, signals=signals,
                                                               only_existing_entities=only_existing_entities,
                                                               entity_type=entity_type, entities=entities, **kwargs)
            # save data
            for data_type, data in data_to_save.items():
                if data:
                    self.post(f'{self.get_signal_type_route(data_type)}/Save', data=data, **kwargs)
        return None
