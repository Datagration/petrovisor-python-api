from petrovisor import PetroVisor
import pandas as pd
import numpy as np


def test_ref_tables(pv_api: PetroVisor):

    # create entity
    entity_name = "Well 001"
    pv_api.add_item('Entity', {
        'Name': entity_name,
        'EntityTypeName': 'Well',
        'Alias': '',
        'IsOpportunity': False,
    })

    # create dataframe
    num_rows = int(10)
    columns = list('ABCDEF')
    df = pd.DataFrame(np.random.uniform(0, 1, size=(num_rows, len(columns))), columns=columns)

    df['Entity'] = None
    df.loc[:num_rows // 2, 'Entity'] = entity_name
    df['Time'] = None
    df['Key'] = [str(i) for i in range(0, len(df))]

    df = df[['Entity', 'Time', 'Key', *columns]]
    df['Key'] = df['Key'].values.astype(str)

    name = 'PyTest New RefTable'

    # delete table if exists
    pv_api.delete_ref_table(name)

    # add new reference table
    pv_api.add_ref_table(name, df, description='Testing API from Python')

    # add data to already existing table
    pv_api.add_ref_table(name, df, description='Testing API from Python')

    # check that table was created
    ref_table_info = pv_api.get_ref_table_data_info(name)
    assert ref_table_info

    # save data and overwrite existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be overwritten
    pv_api.save_ref_table_data(name, df, skip_existing_data=False)

    # save data but keep existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be not overwritten
    pv_api.save_ref_table_data(name, df, skip_existing_data=True)

    # load table
    df = pv_api.load_ref_table_data(name)
    assert df.shape[0] == num_rows

    # delete reference table
    pv_api.delete_ref_table_data(name)
    pv_api.delete_ref_table(name)
