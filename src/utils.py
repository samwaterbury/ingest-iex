"""Common functions and variables shared by the service."""

import json
import os

import boto3

IEX_S3_BUCKET = os.environ["IEX_S3_BUCKET"]
IEX_S3_PREFIX = os.environ["IEX_S3_PREFIX"]
IEX_ENDPOINT = os.environ["IEX_ENDPOINT"]
IEX_TOKEN = os.environ["IEX_TOKEN"]


def load_definitions() -> None:
    """Load the list of IEX signal definitions.

    Returns:
        List of dictionary data source definitions.
    """
    s3_client = boto3.client("s3")

    definitions_filepath = os.path.join(IEX_S3_PREFIX, "definitions.json")
    definitions = json.loads(
        s3_client.get_object(Bucket=IEX_S3_BUCKET, Key=definitions_filepath)["Body"]
        .read()
        .decode("utf-8")
    )

    return definitions
