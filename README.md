# resulty

A Rust-inspired error handling library for Python that makes exceptions more explicit and manageable.

**Note: This is a proof of concept and is not yet available on PyPI.**

## Quick Start

```python
import resulty

# Define your error types
class ValidationError(resulty.ResultyException):
    pass

# Wrap functions to return Result types instead of raising exceptions
@resulty.resulty
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValidationError("Cannot divide by zero")
    return a / b

# Handle results with pattern matching
result = divide(10, 2)
match result:
    case resulty.Ok(value):
        print(f"Success: {value}")  # Success: 5.0
    case resulty.Err(exception):
        print(f"Error: {exception}")

# Zero division returns an error instead of crashing
result = divide(10, 0)
match result:
    case resulty.Ok(value):
        print(f"Success: {value}")
    case resulty.Err(exception):
        print(f"Error: {exception}")  # Error: Cannot divide by zero
```

## Async Support

The `@resulty.resulty` decorator automatically handles both sync and async functions:

```python
@resulty.resulty
async def fetch_data(url: str) -> dict:
    if not url.startswith("https://"):
        raise ValidationError("URL must be HTTPS")
    # ... fetch logic
    return {"data": "example"}

# Usage
result = await fetch_data("https://api.example.com")
match result:
    case resulty.Ok(data):
        print(f"Data: {data}")
    case resulty.Err(exception):
        print(f"Fetch failed: {exception}")
```

## Key Features

- **Explicit error handling** - No silent failures or unexpected exceptions
- **Type safety** - Full generic type support with proper type hints
- **Pattern matching** - Ergonomic error handling with Python's `match/case`
- **Async/await support** - Works seamlessly with both sync and async functions
- **Selective catching** - Only catches `ResultyException` subclasses, other exceptions bubble up
- **Zero runtime overhead** - Simple decorator with minimal performance impact

## Installation

Since this is a proof of concept, install directly from the repository:

```bash
git clone https://github.com/yourusername/resulty.git
cd resulty
poetry install
```

## Why Resulty?

Traditional Python exception handling can lead to:
- Silent failures that are hard to debug
- Unclear error propagation in complex call stacks  
- Functions that can fail in undocumented ways

Resulty makes errors explicit and forces you to handle them, similar to Rust's `Result<T, E>` type, leading to more robust and predictable code.

## Examples

See the [`examples/`](examples/) directory for practical, real-world use cases:

- **API Client** - HTTP error handling, network failures, rate limiting
- **File Operations** - File I/O errors, permissions, format validation  
- **Data Validation** - User input validation, business rules, type checking
- **Database Operations** - SQL constraints, transactions, connection errors

```bash
# Run individual examples
python examples/api_client.py
python examples/data_validation.py

# See examples/README.md for full documentation
```

## Development

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=resulty --cov-report=term-missing

# Type checking
poetry run mypy resulty/ tests/

# Linting and formatting
poetry run ruff check
poetry run ruff format
```
