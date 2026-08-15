import os
import shutil
import sqlite3

src_db = "data/nutrisense (1).db"
dst_db = "data/nutrisense.db"
backend_dst_db = "backend/data/nutrisense.db"

if not os.path.exists(src_db):
    print(f"Error: {src_db} not found!")
    exit(1)

print(f"1. Reading food_items table structure and data from {src_db}...")
conn_src = sqlite3.connect(src_db)
cur_src = conn_src.cursor()

# Get CREATE TABLE sql
cur_src.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='food_items';"
)
create_sql = cur_src.fetchone()[0]

# Get all rows
cur_src.execute("SELECT * FROM food_items;")
rows = cur_src.fetchall()
cur_src.execute("PRAGMA table_info(food_items);")
cols_info = cur_src.fetchall()
col_names = [c[1] for c in cols_info]
conn_src.close()

print(
    f"  Found {len(rows)} rows with {len(col_names)} columns in {src_db}/food_items."
)

print(f"\n2. Replacing food_items table in {dst_db}...")
conn_dst = sqlite3.connect(dst_db)
cur_dst = conn_dst.cursor()

cur_dst.execute("DROP TABLE IF EXISTS food_items;")
cur_dst.execute(create_sql)
conn_dst.commit()

placeholders = ",".join(["?"] * len(col_names))
cur_dst.executemany(f"INSERT INTO food_items VALUES ({placeholders})", rows)
conn_dst.commit()

cur_dst.execute("SELECT COUNT(*) FROM food_items;")
cnt = cur_dst.fetchone()[0]
print(f"  Successfully inserted {cnt} rows into {dst_db}/food_items!")
conn_dst.close()

# Sync to backend/data/nutrisense.db
os.makedirs("backend/data", exist_ok=True)
shutil.copy(dst_db, backend_dst_db)
print(f"\n3. Synced {dst_db} -> {backend_dst_db}")
