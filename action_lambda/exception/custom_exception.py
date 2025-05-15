class CustomException(Exception):
    """Base exception class with configurable error handling properties.

    This class extends the standard Exception class to provide additional
    functionality for error handling and reporting. It allows configuration
    of email notifications, DLQ routing, and error history logging.

    Attributes:
        is_send_email (bool): Whether to send an email notification about this error.
        is_send_to_dlq (bool): Whether to send this error to the Dead Letter Queue.
        is_insert_to_api_error_history (bool): Whether to log this error in the API error history.
    """

    def __init__(
        self,
        message: str,
        is_retry: bool = False,
        is_send_email: bool = True,
        is_send_to_dlq: bool = True,
        is_insert_to_api_error_history: bool = True,
    ) -> None:
        """Initialize the CustomException with configurable error handling properties.

        Args:
            message (str): A descriptive message explaining the error.
            is_retry (bool, optional): Whether to retry the operation. Defaults to False.
            is_send_email (bool, optional): Whether to send an email notification. Defaults to True.
            is_send_to_dlq (bool, optional): Whether to send this error to the Dead Letter Queue. Defaults to True.
            is_insert_to_api_error_history (bool, optional): Whether to log this error in the API error history. Defaults to True
        """
        super().__init__(message)
        self.is_retry = is_retry
        self.is_send_email = is_send_email
        self.is_send_to_dlq = is_send_to_dlq
        self.is_insert_to_api_error_history = is_insert_to_api_error_history

    def __str__(self) -> str:
        """Return a string representation of the exception with its configuration.

        Returns:
            str: A formatted string containing the error message and configuration settings.
        """
        return self.args[0]
