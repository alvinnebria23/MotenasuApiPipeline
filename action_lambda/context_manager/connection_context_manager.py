from typing import Any, Optional, Type

from pymysql.connections import Connection


class ConnectionContextManager:
    """Context manager for handling database connections.

    This module provides a context manager for handling MySQL database connections,
    ensuring proper connection lifecycle management and cleanup.
    """

    def __init__(self, connection: Connection):
        """Initialize the context manager.

        Args:
            connection: Database connection to manage
        """
        self.connection: Connection = connection

    def __enter__(self) -> Connection:
        """Enter the context, returning the actual database connection.

        This method is called when entering a 'with' block and provides the connection
        object that will be used within the block.

        Returns:
            Connection: The managed database connection
        """
        return self.connection

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Exit the context, closing the connection.

        This method is called when exiting a 'with' block (either normally or due to an exception)
        and ensures the connection is properly closed.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        self.connection.close()
