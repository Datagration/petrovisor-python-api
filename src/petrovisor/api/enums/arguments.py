from typing import NewType


class ArgumentType:
    """Registry of argument types"""

    # signals
    StaticNumericSignal = NewType("StaticNumericSignalArg", str)
    StaticStringSignal = NewType("StaticStringSignalArg", str)
    TimeNumericSignal = NewType("TimeNumericSignalArg", str)
    TimeStringSignal = NewType("TimeStringSignalArg", str)
    DepthNumericSignal = NewType("DepthNumericSignalArg", str)
    DepthStringSignal = NewType("DepthStringSignalArg", str)
    PVTSignal = NewType("PVTSignalArg", str)

    # general types
    StringValue = NewType("StringValueArg", str)
    StringOptions = NewType("StringOptionsArg", str)
    Item = NewType("ItemArg", ArgumentItemType)

# not covered by get_item()
# BlobFile = 4,
# Workspace = 9,
# TicketTimeInterval = 18,
# UserGroup = 20,
# TagEntry = 24,
# Snapshot = 32,
# User = 33,
# WorkspaceValue = 47,

class ArgumentItemType:
    Signal = NewType("SignalArg", str)
    Unit = NewType("UnitArg", str)
    EntityType = NewType("EntityTypeArg", str)
    BlobFile = NewType("BlobFileArg", str)
    Entity = NewType("EntityArg", str)
    EntitySet = NewType("EntitySetArg", str)
    Hierarchy = NewType("HierarchyArg", str)
    Calculation = NewType("CalculationArg", str)
    Workspace = NewType("WorkspaceArg", str)
    Tag = NewType("TagArg", str)
    Scope = NewType("ScopeArg", str)
    EventSubscription = NewType("EventSubscriptionArg", str)
    Context = NewType("ContextArg", str)
    EventCalculation = NewType("EventCalculationArg", str)
    CleansingCalculation = NewType("CleansingCalculationArg", str)
    PSharpScript = NewType("PSharpScriptArg", str)
    TicketTimeInterval = NewType("TicketTimeIntervalArg", str)
    Label = NewType("LabelArg", str)
    UserGroup = NewType("UserGroupArg", str)
    WorkflowSchedule = NewType("WorkflowScheduleArg", str)
    Message = NewType("MessageArg", str)
    FilterDefinition = NewType("FilterDefinitionArg", str)
    TagEntry = NewType("TagEntryArg", str)
    Ticket = NewType("TicketArg", str)
    DataConnection = NewType("DataConnectionArg", str)
    DataSource = NewType("DataSourceArg", str)
    DataIntegrationSet = NewType("DataIntegrationSetArg", str)
    Dashboard = NewType("DashboardArg", str)
    Plot = NewType("PlotArg", str)
    Scenario = NewType("ScenarioArg", str)
    Snapshot = NewType("SnapshotArg", str)
    User = NewType("UserArg", str)
    ChartDefinition = NewType("ChartDefinitionArg", str)
    PivotTable = NewType("PivotTableArg", str)
    DCA = NewType("DCAArg", str)
    MLModel = NewType("MLModelArg", str)
    CustomWorkflowActivity = NewType("CustomWorkflowActivityArg", str)
    RWorkflowActivity = NewType("RWorkflowActivityArg", str)
    CleansingScript = NewType("CleansingScriptArg", str)
    ProcessTemplate = NewType("ProcessTemplateArg", str)
    Workflow = NewType("WorkflowArg", str)
    WorkspaceValue = NewType("WorkspaceValueArg", str)
    ReferenceTable = NewType("ReferenceTableArg", str)
    WorkspacePackage = NewType("WorkspacePackageArg", str)
    PythonWorkflowActivity = NewType("PythonWorkflowActivityArg", str)
    DataGrid = NewType("DataGridArg", str)
    WebWorkflowActivity = NewType("WebWorkflowActivityArg", str)
    PowerBIItem = NewType("PowerBIItemArg", str)
    DataIntegrationSession = NewType("DataIntegrationSessionArg", str)
    UserSetting = NewType("UserSettingArg", str)
