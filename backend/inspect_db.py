"""
One-off inspection script. Run from backend/ folder:
    python inspect_db.py
Prints every table name and column info from ocean_data.db.
"""
import sqlite3

conn = sqlite3.connect("ocean_data.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)

for (table_name,) in tables:
    print(f"\n--- {table_name} ---")
    for col in cur.execute(f"PRAGMA table_info({table_name})").fetchall():
        # col = (cid, name, type, notnull, default_value, pk)
        print(f"  {col[1]:<20} {col[2]:<15} notnull={col[3]} pk={col[5]}")

    # also show a sample row so we can see real data shape
    sample = cur.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchone()
    print(f"  sample row: {sample}")

conn.close()
