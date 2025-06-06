from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os
import urllib.parse
import getpass
import logging
import time
import functools

# Set up logging (configuration handled centrally in main.py)
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures."""
    pass


class DatabaseOperationError(Exception):
    """Custom exception for database operation failures."""
    pass


# Import configuration system
from ..config import get_config

# Get configuration
config = get_config()

# Database connection settings
DB_TYPE = config.get('database.type', 'sqlite')  # Default to SQLite for development

if DB_TYPE.lower() == 'sqlite':
    # Use SQLite for development/testing
    DB_PATH = config.get('database.path', 'consultease.db')
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.info(f"Connecting to SQLite database: {DB_PATH}")
else:
    # Get current username - this will match PostgreSQL's peer authentication on Linux
    current_user = getpass.getuser()

    # PostgreSQL connection settings
    DB_USER = config.get('database.user', current_user)
    DB_PASSWORD = config.get('database.password', '')  # Empty password for peer authentication
    DB_HOST = config.get('database.host', 'localhost')
    DB_PORT = config.get('database.port', 5432)  # Default PostgreSQL port
    DB_NAME = config.get('database.name', 'consultease')

    # Create PostgreSQL connection URL
    if DB_HOST == 'localhost' and not DB_PASSWORD:
        # Use Unix socket connection for peer authentication
        DATABASE_URL = f"postgresql+psycopg2://{DB_USER}@/{DB_NAME}"
        logger.info(f"Connecting to PostgreSQL database: {DB_NAME} as {DB_USER} using peer authentication")
    else:
        # Use TCP connection with password
        encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
        DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        logger.info(f"Connecting to PostgreSQL database: {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")

# Configure connection pooling options with sensible defaults
pool_size = config.get('database.pool_size', 5)
max_overflow = config.get('database.max_overflow', 10)
pool_timeout = config.get('database.pool_timeout', 30)
pool_recycle = config.get('database.pool_recycle', 1800)  # Recycle connections after 30 minutes

# Create engine with connection pooling
if DB_TYPE.lower() == 'sqlite':
    # SQLite configuration - use StaticPool for thread safety
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,  # Use StaticPool for SQLite
        connect_args={
            "check_same_thread": False,  # Allow SQLite to be used across threads
            "timeout": 20  # Connection timeout
        },
        pool_pre_ping=True  # Check connection validity before using it
    )
    logger.info("Created SQLite engine with StaticPool and thread safety enabled")
else:
    # PostgreSQL with full connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True  # Check connection validity before using it
    )
    logger.info(f"Created PostgreSQL engine with connection pooling (size={pool_size}, max_overflow={max_overflow})")

# Create session factory with thread safety
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

# Create base class for models
Base = declarative_base()

def get_db(force_new=False, max_retries=3):
    """
    Get database session from the connection pool with enhanced error handling.

    Args:
        force_new (bool): If True, create a new session even if one exists
        max_retries (int): Maximum number of retry attempts for connection failures

    Returns:
        SQLAlchemy session: A database session from the connection pool

    Raises:
        DatabaseConnectionError: When unable to establish database connection
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            # Get a session from the pool
            db = SessionLocal()

            # Enhanced connection test with health check
            try:
                result = db.execute("SELECT 1 as health_check")
                health_check = result.fetchone()
                if not health_check or health_check[0] != 1:
                    raise DatabaseConnectionError("Health check failed")
                logger.debug(f"Database connection test successful (attempt {attempt + 1})")
            except Exception as test_error:
                db.close()
                logger.warning(f"Database connection test failed: {test_error}")

                # Implement exponential backoff for retries
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Max 30 seconds
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise DatabaseConnectionError(f"Database connection test failed after {max_retries} attempts: {test_error}")

            # If force_new is True, ensure we're getting fresh data
            if force_new:
                # Expire all objects in the session to force a refresh from the database
                db.expire_all()

            # Log connection acquisition for debugging
            logger.debug(f"Acquired database connection from pool (attempt {attempt + 1})")

            return db

        except Exception as e:
            last_error = e
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")

            # If we got a session but there was an error, make sure to close it
            if 'db' in locals():
                try:
                    db.close()
                except:
                    pass  # Ignore errors during cleanup

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # Max 10 seconds
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    # All retries failed
    error_msg = f"Failed to establish database connection after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise DatabaseConnectionError(error_msg)

def close_db():
    """
    Remove the current session and return the connection to the pool.
    This should be called when the session is no longer needed.
    """
    try:
        SessionLocal.remove()
        logger.debug("Released database connection back to pool")
    except Exception as e:
        logger.error(f"Error releasing database connection: {str(e)}")

def get_connection_pool_status():
    """
    Get current connection pool status for monitoring.

    Returns:
        dict: Connection pool statistics
    """
    try:
        pool = engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid(),
            'total_connections': pool.size() + pool.overflow(),
            'available_connections': pool.checkedin(),
            'pool_status': 'healthy' if pool.checkedin() > 0 else 'warning'
        }
    except Exception as e:
        logger.error(f"Error getting connection pool status: {e}")
        return {
            'pool_status': 'error',
            'error': str(e)
        }

