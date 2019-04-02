import singer
import pendulum


LOGGER = singer.get_logger()


# Main invokers and runners for command line running
def main_method(config_keys, tap, client, streams):
    try:
        run_tap(config_keys, tap, client, streams)
    except Exception as exc:
        LOGGER.critical(exc)
        raise


def run_tap(config_keys, tap, client, streams):
    args = singer.utils.parse_args(
        required_config_keys=config_keys)

    tap_exc = tap(streams, args, client)

    tap_exc.run()


# Writing records
def transform_write_and_count(stream, records):
    write_records(
        stream.stream,
        [stream.transform_record(rec) for rec in records]
    )


def metrics(stream_name, records):
    with singer.metrics.record_counter(stream_name) as counter:
        counter.increment(len(records))


def write_records(stream_name, records):
    singer.write_records(stream_name, records)
    metrics(stream_name, records)


def format_last_updated_for_request(last_updated, key_format):
    if key_format == 'iso8601':
        return pendulum.parse(last_updated).to_iso8601_string()
    elif key_format == 'timestamp':
        return pendulum.parse(last_updated).int_timestamp
    elif key_format == 'datestring':
        return pendulum.parse(last_updated).to_date_string()
    elif key_format == 'datetime_string':
        return pendulum.parse(last_updated).to_datetime_string()
    else:
        return last_updated


def get_res_data(data, key):
    if key:
        return data[key]
    else:
        return data


# Stream metadata management
def get_base_stream_metadata(stream_catalog):
    metadata = singer.metadata.to_map(stream_catalog.metadata)
    return metadata.get((), {})


def stream_is_selected(stream_catalog):
    stream_metadata = get_base_stream_metadata(stream_catalog)

    inclusion = stream_metadata.get('inclusion')
    selected = stream_metadata.get('selected')

    if inclusion == 'unsupported':
        return False

    elif selected is not None:
        return selected

    return inclusion == 'automatic'


# date / time parsing
def safe_to_iso8601(date_to_parse):
    try:
        pend_date = pendulum.parse(date_to_parse)
    except TypeError:
        pend_date = pendulum.from_timestamp(date_to_parse)

    return pend_date.to_iso8601_string()


def timestamp_to_iso8601(ts):
    """
    Args:
        ts (int): epoch-formatted integer
    Returns:
        ISO 8601-formatted date string
    """
    return pendulum.from_timestamp(int(ts)).to_iso8601_string()


def date_to_date_str(date):
    """
    Args:
        date (str): date string
    Returns:
        date string in the following format: 'YYYY-MM-DD'
    """
    return pendulum.parse(date).to_date_string()


def date_to_datetime_str(date):
    """
    Args:
        date (str): date string
    Returns:
        date string in the following format: 'YYYY-MM-DD hh:mm:ss'
    """
    return pendulum.parse(date).to_datetime_string()
