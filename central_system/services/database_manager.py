"""
Enhanced Database Manager for ConsultEase.
Provides connection pooling, health monitoring, and resilient database operations.
"""

import logging
import time
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Database connection statistics."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    total_queries: int = 0
    failed_queries: int = 0
    avg_query_time: float = 0.0
    last_connection_time: Optional[datetime] = None
    last_error: Optional[str] = None


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""
    pass


class DatabaseManager:
    """
    Enhanced database manager with connection pooling and health monitoring.
    """

    def __init__(self, database_url: str, pool_size: int = 5, max_overflow: int = 10,
                 pool_timeout: int = 30, pool_recycle: int = 1800):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Time to recycle connections (seconds)
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle

        # Connection management
        self.engine = None
        self.SessionLocal = None
        self.is_initialized = False

        # Statistics and monitoring
        self.stats = ConnectionStats()

        # Thread safety
        self.lock = threading.RLock()

        logger.info("Database manager initialized")

    def initialize(self) -> bool:
        """
        Initialize database engine and connection pool.

        Returns:
            bool: True if initialization successful
        """
        with self.lock:
            if self.is_initialized:
                logger.debug("Database manager already initialized")
                return True

            try:
                # Create engine with appropriate configuration for database type
                if self.database_url.startswith('sqlite'):
                    # SQLite configuration - no connection pooling, thread safety enabled
                    self.engine = create_engine(
                        self.database_url,
                        poolclass=StaticPool,  # Use StaticPool for SQLite
                        connect_args={
                            "check_same_thread": False,  # Allow SQLite to be used across threads
                            "timeout": 20  # Connection timeout
                        },
                        pool_pre_ping=True,  # Validate connections before use
                        echo=False  # Set to True for SQL debugging
                    )
                    logger.info("Created SQLite engine with StaticPool and thread safety")
                else:
                    # PostgreSQL configuration - full connection pooling
                    self.engine = create_engine(
                        self.database_url,
                        poolclass=QueuePool,
                        pool_size=self.pool_size,
                        max_overflow=self.max_overflow,
                        pool_timeout=self.pool_timeout,
                        pool_recycle=self.pool_recycle,
                        pool_pre_ping=True,  # Validate connections before use
                        echo=False  # Set to True for SQL debugging
                    )
                    logger.info("Created PostgreSQL engine with QueuePool")

                # Setup event listeners for monitoring
                self._setup_event_listeners()

                # Create session factory
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )

                # Test initial connection
                if self._test_connection():
                    self.is_initialized = True
                    logger.info("Database manager initialized successfully")
                    return True
                else:
                    logger.error("Failed to establish initial database connection")
                    return False

            except Exception as e:
                logger.error(f"Error initializing database manager: {e}")
                self.stats.last_error = str(e)
                return False

    def get_session(self, force_new: bool = False, max_retries: int = 3) -> Session:
        """
        Get database session with retry logic.

        Args:
            force_new: Force creation of new session
            max_retries: Maximum retry attempts

        Returns:
            Session: Database session

        Raises:
            DatabaseConnectionError: If unable to get session
        """
        if not self.is_initialized:
            if not self.initialize():
                raise DatabaseConnectionError("Database manager not initialized")

        last_error = None

        for attempt in range(max_retries):
            try:
                with self.lock:
                    # Create session
                    session = self.SessionLocal()

                    self.stats.total_connections += 1
                    self.stats.active_connections += 1
                    self.stats.last_connection_time = datetime.now()

                    if force_new:
                        session.expire_all()

                    logger.debug(f"Database session acquired (attempt {attempt + 1})")
                    return session

            except Exception as e:
                last_error = e
                self.stats.failed_connections += 1
                logger.warning(f"Database session attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff
                    logger.info(f"Retrying database connection in {wait_time} seconds...")
                    time.sleep(wait_time)

                    # Try to reinitialize if connection is completely lost
                    if isinstance(e, (DisconnectionError, OperationalError)):
                        self._reinitialize_engine()

        # All attempts failed
        self.stats.last_error = str(last_error)
        raise DatabaseConnectionError(f"Unable to get database session after {max_retries} attempts: {last_error}")

    @contextmanager
    def get_session_context(self, force_new: bool = False, max_retries: int = 3):
        """
        Context manager for database sessions with automatic cleanup.

        Args:
            force_new: Force creation of new session
            max_retries: Maximum retry attempts

        Yields:
            Session: Database session
        """
        session = None
        try:
            session = self.get_session(force_new=force_new, max_retries=max_retries)
            yield session
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()
                with self.lock:
                    self.stats.active_connections = max(0, self.stats.active_connections - 1)

    def execute_query(self, query: str, params: Dict = None, max_retries: int = 3) -> Any:
        """
        Execute a query with retry logic.

        Args:
            query: SQL query to execute
            params: Query parameters
            max_retries: Maximum retry attempts

        Returns:
            Query result
        """
        start_time = time.time()

        try:
            with self.get_session_context(max_retries=max_retries) as session:
                result = session.execute(text(query), params or {})

                # Update statistics
                query_time = time.time() - start_time
                self.stats.total_queries += 1
                self._update_avg_query_time(query_time)

                return result

        except Exception as e:
            self.stats.failed_queries += 1
            logger.error(f"Query execution failed: {e}")
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get database health status.

        Returns:
            dict: Health status information
        """
        with self.lock:
            pool_status = {}
            if self.engine and hasattr(self.engine.pool, 'status'):
                pool = self.engine.pool
                pool_status = {
                    'pool_size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }

            return {
                'is_initialized': self.is_initialized,
                'stats': {
                    'total_connections': self.stats.total_connections,
                    'active_connections': self.stats.active_connections,
                    'failed_connections': self.stats.failed_connections,
                    'total_queries': self.stats.total_queries,
                    'failed_queries': self.stats.failed_queries,
                    'avg_query_time': self.stats.avg_query_time,
                    'last_connection_time': self.stats.last_connection_time.isoformat() if self.stats.last_connection_time else None,
                    'last_error': self.stats.last_error
                },
                'pool_status': pool_status
            }

    def _test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                return row and row[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def _reinitialize_engine(self):
        """Reinitialize database engine."""
        try:
            logger.info("Reinitializing database engine...")

            with self.lock:
                # Dispose of old engine
                if self.engine:
                    self.engine.dispose()

                # Reset state
                self.is_initialized = False

                # Reinitialize
                self.initialize()

        except Exception as e:
            logger.error(f"Error reinitializing database engine: {e}")

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring."""
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")

        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")

        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            logger.debug("Database connection checked in to pool")

    def _update_avg_query_time(self, query_time: float):
        """Update average query time."""
        if self.stats.total_queries == 1:
            self.stats.avg_query_time = query_time
        else:
            # Running average
            self.stats.avg_query_time = (
                (self.stats.avg_query_time * (self.stats.total_queries - 1) + query_time) /
                self.stats.total_queries
            )

    def shutdown(self):
        """Shutdown database manager."""
        logger.info("Shutting down database manager...")

        # Dispose of engine
        with self.lock:
            if self.engine:
                self.engine.dispose()
                self.engine = None

            self.SessionLocal = None
            self.is_initialized = False

        logger.info("Database manager shutdown complete")


# Singleton instance
_db_manager: Optional[DatabaseManager] = None
_db_manager_lock = threading.Lock()


def get_database_manager() -> DatabaseManager:
    """
    Get the singleton database manager instance.
    Initializes it if not already done.
    """
    global _db_manager
    if _db_manager is None:
        with _db_manager_lock:
            if _db_manager is None:
                from ..core.config import settings  # Delayed import for config
                db_url = _build_database_url(settings.DATABASE)
                _db_manager = DatabaseManager(
                    database_url=db_url,
                    pool_size=settings.DATABASE.get("POOL_SIZE", 5),
                    max_overflow=settings.DATABASE.get("MAX_OVERFLOW", 10),
                    pool_timeout=settings.DATABASE.get("POOL_TIMEOUT", 30),
                    pool_recycle=settings.DATABASE.get("POOL_RECYCLE", 1800)
                )
                if not _db_manager.initialize():
                    logger.critical("Failed to initialize the database manager.")
                    # Depending on the application's needs, you might want to raise an exception here
                    # or handle it in a way that allows the application to start in a degraded mode.
    return _db_manager


def _build_database_url(db_config: Dict[str, Any]) -> str:
    """
    Build database URL from configuration.
    Supports SQLite and PostgreSQL.
    """
    db_type = db_config.get("TYPE", "sqlite")
    if db_type == "sqlite":
        db_path = db_config.get("PATH", "./consultease.db")
        # Ensure the path is absolute for SQLite if it's a file-based DB
        import os
        if not db_path.startswith("/") and ":memory:" not in db_path:
            db_path = os.path.abspath(db_path)
        return f"sqlite:///{db_path}"
    elif db_type == "postgresql":
        user = db_config.get("USER", "postgres")
        password = db_config.get("PASSWORD", "postgres")
        host = db_config.get("HOST", "localhost")
        port = db_config.get("PORT", 5432)
        db_name = db_config.get("NAME", "consultease")
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def set_database_manager(manager: DatabaseManager):
    """
    Set a custom database manager instance (primarily for testing).
    """
    global _db_manager
    with _db_manager_lock:
        _db_manager = manager
