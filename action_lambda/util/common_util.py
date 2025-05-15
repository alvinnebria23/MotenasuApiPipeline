import logging
import time

from constant.retry_constant import RetryConstant

logger = logging.getLogger(__name__)

class CommonUtil:
    @staticmethod
    def sleep_with_exponential_backoff(retry_count: int) -> None:
        """Implement exponential backoff delay between retries.

        Args:
            retry_count: Current retry attempt number
        """
        sleep_time = RetryConstant.RETRY_DELAY_IN_SECONDS**retry_count
        logger.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)



