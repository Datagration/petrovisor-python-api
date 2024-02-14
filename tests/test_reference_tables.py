from petrovisor import PetroVisor
import pandas as pd
import numpy as np


def test_ref_tables(pv_api: PetroVisor):

    # create dataframe
    num_rows = int(10)
    columns = list('ABCDEF')
    df = pd.DataFrame(np.random.uniform(0, 1, size=(num_rows, len(columns))), columns=columns)

    df['Entity'] = None
    df.loc[:num_rows // 2, 'Entity'] = 'Well 001'
    df['Time'] = None
    df['Key'] = [str(i) for i in range(0, len(df))]

    df = df[['Entity', 'Time', 'Key', *columns]]
    df['Key'] = df['Key'].values.astype(str)

    name = 'PyTest New RefTable'

    # delete table if exists
    response = pv_api.delete_ref_table(name)
    assert response.status_code == 200

    # add new reference table
    response = pv_api.add_ref_table(name, df, description='Testing API from Python')
    assert response.status_code == 200

    # add data to already existing table
    response = pv_api.add_ref_table(name, df, description='Testing API from Python')
    assert response.status_code == 200

    # check that table was created
    ref_table_info = pv_api.get_ref_table_data_info(name)
    assert ref_table_info

    # save data and overwrite existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be overwritten
    response = pv_api.save_ref_table_data(name, df, skip_existing_data=False)
    assert response.status_code == 200

    # save data but keep existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be not overwritten
    response = pv_api.save_ref_table_data(name, df, skip_existing_data=True)
    assert response.status_code == 200

    # load table
    df = pv_api.load_ref_table_data(name)
    assert df.shape[0] == num_rows

    # delete reference table
    pv_api.delete_ref_table_data(name)
    response = pv_api.delete_ref_table(name)
    assert response.status_code == 200
