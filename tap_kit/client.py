import singer
import requests
import backoff

from requests.exceptions import (
    ConnectionError,
    SSLError,
)

LOGGER = singer.get_logger()

RATE_LIMIT_ERROR_CODES =[
    429,
    503
]

BAD_REQUEST_CODES =[
    400,
    502,
    504
]


class RetryableException(Exception):
    pass


class RateLimitException(Exception):
    pass


class BaseClient:
    RATE_LIMIT_PAUSE = 30
    url = None
    auth_type = None

    def __init__(self, config):
        self.config = config

    @staticmethod
    def requests_method(method, request_config, body):
        if 'Content-Type' not in request_config['headers']:
            request_config['headers']['Content-Type'] = 'application/json'

        return requests.request(
            method,
            request_config['url'],
            headers=request_config['headers'],
            params=request_config['params'],
            json=body)

    @backoff.on_exception(backoff.expo,
                          (ConnectionError, SSLError, RetryableException),
                          max_tries=10,
                          factor=2)
    def make_request(self, request_config, body=None, method='GET'):
        LOGGER.info("Making {} request to {}".format(
            method, request_config['url']))

        with singer.metrics.Timer('request_duration', {}) as timer:
            response = self.requests_method(method, request_config, body)


        if response.status_code in RATE_LIMIT_ERROR_CODES + BAD_REQUEST_CODES:
            raise RetryableException()

        response.raise_for_status()

        return response
