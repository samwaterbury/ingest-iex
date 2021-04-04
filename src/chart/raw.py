"""Lambda which ingests data from the IEX /chart API."""

import json
import logging
import os
from datetime import datetime

import boto3
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta

from src.utils import IEX_ENDPOINT, IEX_S3_BUCKET, IEX_S3_PREFIX, IEX_TOKEN

logging.getLogger().setLevel(logging.INFO)


def now() -> datetime:
    """Get current, timezone-aware datetime."""
    return pd.Timestamp.now(tz="UTC").to_pydatetime()


CHART_RANGE_AVAILABLE_VALUES = {
    "5d": lambda: now() - relativedelta(days=5) + relativedelta(days=1),
    "1m": lambda: now() - relativedelta(months=1) + relativedelta(days=1),
    "3m": lambda: now() - relativedelta(months=3) + relativedelta(days=1),
    "6m": lambda: now() - relativedelta(months=6) + relativedelta(days=1),
    "ytd": lambda: now().replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    + relativedelta(days=1),
    "1y": lambda: now() - relativedelta(years=1) + relativedelta(days=1),
    "2y": lambda: now() - relativedelta(years=2) + relativedelta(days=1),
    "5y": lambda: now() - relativedelta(years=5) + relativedelta(days=1),
    "max": lambda: now() - relativedelta(years=15) + relativedelta(days=1),
}


def determine_chart_range(start: datetime) -> str:
    """Determine ``range`` parameter for the chart API given a min date.

    The IEX chart API accepts only one of a fix number of range parameters. Given an
    earliest date for which data is desired, one can find the smallest possible range
    parameter that will return the desired data. This function does that.

    Args:
        start: The earliest date for which data is needed.

    Returns:
        String that can be passed to the ``range`` parameter for the chart API.
    """
    chart_range = "max"
    if start is None:
        return chart_range

    for chart_range, calculate_earliest in CHART_RANGE_AVAILABLE_VALUES.items():
        if calculate_earliest() <= start:
            break

    return chart_range


def get_chart(symbol: str, chart_range: str) -> dict:
    """Retrieve data from IEX's "chart" API.

    https://iexcloud.io/docs/api/#charts

    Args:
        symbol: IEX identifier for the symbol to retrieve.
        chart_range: One of "max", "5y", "2y", "1y", "ytd", "6m", "3m", "1m", or "5d".
            Indicates the period of time to retrieve data for.

    Returns:
        JSON response body as a dictionary.
    """
    logging.info(
        "Retrieving /chart data for symbol '%s' and range '%s'.", symbol, chart_range
    )

    response = requests.get(
        url=f"{IEX_ENDPOINT}/stock/{symbol}/chart/{chart_range}",
        params={
            "token": IEX_TOKEN,
            "chartCloseOnly": True,
            "changeFromClose": True,
        },
    )

    if not response.ok:
        logging.error(
            "IEX /chart API call failed with status code %d.", response.status_code
        )

    return response.json()


def handler(event, _context):
    """Ingest data for a given symbol starting from a specified date."""
    detail = event["detail"]
    definition_key = detail["key"].lower()
    symbol = detail["symbol"]
    start = pd.Timestamp(detail["start"]).to_pydatetime()

    chart_range = determine_chart_range(start)
    data = get_chart(symbol, chart_range)
    file_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Body=bytes(json.dumps(data), encoding="utf-8"),
        Bucket=IEX_S3_BUCKET,
        Key=os.path.join(
            IEX_S3_PREFIX, f"raw/chart/{definition_key}/{file_timestamp}.json"
        ),
    )
