import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "nbp.db"

if not DB.exists():
    raise SystemExit(f"Database not found: {DB}")

con = sqlite3.connect(DB)
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)["name"]
if tables.empty:
    raise SystemExit("No tables in the database")

for t in tables:
    if t.startswith("sqlite_"):
        continue
    df = pd.read_sql(f"SELECT * FROM {t}", con)
    df.to_csv(ROOT / f"{t}.csv", index=False)
    print(f"saved {t}.csv ({len(df)} rows)")
con.close()