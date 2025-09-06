"""
File operations example using resulty for robust error handling.

This example shows how to handle common file operation failures:
- File not found
- Permission denied
- Invalid JSON/CSV format
- Disk space issues
- Concurrent access conflicts
"""

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import resulty


# Define specific error types for file operations
class FileNotFoundError(resulty.ResultyException):
    """File or directory does not exist"""

    pass


class PermissionError(resulty.ResultyException):
    """Insufficient permissions to access file"""

    pass


class InvalidFormatError(resulty.ResultyException):
    """File content is not in expected format"""

    pass


class DiskSpaceError(resulty.ResultyException):
    """Insufficient disk space for operation"""

    pass


class FileOperationError(resulty.ResultyException):
    """General file operation failure"""

    pass


class ConfigManager:
    """Example configuration file manager with robust error handling"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)

    @resulty.resulty
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            if not os.access(self.config_path, os.R_OK):
                raise PermissionError(f"No read permission for: {self.config_path}")

            with open(self.config_path, "r") as f:
                try:
                    config = json.load(f)

                    # Validate required fields
                    if not isinstance(config, dict):
                        raise InvalidFormatError("Config must be a JSON object")

                    return config

                except json.JSONDecodeError as e:
                    raise InvalidFormatError(f"Invalid JSON in config file: {e}")

        except OSError as e:
            if e.errno == 13:  # Permission denied
                raise PermissionError(f"Permission denied: {self.config_path}")
            elif e.errno == 2:  # File not found
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            else:
                raise FileOperationError(f"OS error reading config: {e}")

    @resulty.resulty
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        try:
            # Create parent directories if they don't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Check write permissions
            if self.config_path.exists() and not os.access(self.config_path, os.W_OK):
                raise PermissionError(f"No write permission for: {self.config_path}")

            if not os.access(self.config_path.parent, os.W_OK):
                raise PermissionError(
                    f"No write permission for directory: {self.config_path.parent}"
                )

            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.config_path.with_suffix(".tmp")

            try:
                with open(temp_path, "w") as f:
                    json.dump(config, f, indent=2)

                # Atomic rename
                temp_path.rename(self.config_path)
                return True

            except OSError as e:
                if e.errno == 28:  # No space left on device
                    raise DiskSpaceError("Insufficient disk space to save config")
                else:
                    raise FileOperationError(f"Failed to save config: {e}")
            finally:
                # Clean up temp file if it exists
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass  # Best effort cleanup

        except OSError as e:
            if e.errno == 13:  # Permission denied
                raise PermissionError(f"Permission denied: {self.config_path}")
            else:
                raise FileOperationError(f"OS error saving config: {e}")


class CSVProcessor:
    """Example CSV file processor with error handling"""

    @resulty.resulty
    def read_csv(self, file_path: str) -> List[Dict[str, str]]:
        """Read and parse CSV file"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        if not os.access(path, os.R_OK):
            raise PermissionError(f"No read permission for: {file_path}")

        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                # Detect if file is actually CSV by checking first line
                first_line = f.readline()
                if not first_line.strip():
                    raise InvalidFormatError("CSV file is empty")

                f.seek(0)  # Reset to beginning

                try:
                    reader = csv.DictReader(f)

                    if not reader.fieldnames:
                        raise InvalidFormatError("CSV file has no headers")

                    rows = list(reader)

                    if len(rows) == 0:
                        raise InvalidFormatError("CSV file contains no data rows")

                    return rows

                except csv.Error as e:
                    raise InvalidFormatError(f"Invalid CSV format: {e}")

        except UnicodeDecodeError as e:
            raise InvalidFormatError(f"Invalid file encoding: {e}")
        except OSError as e:
            raise FileOperationError(f"Error reading CSV file: {e}")

    @resulty.resulty
    def write_csv(self, file_path: str, data: List[Dict[str, str]]) -> bool:
        """Write data to CSV file"""
        if not data:
            raise InvalidFormatError("Cannot write empty data to CSV")

        path = Path(file_path)

        # Create parent directories
        path.parent.mkdir(parents=True, exist_ok=True)

        if not os.access(path.parent, os.W_OK):
            raise PermissionError(f"No write permission for directory: {path.parent}")

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(data)

            return True

        except OSError as e:
            if e.errno == 28:  # No space left on device
                raise DiskSpaceError("Insufficient disk space to write CSV")
            else:
                raise FileOperationError(f"Error writing CSV file: {e}")


