from enum import (
    Enum,
    auto,
)


# PetroVisor named item types
class NamedItemType(str, Enum):
    Unit = 'Unit'
    UnitMeasurement = 'UnitMeasurement'
    Entity = 'Entity'
    EntityType = 'EntityType'
    Signal = 'Signal'
    ConfigurationSettingValue = 'ConfigurationSettingValue'
    ConfigurationSettings = 'ConfigurationSettings'
    Tag = 'Tag'
    ProcessTemplate = 'ProcessTemplate'
    MessageEntry = 'MessageEntry'
    Ticket = 'Ticket'
    UserSetting = 'UserSetting'
    CustomWorkflowActivity = 'CustomWorkflowActivity'
    WebWorkflowActivity = 'WebWorkflowActivity'
    EventSubscription = 'EventSubscription'
    WorkspacePackage = 'WorkspacePackage'


# PetroVisor item types
class PetroVisorItemType(str, Enum):
    Hierarchy = 'Hierarchy'
    Scope = 'Scope'
    EntitySet = 'EntitySet'
    Context = 'Context'
    TableCalculation = 'TableCalculation'
    EventCalculation = 'EventCalculation'
    CleansingCalculation = 'CleansingCalculation'
    Plot = 'Plot'
    PSharpScript = 'PSharpScript'
    CleansingScript = 'CleansingScript'
    WorkflowSchedule = 'WorkflowSchedule'
    RWorkflowActivity = 'RWorkflowActivity'
    Workflow = 'Workflow'
    FilterDefinition = 'FilterDefinition'
    Filter = 'Filter'
    DCA = 'DCA'
    ChartDefinition = 'ChartDefinition'
    Chart = 'Chart'
    VoronoiGrid = 'VoronoiGrid'
    GeoDataGrid = 'GeoDataGrid'
    Polygon = 'Polygon'
    PivotTableDefinition = 'PivotTableDefinition'
    PivotTable = 'PivotTable'
    DataIntegrationSet = 'DataIntegrationSet'
    ReferenceTableDefinition = 'ReferenceTableDefinition'
    ReferenceTable = 'ReferenceTable'
    PowerBIItem = 'PowerBIItem'


# PetroVisor info types
class PetroVisorInfoItemType(str, Enum):
    MachineLearningModel = 'MachineLearningModel'
    MLModel = 'MLModel'
    DataGrid = 'DataGrid'
    DataGridSet = 'DataGridSet'
    DataConnection = 'DataConnection'
    DataSource = 'DataSource'
    Scenario = 'Scenario'
    DataIntegrationSession = 'DataIntegrationSession'


# Item types
class ItemType(NamedItemType, PetroVisorItemType, PetroVisorInfoItemType):
    pass
