from exception.custom_exception import CustomException


class DatabaseException(CustomException):
    """Exception raised for general database-related errors.

    This class serves as a base exception for all database-related errors in the system.
    It extends the CustomException class and configures specific behaviors for how
    database errors should be handled.

    Note that in the actual implementation, original MySQLError exceptions are re-raised
    directly when they occur, so this exception is primarily used for other database-related
    errors that don't come from the MySQL driver.

    Default configuration:
    - is_retry: Value is preserved from the constructor parameter (defaults to True)
    - is_send_email = True: Error notification emails will be sent
    - is_send_to_dlq = True: Failed messages will be sent to the dead letter queue
    - is_insert_to_api_error_history = True: Errors will be recorded in the API error history

    Attributes:
        message: The error message describing the exception
    """

    def __init__(self, message: str, is_retry: bool = True, is_send_email: bool = True, is_send_to_dlq: bool = True, is_insert_to_api_error_history: bool = True) -> None:
        """Initialize the DatabaseException.

        Args:
            message (str): A descriptive message explaining the database error.
            is_retry (bool, optional): Whether to retry the operation. Defaults to True.
            is_send_email (bool, optional): Whether to send error notification emails. Defaults to True.
            is_send_to_dlq (bool, optional): Whether to send failed messages to dead letter queue. Defaults to True.
            is_insert_to_api_error_history (bool, optional): Whether to record errors in API error history. Defaults to True.
        """
        super().__init__(message, is_retry, is_send_email, is_send_to_dlq, is_insert_to_api_error_history)
