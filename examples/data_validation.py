"""
Data validation example using resulty for robust error handling.

This example shows how to handle validation failures:
- Required field validation
- Type validation
- Format validation (email, phone, etc.)
- Range validation
- Business rule validation
"""

import re
from datetime import datetime, date
from typing import Dict, Any, Optional
from dataclasses import dataclass

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import resulty


# Define specific validation error types
class ValidationError(resulty.ResultyException):
    """Base validation error"""

    pass


class RequiredFieldError(ValidationError):
    """Required field is missing or empty"""

    pass


class TypeValidationError(ValidationError):
    """Field value has incorrect type"""

    pass


class FormatValidationError(ValidationError):
    """Field value has incorrect format"""

    pass


class RangeValidationError(ValidationError):
    """Field value is outside acceptable range"""

    pass


class BusinessRuleError(ValidationError):
    """Business logic validation failed"""

    pass


@dataclass
class User:
    """User data model"""

    id: Optional[int]
    email: str
    first_name: str
    last_name: str
    age: int
    phone: Optional[str]
    birth_date: date
    salary: Optional[float]
    department: str


class UserValidator:
    """Comprehensive user data validator using resulty"""

    # Email regex pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Phone regex pattern (simple US format)
    PHONE_PATTERN = re.compile(r"^\(\d{3}\) \d{3}-\d{4}$")

    # Valid departments
    VALID_DEPARTMENTS = {
        "engineering",
        "marketing",
        "sales",
        "hr",
        "finance",
        "support",
    }

    @resulty.resulty
    def validate_user(self, data: Dict[str, Any]) -> User:
        """Validate and create a User object from raw data"""

        # Validate required fields
        email = self._validate_email(data)
        first_name = self._validate_first_name(data)
        last_name = self._validate_last_name(data)
        age = self._validate_age(data)
        birth_date = self._validate_birth_date(data)
        department = self._validate_department(data)

        # Validate optional fields
        user_id = self._validate_id(data)
        phone = self._validate_phone(data)
        salary = self._validate_salary(data)

        # Business rule validation
        self._validate_business_rules(age, birth_date, salary, department)

        return User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            age=age,
            phone=phone,
            birth_date=birth_date,
            salary=salary,
            department=department,
        )

    def _validate_email(self, data: Dict[str, Any]) -> str:
        """Validate email field"""
        if "email" not in data:
            raise RequiredFieldError("Email is required")

        email = data["email"]
        if not isinstance(email, str):
            raise TypeValidationError("Email must be a string")

        email = email.strip()
        if not email:
            raise RequiredFieldError("Email cannot be empty")

        if not self.EMAIL_PATTERN.match(email):
            raise FormatValidationError("Invalid email format")

        if len(email) > 254:  # RFC 5321 limit
            raise RangeValidationError("Email address too long")

        return email.lower()

    def _validate_first_name(self, data: Dict[str, Any]) -> str:
        """Validate first name field"""
        if "first_name" not in data:
            raise RequiredFieldError("First name is required")

        first_name = data["first_name"]
        if not isinstance(first_name, str):
            raise TypeValidationError("First name must be a string")

        first_name = first_name.strip()
        if not first_name:
            raise RequiredFieldError("First name cannot be empty")

        if len(first_name) > 50:
            raise RangeValidationError("First name too long (max 50 characters)")

        if not first_name.replace(" ", "").replace("-", "").isalpha():
            raise FormatValidationError(
                "First name can only contain letters, spaces, and hyphens"
            )

        return first_name.title()

    def _validate_last_name(self, data: Dict[str, Any]) -> str:
        """Validate last name field"""
        if "last_name" not in data:
            raise RequiredFieldError("Last name is required")

        last_name = data["last_name"]
        if not isinstance(last_name, str):
            raise TypeValidationError("Last name must be a string")

        last_name = last_name.strip()
        if not last_name:
            raise RequiredFieldError("Last name cannot be empty")

        if len(last_name) > 50:
            raise RangeValidationError("Last name too long (max 50 characters)")

        if not last_name.replace(" ", "").replace("-", "").isalpha():
            raise FormatValidationError(
                "Last name can only contain letters, spaces, and hyphens"
            )

        return last_name.title()

    def _validate_age(self, data: Dict[str, Any]) -> int:
        """Validate age field"""
        if "age" not in data:
            raise RequiredFieldError("Age is required")

        age = data["age"]
        if isinstance(age, str) and age.isdigit():
            age = int(age)
        elif not isinstance(age, int):
            raise TypeValidationError("Age must be an integer")

        if age < 16:
            raise RangeValidationError("Age must be at least 16")
        if age > 120:
            raise RangeValidationError("Age must be less than 120")

        return age

    def _validate_birth_date(self, data: Dict[str, Any]) -> date:
        """Validate birth date field"""
        if "birth_date" not in data:
            raise RequiredFieldError("Birth date is required")

        birth_date = data["birth_date"]

        # Handle different input formats
        if isinstance(birth_date, str):
            try:
                # Try ISO format first
                if "T" in birth_date or " " in birth_date:
                    birth_date = datetime.fromisoformat(
                        birth_date.replace("Z", "+00:00")
                    ).date()
                else:
                    birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    # Try US format
                    birth_date = datetime.strptime(birth_date, "%m/%d/%Y").date()
                except ValueError:
                    raise FormatValidationError(
                        "Invalid birth date format. Use YYYY-MM-DD or MM/DD/YYYY"
                    )

        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        elif not isinstance(birth_date, date):
            raise TypeValidationError("Birth date must be a date, datetime, or string")

        # Validate date range
        today = date.today()
        if birth_date > today:
            raise RangeValidationError("Birth date cannot be in the future")

        # Check reasonable age range (16-120 years)
        min_birth_date = date(today.year - 120, today.month, today.day)
        max_birth_date = date(today.year - 16, today.month, today.day)

        if birth_date < min_birth_date:
            raise RangeValidationError("Birth date indicates age over 120")
        if birth_date > max_birth_date:
            raise RangeValidationError("Birth date indicates age under 16")

        return birth_date

    def _validate_department(self, data: Dict[str, Any]) -> str:
        """Validate department field"""
        if "department" not in data:
            raise RequiredFieldError("Department is required")

        department = data["department"]
        if not isinstance(department, str):
            raise TypeValidationError("Department must be a string")

        department = department.strip().lower()
        if not department:
            raise RequiredFieldError("Department cannot be empty")

        if department not in self.VALID_DEPARTMENTS:
            valid_depts = ", ".join(sorted(self.VALID_DEPARTMENTS))
            raise FormatValidationError(
                f"Invalid department. Must be one of: {valid_depts}"
            )

        return department

    def _validate_id(self, data: Dict[str, Any]) -> Optional[int]:
        """Validate optional ID field"""
        if "id" not in data or data["id"] is None:
            return None

        user_id = data["id"]
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        elif not isinstance(user_id, int):
            raise TypeValidationError("ID must be an integer")

        if user_id <= 0:
            raise RangeValidationError("ID must be a positive integer")

        return user_id

    def _validate_phone(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate optional phone field"""
        if "phone" not in data or not data["phone"]:
            return None

        phone = data["phone"]
        if not isinstance(phone, str):
            raise TypeValidationError("Phone must be a string")

        phone = phone.strip()
        if not phone:
            return None

        if not self.PHONE_PATTERN.match(phone):
            raise FormatValidationError("Phone must be in format: (XXX) XXX-XXXX")

        return phone

    def _validate_salary(self, data: Dict[str, Any]) -> Optional[float]:
        """Validate optional salary field"""
        if "salary" not in data or data["salary"] is None:
            return None

        salary = data["salary"]
        if isinstance(salary, str):
            try:
                salary = float(salary.replace(",", "").replace("$", ""))
            except ValueError:
                raise TypeValidationError("Salary must be a number")
        elif isinstance(salary, int):
            salary = float(salary)
        elif not isinstance(salary, float):
            raise TypeValidationError("Salary must be a number")

        if salary < 0:
            raise RangeValidationError("Salary cannot be negative")
        if salary > 10000000:  # 10M cap
            raise RangeValidationError("Salary cannot exceed $10,000,000")

        return salary

    def _validate_business_rules(
        self, age: int, birth_date: date, salary: Optional[float], department: str
    ) -> None:
        """Validate business logic rules"""
        # Check age consistency with birth date
        today = date.today()
        calculated_age = today.year - birth_date.year
        if today.month < birth_date.month or (
            today.month == birth_date.month and today.day < birth_date.day
        ):
            calculated_age -= 1

        if abs(calculated_age - age) > 1:  # Allow 1 year difference for birthday timing
            raise BusinessRuleError("Age does not match birth date")

        # Department-specific salary rules
        if salary is not None and department == "hr" and salary > 200000:
            raise BusinessRuleError("HR department salary cannot exceed $200,000")

        if salary is not None and department == "engineering" and salary < 50000:
            raise BusinessRuleError("Engineering department minimum salary is $50,000")


def demonstrate_validation():
    """Show various validation error handling scenarios"""
    print("=== Data Validation Error Handling Examples ===\n")

    validator = UserValidator()

    # Test data scenarios
    test_cases = [
        {
            "name": "Valid user",
            "data": {
                "id": 1,
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "age": 30,
                "phone": "(555) 123-4567",
                "birth_date": "1993-05-15",
                "salary": 75000.0,
                "department": "engineering",
            },
        },
        {
            "name": "Missing required field",
            "data": {
                "first_name": "Jane",
                "last_name": "Smith",
                "age": 25,
                "birth_date": "1998-01-01",
                "department": "marketing",
                # Missing email
            },
        },
        {
            "name": "Invalid email format",
            "data": {
                "email": "invalid-email",
                "first_name": "Bob",
                "last_name": "Johnson",
                "age": 35,
                "birth_date": "1988-03-10",
                "department": "sales",
            },
        },
        {
            "name": "Age out of range",
            "data": {
                "email": "young@example.com",
                "first_name": "Too",
                "last_name": "Young",
                "age": 12,  # Too young
                "birth_date": "2011-01-01",
                "department": "support",
            },
        },
        {
            "name": "Invalid department",
            "data": {
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Wonder",
                "age": 28,
                "birth_date": "1995-06-20",
                "department": "mystery",  # Invalid department
            },
        },
        {
            "name": "Age/birth date mismatch",
            "data": {
                "email": "mismatch@example.com",
                "first_name": "Age",
                "last_name": "Mismatch",
                "age": 50,  # Age doesn't match birth date
                "birth_date": "1995-01-01",  # Would make them ~28
                "department": "finance",
            },
        },
        {
            "name": "Business rule violation",
            "data": {
                "email": "hr.person@example.com",
                "first_name": "High",
                "last_name": "Salary",
                "age": 40,
                "birth_date": "1983-01-01",
                "salary": 300000,  # Too high for HR
                "department": "hr",
            },
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}:")

        result = validator.validate_user(test_case["data"])
        match result:
            case resulty.Ok(user):
                print(f"   ✓ Valid: {user.first_name} {user.last_name} ({user.email})")
                print(f"     Age: {user.age}, Department: {user.department}")
                if user.salary:
                    print(f"     Salary: ${user.salary:,.2f}")
            case resulty.Err(error):
                error_type = type(error).__name__
                print(f"   ✗ {error_type}: {error}")

        print()


if __name__ == "__main__":
    demonstrate_validation()
