from typing import NewType


class ArgumentItemType:
    @property
    def BlobFile(self):
        return NewType("BlobFileArg", str)

    @property
    def Calculation(self):
        return NewType("CalculationArg", str)

    @property
    def ChartDefinition(self):
        return NewType("ChartDefinitionArg", str)

    @property
    def CleansingCalculation(self):
        return NewType("CleansingCalculationArg", str)

    @property
    def CleansingScript(self):
        return NewType("CleansingScriptArg", str)

    @property
    def Context(self):
        return NewType("ContextArg", str)

    @property
    def CustomWorkflowActivity(self):
        return NewType("CustomWorkflowActivityArg", str)

    @property
    def Dashboard(self):
        return NewType("DashboardArg", str)

    @property
    def DataConnection(self):
        return NewType("DataConnectionArg", str)

    @property
    def DataGrid(self):
        return NewType("DataGridArg", str)

    @property
    def DataIntegrationSession(self):
        return NewType("DataIntegrationSessionArg", str)

    @property
    def DataIntegrationSet(self):
        return NewType("DataIntegrationSetArg", str)

    @property
    def DataSource(self):
        return NewType("DataSourceArg", str)

    @property
    def DCA(self):
        return NewType("DCAArg", str)

    @property
    def Entity(self):
        return NewType("EntityArg", str)

    @property
    def EntitySet(self):
        return NewType("EntitySetArg", str)

    @property
    def EntityType(self):
        return NewType("EntityTypeArg", str)

    @property
    def EventCalculation(self):
        return NewType("EventCalculationArg", str)

    @property
    def EventSubscription(self):
        return NewType("EventSubscriptionArg", str)

    @property
    def FilterDefinition(self):
        return NewType("FilterDefinitionArg", str)

    @property
    def Hierarchy(self):
        return NewType("HierarchyArg", str)

    @property
    def Label(self):
        return NewType("LabelArg", str)

    @property
    def Message(self):
        return NewType("MessageArg", str)

    @property
    def MLModel(self):
        return NewType("MLModelArg", str)

    @property
    def PivotTable(self):
        return NewType("PivotTableArg", str)

    @property
    def Plot(self):
        return NewType("PlotArg", str)

    @property
    def PowerBIItem(self):
        return NewType("PowerBIItemArg", str)

    @property
    def ProcessTemplate(self):
        return NewType("ProcessTemplateArg", str)

    @property
    def PSharpScript(self):
        return NewType("PSharpScriptArg", str)

    @property
    def PythonWorkflowActivity(self):
        return NewType("PythonWorkflowActivityArg", str)

    @property
    def ReferenceTable(self):
        return NewType("ReferenceTableArg", str)

    @property
    def RWorkflowActivity(self):
        return NewType("RWorkflowActivityArg", str)

    @property
    def Scenario(self):
        return NewType("ScenarioArg", str)

    @property
    def Scope(self):
        return NewType("ScopeArg", str)

    @property
    def Signal(self):
        return NewType("SignalArg", str)

    @property
    def Snapshot(self):
        return NewType("SnapshotArg", str)

    @property
    def Tag(self):
        return NewType("TagArg", str)

    @property
    def TagEntry(self):
        return NewType("TagEntryArg", str)

    @property
    def Ticket(self):
        return NewType("TicketArg", str)

    @property
    def TicketTimeInterval(self):
        return NewType("TicketTimeIntervalArg", str)

    @property
    def Unit(self):
        return NewType("UnitArg", str)

    @property
    def Unknown(self):
        return NewType("UnknownArg", str)

    @property
    def User(self):
        return NewType("UserArg", str)

    @property
    def UserGroup(self):
        return NewType("UserGroupArg", str)

    @property
    def UserSetting(self):
        return NewType("UserSettingArg", str)

    @property
    def WebWorkflowActivity(self):
        return NewType("WebWorkflowActivityArg", str)

    @property
    def Workflow(self):
        return NewType("WorkflowArg", str)

    @property
    def WorkflowSchedule(self):
        return NewType("WorkflowScheduleArg", str)

    @property
    def Workspace(self):
        return NewType("WorkspaceArg", str)

    @property
    def WorkspaceValue(self):
        return NewType("WorkspaceValueArg", str)

    @property
    def WorkspacePackage(self):
        return NewType("WorkspacePackageArg", str)


class ArgumentType:
    """Registry of argument types"""

    # signals
    @property
    def StaticNumericSignal(self):
        return NewType("StaticNumericSignalArg", str)

    @property
    def StaticStringSignal(self):
        return NewType("StaticStringSignalArg", str)

    @property
    def TimeNumericSignal(self):
        return NewType("TimeNumericSignalArg", str)

    @property
    def TimeStringSignal(self):
        return NewType("TimeStringSignalArg", str)

    @property
    def DepthNumericSignal(self):
        return NewType("DepthNumericSignalArg", str)

    @property
    def DepthStringSignal(self):
        return NewType("DepthStringSignalArg", str)

    @property
    def PVTSignal(self):
        return NewType("PVTSignalArg", str)

    # specific types
    @property
    def TagEntries(self):
        return NewType("TagEntriesArg", str)

    # general types
    @property
    def StringValue(self):
        return NewType("StringValueArg", str)

    @property
    def StringOptions(self):
        return NewType("StringOptionsArg", str)

    @property
    def Item(self):
        return NewType("ItemArg", ArgumentItemType)

    @property
    def ItemOptions(self):
        return NewType("ItemOptionsArg", ArgumentItemType)