def monitor_connection_pool():
    """
    Monitor connection pool health and log warnings if issues detected.
    """
    try:
        status = get_connection_pool_status()

        # Log pool status for debugging
        logger.debug(f"Connection pool status: {status}")

        # Check for potential issues
        if status.get('pool_status') == 'error':
            logger.error(f"Connection pool error: {status.get('error')}")
            return False

        # Warn if pool is nearly exhausted
        total_connections = status.get('total_connections', 0)
        available_connections = status.get('available_connections', 0)

        if total_connections > 0:
            utilization = (total_connections - available_connections) / total_connections
            if utilization > 0.8:  # 80% utilization
                logger.warning(f"High connection pool utilization: {utilization:.1%}")
                logger.warning(f"Pool stats: {status}")

        return True

    except Exception as e:
        logger.error(f"Error monitoring connection pool: {e}")
        return False

def recover_connection_pool():
    """
    Attempt to recover from connection pool issues.
    """
    try:
        logger.info("Attempting connection pool recovery...")

        # Force close all connections and recreate pool
        engine.dispose()
        logger.info("Disposed old connection pool")

        # Test new connection
        test_db = get_db()
        test_db.execute("SELECT 1")
        test_db.close()

        logger.info("✅ Connection pool recovery successful")
        return True

    except Exception as e:
        logger.error(f"❌ Connection pool recovery failed: {e}")
        return False

def db_operation_with_retry(max_retries=3, retry_delay=0.5):
    """
    Decorator for database operations with retry logic.

    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (float): Initial delay between retries in seconds (will increase exponentially)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None

            while retries < max_retries:
                db = get_db()
                try:
                    # Call the original function with the db session and all arguments
                    result = func(db, *args, **kwargs)
                    db.commit()
                    return result
                except Exception as e:
                    db.rollback()
                    last_error = e
                    retries += 1

                    # Log the error
                    if retries < max_retries:
                        logger.warning(f"Database operation failed (attempt {retries}/{max_retries}): {e}")
                        # Exponential backoff
                        sleep_time = retry_delay * (2 ** (retries - 1))
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                finally:
                    db.close()

            # If we've exhausted all retries, raise the last error
            raise last_error

        return wrapper

    return decorator

def _create_performance_indexes():
    """
    Create database indexes for frequently queried fields to improve performance.
    This is especially important for Raspberry Pi deployment where query speed matters.
    """
    try:
        # Get database connection
        db = get_db()

        # Define indexes for performance optimization
        indexes = [
            # Student table indexes
            "CREATE INDEX IF NOT EXISTS idx_student_rfid_uid ON students(rfid_uid);",
            "CREATE INDEX IF NOT EXISTS idx_student_name ON students(name);",
            "CREATE INDEX IF NOT EXISTS idx_student_department ON students(department);",

            # Faculty table indexes
            "CREATE INDEX IF NOT EXISTS idx_faculty_ble_id ON faculty(ble_id);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_status ON faculty(status);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_department ON faculty(department);",
            "CREATE INDEX IF NOT EXISTS idx_faculty_name ON faculty(name);",

            # Consultation table indexes
            "CREATE INDEX IF NOT EXISTS idx_consultation_student_id ON consultations(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_faculty_id ON consultations(faculty_id);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_status ON consultations(status);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_created_at ON consultations(created_at);",

            # Admin table indexes
            "CREATE INDEX IF NOT EXISTS idx_admin_username ON admins(username);",
            "CREATE INDEX IF NOT EXISTS idx_admin_is_active ON admins(is_active);",

            # Composite indexes for common query patterns
            "CREATE INDEX IF NOT EXISTS idx_consultation_student_status ON consultations(student_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_faculty_status ON consultations(faculty_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_consultation_requested_at ON consultations(requested_at);",

            # New indexes for enhanced consultation features
            "CREATE INDEX IF NOT EXISTS idx_consultation_busy_at ON consultations(busy_at);",
        ]

        # Execute each index creation
        for index_sql in indexes:
            try:
                db.execute(index_sql)
                logger.debug(f"Created index: {index_sql}")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {index_sql} - {str(e)}")

        db.commit()
        logger.info("Performance indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating performance indexes: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

def migrate_database_for_busy_status():
    """
    Migrate existing database to add busy_at column to consultations table.
    This function is safe to run multiple times.
    """
    try:
        # Get database connection
        db = get_db()

        # Check if busy_at column already exists
        result = db.execute("PRAGMA table_info(consultations);").fetchall()
        columns = [row[1] for row in result]
        
        if 'busy_at' not in columns:
            logger.info("Adding busy_at column to consultations table...")
            db.execute("ALTER TABLE consultations ADD COLUMN busy_at DATETIME;")
            db.commit()
            logger.info("Successfully added busy_at column to consultations table")
        else:
            logger.info("busy_at column already exists in consultations table")

        # Update the consultation status enum to include BUSY if using SQLite
        # Note: SQLite doesn't support ALTER TYPE, so we rely on the application-level enum
        logger.info("Database migration for BUSY status completed successfully")

    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        raise
    finally:
        if 'db' in locals():
            db.close()

def _ensure_admin_account_integrity():
    """
    Ensure admin account exists and is properly configured.
    This function performs comprehensive admin account validation and repair.

    Returns:
        bool: True if admin account is ready, False if there were unrecoverable errors
    """
    db = None
    try:
        # Import models here to avoid circular imports
        from .admin import Admin

        db = get_db()

        # Check for existing admin accounts
        admin_accounts = db.query(Admin).all()
        default_admin = db.query(Admin).filter(Admin.username == "admin").first()

        logger.info(f"Admin account integrity check: Found {len(admin_accounts)} admin account(s)")

        # Case 1: No admin accounts exist at all
        if len(admin_accounts) == 0:
            logger.warning("No admin accounts found - creating default admin account")
            return _create_default_admin(db)

        # Case 2: Default admin doesn't exist but other admins do
        elif not default_admin:
            logger.warning("Default 'admin' account not found - creating it")
            return _create_default_admin(db)

        # Case 3: Default admin exists - validate and fix if needed
        else:
            logger.info("Default admin account found - validating configuration")
            return _validate_and_fix_admin(db, default_admin)

    except Exception as e:
        logger.error(f"Critical error during admin account integrity check: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if db:
            db.close()

def _create_default_admin(db):
    """
    Create the default admin account with secure settings.

    Args:
        db: Database session

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from .admin import Admin

        # Create default admin with temporary password that must be changed
        password_hash, salt = Admin.hash_password("TempPass123!")
        default_admin = Admin(
            username="admin",
            password_hash=password_hash,
            salt=salt,
            is_active=True,
            force_password_change=True  # Force password change on first login
        )

        db.add(default_admin)
        db.commit()

        logger.warning("✅ Created default admin account successfully")
        logger.warning("🔑 Default credentials: admin / TempPass123!")
        logger.warning("⚠️  SECURITY NOTICE: This password MUST be changed on first login!")

        # Verify the account was created correctly
        return _test_admin_login(default_admin, "TempPass123!")

    except Exception as e:
        logger.error(f"Failed to create default admin account: {e}")
        db.rollback()
        return False

