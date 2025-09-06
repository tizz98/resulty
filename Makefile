.PHONY: test test-cov test-doctest mypy lint fmt fmt-check check install clean examples help

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies with poetry"
	@echo "  test       - Run tests with pytest (includes doctests)"
	@echo "  test-cov   - Run tests with coverage report"
	@echo "  test-doctest - Run only doctests"
	@echo "  mypy       - Run type checking"
	@echo "  lint       - Run linting checks"
	@echo "  fmt        - Format code"
	@echo "  fmt-check  - Check code formatting"
	@echo "  check      - Run all checks (lint, mypy, test)"
	@echo "  examples   - Run example scripts"
	@echo "  clean      - Clean up temporary files"

# Install dependencies
install:
	poetry install

# Run tests
test:
	poetry run pytest

# Run tests with coverage
test-cov:
	poetry run pytest --cov=resulty --cov-report=term-missing

# Run only doctests
test-doctest:
	poetry run pytest --doctest-modules resulty/

# Type checking
mypy:
	poetry run mypy resulty/ tests/

# Linting
lint:
	poetry run ruff check

# Formatting
fmt:
	poetry run ruff format

# Check formatting
fmt-check:
	poetry run ruff format --check

# Run all checks
check: lint mypy test

# Run examples
examples:
	@echo "Running API client example..."
	poetry run python examples/api_client.py
	@echo "Running data validation example..."
	poetry run python examples/data_validation.py

# Clean temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage .pytest_cache dist/ build/
