CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INTEGER PRIMARY KEY,
    full_date    TEXT NOT NULL UNIQUE,
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    month_name   TEXT NOT NULL,
    day          INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,
    is_weekend   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_currency (
    currency_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    currency_code  TEXT NOT NULL UNIQUE,
    currency_name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_exchange_rate (
    date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
    currency_key  INTEGER NOT NULL REFERENCES dim_currency(currency_key),
    rate_pln      REAL NOT NULL,
    table_no      TEXT,
    PRIMARY KEY (date_key, currency_key)

);
