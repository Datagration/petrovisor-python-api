# Python 3.7+ compatibility for typing
try:
    from typing import Annotated, get_type_hints, get_args, get_origin
except ImportError:
    # Use typing_extensions in older Python versions
    from typing_extensions import Annotated, get_type_hints, get_args, get_origin

from typing import Union, Optional, Any, List, Tuple
from dataclasses import dataclass
from petrovisor.api.enums.arguments import (
    ArgumentType,
    ArgumentDirection,
    ArgumentOptions,
    ArgumentUnit,
    ArgumentMeasurement,
)


@dataclass
class ArgumentMetadata:
    """Metadata container using dataclasses."""

    type: Any = None
    direction: Optional[str] = ArgumentDirection.In.value
    options: Optional[ArgumentOptions] = None
    unit: Optional[str] = None
    measurement: Optional[Tuple[Any, ...]] = None


class FunctionArgumentsMetadata(dict):
    """Dictionary-like type hints container that allows both dict and attribute access."""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class Argument:
    """Argument class that acts like Annotated, but handles predefined metadata
    (ArgumentOptions, ArgumentUnit, ArgumentMeasurement) in a manageable way.

    Examples
    --------
    param1: Argument[str | Argument.Type.TimeNumericSignal, Argument.Unit("m")]
    param2: Argument[Argument.Type.RefTable, Argument.Direction.Out, Argument.Options(["option1", "option2"])]
    param3: Argument[list[str], Argument.Direction.Out, Argument.Options(["option1", "option2"])]
    """

    Type = ArgumentType
    Direction = ArgumentDirection

    @classmethod
    def Unit(cls, value: str) -> ArgumentUnit:
        """Create ArgumentUnit for use in annotations."""
        return ArgumentUnit(value)

    @classmethod
    def Measurement(cls, value: str) -> ArgumentMeasurement:
        """Create ArgumentMeasurement for use in annotations."""
        return ArgumentMeasurement(value)

    @classmethod
    def Options(cls, options: Union[List[Any], Tuple[Any, ...]]) -> ArgumentOptions:
        """Create ArgumentOptions for use in annotations."""
        return ArgumentOptions(options)

    def __class_getitem__(cls, params):
        """Make Argument[...] act exactly like Annotated[...]."""
        if not isinstance(params, tuple):
            params = (params,)
        return Annotated[params]

    @classmethod
    def get_type_hints(cls, func) -> FunctionArgumentsMetadata:
        """Extract all parameter metadata from a function's type hints."""
        return get_function_arguments_metadata(func)

    @staticmethod
    def is_type(obj) -> bool:
        """Check if an object is a type or type-like construct."""
        # Regular type
        if isinstance(obj, type):
            return True

        # NewType instances (have __supertype__ attribute)
        if hasattr(obj, "__supertype__"):
            return True

        # Generic types, Union types, etc.
        if hasattr(obj, "__origin__") or hasattr(obj, "__args__"):
            return True

        return False


def get_function_arguments_metadata(func) -> FunctionArgumentsMetadata:
    """Get function arguments metadata."""

    # The key insight: get_type_hints with include_extras=True does most of the work!
    type_hints = get_type_hints(func, include_extras=True)

    result = FunctionArgumentsMetadata()

    for param_name, type_hint in type_hints.items():
        if param_name == "return":
            continue

        metadata = extract_metadata_from_type(type_hint)
        if metadata:
            result[param_name] = metadata

    return result


def extract_metadata_from_type(type_hint) -> ArgumentMetadata:
    """Extract ArgumentMetadata from type hints.
    This function relies on get_type_hints(include_extras=True).
    """

    # Handle NewType instances
    if hasattr(type_hint, "__supertype__"):
        return ArgumentMetadata(type=type_hint)

    # Handle Annotated types (from Annotated[...] syntax)
    origin = get_origin(type_hint)
    if origin is Annotated:
        args = get_args(type_hint)
        if not args:
            return ArgumentMetadata()

        base_type = args[0]
        metadata_items = args[1:]

        # Extract predefined metadata types
        direction = ArgumentDirection.In.value
        options = None
        unit = None
        measurement = None

        for item in metadata_items:
            if isinstance(item, ArgumentDirection):
                direction = item.value
            elif isinstance(item, ArgumentOptions):
                options = item.value
            elif isinstance(item, ArgumentUnit):
                unit = item.value
            elif isinstance(item, ArgumentMeasurement):
                measurement = item.value

        return ArgumentMetadata(
            type=base_type,
            direction=direction,
            options=options,
            unit=unit,
            measurement=measurement,
        )

    # Handle Union types
    elif origin is Union:
        union_args = get_args(type_hint)
        return ArgumentMetadata(type=list(union_args))

    # Handle plain types
    else:
        return ArgumentMetadata(type=type_hint)
