import logging

import pandas as pd

logger = logging.getLogger(__name__)

COLUMNS = ["rate_date", "currency_code", "currency_name", "rate_pln", "table_no"]


def transform_rates(raw: list[dict]) -> pd.DataFrame:
    """Сырой JSON от NBP -> чистая плоская таблица."""
    if not raw:
        return pd.DataFrame(columns=COLUMNS)

    # 1. Разворачиваем вложенность: одна строка = одна валюта за один день
    df = pd.json_normalize(raw, record_path="rates", meta=["effectiveDate", "no"])

    # 2. Переименовываем в понятные имена
    df = df.rename(
        columns={
            "effectiveDate": "rate_date",
            "code": "currency_code",
            "currency": "currency_name",
            "mid": "rate_pln",
            "no": "table_no",
        }
    )[COLUMNS]

    # 3. Приводим типы
    df["rate_date"] = pd.to_datetime(df["rate_date"])
    df["rate_pln"] = pd.to_numeric(df["rate_pln"], errors="coerce")
    df["currency_code"] = df["currency_code"].str.strip().str.upper()
    df["currency_name"] = df["currency_name"].str.strip()

    # 4. Чистим: пропуски, нулевые/отрицательные курсы, дубли
    before = len(df)
    df = df.dropna(subset=["rate_date", "currency_code", "rate_pln"])
    df = df[df["rate_pln"] > 0]
    df = df.drop_duplicates(subset=["rate_date", "currency_code"], keep="last")
    logger.info("Удалено строк при очистке: %d", before - len(df))

    # 5. Сортируем и сбрасываем индекс
    return df.sort_values(["rate_date", "currency_code"]).reset_index(drop=True)


if __name__ == "__main__":
    from datetime import date

    from src.extract import extract_rates

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raw = extract_rates(date(2024, 1, 1), date(2024, 6, 30))
    df = transform_rates(raw)

    print(df.head(10))
    print()
    print(df.dtypes)
    print()
    print(f"Строк: {len(df)}, валют: {df['currency_code'].nunique()}, дней: {df['rate_date'].nunique()}")