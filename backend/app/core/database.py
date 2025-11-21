import time
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.config.logging import logger

# Configure engine with optimized settings for SQLite concurrency
engine = create_engine(
    settings.database_url,
    connect_args={
        "check_same_thread": False,
        "timeout": 30.0  # Increased timeout for better lock handling
    },
    poolclass=NullPool,  # No connection pooling for SQLite (each connection needs its own file handle)
    pool_pre_ping=True,  # Verify connections before use
    echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Configure SQLite connection for better concurrency and performance.

    WAL mode enables:
    - Concurrent reads during writes
    - Better performance for concurrent operations
    - Readers don't block writers and vice versa
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Enable Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes while maintaining safety
    cursor.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for lock acquisition
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache for better performance
    cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
    cursor.close()
    logger.debug("SQLite connection configured with WAL mode and optimized pragmas")


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    """
    Dependency injection function for FastAPI endpoints.
    Provides a database session with proper lifecycle management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def retry_on_lock(func, max_retries=3, initial_delay=0.1):
    """
    Retry database operations if SQLite database is locked.

    Uses exponential backoff to handle temporary lock contention.
    This is useful for write operations that may conflict with
    concurrent polling operations.

    Args:
        func: Callable that performs database operation
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles with each retry)

    Returns:
        Result of func() if successful

    Raises:
        OperationalError: If database remains locked after max retries
    """
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Database locked (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise OperationalError("Database locked after max retries")
