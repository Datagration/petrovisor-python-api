import numpy as np
import pandas as pd
from petrovisor import PetroVisor
import uuid


def test_files(api: PetroVisor):
    # Dictionary to json file tests
    d = {
        "a": 1,
        "b": "foo",
        "c": [1, 2, 3],
        "d": {
            "x": [
                "a",
                "b",
                "c",
            ],
            "y": [1, 2, 3],
        },
    }

    json_file_name = str(uuid.uuid4()) + ".json"
    api.upload_object(d, json_file_name, binary=False)

    d_loaded1 = api.get_file(json_file_name, format="json")
    assert d == d_loaded1

    d_loaded2 = api.get_object(json_file_name, binary=False)
    assert d == d_loaded2

    api.delete_file(json_file_name)

    # DataFrame tests
    df = pd.DataFrame(
        np.random.uniform(0, 1, size=(int(1e3), 6)), columns=list("ABCDEF")
    )

    # DataFrame to csv tests
    dataframe_csv_file_name = str(uuid.uuid4()) + ".csv"
    api.upload_object(df, dataframe_csv_file_name)

    df_csv_loaded = api.get_object(dataframe_csv_file_name)
    # assert df.equals(df_csv_loaded)
    assert df.shape == df_csv_loaded.shape

    api.delete_file(dataframe_csv_file_name)

    # DataFrame to excel test
    dataframe_excel_file_name = str(uuid.uuid4()) + ".xlsx"
    api.upload_object(df, dataframe_excel_file_name)

    df_excel_loaded = api.get_object(dataframe_excel_file_name)
    # assert df.equals(df_excel_loaded)
    assert df.shape == df_excel_loaded.shape

    api.delete_file(dataframe_excel_file_name)

    # DataFrame to pickle test
    dataframe_pickle_file_name = str(uuid.uuid4()) + ".pkl"
    api.upload_object(df, dataframe_pickle_file_name)

    df_pickle_loaded = api.get_object(dataframe_pickle_file_name)
    assert df.equals(df_pickle_loaded)

    api.delete_file(dataframe_pickle_file_name)
