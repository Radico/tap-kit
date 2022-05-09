import singer

from .utils import safe_to_iso8601

from pycore.text import to_unicode   


_META_FIELDS = {
    'table-key-properties': 'key_properties',
    'replication-method': 'replication_method',
    'forced-replication-method': 'replication_method',
    'valid-replication-keys': 'valid_replication_keys',
    'replication-key': 'replication_key',
    'selected-by-default': 'selected_by_default',
    'incremental-search-key': 'incremental_search_key',
    'api-path': 'api_path',
    'selected': 'selected'
}


class Stream:
    """
    Class representing a Singer stream and the required metadata to properly
    sync the stream
    Each stream has a stream, key_properties and bookmark field (if incremental)
    """

    stream = None
    api_path = None
    schema = None

    meta_fields = {v: None for k, v in _META_FIELDS.items()}

    def __init__(self, config=None, state=None, catalog=None):
        self.config = config
        self.state = state
        self.catalog = catalog
        self.api_path = self.api_path if self.api_path else self.stream

        self.build_params()

    def __str__(self):
        return self.stream

    def build_params(self):
        if self.catalog:
            self.stream = self.catalog.stream
            self.schema = self.catalog.schema
            self.meta_fields['replication_key'] = self.stream_metadata.get('replication-key')

    # ------------------------- DISCOVER MODE ------------------------- #

    def build_base_metadata(self, metadata):
        for field in _META_FIELDS:
            if self.meta_fields.get(_META_FIELDS[field]) is not None:
                self.write_base_metadata(
                    metadata, field, self.meta_fields[_META_FIELDS[field]]
                )

        self.write_base_metadata(metadata, 'inclusion', 'available')
        self.write_base_metadata(metadata, 'schema-name', self.stream)

    @staticmethod
    def write_base_metadata(metadata, k, v):
        singer.metadata.write(metadata, (), k, v)

    @property
    def stream_metadata(self):
        if self.catalog:
            return singer.metadata.to_map(self.catalog.metadata).get((), {})

    def generate_catalog(self):
        schema = self.schema
        mdata = singer.metadata.new()

        self.build_base_metadata(mdata)

        for field_name, field_schema in schema.get('properties').items():

            singer.metadata.write(
                mdata,
                ('properties', field_name),
                'inclusion',
                'automatic'
                if field_name in self.meta_fields['key_properties']
                else 'available'
            )

        return {
            'tap_stream_id': self.stream,
            'stream': self.stream,
            'schema': schema,
            'metadata': singer.metadata.to_list(mdata)
        }

    def get_catalog_keys(self):
        return list(self.catalog.schema.properties.keys())

    # ------------------------- SYNC MODE ------------------------- #

    @property
    def is_incremental(self):
        return self.stream_metadata.get('replication-method').lower() == 'incremental'

    @property
    def filter_key(self):
        return 'incremental-search-key' \
            if 'incremental-search-key' in self.stream_metadata \
            else 'replication-key'

    def write_schema(self):
        singer.write_schema(
            self.catalog.stream,
            self.catalog.schema.to_dict(),
            key_properties=self.stream_metadata.get('table-key-properties', []))

    def transform_record(self, record):
        with singer.Transformer() as tx:
            metadata = self.stream_metadata if self.catalog.metadata else {}

            record = validate_ingestible_data(record)

            return tx.transform(
                record,
                self.catalog.schema.to_dict(),
                metadata)

    # ------------------------- UPDATING STREAM STATE ------------------------- #

    def set_stream_state(self, state):
        self.state = state

    def get_bookmark(self):
        return singer.get_bookmark(self.state,
                                   self.stream,
                                   self.stream_metadata.get('replication-key'))

    def update_bookmark(self, last_updated):
        singer.bookmarks.write_bookmark(self.state,
                                        self.stream,
                                        self.stream_metadata.get('replication-key'),
                                        safe_to_iso8601(last_updated))
        singer.write_state(self.state)

    def update_start_date_bookmark(self):
        val = self.get_bookmark()

        if not val:
            val = self.config['start_date']
            self.update_bookmark(val)

    def update_and_return_bookmark(self):
        self.update_start_date_bookmark()
        return self.get_bookmark()

def validate_ingestible_data(record):
    from pycore.text import to_unicode
    import re
    
    for key, value in record.items():
        if isinstance(value, dict):
            validate_ingestible_data(value)
        else:
            try:
                record[key] = to_unicode(value)
            except UnicodeDecodeError as e:
                record[key] = ''
                pass
            if len(str(value)) != len(str(value).encode()):
                record[key] = value.encode("ascii", "ignore").replace(b'\x00', b'').decode()
    
    return record