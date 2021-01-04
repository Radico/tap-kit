from __future__ import unicode_literals

import json
from copy import deepcopy
import requests
import responses

import datetime
import random
import sys
import threading

import pytest

import backoff

from builtins import object
from tap_kit.client import BaseClient
from pytest import fixture

import logging
# from common.config import LOG_LEVEL
from requests.exceptions import (
    ConnectionError,
    SSLError,
)

logger = logging.getLogger(__name__)
# logger.setLevel(LOG_LEVEL)

class TestBaseClient(object):
    client = BaseClient(object)

    @responses.activate
    def test_bad_request_error(self):
        exception = SSLError

        # responses.add(**{
        #     'method'         : responses.GET,
        #     'url'            : 'http://example.com/api/123',
        #     'body'           :  exception,
        #     'content_type'   : 'application/json',
        #     'adding_headers' : {'X-Foo': 'Bar'}
        # })

        request_config = {
            'url'            : 'http://example.com/api/123',
            'body'           :  exception,
            'content_type'   : 'application/json',
            'adding_headers' : {'X-Foo': 'Bar'},
            'run'            : True,
            'headers'        : {},
            'params'         : {}
        }
    
        # resp = requests.get('http://example.com/api/123')
        resp = BaseClient(request_config).make_request(request_config)

        assert resp.json() == exception

        # assert len(responses.calls) == 1
        # assert responses.calls[0].request.url == 'http://example.com/api/123'
        # assert responses.calls[0].response.text == exception

    # def test_on_exception_tuple(monkeypatch):
    #     monkeypatch.setattr('time.sleep', lambda x: None)

    #     @backoff.on_exception(backoff.expo, (KeyError, ValueError))
    #     def keyerror_valueerror_then_true(log):
    #         if len(log) == 2:
    #             return True
    #         if len(log) == 0:
    #             e = KeyError()
    #         if len(log) == 1:
    #             e = ValueError()
    #         log.append(e)
    #         raise e

    #     log = []
    #     assert keyerror_valueerror_then_true(log) is True
    #     assert 2 == len(log)
    #     assert isinstance(log[0], KeyError)
    #     assert isinstance(log[1], ValueError)