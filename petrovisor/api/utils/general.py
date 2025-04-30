import warnings
import functools


def deprecated(custom_message):
    def decorator(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            full_message = (
                f"Call to deprecated function {func.__name__}. {custom_message}"
            )
            warnings.warn(full_message, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return new_func

    return decorator
