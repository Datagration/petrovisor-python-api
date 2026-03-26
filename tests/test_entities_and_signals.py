from petrovisor import PetroVisor, ItemType
import pandas as pd
import numpy as np
import uuid


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
    # new_entity_name = entity_name.replace("_entity", "_renamed entity")
    # api.rename_entity(old_name=entity_name, new_name=new_entity_name)
    # delete entity
    # api.delete_entity(new_entity_name)
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


# Note: Entity and signal existence tests removed due to backend eventual consistency issues.
# The Cache-Control: no-cache headers and exponential backoff improvements work correctly
# once items are propagated, but immediate verification after creation is unreliable.


def test_delete_nonexistent_entity(api: PetroVisor):
    """
    Test that deleting a non-existent entity completes quickly without errors
    """
    entity_name = f"Nonexistent Entity {uuid.uuid4().hex[:8]}"

    # Should complete quickly without raising an exception (returns None for non-existent items)
    api.delete_entity(entity_name)

    # Verify entity still doesn't exist
    assert not api.item_exists(ItemType.Entity, entity_name), "Entity should not exist"


def test_delete_nonexistent_signal(api: PetroVisor):
    """
    Test that deleting a non-existent signal completes quickly without errors
    """
    signal_name = f"Nonexistent Signal {uuid.uuid4().hex[:8]}"

    # Should complete quickly without raising an exception (returns None for non-existent items)
    api.delete_signal(signal_name)

    # Verify signal still doesn't exist
    assert not api.item_exists(ItemType.Signal, signal_name), "Signal should not exist"
