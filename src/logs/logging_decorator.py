import functools
from typing import Any, Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def log(logging_func: Callable[..., Any]) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Returns a logging-decorator with given logging severity.

    -----
    Parameters:

        logging_func: Callable[..., Any]

            Logging function with appropriate severity level.

            Examples: logging.info, logging.warning, ...

    -----
    Returns:

        Callable
            Logging-decorator with desired severity.
    """

    def log_wrapper(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            logging_func(f"Calling {func.__name__}")
            logging_func(f"args: {args}")
            logging_func(f"kwargs: {kwargs}")

            value = func(*args, **kwargs)

            logging_func(f"Finished {func.__name__}")

            return value

        return wrapper

    return log_wrapper
