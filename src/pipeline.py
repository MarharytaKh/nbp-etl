import argparse
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import text

from src.extract import extract_rates
from src.load import get_engine, init_schema, load_rates
from src.transform import transform_rates

DEFAULT_START = date(2024, 1, 1)

logger = logging.getLogger(__name__)


def last_loaded_date(engine) -> date | None:
    init_schema(engine)
    with engine.connect() as conn:
        value = conn.execute(text("SELECT MAX(full_date) FROM dim_date")).scalar()
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def run(start: date | None = None, end: date | None = None, engine=None) -> int:
    engine = engine or get_engine()
    end = end or date.today()

    if start is None:
        last = last_loaded_date(engine)
        start = last + timedelta(days=1) if last else DEFAULT_START

    if start > end:
        logger.info("Already up to date")
        return 0

    logger.info("Running pipeline for %s - %s", start, end)
    raw = extract_rates(start, end)
    df = transform_rates(raw)
    return load_rates(df, engine)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load NBP exchange rates (table A) into a SQLite star schema."
    )
    parser.add_argument("--start", type=date.fromisoformat,
                        help="first date YYYY-MM-DD (default: day after the last loaded date)")
    parser.add_argument("--end", type=date.fromisoformat,
                        help="last date YYYY-MM-DD (default: today)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    loaded = run(args.start, args.end)
    logger.info("Done, %d rows loaded", loaded)


if __name__ == "__main__":
    main()
