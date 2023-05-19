import asyncio
import ssl
from typing import Callable

import aiohttp

from logs.Logger import get_logger
from proxy.proxy_manager import ProxyManager

from retry_strategies.retry_strategy import RetryStrategy

logger = get_logger(__name__)

class RequestGenerator:
    def __init__(self, headers=None, retry_strategy: RetryStrategy = None):
        """
        Initializes a new RequestGenerator object with the provided headers and retry strategy.

        :param headers: A dictionary of headers to be used in the HTTP requests.
        :param retry_strategy: A RetryStrategy object to be used in case of failed requests.
        """

        logger.info("Initializing RequestGenerator")
        # Set default headers if none are provided
        if headers is None:
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/106.0.0.0 Safari/537.36 "
            }

        self.headers = headers
        self.retry_strategy = retry_strategy

    async def get(self, url, headers=None, cookies=None, proxy: dict = None, message_id=None):
        """
        Sends an HTTP GET request to the specified URL with the specified headers and cookies.

        :param url: The URL to send the GET request to.
        :param headers: A dictionary of headers to be used in the GET request.
        :param cookies: A dictionary of cookies to be used in the GET request.
        :param proxy: A dictionary representing the proxy to use for the request.
        :param message_id: An identifier for the message associated with the request.
        :return: The response text if the request was successful, otherwise None.
        """

        headers = headers or self.headers
        response = None

        try:
            logger.info(f"Inside the get method for URL: {url}")
            async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=5) as session:
                async with session.get(url=url, proxy=ProxyManager.proxy_to_string(proxy), ssl=False, timeout=5) as response:
                    if response.status != 200 and response.status != 201:
                        raise aiohttp.ClientError(f"Unexpected status code {response.status} for URL: {url}")

                    logger.info(f"Succesfully made request for URL: {url}")
                    self.retry_strategy.update_proxy_rank(proxy, 1)
                    self.retry_strategy.reset_retries()
                    return await response.text()

                # return response.text()

        except (aiohttp.ClientError, asyncio.TimeoutError, AttributeError) as e:

            logger.error(f"Request failed for URL: {url}, with id: {message_id}. Going to evaluate.")

            # If the request failed, evaluate the retry strategy to determine if the request should be retried
            # Check retry strategy to see the evaluation logic
            if self.retry_strategy.evaluate(response=response, message_id=message_id):

                logger.warning(f"Retrying request for URL: {url}")
                # Decrease the rank of the proxy that was used for the failed request
                self.retry_strategy.update_proxy_rank(proxy, -1)

                # Get new proxy and new cookies for new request
                new_proxy = self.retry_strategy.get_new_proxy()
                new_cookies = self.retry_strategy.get_new_cookies()

                # Try again
                return await self.get(url, headers, new_cookies, new_proxy, message_id)

            else:
                logger.error(f"Request failed for URL: {url}, status code: {response.status if response else 0}, returning None")
                return None

    async def post(self, url, headers=None, body=None, proxy: dict = None, message_id=None):
        """
        Sends an HTTP POST request to the specified URL with the specified headers and body.

        :param url: The URL to send the POST request to.
        :param headers: A dictionary of headers to be used in the POST request
        :param body: The body of the POST request.
        :param proxy: A dictionary representing the proxy to use for the request.
        :param message_id: An identifier for the message associated with the request.

        :return: The response text if the request was successful, otherwise None.
    """
        headers = headers or self.headers
        response = None

        try:
            logger.info(f"Inside the post method for id: {message_id}")
            async with aiohttp.ClientSession(headers=headers, timeout=5) as session:
                async with session.post(url=url, data=body, proxy=ProxyManager.proxy_to_string(proxy), timeout=5) as response:
                    if response.status != 200 and response.status != 201:
                        raise aiohttp.ClientError(f"Unexpected status code {response.status} for URL: {url}")

                    logger.info(f"Succesfully made request for URL: {url} with id: {message_id}")
                    self.retry_strategy.update_proxy_rank(proxy, 1)
                    self.retry_strategy.reset_retries()
                    return await response.text()

                # return response.text()

        except (aiohttp.ClientError, asyncio.TimeoutError, AttributeError) as e:

            logger.error(f"Request failed for URL: {url}, with id: {message_id}. Going to evaluate.")

            if self.retry_strategy.evaluate(response=response, message_id=message_id):
                logger.warning(f"Retrying request for URL: {url}")
                self.retry_strategy.update_proxy_rank(proxy, -1)

                new_proxy = self.retry_strategy.get_new_proxy()

                return await self.post(url=url, headers=headers, body=body, proxy=new_proxy, message_id=message_id)
            else:
                logger.error(f"Request failed for URL: {url}, status code: {response.status if response else 0}, returning None")
                return None
