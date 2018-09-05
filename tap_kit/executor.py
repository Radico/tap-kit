#!/usr/bin/env python3
import sys
import json

import singer

from singer.catalog import Catalog, CatalogEntry, Schema

from .streams import Stream
from .utils import (
    stream_is_selected, transform_write_and_count, get_latest_for_next_call,
    format_last_updated_for_request, get_res_data
)

LOGGER = singer.get_logger()


class TapExecutor:
    url = None
    pagination_type = None
    replication_key_format = 'iso8601'
    res_json_key = None

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

    def call_incremental_stream(self, stream):
        """
        Method to call all incremental synced streams
        """

        last_updated = format_last_updated_for_request(
            stream.update_and_return_bookmark(), self.replication_key_format)

        url_for_request = self.generate_api_url(stream)

        request_config = {
            'url': url_for_request,
            'headers': {},
            'params': {stream.stream_metadata[stream.filter_key]: last_updated},
            'run': True
        }

        LOGGER.info("Extracting %s since %s" % (stream, last_updated))

        while request_config['run']:

            res = self.client.make_request(request_config)

            records = get_res_data(res.json(), self.res_json_key)

            transform_write_and_count(stream, records)

            last_updated = get_latest_for_next_call(
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
            if res['count'] == 1000:
                request_config['params']['start_time'] = res['end_time']
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
