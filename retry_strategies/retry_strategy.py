from abc import ABC

import requests

from proxy.proxy_manager import ProxyManager
from logs.Logger import get_logger

logger = get_logger(__name__)


class RetryStrategy(ABC):

    def __init__(self, max_retries: int, proxy_manager=None):
        logger.info(f"Initializing {self.__class__.__name__} with max_retries: {max_retries}")

        self.proxy_manager = proxy_manager or ProxyManager(proxy_list_size=50)
        self.proxy_manager.load_proxies()

        self.max_retries = max_retries
        self.retries = 0

    def update_proxy_rank(self, proxy: dict, delta: int):
        self.proxy_manager.update_proxy_rank(proxy, delta)

    def get_new_proxy(self):
        proxy = self.proxy_manager.get_proxy()
        logger.info(f"New proxy: {proxy}")
        return proxy


    def refresh_proxy(self):
        logger.info(f"Refreshing proxy...")
        self.proxy_manager.load_proxies()

    def reset_retries(self):
        if self.retries > 0:
            logger.info(f"Resetting retry counter to 0")
            self.retries = 0

    def should_retry(self):
        logger.info(f"Retries for {self.__class__.__name__} is {self.retries} and max_retries is {self.max_retries}")
        if self.retries < self.max_retries:
            self.retries += 1
            return True

        logger.warning(f"Max retries reached for {self.__class__.__name__}")
        return False

    def evaluate(self, response, message_id : str) -> bool:

        if response:
            response_code = response.status
            logger.warning(f"Response code: {response_code} for message {message_id}")
        else:
            logger.warning(f"No response received for message {message_id}")
            response_code = 0

        # Sometimes the url doesn't exist, so we can just ignore it
        if response_code in (404, 400):
            return False

        # Define a set of HTTP status codes that indicate an error that you can solve via retrying.
        error_codes = {403, 500, 503, 504, 412, 0}

        # Check the retry count
        should_retry = self.should_retry()

        # 3 is arbitrary, load the proxy list again. It will be running parallely so new proxies will be loaded
        if response_code in error_codes and self.retries % 3 == 0:
            logger.info(f"Received status code {self.retries}, retry limit reached, refreshing proxy")
            self.refresh_proxy()

        return True

