"""
Database operations example using resulty for robust error handling.

This example shows how to handle common database operation failures:
- Connection failures
- Query syntax errors
- Constraint violations
- Transaction rollbacks
- Record not found errors
- Concurrent access conflicts

Note: This example uses SQLite for simplicity and doesn't require external dependencies.
"""

import sqlite3
import tempfile
import os
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from pathlib import Path

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import resulty


# Define specific error types for database operations
class DatabaseError(resulty.ResultyException):
    """Base database error"""

    pass


class ConnectionError(DatabaseError):
    """Database connection failed"""

    pass


class QueryError(DatabaseError):
    """SQL query execution failed"""

    pass


class IntegrityError(DatabaseError):
    """Database constraint violation"""

    pass


class NotFoundError(DatabaseError):
    """Record not found"""

    pass


class TransactionError(DatabaseError):
    """Transaction operation failed"""

    pass


class UserRepository:
    """Example user repository with robust database error handling"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        age INTEGER CHECK (age >= 16 AND age <= 120),
                        department TEXT NOT NULL,
                        salary REAL CHECK (salary >= 0),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize database: {e}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                raise ConnectionError("Database is locked by another process")
            else:
                raise ConnectionError(f"Database connection failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected database error: {e}")
        finally:
            if conn:
                conn.close()

    @resulty.resulty
    def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create a new user and return the user ID"""
        required_fields = ["email", "first_name", "last_name", "age", "department"]

        # Validate required fields
        for field in required_fields:
            if field not in user_data or not user_data[field]:
                raise QueryError(f"Required field missing: {field}")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (email, first_name, last_name, age, department, salary)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_data["email"],
                        user_data["first_name"],
                        user_data["last_name"],
                        user_data["age"],
                        user_data["department"],
                        user_data.get("salary"),
                    ),
                )

                user_id = cursor.lastrowid
                conn.commit()
                return user_id

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise IntegrityError(
                    f"User with email {user_data['email']} already exists"
                )
            elif "CHECK constraint failed" in str(e):
                raise IntegrityError(
                    "User data violates database constraints (age or salary)"
                )
            else:
                raise IntegrityError(f"Database constraint violation: {e}")

        except sqlite3.Error as e:
            raise QueryError(f"Failed to create user: {e}")

    @resulty.resulty
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Retrieve a user by ID"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise QueryError("User ID must be a positive integer")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))

                row = cursor.fetchone()
                if row is None:
                    raise NotFoundError(f"User with ID {user_id} not found")

                # Convert Row to dict
                return dict(row)

        except sqlite3.Error as e:
            raise QueryError(f"Failed to retrieve user: {e}")

    @resulty.resulty
    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Retrieve a user by email"""
        if not email or not isinstance(email, str):
            raise QueryError("Email must be a non-empty string")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE email = ?", (email.lower(),)
                )

                row = cursor.fetchone()
                if row is None:
                    raise NotFoundError(f"User with email {email} not found")

                return dict(row)

        except sqlite3.Error as e:
            raise QueryError(f"Failed to retrieve user: {e}")

    @resulty.resulty
    def list_users(
        self, department: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List users, optionally filtered by department"""
        if limit <= 0 or limit > 1000:
            raise QueryError("Limit must be between 1 and 1000")

        try:
            with self._get_connection() as conn:
                if department:
                    cursor = conn.execute(
                        "SELECT * FROM users WHERE department = ? ORDER BY created_at DESC LIMIT ?",
                        (department, limit),
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM users ORDER BY created_at DESC LIMIT ?", (limit,)
                    )

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            raise QueryError(f"Failed to list users: {e}")

    @resulty.resulty
    def update_user_salary(self, user_id: int, new_salary: float) -> bool:
        """Update a user's salary"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise QueryError("User ID must be a positive integer")

        if not isinstance(new_salary, (int, float)) or new_salary < 0:
            raise QueryError("Salary must be a non-negative number")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE users SET salary = ? WHERE id = ?",
                    (float(new_salary), user_id),
                )

                if cursor.rowcount == 0:
                    raise NotFoundError(f"User with ID {user_id} not found")

                conn.commit()
                return True

        except sqlite3.IntegrityError as e:
            raise IntegrityError(f"Salary update violates constraints: {e}")
        except sqlite3.Error as e:
            raise QueryError(f"Failed to update user salary: {e}")

    @resulty.resulty
    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID"""
        if not isinstance(user_id, int) or user_id <= 0:
            raise QueryError("User ID must be a positive integer")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

                if cursor.rowcount == 0:
                    raise NotFoundError(f"User with ID {user_id} not found")

                conn.commit()
                return True

        except sqlite3.Error as e:
            raise QueryError(f"Failed to delete user: {e}")

    @resulty.resulty
    def transfer_user_department(
        self, from_dept: str, to_dept: str, user_email: str
    ) -> bool:
        """Transfer a user between departments (transactional operation)"""
        if not all([from_dept, to_dept, user_email]):
            raise QueryError(
                "All parameters (from_dept, to_dept, user_email) are required"
            )

        try:
            with self._get_connection() as conn:
                # Start transaction
                conn.execute("BEGIN TRANSACTION")

                try:
                    # Verify user exists and is in the source department
                    cursor = conn.execute(
                        "SELECT id, department FROM users WHERE email = ?",
                        (user_email,),
                    )

                    row = cursor.fetchone()
                    if row is None:
                        raise NotFoundError(f"User with email {user_email} not found")

                    current_dept = row["department"]
                    if current_dept != from_dept:
                        raise QueryError(
                            f"User is in {current_dept} department, not {from_dept}"
                        )

                    # Update the department
                    cursor = conn.execute(
                        "UPDATE users SET department = ? WHERE email = ?",
                        (to_dept, user_email),
                    )

                    if cursor.rowcount == 0:
                        raise QueryError("Failed to update user department")

                    # Log the transfer (simulated)
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO user_transfers 
                        (user_email, from_dept, to_dept, transfer_date) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                        (user_email, from_dept, to_dept),
                    )

                    # Commit transaction
                    conn.commit()
                    return True

                except Exception as e:
                    # Rollback on any error
                    conn.rollback()
                    raise TransactionError(f"Department transfer failed: {e}")

        except sqlite3.Error as e:
            raise QueryError(f"Transaction error: {e}")


