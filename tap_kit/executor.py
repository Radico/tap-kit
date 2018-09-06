#!/usr/bin/env python3
import sys
import json

import singer
import base64

from singer.catalog import Catalog, CatalogEntry, Schema

from .streams import Stream
from .utils import (
    stream_is_selected, transform_write_and_count, safe_to_iso8601,
    format_last_updated_for_request, get_res_data
)

LOGGER = singer.get_logger()


class TapExecutor:
    url = None
    pagination_type = None
    replication_key_format = 'iso8601'
    res_json_key = None
    auth_type = None

    """
    url = None
    pagination_type = None
    replication_key_format = 'iso8601'
    res_json_key = None
    """

    def __init__(self, streams, args, client):
        """

        :param streams:
        :param args:
        :param client:
        """
        self.streams = streams
        self.args = args
        self.config = args.config
        self.state = args.state
        self.catalog = None
        self.selected_catalog = None
        self.client = client(self.config)

    def run(self):
        if self.args.discover:
            self.discover()
        else:
            self.sync()

    def get_res_json_key(self, stream):
        if self.res_json_key == 'STREAM':
            return stream.stream
        else:
            return self.res_json_key

    def set_catalog(self):
        self.catalog = Catalog.from_dict(self.args.properties) \
            if self.args.properties else self.discover()

        self.selected_catalog = [s for s in self.catalog.streams
                                 if stream_is_selected(s)]

    def call_full_stream(self, stream):
        """
        Method to call all full replication synced streams
        """

        LOGGER.info("Extracting %s" % stream)
        url = self.url + stream.stream

        while True:

            res = self.client.make_request(url, stream.api_path)

            transform_write_and_count(stream, res.json())

            break

    def generate_api_url(self, stream):
        return self.url + stream.stream

    def generate_auth(self):
        if self.auth_type == 'basic':
            return base64.b64encode(
                '{username}:{password}'.format(
                    username=self.config.get('username'),
                    password=self.config.get('password')
                ).encode('ascii')).decode("utf-8")
        elif self.auth_type == 'basic_key':
            return base64.b64encode(
                '{api_key}:{password}'.format(
                    api_key=self.config.get('api_key'),
                    password=''
                ).encode('ascii')).decode("utf-8")
        else:
            return None

    def build_headers(self):
        return {
            "Authorization": "Basic %s" % self.generate_auth()
        }

    def build_params(self, stream, last_updated):
        return {
            stream.stream_metadata[stream.filter_key]: last_updated
        }

    def get_latest_for_next_call(self, records, replication_key, last_updated):
        return max([safe_to_iso8601(r[replication_key]) for r in records
                   ] + [safe_to_iso8601(last_updated)])

    def should_write(self, records, stream, last_updated):
        return True


    def call_incremental_stream(self, stream):
        """
        Method to call all incremental synced streams
        """

        last_updated = format_last_updated_for_request(
            stream.update_and_return_bookmark(), self.replication_key_format)

        request_config = {
            'url': self.generate_api_url(stream),
            'headers': self.build_headers(),
            'params': self.build_params(stream, last_updated),
            'run': True
        }

        print(request_config)

        LOGGER.info("Extracting %s since %s" % (stream, last_updated))

        while request_config['run']:

            res = self.client.make_request(request_config)

            records = get_res_data(res.json(), self.get_res_json_key(stream))

            if self.should_write(records, stream, last_updated):
                transform_write_and_count(stream, records)

            last_updated = self.get_latest_for_next_call(
                records,
                stream.stream_metadata['replication-key'],
                last_updated
            )

            request_config = self.update_for_next_call(res, request_config,
                                                       last_updated)

        return last_updated

    def update_for_next_call(self, res, request_config, last_updated):
        if self.pagination_type == 'next':
            if 'next' in res.links:
                request_config['url'] = res.links['next']['url']
                return request_config
            else:
                request_config['run'] = False
                return request_config
        elif self.pagination_type == 'precise':
            if res.json()['count'] == 1000:
                request_config['params']['start_time'] = res.json()['end_time']
            else:
                request_config['run'] = False
                return request_config

    def sync_stream(self, stream):
        stream.write_schema()

        if stream.is_incremental:
            stream.set_stream_state(self.state)
            last_updated = self.call_incremental_stream(stream)
            stream.update_bookmark(last_updated)

        else:
            self.call_full_stream(stream)

    def sync(self):

        self.set_catalog()

        for c in self.selected_catalog:
            self.sync_stream(
                Stream(config=self.config, state=self.state, catalog=c)
            )

    def discover(self):

        catalog = [
            stream().generate_catalog() for stream in self.streams
        ]

        return json.dump({'streams': catalog}, sys.stdout, indent=4)
