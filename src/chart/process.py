"""Lambda which processes raw IEX /chart data."""

import json
import os

import boto3
import pandas as pd

from src.utils import IEX_S3_BUCKET, IEX_S3_PREFIX


def handler(event, _context):
    """Process a single file of raw data."""
    created_key = event["Records"][0]["s3"]["object"]["key"]
    *_, definition_key, filename = created_key.split("/")
    definition_key = definition_key.upper()
    timestamp, ext = filename.split(".")
    if ext != "json":
        raise ValueError("Received event notification for non-JSON file.")

    s3_client = boto3.client("s3")
    raw_data = json.loads(
        s3_client.get_object(Bucket=IEX_S3_BUCKET, Key=created_key)["Body"]
        .read()
        .decode("utf-8")
    )

    processed_data = (
        pd.DataFrame(raw_data)
        .rename(columns={"date": "timestamp", "changePercent": "percent_change"})
        .assign(
            timestamp=lambda df: (
                df["timestamp"]
                .pipe(pd.to_datetime, format="%Y-%m-%d")
                .add(pd.Timedelta("17H"))
                .dt.tz_localize(tz="US/Pacific")
                .dt.tz_convert("UTC")
            ),
            key=definition_key,
        )
        .set_index("timestamp")[["key", "percent_change", "volume"]]
        .astype({"key": "category", "percent_change": "float64", "volume": "int64"})
    )

    temp_filepath = "/tmp/processed.parquet"
    processed_data.to_parquet(temp_filepath, index=True, coerce_timestamps="ms")
    with open(temp_filepath, mode="rb") as f:
        contents = f.read()

    s3_client.put_object(
        Body=contents,
        Bucket=IEX_S3_BUCKET,
        Key=os.path.join(
            IEX_S3_PREFIX, f"processed/{definition_key}/{timestamp}.parquet"
        ),
    )
