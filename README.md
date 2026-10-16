# NBP Exchange Rates ETL

A small ETL pipeline that collects daily average exchange rates (table A) from the
[National Bank of Poland API](https://api.nbp.pl/), cleans them and loads them into a
SQLite data warehouse built as a star schema, ready for SQL analysis or a BI tool.

## How it works

**Extract** (`src/extract.py`)
The NBP API returns a limited date range per request, so a longer period is split into
90-day chunks. Failed requests are retried with a growing pause (2, 4, 8 s). Days without
data (weekends, public holidays) come back as 404 and are skipped.

**Transform** (`src/transform.py`)
The nested JSON is flattened with pandas into one row per currency per day. Types are
fixed, codes are normalised, and rows with missing or non-positive rates and duplicate
`(date, currency)` pairs are removed.

**Load** (`src/load.py`)
Data goes into a star schema:

```
            dim_date                     dim_currency
   (date_key, year, quarter,      (currency_key, code, name)
    month, day_of_week, ...)                 |
                 \                           /
                  fact_exchange_rate
           (date_key, currency_key, rate_pln)
```

The fact table has a primary key on `(date_key, currency_key)` and rows are written with
an upsert (`INSERT ... ON CONFLICT DO UPDATE`). Each load runs in a single transaction.
This makes the pipeline idempotent: running it twice for the same period does not create
duplicates, and a corrected rate from NBP simply overwrites the old value.

**Pipeline** (`src/pipeline.py`)
Without arguments, it checks the last date already in the database and loads only the
new days up to today. On an empty database it starts from 2024-01-01.

## Running

```bash
pip install -r requirements.txt

python -m src.pipeline
python -m src.pipeline --start 2024-01-01 --end 2024-06-30
```

The database is created in `data/nbp.db`.

### Daily schedule

Linux / macOS (cron, every weekday at 13:00, after NBP publishes the table):

```
0 13 * * 1-5 cd /path/to/nbp-etl && python -m src.pipeline >> pipeline.log 2>&1
```

On Windows the same command can be added to Task Scheduler.

## Analytics

`sql/analytics.sql` contains example queries:

1. Latest rate for every currency
2. Monthly average, min and max for EUR, USD, GBP and CHF
3. Change between the first and the last rate in the period, per currency
4. Top 10 most volatile currencies (price range as % of the average)
5. Biggest day-to-day moves of EUR and USD (window function `LAG`)
6. Data quality check: currencies with missing trading days

Example results for January–June 2024 (125 trading days, 33 currencies, 4,125 rows):
USD/PLN rose by 2.25% over the period, and its largest single-day move was +1.96% on
2024-06-10.

## Tests

```bash
pytest
```

The tests cover data cleaning, idempotent loading (same data loaded twice, row count
unchanged), updating a corrected rate, and the incremental start date of the pipeline.
The API is mocked, so tests run offline.

## Tech

Python, pandas, requests, SQLAlchemy, SQLite, pytest

## Next steps

- Power BI report on top of the star schema
- Alert when a scheduled run fails
- Table C (buy/sell rates) and gold prices from the same API
