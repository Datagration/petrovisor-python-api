from petrovisor.api.utils.datastructs import strconstants


# Item types
@strconstants(supress_warnings=True)
class ItemType:
    # named item types
    Unit = "Unit"
    UnitMeasurement = "UnitMeasurement"
    Entity = "Entity"
    EntityType = "EntityType"
    Signal = "Signal"
    Tag = "Tag"
    Label = "Label"
    MessageEntry = "MessageEntry"
    Ticket = "Ticket"
    ProcessTemplate = "ProcessTemplate"
    UserSetting = "UserSetting"
    EventSubscription = "EventSubscription"
    # PetroVisor item types
    ConfigurationSettings = "ConfigurationSettings"
    ConfigurationSettingValue = (
        "ConfigurationSettingValue"  # alias ConfigurationSettings
    )
    RefTable = "RefTable"
    PivotTable = "PivotTable"
    PivotTableDefinition = "PivotTableDefinition"  # alias PivotTable
    Hierarchy = "Hierarchy"
    Scope = "Scope"
    EntitySet = "EntitySet"
    Context = "Context"
    TableCalculation = "TableCalculation"
    EventCalculation = "EventCalculation"
    CleansingCalculation = "CleansingCalculation"
    PSharpScript = "PSharpScript"
    CleansingScript = "CleansingScript"
    Plot = "Plot"
    Chart = "Chart"
    ChartDefinition = "ChartDefinition"  # alias Chart
    Filter = "Filter"
    FilterDefinition = "FilterDefinition"  # alias Filter
    Workflow = "Workflow"
    WorkflowSchedule = "WorkflowSchedule"
    CustomWorkflowActivity = "CustomWorkflowActivity"
    RWorkflowActivity = "RWorkflowActivity"
    PythonWorkflowActivity = "PythonWorkflowActivity"
    WebWorkflowActivity = "WebWorkflowActivity"
    DataIntegrationSet = "DataIntegrationSet"
    WorkspacePackage = "WorkspacePackage"
    DCA = "DCA"
    PowerBIItem = "PowerBIItem"
    Dashboard = "Dashboard"
    # PetroVisor info types
    MLModel = "MLModel"
    MachineLearningModel = "MachineLearningModel"  # alias MLModel
    DataGrid = "DataGrid"
    DataConnection = "DataConnection"
    DataSourceMapping = "DataSourceMapping"
    DataIntegrationSession = "DataIntegrationSession"
    Scenario = "Scenario"