def demonstrate_file_operations():
    """Show various file operation error handling scenarios"""
    print("=== File Operations Error Handling Examples ===\n")

    # Create a temporary directory for examples
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 1. Config file operations
        print("1. Configuration file operations:")
        config_manager = ConfigManager(temp_path / "config.json")

        # Try to load non-existent config
        result = config_manager.load_config()
        match result:
            case resulty.Ok(config):
                print(f"   Loaded config: {config}")
            case resulty.Err(error):
                print(f"   Expected error loading non-existent config: {error}")

        # Save a new config
        sample_config = {
            "app_name": "resulty_example",
            "debug": True,
            "database": {"host": "localhost", "port": 5432},
        }

        result = config_manager.save_config(sample_config)
        match result:
            case resulty.Ok(success):
                print(f"   Config saved successfully: {success}")
            case resulty.Err(error):
                print(f"   Error saving config: {error}")

        # Now load the saved config
        result = config_manager.load_config()
        match result:
            case resulty.Ok(config):
                print(f"   Loaded config: {config['app_name']}")
            case resulty.Err(error):
                print(f"   Error loading config: {error}")

        print()

        # 2. CSV operations
        print("2. CSV file operations:")
        csv_processor = CSVProcessor()

        # Try to read non-existent CSV
        result = csv_processor.read_csv(str(temp_path / "nonexistent.csv"))
        match result:
            case resulty.Ok(data):
                print(f"   Loaded CSV data: {len(data)} rows")
            case resulty.Err(error):
                print(f"   Expected error reading non-existent CSV: {error}")

        # Create and write sample CSV data
        sample_data = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Chicago"},
        ]

        csv_path = temp_path / "users.csv"
        result = csv_processor.write_csv(str(csv_path), sample_data)
        match result:
            case resulty.Ok(success):
                print(f"   CSV written successfully: {success}")
            case resulty.Err(error):
                print(f"   Error writing CSV: {error}")

        # Read the CSV back
        result = csv_processor.read_csv(str(csv_path))
        match result:
            case resulty.Ok(data):
                print(f"   Read CSV data: {len(data)} rows")
                for row in data:
                    print(f"   - {row['name']}, {row['age']}, {row['city']}")
            case resulty.Err(error):
                print(f"   Error reading CSV: {error}")

        print()

        # 3. Invalid file format scenarios
        print("3. Invalid format error handling:")

        # Create invalid JSON file
        invalid_json_path = temp_path / "invalid.json"
        with open(invalid_json_path, "w") as f:
            f.write("{ invalid json content")

        invalid_config_manager = ConfigManager(invalid_json_path)
        result = invalid_config_manager.load_config()
        match result:
            case resulty.Ok(config):
                print(f"   Unexpected success: {config}")
            case resulty.Err(error):
                print(f"   Expected error with invalid JSON: {error}")

        # Create empty CSV file
        empty_csv_path = temp_path / "empty.csv"
        with open(empty_csv_path, "w") as f:
            f.write("")  # Empty file

        result = csv_processor.read_csv(str(empty_csv_path))
        match result:
            case resulty.Ok(data):
                print(f"   Unexpected success: {data}")
            case resulty.Err(error):
                print(f"   Expected error with empty CSV: {error}")

        print()


if __name__ == "__main__":
    demonstrate_file_operations()
