from src.transform import transform_rates


def make_raw():
    return [
        {
            "no": "001/A/NBP/2024",
            "effectiveDate": "2024-01-02",
            "rates": [
                {"currency": "euro ", "code": " eur", "mid": 4.3434},
                {"currency": "dolar amerykański", "code": "USD", "mid": 3.9432},
                {"currency": "frank szwajcarski", "code": "CHF", "mid": 0},
                {"currency": "funt szterling", "code": "GBP", "mid": None},
            ],
        },
        {
            "no": "001/A/NBP/2024",
            "effectiveDate": "2024-01-02",
            "rates": [{"currency": "euro", "code": "EUR", "mid": 4.3500}],
        },
    ]


def test_cleans_and_deduplicates():
    df = transform_rates(make_raw())

    assert list(df["currency_code"]) == ["EUR", "USD"]
    assert df.loc[df["currency_code"] == "EUR", "rate_pln"].item() == 4.35
    assert df.loc[df["currency_code"] == "EUR", "currency_name"].item() == "euro"


def test_empty_input_returns_empty_frame():
    df = transform_rates([])

    assert df.empty
    assert list(df.columns) == ["rate_date", "currency_code", "currency_name", "rate_pln", "table_no"]
