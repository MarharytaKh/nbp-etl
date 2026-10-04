import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DB_URL = f"sqlite:///{ROOT / 'data' / 'nbp.db'}"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


def get_engine():
    (ROOT / "data").mkdir(exist_ok=True)
    return create_engine(DB_URL)


def init_schema(engine) -> None:
    """Создаёт таблицы, если их ещё нет."""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        raw.cursor().executescript(sql)
        raw.commit()
    finally:
        raw.close()


def load_dim_date(conn, df: pd.DataFrame) -> None:
    dates = pd.to_datetime(df["rate_date"].drop_duplicates())
    rows = [
        {
            "date_key": int(d.strftime("%Y%m%d")),
            "full_date": d.strftime("%Y-%m-%d"),
            "year": d.year,
            "quarter": d.quarter,
            "month": d.month,
            "month_name": d.strftime("%B"),
            "day": d.day,
            "day_of_week": d.dayofweek + 1,
            "is_weekend": int(d.dayofweek >= 5),
        }
        for d in dates
    ]
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO dim_date
            (date_key, full_date, year, quarter, month, month_name, day, day_of_week, is_weekend)
            VALUES (:date_key, :full_date, :year, :quarter, :month, :month_name,
                    :day, :day_of_week, :is_weekend)
            """
        ),
        rows,
    )


def load_dim_currency(conn, df: pd.DataFrame) -> None:
    rows = (
        df[["currency_code", "currency_name"]]
        .drop_duplicates("currency_code", keep="last")
        .to_dict("records")
    )
    conn.execute(
        text(
            """
            INSERT INTO dim_currency (currency_code, currency_name)
            VALUES (:currency_code, :currency_name)
            ON CONFLICT(currency_code) DO UPDATE SET currency_name = excluded.currency_name
            """
        ),
        rows,
    )


def load_fact(conn, df: pd.DataFrame) -> int:
    currency_map = dict(
        conn.execute(text("SELECT currency_code, currency_key FROM dim_currency")).all()
    )
    rows = [
        {
            "date_key": int(r.rate_date.strftime("%Y%m%d")),
            "currency_key": currency_map[r.currency_code],
            "rate_pln": float(r.rate_pln),
            "table_no": r.table_no,
        }
        for r in df.itertuples(index=False)
    ]
    conn.execute(
        text(
            """
            INSERT INTO fact_exchange_rate (date_key, currency_key, rate_pln, table_no)
            VALUES (:date_key, :currency_key, :rate_pln, :table_no)
            ON CONFLICT(date_key, currency_key) DO UPDATE SET
                rate_pln = excluded.rate_pln,
                table_no = excluded.table_no
            """
        ),
        rows,
    )
    return len(rows)


def load_rates(df: pd.DataFrame, engine=None) -> int:
    """Грузит DataFrame в звёздную схему. Можно запускать сколько угодно раз."""
    if df.empty:
        logger.info("Нечего загружать")
        return 0
    engine = engine or get_engine()
    init_schema(engine)
    with engine.begin() as conn:  # одна транзакция: или всё, или ничего
        load_dim_date(conn, df)
        load_dim_currency(conn, df)
        n = load_fact(conn, df)
    logger.info("Загружено строк фактов: %d", n)
    return n


if __name__ == "__main__":
    from datetime import date

    from src.extract import extract_rates
    from src.transform import transform_rates

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    df = transform_rates(extract_rates(date(2024, 1, 1), date(2024, 6, 30)))

    engine = get_engine()
    for run in (1, 2):  # грузим ДВАЖДЫ, чтобы проверить идемпотентность
        load_rates(df, engine)
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_exchange_rate")).scalar()
        print(f"После запуска {run}: строк в fact_exchange_rate = {count}")