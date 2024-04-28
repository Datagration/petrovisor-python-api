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
    time_start = "2021-01-01T00:00:00"
    time_end = "2022-01-01T00:00:00"
    time_step = TimeIncrement.Daily.name
    depth_start = 0
    depth_end = 10
    depth_step = DepthIncrement.Meter.name
    scope = Scope(name="Field 1 Wells Scope",
                  time_start=time_start,
                  time_end=time_end,
                  time_step=time_step,
                  depth_start=depth_start,
                  depth_end=depth_end,
                  depth_step=depth_step,
                  )

    # create context
    context = Context(name="Context",
                      scope=scope,
                      entity_set=entity_set,
                      hierarchy=hierarchy,
                      )

    # data preparation
    entity_col = "Entity"
    time_col = "Date"
    depth_col = "Depth [m]"
    letters = list(map(chr, range(97, 123)))
    num_wells = 5
    depth_steps = 10
    time_steps = 100
    # now = datetime.now()

    # static data
    data_stat = []
    for i in range(0, num_wells):
        well_idx = i + 1
        entities = [f"Well 00{well_idx}"]
        num_vals = [i]
        str_vals = [letters[i]]
        data_stat.append(pd.DataFrame({
            entity_col: entities,
            stat_num_signal: num_vals,
            stat_str_signal: str_vals,
        }))
    df_stat = pd.concat(data_stat, ignore_index=True)

    # save static data
    api.save_table_data(df_stat)

    # time data
    data_time = []
    for i in range(0, num_wells):
        well_idx = i + 1
        entities = np.repeat(f"Well 00{well_idx}", time_steps)
        dates = pd.date_range(time_start, periods=time_steps, freq="d").to_list()
        num_vals = np.random.uniform(1, 4, time_steps)
        str_vals = np.random.choice(letters, time_steps)
        data_time.append(pd.DataFrame({
            entity_col: entities,
            time_col: dates,
            time_num_signal: num_vals,
            time_str_signal: str_vals,
        }))
    df_time = pd.concat(data_time, ignore_index=True)

    # save time data
    api.save_table_data(df_time)

    # depth data
    data_depth = []
    for i in range(0,num_wells):
        well_idx = i + 1
        entities = np.repeat(f"Well 00{well_idx}",depth_steps)
        depths = np.arange(0,depth_steps).tolist()
        num_vals = np.sin(np.linspace(0,1,depth_steps))*100
        str_vals = np.random.choice(letters, depth_steps)
        data_depth.append(pd.DataFrame({
            entity_col: entities,
            depth_col: depths,
            depth_num_signal: num_vals,
            depth_str_signal: str_vals,
        }))
    df_depth = pd.concat(data_depth, ignore_index=True)

    # save depth data
    api.save_table_data(df_depth)

    # load static signals
    df_loaded = api.load_signals_data([stat_num_signal,
                                       stat_str_signal,
                                       ],
                                      context=context)
    assert df_loaded.shape[0] >= num_wells + 1

    # load time signals
    df_loaded = api.load_signals_data([time_num_signal,
                                       time_str_signal],
                                      context=context)
    assert df_loaded.shape[0] >= num_wells * time_steps

    # load depth signals
    df_loaded = api.load_signals_data([depth_num_signal,
                                       depth_str_signal,
                                      ],
                                      context=context)
    assert df_loaded.shape[0] >= num_wells * depth_steps

    # load static, time and depth signals
    df_loaded = api.load_signals_data([stat_num_signal,
                                       stat_str_signal,
                                       time_num_signal,
                                       time_str_signal,
                                       depth_num_signal,
                                       depth_str_signal,
                                       ],
                                      context=context)
    assert df_loaded.shape[0] >= num_wells * time_steps * depth_steps
