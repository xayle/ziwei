import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "data" / "mingli.db"
print(f"Checking database at: {db_path}")

if not db_path.exists():
    print(f"ERROR: Database file not found at {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 获取表列表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nFound {len(tables)} tables:")
for t in tables:
    print(f"  - {t[0]}")

# 查询users表
print("\n=== Users Table Columns ===")
cursor.execute("PRAGMA table_info(users)")
rows = cursor.fetchall()
if rows:
    for r in rows:
        print(f"  {r[1]}: {r[2]}")
else:
    print("  ERROR: Users table has no columns or doesn't exist")

conn.close()

