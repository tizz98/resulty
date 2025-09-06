from dataclasses import dataclass
from functools import wraps
import typing as t
import inspect
from typing import TypeVar, ParamSpec, Callable, Awaitable, overload


__all__ = ["resulty", "ResultyException", "Result", "Ok", "Err"]


T = TypeVar("T")
P = ParamSpec("P")


class ResultyException(Exception):
    pass


@dataclass(frozen=True)
class Ok(t.Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    exc: ResultyException


Result = t.Union[Ok[T], Err]


@overload
def resulty(fn: Callable[P, T]) -> Callable[P, Result[T]]: ...


@overload
def resulty(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[Result[T]]]: ...


def resulty(fn):
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
