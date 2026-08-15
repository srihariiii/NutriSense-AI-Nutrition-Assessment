import os
import shutil
import sqlite3

src_db = "data/nutrition.db"
users_db = "data/users.db"
dst_db = "backend/data/nutrition.db"

# Sync tables from users.db if present
if os.path.exists(users_db):
    conn_u = sqlite3.connect(users_db)
    conn_n = sqlite3.connect(src_db)

    for table in ["users", "health_profiles", "diary_entries", "lab_results"]:
        try:
            cur_u = conn_u.cursor()
            cur_u.execute(f"SELECT count(*) FROM {table}")
            u_count = cur_u.fetchone()[0]
            if u_count > 0:
                print(f"Syncing table '{table}' ({u_count} rows)...")
                cur_u.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                )
                sql_row = cur_u.fetchone()
                if sql_row and sql_row[0]:
                    conn_n.cursor().execute(f"DROP TABLE IF EXISTS {table}")
                    conn_n.cursor().execute(sql_row[0])
                    conn_n.commit()

                cur_u.execute(f"SELECT * FROM {table}")
                rows = cur_u.fetchall()
                if rows:
                    placeholders = ",".join(["?"] * len(rows[0]))
                    conn_n.cursor().executemany(
                        f"INSERT INTO {table} VALUES ({placeholders})", rows
                    )
                    conn_n.commit()
        except Exception as e:
            print(f"Note on {table}:", e)

    conn_u.close()
    conn_n.close()

# Remove old/unused tables
conn = sqlite3.connect(src_db)
cur = conn.cursor()
for tbl in ["assessments", "meal_plans", "progress_snapshots", "symptom_responses"]:
    cur.execute(f"DROP TABLE IF EXISTS {tbl}")
conn.commit()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print("\nTables in data/nutrition.db:")
for t in tables:
    cur.execute(f"SELECT count(*) FROM {t}")
    print(f"  - {t}: {cur.fetchone()[0]} rows")
conn.close()

# Sync to backend/data/nutrition.db
os.makedirs("backend/data", exist_ok=True)
shutil.copy(src_db, dst_db)
print(f"\nSuccessfully synced {src_db} -> {dst_db}")
