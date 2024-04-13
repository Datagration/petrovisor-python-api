import warnings


# string constants
def strconstants(cls=None, supress_warnings=False):
    """
    Decorator to create string constants class
    which returns field as is if it doesn't exist
    and sends warning if supress_warnings is set to False
    """

    def wrap(cls):

        # static class
        class StaticClass:
            """
            Static class which raises error if instance of the class is created
            """

            def __new__(cls, *args, **kwargs):
                raise TypeError(
                    f"Instances of static class '{cls.__name__}' cannot be created."
                )

        # metaclass with customized __getattr___
        class StrConstantsMeta(type):
            """
            String constants metaclass which sends warning if field doesn't exist
            """

            def __getattr__(cls, attr):
                if attr in cls.__dict__:
                    return cls.__dict__[attr]
                if not supress_warnings:
                    warnings.warn(
                        f"Field '{attr}' does not exist in '{cls.__name__}'."
                        "Returning attribute as is.",
                        RuntimeWarning,
                        stacklevel=1,
                    )
                return attr

        # static string constants
        class StrConstants(cls, StaticClass, metaclass=StrConstantsMeta):
            """
            Static string constants class which sends warning if field doesn't exist
            """

            pass

        return StrConstants

    # See if decorator is called with or without parentheses.
    if cls is None:
        # decorator is called with parentheses.
        return wrap
    # decorator is called without parentheses.
    return wrap(cls)
