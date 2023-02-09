import functools
from typing import Any, Callable


def log(logging_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for logging messages.

    -----
    Parameters:

        logging_func: Callable[..., Any]

            Logging function with appropriate severity level.

            Examples: logging.info, logging.warning, ...
    """

    def log_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logging_func(f"Calling {func.__name__}")
            logging_func(f"args: {args}")
            logging_func(f"kwargs: {kwargs}")

            value = func(*args, **kwargs)

            logging_func(f"Finished {func.__name__}")

            return value

        return wrapper

    return log_wrapper
