# RequestGenerator

This Python package provides a class RequestGenerator for sending async HTTP GET and POST requests with automatic retries in case of failures. This is especially useful for handling network errors or server-side issues that can be resolved by reattempting the request. It's super fast.
## Features

    Configurable headers
    Automatic retries using a pluggable retry strategy
    Optional use of proxies with automatic proxy management
    Configurable timeouts
    Detailed logging of request attempts and outcomes

## Requirements

    Python 3.7+
    aiohttp
    asyncio

## Usage


### Define your retry strategy
```python
retry_strategy = RetryStrategy()
```
### Instantiate RequestGenerator
```python
generator = RequestGenerator(headers={"Custom-Header": "Value"}, retry_strategy=retry_strategy)
```

### List of requests
```python
requests = ["https://httpbin.org/get", "https://httpbin.org/get"]
```

### Default parser function

```python
def default_parser(row_response: list):
    return [json.loads(response) for response in row_response]
```

### Function to parse requests

```python
async def parse_requests(req_list, parser, method, generator):
    tasks = []
    for url in req_list:
        if method == HttpMethod.GET:
            task = asyncio.ensure_future(generator.get(url))
        elif method == HttpMethod.POST:
            task = asyncio.ensure_future(generator.post(url))
        tasks.append(task)

    responses = await asyncio.gather(*tasks)

    return parser(responses)

### Use parse_requests function
responses = asyncio.run(parse_requests(req_list=requests, parser=default_parser, method=HttpMethod.GET, generator=generator))
```
