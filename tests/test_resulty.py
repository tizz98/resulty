import resulty
import pytest


def resulty_factory(value=None, exception=None):
    @resulty.resulty
    def some_resulty_method():
        if exception:
            raise exception

        return value

    return some_resulty_method


def async_resulty_factory(value=None, exception=None):
    @resulty.resulty
    async def some_async_resulty_method():
        if exception:
            raise exception

        return value

    return some_async_resulty_method


class CustomResultyException(resulty.ResultyException):
    pass


class CustomException(Exception):
    pass


class TestSyncResulty:
    def test_error(self):
        given_exc = CustomResultyException()

        match resulty_factory(exception=given_exc):
            case resulty.Ok(_):
                assert False, "expected error"
            case resulty.Err(got_exc):
                assert got_exc is given_exc, "expected error to be the same"

    def test_ok(self):
        given_val = object()

        match resulty_factory(value=given_val):
            case resulty.Ok(got_val):
                assert got_val is given_val, "expected matching value"
            case resulty.Err(_):
                assert False, "expected ok"

    def test_non_resulty_exception(self):
        given_exc = CustomException()

        try:
            match resulty_factory(exception=given_exc):
                case resulty.Ok(_):
                    assert False, "expected error"
                case resulty.Err(_):
                    assert False, "expected thrown error"
        except Exception as e:
            assert e is given_exc, "expected same error"

    def test_args_forwarding(self):
        @resulty.resulty
        def add_numbers(a, b, c=0):
            return a + b + c

        result = add_numbers(1, 2, c=3)
        match result:
            case resulty.Ok(value):
                assert value == 6
            case resulty.Err(_):
                assert False, "expected ok"

    def test_kwargs_forwarding(self):
        @resulty.resulty
        def build_string(**kwargs):
            return "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

        result = build_string(name="test", value=42, flag=True)
        match result:
            case resulty.Ok(value):
                assert value == "flag=True_name=test_value=42"
            case resulty.Err(_):
                assert False, "expected ok"

    def test_mixed_args_kwargs(self):
        @resulty.resulty
        def complex_function(prefix, *args, suffix="end", **kwargs):
            parts = (
                [prefix]
                + list(args)
                + [f"{k}:{v}" for k, v in kwargs.items()]
                + [suffix]
            )
            return "-".join(str(p) for p in parts)

        result = complex_function(
            "start", "middle1", "middle2", suffix="finish", extra="data"
        )
        match result:
            case resulty.Ok(value):
                assert value == "start-middle1-middle2-extra:data-finish"
            case resulty.Err(_):
                assert False, "expected ok"

    def test_args_with_exception(self):
        @resulty.resulty
        def divide(a, b):
            if b == 0:
                raise CustomResultyException("Division by zero")
            return a / b

        result = divide(10, 0)
        match result:
            case resulty.Ok(_):
                assert False, "expected error"
            case resulty.Err(exc):
                assert isinstance(exc, CustomResultyException)
                assert str(exc) == "Division by zero"


@pytest.mark.asyncio
class TestAsyncioResulty:
    async def test_error(self):
        given_exc = CustomResultyException()

        async_method = async_resulty_factory(exception=given_exc)
        result = await async_method()

        match result:
            case resulty.Ok(_):
                assert False, "expected error"
            case resulty.Err(got_exc):
                assert got_exc is given_exc, "expected error to be the same"

    async def test_ok(self):
        given_val = object()

        async_method = async_resulty_factory(value=given_val)
        result = await async_method()

        match result:
            case resulty.Ok(got_val):
                assert got_val is given_val, "expected matching value"
            case resulty.Err(_):
                assert False, "expected ok"

    async def test_non_resulty_exception(self):
        given_exc = CustomException()

        async_method = async_resulty_factory(exception=given_exc)

        try:
            result = await async_method()
            match result:
                case resulty.Ok(_):
                    assert False, "expected error"
                case resulty.Err(_):
                    assert False, "expected thrown error"
        except Exception as e:
            assert e is given_exc, "expected same error"

    async def test_args_forwarding(self):
        @resulty.resulty
        async def add_numbers_async(a, b, c=0):
            return a + b + c

        result = await add_numbers_async(1, 2, c=3)
        match result:
            case resulty.Ok(value):
                assert value == 6
            case resulty.Err(_):
                assert False, "expected ok"

    async def test_kwargs_forwarding(self):
        @resulty.resulty
        async def build_string_async(**kwargs):
            return "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

        result = await build_string_async(name="test", value=42, flag=True)
        match result:
            case resulty.Ok(value):
                assert value == "flag=True_name=test_value=42"
            case resulty.Err(_):
                assert False, "expected ok"

    async def test_mixed_args_kwargs(self):
        @resulty.resulty
        async def complex_function_async(prefix, *args, suffix="end", **kwargs):
            parts = (
                [prefix]
                + list(args)
                + [f"{k}:{v}" for k, v in kwargs.items()]
                + [suffix]
            )
            return "-".join(str(p) for p in parts)

        result = await complex_function_async(
            "start", "middle1", "middle2", suffix="finish", extra="data"
        )
        match result:
            case resulty.Ok(value):
                assert value == "start-middle1-middle2-extra:data-finish"
            case resulty.Err(_):
                assert False, "expected ok"

    async def test_args_with_exception(self):
        @resulty.resulty
        async def divide_async(a, b):
            if b == 0:
                raise CustomResultyException("Division by zero")
            return a / b

        result = await divide_async(10, 0)
        match result:
            case resulty.Ok(_):
                assert False, "expected error"
            case resulty.Err(exc):
                assert isinstance(exc, CustomResultyException)
                assert str(exc) == "Division by zero"
