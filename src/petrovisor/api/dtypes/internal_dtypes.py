from enum import Enum, IntEnum


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


# Reference table column type
class RefTableColumnType(Enum):
    Numeric = (0,)
    String = (1,)
    DateTime = (2,)
    Bool = (3,)
