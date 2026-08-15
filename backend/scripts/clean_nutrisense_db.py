import os
import shutil
import sqlite3

db_path = "data/nutrisense.db"
backend_db_path = "backend/data/nutrisense.db"

# 1. Clean up unused tables in nutrisense.db
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    bad_tables = ["assessments", "meal_plans", "progress_snapshots", "symptom_responses"]
    for t in bad_tables:
        cur.execute(f"DROP TABLE IF EXISTS {t};")
        print(f"Dropped table '{t}' from {db_path}")
    conn.commit()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    print(f"\nRemaining tables in {db_path}:")
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t};")
        print(f"  - {t}: {cur.fetchone()[0]} rows")
    conn.close()

# 2. Sync to backend/data/nutrisense.db
os.makedirs("backend/data", exist_ok=True)
shutil.copy(db_path, backend_db_path)
print(f"\nSynced {db_path} -> {backend_db_path}")

# 3. Delete unwanted files/folders in data and backend/data
files_to_remove = [
    "data/nutrition.db",
    "data/users.db",
    "backend/data/nutrition.db",
    "backend/data/users.db",
    "data/download_ifct (1).sh",
    "data/download_usda (1).sh",
]

print("\nCleaning up unwanted files/folders:")
for f in files_to_remove:
    if os.path.exists(f):
        os.remove(f)
        print(f"  Removed: {f}")
