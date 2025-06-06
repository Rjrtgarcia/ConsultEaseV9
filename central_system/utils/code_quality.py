"""
Code quality utilities and refactoring helpers for ConsultEase.
Provides common patterns and utilities to improve code maintainability.
"""

import logging
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, TypeVar
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class OperationResult:
    """
    Standardized result container for operations.
    Provides consistent success/error handling across the codebase.
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_result(cls, data: Any = None, metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult':
        """Create a successful operation result."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def error_result(cls, error: str, error_code: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult':
        """Create an error operation result."""
        return cls(success=False, error=error, error_code=error_code, metadata=metadata)
    
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.success
    
    def is_error(self) -> bool:
        """Check if operation failed."""
        return not self.success
    
    def get_data(self, default: Any = None) -> Any:
        """Get operation data with optional default."""
        return self.data if self.success else default
    
    def get_error_message(self) -> str:
        """Get error message or empty string if successful."""
        return self.error or ""


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.code = code
        self.message = message


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.message = message


def safe_operation(default_return: Any = None, log_errors: bool = True) -> Callable:
    """
    Decorator for safe operation execution with standardized error handling.
    
    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors
    
    Returns:
        Decorated function that returns OperationResult
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> OperationResult:
            try:
                result = func(*args, **kwargs)
                return OperationResult.success_result(result)
            except ValidationError as e:
                if log_errors:
                    logger.warning(f"Validation error in {func.__name__}: {e.message}")
                return OperationResult.error_result(e.message, "VALIDATION_ERROR")
            except BusinessLogicError as e:
                if log_errors:
                    logger.warning(f"Business logic error in {func.__name__}: {e.message}")
                return OperationResult.error_result(e.message, e.code)
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return OperationResult.error_result(str(e), "UNEXPECTED_ERROR")
        return wrapper
    return decorator


def retry_operation(max_retries: int = 3, delay: float = 0.1, 
                   exponential_backoff: bool = True) -> Callable:
    """
    Decorator for retrying operations with configurable backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries
        exponential_backoff: Whether to use exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        sleep_time = delay * (2 ** attempt) if exponential_backoff else delay
                        logger.debug(f"Retry {attempt + 1}/{max_retries} for {func.__name__} in {sleep_time}s")
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Operation {func.__name__} failed after {max_retries} retries")
            
            raise last_exception
        return wrapper
    return decorator


def timed_operation(log_slow_threshold: float = 1.0) -> Callable:
    """
    Decorator for timing operations and logging slow ones.
    
    Args:
        log_slow_threshold: Threshold in seconds to log slow operations
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if duration > log_slow_threshold:
                    logger.warning(f"Slow operation {func.__name__}: {duration:.2f}s")
                else:
                    logger.debug(f"Operation {func.__name__}: {duration:.2f}s")
        return wrapper
    return decorator


@contextmanager
def error_context(operation_name: str, reraise: bool = True):
    """
    Context manager for standardized error handling and logging.
    
    Args:
        operation_name: Name of the operation for logging
        reraise: Whether to reraise exceptions
    """
    try:
        logger.debug(f"Starting operation: {operation_name}")
        yield
        logger.debug(f"Completed operation: {operation_name}")
    except Exception as e:
        logger.error(f"Error in operation {operation_name}: {str(e)}")
        if reraise:
            raise


class InputValidator:
    """
    Centralized input validation utilities.
    """
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Any:
        """Validate that a required field is not None or empty."""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required", field_name, "REQUIRED")
        return value
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: int = 0, 
                             max_length: int = None) -> str:
        """Validate string length constraints."""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name, "INVALID_TYPE")
        
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters", 
                field_name, "TOO_SHORT"
            )
        
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters", 
                field_name, "TOO_LONG"
            )
        
        return value
    
    @staticmethod
    def validate_email(email: str, field_name: str = "email") -> str:
        """Validate email format."""
        import re
        
        if not isinstance(email, str):
            raise ValidationError(f"{field_name} must be a string", field_name, "INVALID_TYPE")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(f"Invalid {field_name} format", field_name, "INVALID_FORMAT")
        
        return email.lower().strip()
    
    @staticmethod
    def validate_integer_range(value: int, field_name: str, min_value: int = None, 
                             max_value: int = None) -> int:
        """Validate integer range constraints."""
        if not isinstance(value, int):
            raise ValidationError(f"{field_name} must be an integer", field_name, "INVALID_TYPE")
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}", 
                field_name, "TOO_SMALL"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}", 
                field_name, "TOO_LARGE"
            )
        
        return value


class DataProcessor:
    """
    Common data processing utilities.
    """
    
    @staticmethod
    def chunk_list(data: List[T], chunk_size: int) -> List[List[T]]:
        """Split a list into chunks of specified size."""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    @staticmethod
    def filter_dict(data: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
        """Filter dictionary to only include allowed keys."""
        return {k: v for k, v in data.items() if k in allowed_keys}
    
    @staticmethod
    def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple dictionaries, with later ones taking precedence."""
        result = {}
        for d in dicts:
            result.update(d)
        return result
    
    @staticmethod
    def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Safely get nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default


def create_error_handler(operation_name: str, default_return: Any = None) -> Callable:
    """
    Create a standardized error handler for specific operations.
    
    Args:
        operation_name: Name of the operation for logging
        default_return: Default value to return on error
    
    Returns:
        Error handler function
    """
    def error_handler(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"Validation error in {operation_name}: {e.message}")
                return default_return
            except BusinessLogicError as e:
                logger.warning(f"Business logic error in {operation_name}: {e.message}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                return default_return
        return wrapper
    return error_handler


# Common validation patterns
def validate_faculty_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate faculty data with standardized rules."""
    validator = InputValidator()
    
    validated = {}
    validated['name'] = validator.validate_string_length(
        validator.validate_required(data.get('name'), 'name'),
        'name', min_length=2, max_length=100
    )
    validated['department'] = validator.validate_string_length(
        validator.validate_required(data.get('department'), 'department'),
        'department', min_length=2, max_length=100
    )
    validated['email'] = validator.validate_email(
        validator.validate_required(data.get('email'), 'email')
    )
    
    # Optional fields
    if 'ble_id' in data and data['ble_id']:
        validated['ble_id'] = validator.validate_string_length(
            data['ble_id'], 'ble_id', min_length=12, max_length=17
        )
    
    return validated


def validate_student_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate student data with standardized rules."""
    validator = InputValidator()
    
    validated = {}
    validated['name'] = validator.validate_string_length(
        validator.validate_required(data.get('name'), 'name'),
        'name', min_length=2, max_length=100
    )
    validated['student_id'] = validator.validate_string_length(
        validator.validate_required(data.get('student_id'), 'student_id'),
        'student_id', min_length=5, max_length=20
    )
    validated['email'] = validator.validate_email(
        validator.validate_required(data.get('email'), 'email')
    )
    
    # Optional fields
    if 'course' in data and data['course']:
        validated['course'] = validator.validate_string_length(
            data['course'], 'course', max_length=100
        )
    
    return validated
