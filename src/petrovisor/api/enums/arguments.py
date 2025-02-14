from typing import NewType, Literal, get_args

# signals
StaticNumericSignalArg = NewType("StaticNumericSignal", str)
StaticStringSignalArg = NewType("StaticStringSignal", str)
TimeNumericSignalArg = NewType("TimeNumericSignal", str)
TimeStringSignalArg = NewType("TimeStringSignal", str)
DepthNumericSignalArg = NewType("DepthNumericSignal", str)
DepthStringSignalArg = NewType("DepthStringSignal", str)
PVTSignalArg = NewType("PVTSignal", str)
# workspace values
WorkspaceValueArg = NewType("WorkspaceValue", str)
# general types
StringValueArg = NewType("StringValue", str)
StringOptionsArg = NewType("StringOptions", str)
# specific items
TagEntriesArg = NewType("TagEntries", str)
HierarchyArg = NewType("Hierarchy", str)
RefTableArg = NewType("RefTable", str)


class ArgumentType(Enum):
    """Registry of argument types"""

    # signals
    StaticNumericSignal = StaticNumericSignalArg
    StaticStringSignal = StaticStringSignalArg
    TimeNumericSignal = TimeNumericSignalArg
    TimeStringSignal = TimeStringSignalArg
    DepthNumericSignal = DepthNumericSignalArg
    DepthStringSignal = DepthStringSignalArg
    PVTSignal = PVTSignalArg
    # workspace values
    WorkspaceValue = WorkspaceValueArg
    # general types
    StringValue = StringValueArg
    StringOptions = StringOptionsArg
    # specific items
    TagEntries = TagEntriesArg
    Hierarchy = HierarchyArg
    RefTable = RefTableArg
