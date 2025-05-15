from exception.database_exception import DatabaseException


class DatabaseLockException(DatabaseException):
    """Exception raised when database lock-related errors occur.

    This exception is specifically designed for handling MySQL error codes 1205 (Lock wait timeout exceeded)
    and 1213 (Deadlock found) that occur during database operations. These errors indicate
    transient concurrency issues that can often be resolved by retrying the operation.

    Note: In the current implementation, original MySQL exceptions are re-raised directly
    rather than being wrapped in this exception class.

    The exception is configured with:
    - is_retry = False: The operation will not be automatically retried at the API level
    - is_send_email = True: Error notification emails will be sent
    - is_send_to_dlq = True: Failed messages will be sent to the dead letter queue
    - is_insert_to_api_error_history = True: Errors will be recorded in the API error history

    Attributes:
        message: The error message describing the exception
    """

    def __init__(self, message: str) -> None:
        """Initialize the DatabaseLockException.

        Args:
            message (str): A descriptive message explaining the database lock error.

        Note:
            This initializes the exception with specific configurations:
            - is_retry = False: Do not retry the operation at the API level
            - is_send_email = True: Send error notification emails
            - is_send_to_dlq = True: Send failed messages to dead letter queue
            - is_insert_to_api_error_history = True: Record errors in API error history
        """
        # Set is_retry explicitly to False for lock exceptions
        is_retry = False
        is_send_email = True
        is_send_to_dlq = True
        is_insert_to_api_error_history = True
        super().__init__(message, is_retry, is_send_email, is_send_to_dlq, is_insert_to_api_error_history)
