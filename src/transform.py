import logging

import pandas as pd

logger = logging.getLogger(__name__)

COLUMNS = ["rate_date", "currency_code", "currency_name", "rate_pln", "table_no"]


def transform_rates(raw: list[dict]) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.json_normalize(raw, record_path="rates", meta=["effectiveDate", "no"])

    df = df.rename(
        columns={
            "effectiveDate": "rate_date",
            "code": "currency_code",
            "currency": "currency_name",
            "mid": "rate_pln",
            "no": "table_no",
        }
    )[COLUMNS]

    df["rate_date"] = pd.to_datetime(df["rate_date"])
    df["rate_pln"] = pd.to_numeric(df["rate_pln"], errors="coerce")
    df["currency_code"] = df["currency_code"].str.strip().str.upper()
    df["currency_name"] = df["currency_name"].str.strip()

    before = len(df)
    df = df.dropna(subset=["rate_date", "currency_code", "rate_pln"])
    df = df[df["rate_pln"] > 0]
    df = df.drop_duplicates(subset=["rate_date", "currency_code"], keep="last")
    logger.info("Rows removed during cleaning: %d", before - len(df))

    return df.sort_values(["rate_date", "currency_code"]).reset_index(drop=True)
