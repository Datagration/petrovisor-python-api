from enum import Enum


class ArgumentType(Enum):
    # signals
    StaticNumericSignal =  "StaticNumericSignal"
    StaticStringSignal = "StaticStringSignal"

    TimeNumericSignal = "TimeNumericSignal"
    TimeStringSignal = "TimeStringSignal"

    DepthNumericSignal = "DepthNumericSignal"
    DepthStringSignal = "DepthStringSignal"

    PVTSignal = "PVTSignal"

    # specific types
    TagEntries = "TagEntries"

    # general types
    String = "String"

    # PetroVisor Item Type
    BlobFile = "BlobFile"
    Calculation = "Calculation"
    ChartDefinition = "ChartDefinition"
    CleansingCalculation = "CleansingCalculation"
    CleansingScript = "CleansingScript"
    Context = "Context"
    CustomWorkflowActivity = "CustomWorkflowActivity"
    # Dashboard = "Dashboard"
    DataConnection = "DataConnection"
    DataGrid = "DataGrid"
    DataIntegrationSession = "DataIntegrationSession"
    DataIntegrationSet = "DataIntegrationSet"
    DataSource = "DataSource"
    DCA = "DCA"
    Entity = "Entity"
    EntitySet = "EntitySet"
    EntityType = "EntityType"
    EventCalculation = "EventCalculation"
    EventSubscription = "EventSubscription"
    FilterDefinition = "FilterDefinition"
    Hierarchy = "Hierarchy"
    # Label = "Label"
    # Message = "Message"
    MLModel = "MLModel"
    PivotTable = "PivotTable"
    # PowerBIItem = "PowerBIItem"
    ProcessTemplate = "ProcessTemplate"
    PSharpScript = "PSharpScript"
    PythonWorkflowActivity = "PythonWorkflowActivity"
    ReferenceTable = "ReferenceTable"
    RWorkflowActivity = "RWorkflowActivity"
    Scenario = "Scenario"
    Scope = "Scope"
    Signal = "Signal"
    # Snapshot = "Snapshot"
    Tag = "Tag"
    TagEntry = "TagEntry"
    # Ticket = "Ticket"
    # TicketTimeInterval = "TicketTimeInterval"
    Unit = "Unit"
    Unknown = "Unknown"
    User = "User"
    UserGroup = "UserGroup"
    UserSetting = "UserSetting"
    WebWorkflowActivity = "WebWorkflowActivity"
    Workflow = "Workflow"
    WorkflowSchedule = "WorkflowSchedule"
    # Workspace = "Workspace"
    WorkspacePackage = "WorkspacePackage"
    WorkspaceValue = "WorkspaceValue"
