"""
Database operation utilities for ConsultEase.
Provides common database operations with retry logic.
"""
import logging
import functools
from sqlalchemy.exc import SQLAlchemyError
from ..models.base import db_operation_with_retry

logger = logging.getLogger(__name__)

@db_operation_with_retry(max_retries=3)
def get_by_id(db, model_class, id):
    """
    Get a model instance by ID with retry logic.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        id: Primary key ID

    Returns:
        Model instance or None if not found
    """
    return db.query(model_class).filter(model_class.id == id).first()

@db_operation_with_retry(max_retries=3)
def create_entity(db, model_class, **kwargs):
    """
    Create a new entity with retry logic.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        **kwargs: Entity attributes

    Returns:
        Created entity
    """
    entity = model_class(**kwargs)
    db.add(entity)
    db.flush()  # Flush to get the ID
    return entity

@db_operation_with_retry(max_retries=3)
def update_entity(db, entity, **kwargs):
    """
    Update an entity with retry logic.

    Args:
        db: Database session
        entity: Entity to update
        **kwargs: Attributes to update

    Returns:
        Updated entity
    """
    for key, value in kwargs.items():
        setattr(entity, key, value)
    db.flush()
    return entity

@db_operation_with_retry(max_retries=3)
def delete_entity(db, entity):
    """
    Delete an entity with retry logic.

    Args:
        db: Database session
        entity: Entity to delete

    Returns:
        True if successful
    """
    db.delete(entity)
    return True

@db_operation_with_retry(max_retries=3)
def get_all(db, model_class, **filters):
    """
    Get all entities of a model class with optional filters.

    Args:
        db: Database session
        model_class: SQLAlchemy model class
        **filters: Optional filters

    Returns:
        List of entities
    """
    query = db.query(model_class)

    # Apply filters if provided
    for attr, value in filters.items():
        if hasattr(model_class, attr):
            query = query.filter(getattr(model_class, attr) == value)

    return query.all()

def safe_commit(db):
    """
    Safely commit changes to the database with error handling.

    Args:
        db: Database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error committing changes: {e}")
        return False

class DatabaseTransaction:
    """
    Context manager for database transactions with automatic rollback on errors.
    Ensures consistent transaction handling across the application.
    """

    def __init__(self, db_session=None, auto_commit=True, max_retries=3):
        """
        Initialize transaction context manager.

        Args:
            db_session: Existing database session (if None, creates new one)
            auto_commit: Whether to automatically commit on success
            max_retries: Maximum number of retry attempts on failure
        """
        self.db_session = db_session
        self.auto_commit = auto_commit
        self.max_retries = max_retries
        self.created_session = False
        self.transaction_started = False

    def __enter__(self):
        """Enter the transaction context."""
        if self.db_session is None:
            from ..models.base import get_db
            self.db_session = get_db()
            self.created_session = True

        # Begin transaction if not already in one
        if not self.db_session.in_transaction():
            self.db_session.begin()
            self.transaction_started = True

        return self.db_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the transaction context with proper cleanup."""
        try:
            if exc_type is None:
                # No exception occurred
                if self.auto_commit and self.transaction_started:
                    self.db_session.commit()
                    logger.debug("Transaction committed successfully")
            else:
                # Exception occurred, rollback
                if self.transaction_started:
                    self.db_session.rollback()
                    logger.warning(f"Transaction rolled back due to exception: {exc_type.__name__}: {exc_val}")

        except Exception as cleanup_error:
            logger.error(f"Error during transaction cleanup: {cleanup_error}")

        finally:
            # Close session if we created it
            if self.created_session:
                self.db_session.close()

def atomic_operation(max_retries=3, retry_delay=0.1):
    """
    Decorator for atomic database operations with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            import functools

            last_error = None

            for attempt in range(max_retries):
                try:
                    with DatabaseTransaction() as db:
                        # Call the function with the database session
                        result = func(db, *args, **kwargs)
                        return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Atomic operation failed (attempt {attempt + 1}/{max_retries}): {e}")

                    if attempt < max_retries - 1:
                        sleep_time = retry_delay * (2 ** attempt)
                        time.sleep(sleep_time)

            # All retries failed
            logger.error(f"Atomic operation failed after {max_retries} attempts: {last_error}")
            raise last_error

        return wrapper
    return decorator

def bulk_operation(db, operations, batch_size=100):
    """
    Execute bulk database operations in batches with transaction management.

    Args:
        db: Database session
        operations: List of operations (functions that take db as first parameter)
        batch_size: Number of operations per batch

    Returns:
        tuple: (success_count, error_count, errors)
    """
    success_count = 0
    error_count = 0
    errors = []

    # Process operations in batches
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]

        try:
            with DatabaseTransaction(db, auto_commit=False) as tx_db:
                batch_errors = []

                for operation in batch:
                    try:
                        operation(tx_db)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        batch_errors.append(str(e))
                        logger.error(f"Bulk operation error: {e}")

                # Only commit if no errors in this batch
                if not batch_errors:
                    tx_db.commit()
                    logger.debug(f"Committed batch of {len(batch)} operations")
                else:
                    tx_db.rollback()
                    errors.extend(batch_errors)
                    logger.warning(f"Rolled back batch due to {len(batch_errors)} errors")

        except Exception as e:
            error_count += len(batch)
            errors.append(f"Batch transaction failed: {e}")
            logger.error(f"Batch transaction failed: {e}")

    return success_count, error_count, errors

def safe_execute_with_retry(db, operation, max_retries=3):
    """
    Safely execute a database operation with retry logic.

    Args:
        db: Database session
        operation: Function to execute (takes db as parameter)
        max_retries: Maximum retry attempts

    Returns:
        tuple: (success, result_or_error)
    """
    import time

    for attempt in range(max_retries):
        try:
            result = operation(db)
            return True, result

        except Exception as e:
            logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt < max_retries - 1:
                db.rollback()
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            else:
                return False, e

    return False, "Max retries exceeded"
