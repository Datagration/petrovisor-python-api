from petrovisor import PetroVisor
import pandas as pd
import numpy as np


def test_signals_by_entity(api: PetroVisor):
    """
    Test retrieving signals by entity type
    """
    # add new entity
    entity_name = (
        r"_entity with special characters %*,$&^§()#//=2!~*'"  # except '?', ';'
    )
    api.add_item(
        "Entity",
        {
            "Name": entity_name,
            "EntityTypeName": "Well",
            "Alias": "",
            "IsOpportunity": False,
        },
    )
    # rename entity
    new_entity_name = entity_name.replace("_entity", "_renamed entity")
    # pv_api.rename_entity(old_name=entity_name, new_name=new_entity_name)
    # delete entity
    # pv_api.delete_entity(new_entity_name)
    # add signal
    signal_name = "Time Signal"
    signal_unit = " "
    max_length = 29
    short_signal_name = (
        signal_name[:max_length] if len(signal_name) > max_length else signal_name
    )
    api.add_item(
        "Signal",
        {
            "Name": signal_name,
            "ShortName": short_signal_name,
            "SignalType": "TimeDependent",
            "MeasurementName": "Dimensionless",
            "StorageUnitName": signal_unit,
            "AggregationType": "Sum",
            "ContainerAggregationType": "Sum",
        },
    )
    # add signal data
    num_rows = 5
    signal_col = f"{signal_name} [{signal_unit}]"
    df = pd.DataFrame(
        {
            "Entity": np.repeat(entity_name, num_rows),
            "Date": pd.date_range("2023-11-29", periods=num_rows, freq="D"),
            signal_col: np.random.rand(num_rows),
        }
    )
    api.save_table_data(df)
    # get signals by entity
    entity_signals = api.get_signals(entity=entity_name, signal_type="time")
    assert signal_name in [s["Name"] for s in entity_signals]
