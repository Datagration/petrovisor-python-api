from typing import NewType, Literal, get_args

# signals
StaticNumericSignalArg = NewType("StaticNumericSignalArg", str)
StaticStringSignalArg = NewType("StaticStringSignalArg", str)
TimeNumericSignalArg = NewType("TimeNumericSignalArg", str)
TimeStringSignalArg = NewType("TimeStringSignalArg", str)
DepthNumericSignalArg = NewType("DepthNumericSignalArg", str)
DepthStringSignalArg = NewType("DepthStringSignalArg", str)
PVTSignalArg = NewType("PVTSignalArg", str)
# workspace values
WorkspaceValueArg = NewType("WorkspaceValueArg", str)
# general types
StringValueArg = NewType("StringValueArg", str)
StringOptionsArg = NewType("StringOptionsArg", str)
# specific items
TagEntriesArg = NewType("TagEntriesArg", str)
HierarchyArg = NewType("HierarchyArg", str)
RefTableArg = NewType("RefTableArg", str)


class ArgumentType:
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