def demonstrate_database_operations():
    """Show various database operation error handling scenarios"""
    print("=== Database Operations Error Handling Examples ===\n")

    # Create a temporary database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "example.db"
        repository = UserRepository(str(db_path))

        print("1. Create users (success and constraint violations):")

        # Valid user creation
        valid_user = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "department": "engineering",
            "salary": 75000,
        }

        result = repository.create_user(valid_user)
        match result:
            case resulty.Ok(user_id):
                print(f"   ✓ Created user with ID: {user_id}")
            case resulty.Err(error):
                print(f"   ✗ Error creating user: {error}")

        # Duplicate email (should fail)
        result = repository.create_user(valid_user)
        match result:
            case resulty.Ok(user_id):
                print(f"   Unexpected success: {user_id}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (duplicate email): {error}")

        # Invalid age (should fail)
        invalid_user = valid_user.copy()
        invalid_user["email"] = "invalid@example.com"
        invalid_user["age"] = 10  # Too young

        result = repository.create_user(invalid_user)
        match result:
            case resulty.Ok(user_id):
                print(f"   Unexpected success: {user_id}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (age constraint): {error}")

        print()

        print("2. Retrieve users (success and not found):")

        # Successful retrieval
        result = repository.get_user_by_email("john.doe@example.com")
        match result:
            case resulty.Ok(user):
                print(f"   ✓ Found user: {user['first_name']} {user['last_name']}")
            case resulty.Err(error):
                print(f"   ✗ Error retrieving user: {error}")

        # User not found
        result = repository.get_user_by_email("nonexistent@example.com")
        match result:
            case resulty.Ok(user):
                print(f"   Unexpected success: {user}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (user not found): {error}")

        # Invalid user ID
        result = repository.get_user_by_id(-1)
        match result:
            case resulty.Ok(user):
                print(f"   Unexpected success: {user}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (invalid ID): {error}")

        print()

        print("3. List and update operations:")

        # Create a few more users for listing
        test_users = [
            {
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "age": 28,
                "department": "marketing",
                "salary": 65000,
            },
            {
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Johnson",
                "age": 35,
                "department": "engineering",
                "salary": 85000,
            },
        ]

        for user in test_users:
            repository.create_user(user)

        # List all users
        result = repository.list_users()
        match result:
            case resulty.Ok(users):
                print(f"   ✓ Found {len(users)} total users")
            case resulty.Err(error):
                print(f"   ✗ Error listing users: {error}")

        # List users by department
        result = repository.list_users(department="engineering")
        match result:
            case resulty.Ok(users):
                print(f"   ✓ Found {len(users)} engineering users")
            case resulty.Err(error):
                print(f"   ✗ Error listing users: {error}")

        # Update salary (successful)
        result = repository.update_user_salary(1, 80000)
        match result:
            case resulty.Ok(success):
                print(f"   ✓ Updated salary successfully: {success}")
            case resulty.Err(error):
                print(f"   ✗ Error updating salary: {error}")

        # Update salary (user not found)
        result = repository.update_user_salary(999, 80000)
        match result:
            case resulty.Ok(success):
                print(f"   Unexpected success: {success}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (user not found): {error}")

        print()

        print("4. Transaction operations:")

        # Successful department transfer
        result = repository.transfer_user_department(
            "marketing", "sales", "alice@example.com"
        )
        match result:
            case resulty.Ok(success):
                print(f"   ✓ Department transfer successful: {success}")
            case resulty.Err(error):
                print(f"   ✗ Error in department transfer: {error}")

        # Failed transfer (user not in source department)
        result = repository.transfer_user_department(
            "hr", "finance", "alice@example.com"
        )
        match result:
            case resulty.Ok(success):
                print(f"   Unexpected success: {success}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (wrong source dept): {error}")

        print()

        print("5. Delete operations:")

        # Successful deletion
        result = repository.delete_user(2)  # Alice
        match result:
            case resulty.Ok(success):
                print(f"   ✓ User deleted successfully: {success}")
            case resulty.Err(error):
                print(f"   ✗ Error deleting user: {error}")

        # Delete non-existent user
        result = repository.delete_user(999)
        match result:
            case resulty.Ok(success):
                print(f"   Unexpected success: {success}")
            case resulty.Err(error):
                print(f"   ✓ Expected error (user not found): {error}")

        print()


if __name__ == "__main__":
    demonstrate_database_operations()
