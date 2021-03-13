"""Trigger for individual IEX ingestion functions."""

import json
import logging
import os
import re
from datetime import datetime

import boto3
import pandas as pd

from src.utils import IEX_S3_BUCKET, IEX_S3_PREFIX, load_definitions

logging.getLogger().setLevel(logging.INFO)


def determine_recency(data_key: str) -> pd.Timedelta:
    """Determine time of latest ingested data for a specific key.

    Args:
        data_key: String key identifier for the IEX data source.

    Returns:
        Latest ingestion timestamp.
    """
    s3_client = boto3.client("s3")

    data_prefix = os.path.join(IEX_S3_PREFIX, "raw", data_key.lower()) + "/"
    data_objects = s3_client.list_objects_v2(
        Bucket=IEX_S3_BUCKET,
        Prefix=data_prefix,
    )

    regex = re.compile(r"^\d{14}\.json$")
    latest_timestamp = None
    if data_objects["KeyCount"] > 0:
        for item in reversed(data_objects["Contents"]):
            filename = item["Key"][len(data_prefix) :]
            if regex.match(filename):
                filename = filename[:-5]
                naive_timestamp = datetime.strptime(filename, "%Y%m%d%H%M%S")
                latest_timestamp = pd.Timestamp(naive_timestamp, tz="UTC")
                break

    logging.info(
        "Found latest timestamp '%s' for key '%s'.", latest_timestamp, data_key
    )

    return latest_timestamp


def handler(_event, _context) -> None:
    """Determine which ingestion functions need to run and execute them."""
    events_client = boto3.client("events")

    definitions = load_definitions()
    for definition in definitions:
        data_key = definition["key"]
        data_symbol = definition["symbol"]
        data_frequency = pd.Timedelta(definition["frequency"])

        now = pd.Timestamp.now(tz="UTC")
        latest_timestamp = determine_recency(data_key)
        if latest_timestamp and now - latest_timestamp < data_frequency:
            continue

        events_client.put_events(
            Entries=[
                {
                    "Source": "ingestion.iex.trigger",
                    "DetailType": "IEX Ingestion Trigger",
                    "Detail": json.dumps(
                        {
                            "key": data_key,
                            "symbol": data_symbol,
                            "start": latest_timestamp and latest_timestamp.isoformat(),
                        }
                    ),
                    "EventBusName": "iex-ingestion",
                }
            ]
        )
