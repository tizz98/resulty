from dataclasses import dataclass
from functools import wraps
import typing as t
import inspect
from typing import TypeVar, ParamSpec, Callable, Awaitable, overload


__all__ = ["resulty", "ResultyException", "Result", "Ok", "Err"]


T = TypeVar("T")
P = ParamSpec("P")


class ResultyException(Exception):
    """Base exception class for resulty error handling.

    Only exceptions that inherit from ResultyException will be caught
    and converted to Err results by the @resulty decorator. Other
    exceptions will bubble up normally.
    """
    pass


class ResultMixin:
    """Mixin class providing Rust-like methods for Result types."""

    def is_ok(self) -> bool:
        """Check if this result is an Ok variant.

        Returns:
            True if this is an Ok result, False if it's an Err result.
        """
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        """Check if this result is an Err variant.

        Returns:
            True if this is an Err result, False if it's an Ok result.
        """
        return isinstance(self, Err)

    def unwrap(self):
        """Extract the contained value or raise the contained exception.

        Returns:
            The contained value if this is an Ok result.

        Raises:
            The contained exception if this is an Err result.
        """
        if isinstance(self, Err):
            raise self.exc
        return self.value


@dataclass(frozen=True)
class Ok(t.Generic[T], ResultMixin):
    """Represents a successful result containing a value.

    Args:
        value: The successful result value of type T.

    Example:
        >>> result = Ok("success")
        >>> result.is_ok()
        True
        >>> result.unwrap()
        'success'
    """
    value: T


@dataclass(frozen=True)
class Err(ResultMixin):
    """Represents a failed result containing an exception.

    Args:
        exc: The exception that caused the failure.

    Example:
        >>> from resulty import ResultyException
        >>> class MyError(ResultyException):
        ...     pass
        >>> result = Err(MyError("something went wrong"))
        >>> result.is_err()
        True
        >>> try:
        ...     result.unwrap()
        ... except MyError as e:
        ...     print(f"Caught: {e}")
        Caught: something went wrong
    """
    exc: ResultyException


Result = t.Union[Ok[T], Err]
"""Type alias for a result that can be either Ok[T] or Err."""


@overload
def resulty(fn: Callable[P, T]) -> Callable[P, Result[T]]: ...


@overload
def resulty(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[Result[T]]]: ...


def resulty(fn):
    """Decorator that converts exceptions to Result types.

    This decorator catches ResultyException instances and converts them to
    Err results, while successful returns are wrapped in Ok results.
    Other exceptions bubble up normally.

    Works with both synchronous and asynchronous functions.

    Args:
        fn: The function to wrap. Can be sync or async.

    Returns:
        A wrapped function that returns Result[T] instead of T.
        For async functions, returns Awaitable[Result[T]].

    Example:
        >>> @resulty
        ... def divide(a: int, b: int) -> float:
        ...     if b == 0:
        ...         raise ResultyException("Division by zero")
        ...     return a / b
        >>>
        >>> result = divide(10, 2)
        >>> match result:
        ...     case Ok(value):
        ...         print(f"Success: {value}")
        ...     case Err(exc):
        ...         print(f"Error: {exc}")
        Success: 5.0
    """
    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def _inner_async_resulty(*args, **kwargs):
            try:
                result = await fn(*args, **kwargs)
                return Ok(result)
            except ResultyException as e:
                return Err(e)

        return _inner_async_resulty
    else:

        @wraps(fn)
        def _inner_resulty(*args, **kwargs):
            try:
                return Ok(fn(*args, **kwargs))
            except ResultyException as e:
                return Err(e)

        return _inner_resulty
