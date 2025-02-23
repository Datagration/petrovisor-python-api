from typing import NewType


class ArgumentItemType:
    @property
    def BlobFile(self):
        return NewType("BlobFile", str)

    @property
    def Calculation(self):
        return NewType("Calculation", str)

    @property
    def ChartDefinition(self):
        return NewType("ChartDefinition", str)

    @property
    def CleansingCalculation(self):
        return NewType("CleansingCalculation", str)

    @property
    def CleansingScript(self):
        return NewType("CleansingScript", str)

    @property
    def Context(self):
        return NewType("Context", str)

    @property
    def CustomWorkflowActivity(self):
        return NewType("CustomWorkflowActivity", str)

    @property
    def Dashboard(self):
        return NewType("Dashboard", str)

    @property
    def DataConnection(self):
        return NewType("DataConnection", str)

    @property
    def DataGrid(self):
        return NewType("DataGrid", str)

    @property
    def DataIntegrationSession(self):
        return NewType("DataIntegrationSession", str)

    @property
    def DataIntegrationSet(self):
        return NewType("DataIntegrationSet", str)

    @property
    def DataSource(self):
        return NewType("DataSource", str)

    @property
    def DCA(self):
        return NewType("DCA", str)

    @property
    def Entity(self):
        return NewType("Entity", str)

    @property
    def EntitySet(self):
        return NewType("EntitySet", str)

    @property
    def EntityType(self):
        return NewType("EntityType", str)

    @property
    def EventCalculation(self):
        return NewType("EventCalculation", str)

    @property
    def EventSubscription(self):
        return NewType("EventSubscription", str)

    @property
    def FilterDefinition(self):
        return NewType("FilterDefinition", str)

    @property
    def Hierarchy(self):
        return NewType("Hierarchy", str)

    @property
    def Label(self):
        return NewType("Label", str)

    @property
    def Message(self):
        return NewType("Message", str)

    @property
    def MLModel(self):
        return NewType("MLModel", str)

    @property
    def PivotTable(self):
        return NewType("PivotTable", str)

    @property
    def PowerBIItem(self):
        return NewType("PowerBIItem", str)

    @property
    def ProcessTemplate(self):
        return NewType("ProcessTemplate", str)

    @property
    def PSharpScript(self):
        return NewType("PSharpScript", str)

    @property
    def PythonWorkflowActivity(self):
        return NewType("PythonWorkflowActivity", str)

    @property
    def ReferenceTable(self):
        return NewType("ReferenceTable", str)

    @property
    def RWorkflowActivity(self):
        return NewType("RWorkflowActivity", str)

    @property
    def Scenario(self):
        return NewType("Scenario", str)

    @property
    def Scope(self):
        return NewType("Scope", str)

    @property
    def Signal(self):
        return NewType("Signal", str)

    @property
    def Snapshot(self):
        return NewType("Snapshot", str)

    @property
    def Tag(self):
        return NewType("Tag", str)

    @property
    def TagEntry(self):
        return NewType("TagEntry", str)

    @property
    def Ticket(self):
        return NewType("Ticket", str)

    @property
    def TicketTimeInterval(self):
        return NewType("TicketTimeInterval", str)

    @property
    def Unit(self):
        return NewType("Unit", str)

    @property
    def Unknown(self):
        return NewType("Unknown", str)

    @property
    def User(self):
        return NewType("User", str)

    @property
    def UserGroup(self):
        return NewType("UserGroup", str)

    @property
    def UserSetting(self):
        return NewType("UserSetting", str)

    @property
    def WebWorkflowActivity(self):
        return NewType("WebWorkflowActivity", str)

    @property
    def Workflow(self):
        return NewType("Workflow", str)

    @property
    def WorkflowSchedule(self):
        return NewType("WorkflowSchedule", str)

    @property
    def Workspace(self):
        return NewType("Workspace", str)

    @property
    def WorkspaceValue(self):
        return NewType("WorkspaceValue", str)

    @property
    def WorkspacePackage(self):
        return NewType("WorkspacePackage", str)


class ArgumentType:
    """Registry of argument types"""

    # signals
    @property
    def StaticNumericSignal(self):
        return NewType("StaticNumericSignal", str)

    @property
    def StaticStringSignal(self):
        return NewType("StaticStringSignal", str)

    @property
    def TimeNumericSignal(self):
        return NewType("TimeNumericSignal", str)

    @property
    def TimeStringSignal(self):
        return NewType("TimeStringSignal", str)

    @property
    def DepthNumericSignal(self):
        return NewType("DepthNumericSignal", str)

    @property
    def DepthStringSignal(self):
        return NewType("DepthStringSignal", str)

    @property
    def PVTSignal(self):
        return NewType("PVTSignal", str)

    # specific types
    @property
    def TagEntries(self):
        return NewType("TagEntries", str)

    # general types
    @property
    def String(self):
        return NewType("String", str)

    @property
    def StringOptions(self):
        return NewType("StringOptions", str)

    @property
    def Item(self):
        return NewType("Item", ArgumentItemType)

    @property
    def ItemOptions(self):
        return NewType("ItemOptions", ArgumentItemType)
