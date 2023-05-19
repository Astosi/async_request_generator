import asyncio
import json
from enum import Enum
from typing import Callable

from request_generator import RequestGenerator

from logs.Logger import get_logger

logger = get_logger(__name__)


class HttpMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'


# Use request generator to fetch data from the API
async def fetch_data(req_list: list, method: HttpMethod, generator: RequestGenerator) -> tuple:
    coroutines = []

    if method == HttpMethod.GET:
        coroutines = [generator.get(**req) for req in req_list]

    elif method == HttpMethod.POST:
        coroutines = [generator.post(**req) for req in req_list]

    elif method == HttpMethod.PUT:
        logger.warning("PUT method is not implemented yet.")

    elif method == HttpMethod.DELETE:
        logger.warning("DELETE method is not implemented yet.")

    return await asyncio.gather(*coroutines)


async def parse_requests(req_list: list, parser: Callable, method: HttpMethod,
                         generator: RequestGenerator) -> tuple:
    # Wait for the responses to come back
    responses = await fetch_data(req_list, method, generator)

    # It uses special parsers to parse the responses. Check out the parsers in utils/parsers.py
    results = parser(responses)

    return results
