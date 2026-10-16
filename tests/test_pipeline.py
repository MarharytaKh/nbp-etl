from datetime import date

import src.pipeline as pipeline
from src.load import get_engine


def fake_extract(calls):
    def extract(start, end):
        calls.append((start, end))
        return [
            {
                "no": "001/A/NBP/2024",
                "effectiveDate": end.isoformat(),
                "rates": [{"currency": "euro", "code": "EUR", "mid": 4.3}],
            }
        ]

    return extract


def test_next_run_starts_after_last_loaded_date(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline, "extract_rates", fake_extract(calls))
    engine = get_engine(f"sqlite:///{tmp_path / 'test.db'}")

    pipeline.run(date(2024, 1, 2), date(2024, 1, 5), engine)
    pipeline.run(end=date(2024, 1, 10), engine=engine)

    assert calls[1] == (date(2024, 1, 6), date(2024, 1, 10))


def test_up_to_date_does_not_call_api(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline, "extract_rates", fake_extract(calls))
    engine = get_engine(f"sqlite:///{tmp_path / 'test.db'}")

    pipeline.run(date(2024, 1, 2), date(2024, 1, 5), engine)
    loaded = pipeline.run(end=date(2024, 1, 5), engine=engine)

    assert loaded == 0
    assert len(calls) == 1
