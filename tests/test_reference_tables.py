from petrovisor import PetroVisor, ItemType
import pandas as pd
import numpy as np
import uuid


def test_ref_tables(api: PetroVisor):

    # create entity
    entity_name = "Well 001"
    api.add_item(
        "Entity",
        {
            "Name": entity_name,
            "EntityTypeName": "Well",
            "Alias": "",
            "IsOpportunity": False,
        },
    )

    # create dataframe
    num_rows = int(10)
    columns = list("ABCDEF")
    df = pd.DataFrame(
        np.random.uniform(0, 1, size=(num_rows, len(columns))), columns=columns
    )

    df["Entity"] = None
    df.loc[: num_rows // 2, "Entity"] = entity_name
    df["Time"] = None
    df["Key"] = [str(i) for i in range(0, len(df))]

    df = df[["Entity", "Time", "Key", *columns]]
    df["Key"] = df["Key"].values.astype(str)

    # create unique name to avoid interference
    name = str(uuid.uuid4())
    while api.item_exists(ItemType.RefTable, name):
        name = str(uuid.uuid4())

    # add new reference table
    api.add_ref_table(name, df, description="Testing API from Python")

    # add data to already existing table
    api.add_ref_table(name, df, description="Testing API from Python")

    # check that table was created
    assert api.get_ref_table_data_info(name)

    # save data and overwrite existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be overwritten
    api.save_ref_table_data(name, df, skip_existing_data=False)

    # save data but keep existing data
    # meaning that rows with the same 'Entity', 'Timestamp/Date/Time', 'Key' will be not overwritten
    api.save_ref_table_data(name, df, skip_existing_data=True)

    # load table
    df = api.load_ref_table_data(name)
    assert df.shape[0] == num_rows

    # delete reference table data
    api.delete_ref_table_data(name)

    # delete reference table
    api.delete_ref_table(name)
