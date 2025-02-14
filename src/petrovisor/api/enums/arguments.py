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
    # StringValue = NewType("StringValueArg", str)
    # StringOptions = NewType("StringOptionsArg", str)

    # string with item type
    # WorkspaceValue = NewType("WorkspaceValueArg", str)
    # TagEntries = NewType("TagEntriesArg", str)
    # Hierarchy = NewType("HierarchyArg", str)
    # RefTable = NewType("RefTableArg", str)
