# Python 3.7+ compatibility for typing
try:
    from typing import NewType
except ImportError:
    # Use typing_extensions in older Python versions
    from typing_extensions import NewType

from typing import Optional, Any, List, Dict, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class ArgumentType:
    """Types of arguments supported by PetroVisor"""

    # general types
    String = NewType("String", str)
    Number = NewType("Number", Union[float, int])
    Dictionary = NewType("Dictionary", Dict[str, Any])
    Enumeration = NewType("Enumeration", Dict[str, int])

    # signals
    StaticNumericSignal = NewType("StaticNumericSignal", str)
    StaticStringSignal = NewType("StaticStringSignal", str)
    TimeNumericSignal = NewType("TimeNumericSignal", str)
    TimeStringSignal = NewType("TimeStringSignal", str)
    DepthNumericSignal = NewType("DepthNumericSignal", str)
    DepthStringSignal = NewType("DepthStringSignal", str)
    PVTSignal = NewType("PVTSignal", str)

    # specific types
    TagEntries = NewType("TagEntries", str)

    # PetroVisor Item Types
    # BlobFile = NewType("BlobFile", str) # Not supported in UI
    Calculation = NewType("Calculation", str)
    ChartDefinition = NewType("ChartDefinition", str)
    CleansingCalculation = NewType("CleansingCalculation", str)
    CleansingScript = NewType("CleansingScript", str)
    Context = NewType("Context", str)
    CustomWorkflowActivity = NewType("CustomWorkflowActivity", str)
    # Dashboard = NewType("Dashboard", str) # Not supported in UI
    DataConnection = NewType("DataConnection", str)
    DataGrid = NewType("DataGrid", str)
    DataIntegrationSession = NewType("DataIntegrationSession", str)
    DataIntegrationSet = NewType("DataIntegrationSet", str)
    DataSource = NewType("DataSource", str)
    DCA = NewType("DCA", str)
    Entity = NewType("Entity", str)
    EntitySet = NewType("EntitySet", str)
    EntityType = NewType("EntityType", str)
    EventCalculation = NewType("EventCalculation", str)
    EventSubscription = NewType("EventSubscription", str)
    FilterDefinition = NewType("FilterDefinition", str)
    Hierarchy = NewType("Hierarchy", str)
    # Label = NewType("Label", str) # Not supported in UI
    # Message = NewType( "Message", str) # Not supported in UI
    MLModel = NewType("MLModel", str)
    PivotTable = NewType("PivotTable", str)
    # PowerBIItem = NewType("PowerBIItem", str) # Not supported in UI
    ProcessTemplate = NewType("ProcessTemplate", str)
    PSharpScript = NewType("PSharpScript", str)
    PythonWorkflowActivity = NewType("PythonWorkflowActivity", str)
    ReferenceTable = NewType("ReferenceTable", str)
    RWorkflowActivity = NewType("RWorkflowActivity", str)
    Scenario = NewType("Scenario", str)
    Scope = NewType("Scope", str)
    Signal = NewType("Signal", str)
    # Snapshot = "Snapshot", str)
    Tag = NewType("Tag", str)
    TagEntry = NewType("TagEntry", str)
    # Ticket = NewType("Ticket", str) # Not supported in UI
    # TicketTimeInterval = NewType("TicketTimeInterval", str) # Not supported in UI
    Unit = NewType("Unit", str)
    Unknown = NewType("Unknown", str)
    User = NewType("User", str)
    UserGroup = NewType("UserGroup", str)
    UserSetting = NewType("UserSetting", str)
    WebWorkflowActivity = NewType("WebWorkflowActivity", str)
    Workflow = NewType("Workflow", str)
    WorkflowSchedule = NewType("WorkflowSchedule", str)
    # Workspace = NewType("Workspace", str) # Not supported in UI
    WorkspacePackage = NewType("WorkspacePackage", str)
    WorkspaceValue = NewType("WorkspaceValue", str)


class ArgumentDirection(str, Enum):
    """Parameter direction.

    Uses string values for input/output direction indicators.
    """

    In = "in"
    Out = "out"


@dataclass
class ArgumentOptions:
    """Container for domain-specific information about an argument.

    Examples
    --------
        ArgumentOptions("low", "medium", "high")
        ArgumentOptions(["low", "medium", "high"])
        ArgumentOptions(("option1", "option2"))
        ArgumentOptions(1, 2, 3, 4)
    """

    value: Tuple[Any, ...] = ()

    def __init__(self, *args):
        """Initialize ArgumentOptions with flexible input formats.

        Parameters
        ----------
        *args : Any
            - Multiple individual arguments: ArgumentOptions(1, 2, 3)
            - Single list: ArgumentOptions([1, 2, 3])
            - Single tuple: ArgumentOptions((1, 2, 3))
            - Empty: ArgumentOptions()
        """
        if len(args) == 0:
            # Empty case: ArgumentOptions()
            self.value = tuple()
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            # Single list/tuple case: ArgumentOptions([1, 2, 3]) or ArgumentOptions((1, 2, 3))
            self.value = tuple(args[0])
        else:
            # Multiple arguments case: ArgumentOptions(1, 2, 3)
            self.value = tuple(args)


@dataclass
class ArgumentUnit:
    """Container for unit information.

    Parameters
    ----------
    value : str, optional
        The unit of measurement (e.g., "m", "s", "kg").
    """

    value: Optional[str] = None


@dataclass
class ArgumentMeasurement:
    """Container for measurement information.

    Parameters
    ----------
    value : str, optional
        The type of measurement (e.g., "depth", "pressure").
    """

    value: Optional[str] = None
