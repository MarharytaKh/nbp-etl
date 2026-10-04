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
    """Режет период [start, end] на куски не длиннее chunk_days."""
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

            # 404
            if response.status_code == 404:
                logger.info("Нет данных за %s - %s", start, end)
                return []

            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            logger.warning("Попытка %d/%d не удалась: %s", attempt, MAX_RETRIES, exc)
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 ** attempt)  # пауза 2, 4, 8 сек


def extract_rates(start: date, end: date) -> list[dict]:
    all_tables = []
    for chunk_start, chunk_end in make_chunks(start, end):
        logger.info("Загружаю %s - %s", chunk_start, chunk_end)
        all_tables.extend(fetch_chunk(chunk_start, chunk_end))
        time.sleep(0.3)  # не долбим API
    return all_tables


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    data = extract_rates(date(2024, 1, 1), date(2024, 6, 30))
    print(f"Получено таблиц (торговых дней): {len(data)}")
    print(data[0])