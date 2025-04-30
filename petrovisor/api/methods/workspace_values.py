from typing import (
    Any,
    Optional,
    List,
    Dict,
    Union,
    Tuple,
)

from petrovisor.api.utils.helper import ApiHelper
from petrovisor.api.protocols.protocols import SupportsRequests


# Workspace value API calls
class WorkspaceValuesMixin(SupportsRequests):
    """
    Workspace value API calls
    """

    # get workspace value names
    def get_workspace_value_names(self, **kwargs) -> List[str]:
        """
        Get all workspace value names
        """
        route = "ConfigurationSettings"
        return self.get(f"{route}", **kwargs)

    # get workspace values
    def get_workspace_values(
        self, value_type: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Get all workspace values

        Parameters
        ----------
        value_type : str, default None
            Value type: 'Numeric', 'NumericWithUnit', 'String', 'List', 'Dictionary', 'Enumeration'
        """
        route = "ConfigurationSettings"
        if value_type:
            t = ApiHelper.get_comparison_string(value_type)
            if t in {"numeric"}:
                value_type = "Numeric"
            elif t in {"numericwithunit"}:
                value_type = "NumericWithUnit"
            elif t in {"string", "str"}:
                value_type = "String"
            elif t in {"list"}:
                value_type = "List"
            elif t in {"dictionary", "dict"}:
                value_type = "Dictionary"
            elif t in {"enumeration", "enum"}:
                value_type = "Enumeration"
            else:
                raise ValueError(
                    f"PetroVisor::get_workspace_values(): "
                    f"unknown workspace value type: '{value_type}'. "
                    f"Known workspace value types: "
                    f"{WorkspaceValueMixinHelper.get_workspace_value_types()}"
                )
            values = self.get(f"{route}/{value_type}/{route}", **kwargs)
        else:
            values = self.get(f"{route}/All", **kwargs)
        return {
            value["Name"]: WorkspaceValueMixinHelper.get_workspace_value(
                value, **kwargs
            )
            for value in values
        }

    # get workspace value
    def get_workspace_value(self, name: str, **kwargs) -> Tuple[Any, str]:
        """
        Get workspace value

        Parameters
        ----------
        name : str
            Variable name
        """
        route = "ConfigurationSettings"
        # get workspace value
        value = self.get(f"{route}/{self.encode(name)}", **kwargs)
        return WorkspaceValueMixinHelper.get_workspace_value(value, **kwargs)

    # add workspace value
    def add_workspace_value(
        self,
        name: str,
        value: Union[str, List[Any], Dict[str, Any], Tuple, float, int],
        unit: Union[Dict, str] = "",
        description: Optional[str] = "",
        **kwargs,
    ) -> Any:
        """
        Add or edit workspace value

        Parameters
        ----------
        name : str
            Variable name
        value : str | dict | list | enum | float | int
            Variable value
        unit : str
            Unit object or Unit name
        description : str
            Description
        """
        route = "ConfigurationSettings"
        # value specs
        value_specs = WorkspaceValueMixinHelper.get_workspace_value_specs(
            name, value, unit=unit, description=description, **kwargs
        )
        # get existing workspace values names
        workspace_value_names = self.get_workspace_value_names(**kwargs)
        if name in workspace_value_names:
            return self.put(f"{route}/{self.encode(name)}", data=value_specs, **kwargs)
        return self.post(f"{route}", data=value_specs, **kwargs)

    # rename workspace value
    def rename_workspace_value(self, old_name: str, new_name: str, **kwargs) -> Dict:
        """
        Rename workspace value

        Parameters
        ----------
        old_name : str
            Old variable name
        new_name : str
            New variable name
        """
        route = "ConfigurationSettings"
        return self.post(
            f"{route}/Rename",
            query={
                "OldName": old_name,
                "NewName": new_name,
            },
            **kwargs,
        )

    # delete workspace value
    def delete_workspace_value(self, name: str, **kwargs) -> Dict:
        """
        Delete workspace value

        Parameters
        ----------
        name : str
            Variable name
        """
        route = "ConfigurationSettings"
        return self.delete(f"{route}/{self.encode(name)}", **kwargs)


# Workspace value mixin Helper
class WorkspaceValueMixinHelper:
    """
    Workspace value mixin Helper
    """

    # get known workspace value types
    @staticmethod
    def get_workspace_value_types():
        return [
            "Numeric",
            "NumericWithUnit",
            "String",
            "List",
            "Dictionary",
            "Enumeration",
        ]

    # get workspace value
    @staticmethod
    def get_workspace_value(value: Dict, **kwargs) -> Any:
        """
        Get workspace value

        Parameters
        ----------
        value : dict
            Value specs
        """

        if value and "ValueType" in value and value["ValueType"]:
            value_type = value["ValueType"]
            if value_type == "NumericWithUnit":
                return value["NumericValue"], value["UnitName"]
            for vtype in ["Numeric", "String", "List", "Dictionary", "Enumeration"]:
                if value_type == vtype:
                    return value[f"{vtype}Value"]
        return None

    # get workspace value specs
    @staticmethod
    def get_workspace_value_specs(
        name: str,
        value: Union[str, List[Any], Dict[str, Any], Tuple],
        unit: Union[Dict, str] = "",
        description: Optional[str] = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Add or edit workspace value

        Parameters
        ----------
        name : str
            Variable name
        value : str | dict | list | enum | float | int
            Variable value
        unit : str
            Unit object or Unit name
        description : str
            Description
        """
        # get value type, unit

        value_type = None
        value_unit: str = ""
        if isinstance(value, list):
            value_type = "List"
            valid_value = [str(v) for v in value]
        elif isinstance(value, dict):
            value_type = "Dictionary"
            valid_value = {str(k): str(v) for k, v in value.items()}
        elif isinstance(value, tuple):
            value_type = "Enumeration"
            valid_value = {}
            eid = -1
            for v in value:
                if isinstance(v, (tuple, list)) and len(v) > 1:
                    eid = int(v[1])
                    valid_value[str(v[0])] = eid
                else:
                    eid += 1
                    valid_value[str(v)] = eid
        else:
            valid_value = value
            if isinstance(value, str):
                value_type = "String"
            elif ApiHelper.is_float(value) or ApiHelper.is_int(value):
                value_unit = ApiHelper.get_object_name(unit, **kwargs) if unit else ""
                value_type = "NumericWithUnit" if value_unit else "Numeric"

        # get value field name
        value_field_name = (
            "NumericValue" if value_type == "NumericWithUnit" else f"{value_type}Value"
        )

        # value specs
        value_specs = {
            "Name": name,
            value_field_name: valid_value,
            "Description": description,
            "ValueType": value_type,
        }
        if value_unit:
            value_specs["UnitName"] = value_unit
        return value_specs
