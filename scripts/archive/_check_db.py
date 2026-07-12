"""Quick script to check existing database tables."""
from db import get_engine
import sqlalchemy

e = get_engine()
with e.connect() as conn:
    r = conn.execute(sqlalchemy.text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    tables = [x[0] for x in r.fetchall()]
    print("Tables:", tables)
    print("llm_drafts exists:", "llm_drafts" in tables)
