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
    num_rows = int(100)
    columns = list("ABCDEF")
    df = pd.DataFrame(
        np.random.uniform(0, 1, size=(num_rows, len(columns))), columns=columns
    )

    df["Entity"] = None
    df.loc[: num_rows // 2, "Entity"] = entity_name
    df["Key"] = [i for i in range(0, len(df))]

    # Generate time series data with some gaps
    start_date = datetime(2025, 1, 1)  # Starting from January 1st, 2025
    time_interval = timedelta(hours=1)  # 1-hour interval

    # Create base time series
    time_series = [start_date + i * time_interval for i in range(num_rows)]

    # Introduce random gaps (None values) in about 10% of the data
    time_series = np.array(time_series, dtype=object)
    gap_indices = np.arange(
        9, num_rows, 10
    )  # Creates gaps at every 10th position (0-based)
    time_series[gap_indices] = None

    # Assign the time series to the DataFrame
    df["Time"] = time_series

    # reorder columns and rename
    df = df[["Entity", "Time", "Key", *columns]]
    df = df.rename(columns={"F": "F [cm]", "E": "E [ft]"})

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
    df = api.load_ref_table_data(
        name,
        date_start=datetime(2025, 1, 1),
        date_end=datetime(2025, 1, 2),
        columns=["F [cm]", "E [cm]"],
        top=10,
        all_cols=False,
        where="[Entity] = 'Well 001' AND [Key] >= '20'",
    )
    assert df.shape[0] == num_rows

    # delete reference table data
    api.delete_ref_table_data(
        name,
        entities=["Well 001", None],
        date_start=datetime(2025, 1, 1),
        date_end=datetime(2025, 1, 10),
        drop_null_dates=True,
        where="[Key] > '20'",
    )

    # delete reference table
    api.delete_ref_table(name)
