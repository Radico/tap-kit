import singer
import requests
import backoff

LOGGER = singer.get_logger()


class RateLimitException(Exception):
    pass


class BaseClient:
    RATE_LIMIT_PAUSE = 30
    url = None
    auth_type = None

    def __init__(self, config):
        self.config = config

    def get_authorization(self):
        if self.auth_type == 'basic':
            return requests.auth.HTTPBasicAuth(
                self.config.get('user_name'),
                self.config.get('password')
            )
        elif self.auth_type == 'basic_key':
            return requests.auth.HTTPBasicAuth(
                self.config.get('api_key'), '')
        else:
            return None

    def requests_method(self, method, request_config, body):
        request_config.update(
            {
                'headers': {'Content-Type': 'application/json'}
            }
        )

        return requests.request(
            method,
            request_config['url'],
            headers=request_config['headers'],
            auth=self.get_authorization(),
            params=request_config['params'],
            json=body)

    @backoff.on_exception(backoff.expo,
                          RateLimitException,
                          max_tries=10,
                          factor=2)
    def make_request(self, request_config, body=None, method='GET'):

        LOGGER.info("Making {} request to {}".format(
            method, request_config['url']))

        with singer.metrics.Timer('request_duration', {}) as timer:
            response = self.requests_method(method, request_config, body)

        if response.status_code in [429, 503]:
            raise RateLimitException()

        response.raise_for_status()

        return response
