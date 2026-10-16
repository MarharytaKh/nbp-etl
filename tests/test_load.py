from sqlalchemy import text

from src.load import get_engine, load_rates
from src.transform import transform_rates


def raw_for(day, eur):
    return [
        {
            "no": "001/A/NBP/2024",
            "effectiveDate": day,
            "rates": [
                {"currency": "euro", "code": "EUR", "mid": eur},
                {"currency": "dolar amerykański", "code": "USD", "mid": 3.9432},
            ],
        }
    ]


def count_facts(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM fact_exchange_rate")).scalar()


def test_loading_twice_creates_no_duplicates(tmp_path):
    engine = get_engine(f"sqlite:///{tmp_path / 'test.db'}")
    df = transform_rates(raw_for("2024-01-02", 4.3434))

    load_rates(df, engine)
    load_rates(df, engine)

    assert count_facts(engine) == 2


def test_reload_updates_changed_rate(tmp_path):
    engine = get_engine(f"sqlite:///{tmp_path / 'test.db'}")

    load_rates(transform_rates(raw_for("2024-01-02", 4.3434)), engine)
    load_rates(transform_rates(raw_for("2024-01-02", 4.3500)), engine)

    with engine.connect() as conn:
        rate = conn.execute(
            text(
                "SELECT f.rate_pln FROM fact_exchange_rate f "
                "JOIN dim_currency c ON c.currency_key = f.currency_key "
                "WHERE c.currency_code = 'EUR'"
            )
        ).scalar()
    assert rate == 4.35
    assert count_facts(engine) == 2