def _validate_and_fix_admin(db, admin):
    """
    Validate and fix the existing default admin account.

    Args:
        db: Database session
        admin: Admin account object

    Returns:
        bool: True if admin is valid/fixed, False otherwise
    """
    try:
        issues_found = []
        fixes_applied = []

        # Check if account is active
        if not admin.is_active:
            issues_found.append("Account is inactive")
            admin.is_active = True
            fixes_applied.append("Activated account")

        # Check if admin account has a secure password set
        # We don't store or test default passwords for security
        if admin.force_password_change:
            logger.warning("⚠️  Admin account requires password change on next login")
            issues_found.append("Password change required")

        # Ensure password change is forced for security if account seems to have default settings
        if not admin.force_password_change and admin.created_at == admin.last_password_change:
            admin.force_password_change = True
            fixes_applied.append("Enabled forced password change for security")

        # Apply fixes if any were needed
        if fixes_applied:
            db.commit()
            logger.warning(f"🔧 Fixed admin account issues: {', '.join(fixes_applied)}")
            logger.info("🔑 Admin account is configured - use admin interface to set secure password")
        else:
            logger.info("✅ Default admin account is properly configured")

        # Return success - we don't test passwords for security
        return True

    except Exception as e:
        logger.error(f"Failed to validate/fix admin account: {e}")
        db.rollback()
        return False

def _test_admin_login(admin, password):
    """
    Test admin login functionality to ensure it works.

    Args:
        admin: Admin account object
        password: Password to test

    Returns:
        bool: True if login test successful, False otherwise
    """
    try:
        # Test password verification
        if admin.check_password(password):
            logger.info("✅ Admin login test successful")
            return True
        else:
            logger.error("❌ Admin login test failed - password verification failed")
            return False

    except Exception as e:
        logger.error(f"❌ Admin login test failed with error: {e}")
        return False

def init_db(force_recreate=False, auto_create_admin=True):
    """
    Initialize the database with all tables and indexes.
    
    Args:
        force_recreate (bool): If True, drop and recreate all tables
        auto_create_admin (bool): If True, automatically ensure admin account exists
    """
    try:
        logger.info("Initializing database...")
        
        if force_recreate:
            logger.warning("Force recreating database - all data will be lost!")
            Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Run database migration for BUSY status
        migrate_database_for_busy_status()
        
        # Create performance indexes
        _create_performance_indexes()
        
        # Ensure admin account integrity only if requested
        if auto_create_admin:
            _ensure_admin_account_integrity()
            logger.info("Admin account integrity ensured")
        else:
            logger.info("Skipping automatic admin account creation (will be handled by application)")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise