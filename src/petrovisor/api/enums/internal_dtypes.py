from enum import (
    Enum,
    IntEnum,
    auto,
)


# Signal types
class SignalType(IntEnum):
    """
    PetroVisor signal types
    """

    # Static signal type specifies signals which value is a numeric constant over a time or depth
    Static = 0
    # Time-dependent type specifies signals which are functions of time
    TimeDependent = 1
    # Depth-dependent type specifies signals which are functions of depth
    DepthDependent = 2
    # String signal type specifies signals which value is a string constant over a time or depth
    String = 3
    # PVT signal type specifies signals which are functions of pressure and temperature
    PVT = 4
    # String time-dependent signal type specifies signals which value is a string constant over a time or depth
    StringTimeDependent = 5
    # Signals which have a series of depth-based string values
    StringDepthDependent = 6


class AggregationType(IntEnum):
    # Sum
    Sum = 0
    # Average
    Average = auto()
    # Maximum
    Max = auto()
    # Minimum
    Min = auto()
    # First value
    First = auto()
    # Last Value
    Last = auto()
    # Number of values
    Count = auto()
    # No aggregation
    NoAggregation = auto()
    # Median of values
    Median = auto()
    # Mode of values
    Mode = auto()
    # Standard deviation of values
    StandardDeviation = auto()
    # Variance of values
    Variance = auto()
    # The 100th percentile of values
    Percentile = auto()
    # The range of the elements of values
    Range = auto()


# Reference table column type
class RefTableColumnType(Enum):
    Numeric = (0,)
    String = (1,)
    DateTime = (2,)
    Bool = (3,)
