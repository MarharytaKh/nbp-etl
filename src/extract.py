import logging
import time
from datetime import date, timedelta

import requests

BASE_URL = "https://api.nbp.pl/api/exchangerates/tables/A"
CHUNK_DAYS = 90
TIMEOUT = 30
MAX_RETRIES = 3

logger = logging.getLogger(__name__)


def make_chunks(start: date, end: date, chunk_days: int = CHUNK_DAYS):
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def fetch_chunk(start: date, end: date) -> list[dict]:
    url = f"{BASE_URL}/{start.isoformat()}/{end.isoformat()}/"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params={"format": "json"}, timeout=TIMEOUT)

            if response.status_code == 404:
                logger.info("No data for %s - %s", start, end)
                return []

            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 ** attempt)


def extract_rates(start: date, end: date) -> list[dict]:
    all_tables = []
    for chunk_start, chunk_end in make_chunks(start, end):
        logger.info("Fetching %s - %s", chunk_start, chunk_end)
        all_tables.extend(fetch_chunk(chunk_start, chunk_end))
        time.sleep(0.3)
    return all_tables
