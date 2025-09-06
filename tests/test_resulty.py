import pytest

import resulty


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


class TestResultMixin:
    """Test the Rust-like methods provided by ResultMixin"""
    
    def test_is_ok_with_ok_result(self):
        result = resulty.Ok("success")
        assert result.is_ok() is True
        assert result.is_err() is False
    
    def test_is_ok_with_err_result(self):
        result = resulty.Err(CustomResultyException("error"))
        assert result.is_ok() is False
        assert result.is_err() is True
    
    def test_is_err_with_ok_result(self):
        result = resulty.Ok(42)
        assert result.is_err() is False
        assert result.is_ok() is True
    
    def test_is_err_with_err_result(self):
        result = resulty.Err(CustomResultyException("failure"))
        assert result.is_err() is True
        assert result.is_ok() is False
    
    def test_unwrap_ok_result(self):
        expected_value = "test_value"
        result = resulty.Ok(expected_value)
        
        # unwrap() should return the value for Ok
        assert result.unwrap() is expected_value
    
    def test_unwrap_err_result(self):
        expected_exc = CustomResultyException("test error")
        result = resulty.Err(expected_exc)
        
        # unwrap() should raise the exception for Err
        with pytest.raises(CustomResultyException) as exc_info:
            result.unwrap()
        
        assert exc_info.value is expected_exc
    
    def test_unwrap_with_different_value_types(self):
        # Test with various value types
        test_cases = [
            42,
            "string",
            [1, 2, 3],
            {"key": "value"},
            None,
            True,
            False,
        ]
        
        for expected_value in test_cases:
            result = resulty.Ok(expected_value)
            assert result.unwrap() == expected_value
    
    def test_unwrap_with_different_exception_types(self):
        # Test with different ResultyException subclasses
        class CustomError1(resulty.ResultyException):
            pass
        
        class CustomError2(resulty.ResultyException):
            pass
        
        error1 = CustomError1("error 1")
        error2 = CustomError2("error 2")
        
        result1 = resulty.Err(error1)
        result2 = resulty.Err(error2)
        
        with pytest.raises(CustomError1) as exc_info1:
            result1.unwrap()
        assert exc_info1.value is error1
        
        with pytest.raises(CustomError2) as exc_info2:
            result2.unwrap()
        assert exc_info2.value is error2
    
    def test_chaining_result_methods(self):
        # Test that methods can be used together logically
        ok_result = resulty.Ok("success")
        err_result = resulty.Err(CustomResultyException("failure"))
        
        # Check Ok result
        if ok_result.is_ok():
            value = ok_result.unwrap()
            assert value == "success"
        else:
            assert False, "Should be Ok"
        
        # Check Err result
        if err_result.is_err():
            with pytest.raises(CustomResultyException):
                err_result.unwrap()
        else:
            assert False, "Should be Err"
    
    def test_result_methods_with_resulty_decorator(self):
        # Test that ResultMixin methods work with decorator-created results
        @resulty.resulty
        def successful_function():
            return "decorator_success"
        
        @resulty.resulty
        def failing_function():
            raise CustomResultyException("decorator_error")
        
        ok_result = successful_function()
        err_result = failing_function()
        
        # Test Ok result from decorator
        assert ok_result.is_ok()
        assert not ok_result.is_err()
        assert ok_result.unwrap() == "decorator_success"
        
        # Test Err result from decorator
        assert err_result.is_err()
        assert not err_result.is_ok()
        with pytest.raises(CustomResultyException) as exc_info:
            err_result.unwrap()
        assert str(exc_info.value) == "decorator_error"
