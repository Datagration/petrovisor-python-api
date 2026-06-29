from enum import (
    Enum,
    IntEnum,
    auto,
)


# Time increment for aggregation
class TimeIncrement(IntEnum):
    """
    PetroVisor time increments
    """

    # Every second
    EverySecond = auto()
    # Every minute
    EveryMinute = auto()
    # Every five minute
    EveryFiveMinutes = auto()
    # Every fifteen minute
    EveryFifteenMinutes = auto()
    # Every hour
    Hourly = auto()
    # Every day
    Daily = auto()
    # Every month
    Monthly = auto()
    # Every quarter
    Quarterly = auto()
    # Every year
    Yearly = auto()


# Aggregation function for data retrieval
class AggregationFunction(str, Enum):
    """
    PetroVisor aggregation functions for data retrieval (Data/Retrieve endpoint).
    Values match the API string representation directly.
    Consistent with pandas aggfunc names where possible.
    """

    Sum = "Sum"
    Average = "Average"  # pandas: 'mean'
    Max = "Max"
    Min = "Min"
    First = "First"
    Last = "Last"
    Count = "Count"
    Median = "Median"
    Mode = "Mode"
    StandardDeviation = "StandardDeviation"  # pandas: 'std'
    Variance = "Variance"  # pandas: 'var'
    Percentile = "Percentile"
    Range = "Range"
    CountDistinct = "CountDistinct"


# Depth increment for aggregation
class DepthIncrement(IntEnum):
    """
    PetroVisor depth increments
    """

    # 0.1 m (Every tenth of meter)
    TenthMeter = 0
    # 0.125 m (Every eighth of meter)
    EighthMeter = 1
    # 0.1524 m (Every half of foot)
    HalfFoot = 2
    # 0.3048 m (Every foot)
    Foot = 3
    # 0.5 m (Every half of meter)
    HalfMeter = 4
    # 1 m (Every meter)
    Meter = 5
