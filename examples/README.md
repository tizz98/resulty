# Resulty Examples

This directory contains practical examples demonstrating real-world use cases of the `resulty` library for robust error handling in Python applications.

## Examples Overview

### 1. API Client (`api_client.py`)
Demonstrates error handling for HTTP API calls, including:
- Network connectivity failures
- HTTP error responses (4xx, 5xx)
- JSON parsing errors
- Rate limiting
- Timeout handling

**Run**: `python examples/api_client.py`

**Key scenarios**:
- Successful API calls to JSONPlaceholder
- 404 errors for non-existent resources
- Simulated server errors, rate limits, and network failures
- Proper error categorization with specific exception types

### 2. File Operations (`file_operations.py`)
Shows error handling for file system operations, including:
- File not found errors
- Permission denied errors
- Invalid file formats (JSON, CSV)
- Disk space issues
- Atomic file operations

**Run**: `python examples/file_operations.py`

**Key scenarios**:
- Configuration file loading and saving
- CSV file processing with validation
- Invalid JSON and empty file handling
- Temporary file cleanup and atomic writes

### 3. Data Validation (`data_validation.py`)
Comprehensive data validation with detailed error reporting:
- Required field validation
- Type checking and format validation
- Range validation (age, salary limits)
- Business rule enforcement
- Email, phone number, and date format validation

**Run**: `python examples/data_validation.py`

**Key scenarios**:
- User data validation with multiple field types
- Format validation for emails and phone numbers
- Age/birth date consistency checks
- Department-specific salary rules
- Detailed error messages for each validation failure

### 4. Database Operations (`database_operations.py`)
Database error handling patterns using SQLite:
- Connection failures
- SQL constraint violations
- Record not found errors
- Transaction rollbacks
- Concurrent access conflicts

**Run**: `python examples/database_operations.py`

**Key scenarios**:
- User CRUD operations with proper error handling
- Unique constraint violations (duplicate emails)
- Check constraint violations (invalid age/salary)
- Transactional operations with rollback
- Connection timeout and locking issues

## Running the Examples

All examples are self-contained and can be run independently:

```bash
# Run individual examples
python examples/api_client.py
python examples/file_operations.py
python examples/data_validation.py
python examples/database_operations.py

# Or run all examples
for example in examples/*.py; do
    echo "=== Running $example ==="
    python "$example"
    echo
done
```

## Key Learning Points

### Error Categorization
Each example shows how to create specific exception types that inherit from `resulty.ResultyException`:
- `NetworkError`, `HTTPStatusError` for API calls
- `FileNotFoundError`, `PermissionError` for file operations  
- `ValidationError`, `TypeValidationError` for data validation
- `ConnectionError`, `QueryError` for database operations

### Pattern Matching
All examples use Python's `match/case` pattern matching for ergonomic error handling:

```python
import resulty

result = some_operation()
match result:
    case resulty.Ok(value):
        # Handle success
        print(f"Success: {value}")
    case resulty.Err(error):
        # Handle specific error types
        if isinstance(error, SpecificError):
            # Custom handling
        print(f"Error: {error}")
```

### Async Support
The API client example shows that the `@resulty.resulty` decorator works identically with async functions, requiring no changes to error handling patterns.

### Real-world Scenarios
Each example focuses on common failure modes that developers encounter:
- Network instability and API changes
- File system permissions and disk space
- Invalid user input and data corruption
- Database constraints and concurrent access

### Error Recovery
Examples demonstrate different error recovery strategies:
- **Fail fast**: Stop execution on validation errors
- **Graceful degradation**: Continue with default values when possible
- **Retry logic**: Could be added for transient network errors
- **User feedback**: Provide meaningful error messages

## Integration Patterns

These examples can be adapted for various Python frameworks:

- **Web APIs**: Use the validation patterns with FastAPI/Django request handling
- **Data pipelines**: Apply file operation patterns for ETL processes
- **Microservices**: Use API client patterns for service communication
- **Background jobs**: Apply database patterns for job queues and state management

## Best Practices Demonstrated

1. **Specific error types** - Create meaningful exception hierarchies
2. **Early validation** - Validate inputs before processing
3. **Resource cleanup** - Use context managers and proper error handling
4. **Atomic operations** - Use transactions and temporary files
5. **User-friendly errors** - Provide actionable error messages
6. **Logging integration** - Error information is easily extractable for logging

Each example is designed to be educational and directly applicable to production code, showing how `resulty` can make Python applications more robust and maintainable.