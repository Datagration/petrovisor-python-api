import numpy as np
import pandas as pd
from datetime import datetime
from petrovisor import (
    Signal,
    Entity,
    EntitySet,
    Hierarchy,
    Scope,
    Context,
    SignalType,
    ItemType,
    TimeIncrement,
    DepthIncrement,
)
from petrovisor import PetroVisor


def test_signals(api: PetroVisor):
    stat_num_signal = "static numeric signal"
    stat_str_signal = "static string signal"
    time_num_signal = "time numeric signal"
    time_str_signal = "time string signal"
    depth_num_signal = "depth numeric signal"
    depth_str_signal = "depth string signal"
    signals = [
        Signal(
            type=SignalType.Static.name,
            name=stat_num_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
        Signal(
            type=SignalType.String.name,
            name=stat_str_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
        Signal(
            type=SignalType.TimeDependent.name,
            name=time_num_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
        Signal(
            type=SignalType.StringTimeDependent.name,
            name=time_str_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
        Signal(
            type=SignalType.DepthDependent.name,
            name=depth_num_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
        Signal(
            type=SignalType.StringDepthDependent.name,
            name=depth_str_signal,
            unit=" ",
            unit_measurement="Dimensionless",
        ),
    ]

    # create signals
    for signal in signals:
        if not api.item_exists(ItemType.Signal, signal.name):
            api.add_signal(signal)

    # entities
    entities = [
        Entity(name="Well 001", type="Well"),
        Entity(name="Well 002", type="Well"),
        Entity(name="Well 003", type="Well"),
        Entity(name="Well 004", type="Well"),
        Entity(name="Well 005", type="Well"),
        Entity(name="Field 1", type="Field"),
    ]

    # create entities
    for entity in entities:
        if not api.item_exists(ItemType.Entity, entity.name):
            api.add_entity(entity)

    # create entity set
    entity_set = EntitySet(name="Field 1 Wells",
                           entities=entities)

    # create hierarchy
    relationship = {
        "Well 001": "Field 1",
        "Well 002": "Field 1",
        "Well 003": "Field 1",
        "Well 004": "Field 1",
        "Well 005": "Field 1",
    }
    hierarchy = Hierarchy(name="Field 1 Wells",
                          relationship=relationship,
                          )

    # create scope
    scope = Scope(name="Field 1 Wells Scope",
                  time_start="2021-01-01T00:00:00",
                  time_end="2022-01-01T00:00:00",
                  time_step=TimeIncrement.Daily.name,
                  depth_start=0,
                  depth_end=10,
                  depth_step=DepthIncrement.Meter.name,
                  )

    # create context
    context = Context(name="Context",
                      scope=scope,
                      entity_set=entity_set,
                      hierarchy=hierarchy,
                      )

    # create DataFrame
    now = datetime.now()
    n = 100
    entity_col = "Entity"
    time_col = "Date"
    depth_col = "Depth [m]"
    depth_step = 10
    df = pd.DataFrame({
        entity_col: "Well 001",
        time_col: pd.date_range("2021-01-01T00:00:00", periods=n, freq="d").to_list(),
        # depth_col: np.arange(0,n*depth_step,depth_step).tolist(),
        stat_num_signal: np.repeat(10, n),
        stat_str_signal: np.repeat("a", n),
        time_num_signal: np.random.uniform(1, 4, n),
        time_str_signal: np.repeat("a", n),
        # depth_num_signal: n*np.sin(np.linspace(0,1,n)*100),
        # depth_str_signal: np.repeat("a", n),
    })
    num_rows = df.shape[0]

    # save data
    api.save_table_data(df)

    # load signals
    df_loaded = api.load_signals_data(signals, context=context)
    num_rows_loaded = df_loaded.shape[0]
