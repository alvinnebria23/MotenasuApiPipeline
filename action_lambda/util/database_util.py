import os
import logging
from typing import Any, Callable, Optional, Tuple, TypeVar

import pymysql
from constant.retry_constant import RetryConstant
from context_manager.connection_context_manager import ConnectionContextManager
from exception.database_lock_exception import DatabaseLockException
from exception.database_exception import DatabaseException
from util.common_util import CommonUtil
from dbutils.pooled_db import PooledDB
from pymysql.connections import Connection
from pymysql.constants import CLIENT
from pymysql.cursors import DictCursor
from pymysql.err import MySQLError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Type aliases
T = TypeVar('T')
QueryCallback = Callable[[DictCursor], T]


class DatabaseUtil:
    """Database utility class for managing MySQL database connections and operations.

    This module provides a connection pool and utility methods for database operations,
    with built-in retry logic for handling transient database errors.
    """

    _connection_pool: Optional[PooledDB] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize the database connection pool with configuration from environment variables.

        The pool is configured with connection limits and MySQL-specific settings.
        """
        cls._connection_pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=5,
            maxcached=10,
            blocking=True,
            ping=0,
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
            cursorclass=DictCursor,
            client_flag=CLIENT.MULTI_STATEMENTS,
        )

    @classmethod
    def get_connection(cls) -> Connection:
        """Get a connection from the pool, initializing if necessary.

        Returns:
            Connection: A database connection from the pool
        """
        if cls._connection_pool is None:
            cls.initialize()
        return cls._connection_pool.connection()

    @classmethod
    def close_all_connections(cls) -> None:
        """Close all connections in the pool."""
        if cls._connection_pool is not None:
            cls._connection_pool.close()

    @classmethod
    def retry_query(cls, cursor: DictCursor, callback: QueryCallback[T]) -> T:
        """Execute a database query with retry logic for transient errors.

        Args:
            cursor: Database cursor
            callback: Function that executes the actual query

        Returns:
            T: Result from the callback function

        Raises:
            DatabaseLockException: If a retryable error occurs and max retries are exceeded
            DatabaseException: If a non-retryable MySQL error occurs
            Exception: If a general exception occurs
        """
        # List of error codes that are considered retryable
        retryable_errors = {
            1205,  # Lock wait timeout exceeded
            1213,  # Deadlock found
        }

        attempt_num = 0
        max_attempts = RetryConstant.DEFAULT_MAX_RETRIES

        while attempt_num < max_attempts:
            try:
                # Attempt to execute the callback
                return callback(cursor)

            except MySQLError as e:
                # Log the error
                logger.error(f"Database error: {str(e)}")

                # Extract error code safely
                error_code = None
                if hasattr(e, 'args') and len(e.args) > 0 and isinstance(e.args[0], int):
                    error_code = e.args[0]
                # Only consider retrying for known retryable errors
                if error_code in retryable_errors:
                    attempt_num += 1

                    # If we have attempts left, sleep and retry
                    if attempt_num < max_attempts:
                        logger.error(f"Retryable error (code={error_code}). Retrying ({attempt_num}/{max_attempts-1})...")
                        CommonUtil.sleep_with_exponential_backoff(attempt_num)
                        continue
                    else:
                        logger.error(f"Max retries exceeded. Error: {str(e)}")
                        # Use the original error tuple or message to preserve error details
                        raise DatabaseLockException(e.args if hasattr(e, 'args') else str(e))
                else:
                    logger.error(f"Non-retryable error: {str(e)}")
                    # Use the original error tuple or message to preserve error details
                    raise DatabaseException(e.args if hasattr(e, 'args') else str(e))
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                # Re-raise the original exception
                raise
        return None


    @classmethod
    def execute(
        cls,
        cursor: DictCursor,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
        execute_many: bool = False,
    ) -> int:
        """Execute a SQL query with retry logic.

        Args:
            cursor: Database cursor
            sql: SQL query string
            params: Query parameters
            execute_many: Whether to use executemany

        Returns:
            int: Number of affected rows
        """

        def callback(cursor: DictCursor) -> int:
            if execute_many:
                cursor.executemany(sql, params or ())
            else:
                cursor.execute(sql, params or ())
            return cursor.rowcount

        return cls.retry_query(cursor, callback)


    @classmethod
    def connection(cls) -> ConnectionContextManager:
        """Get a connection context manager for use in with statements.

        This method returns a context manager that, when used in a 'with' statement,
        will provide a database Connection object and ensure it's properly closed:

        Example:
            with DatabaseUtil.connection() as conn:  # conn will be of type Connection
                cursor = conn.cursor()
                # ... use the connection ...
            # connection is automatically closed here

        Returns:
            ConnectionContextManager: Context manager that provides a database connection
        """
        return ConnectionContextManager(cls.get_connection())
