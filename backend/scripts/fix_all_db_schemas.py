"""
Migration & Alignment script to ensure ALL tables in data/nutrisense.db
match the exact SQLAlchemy models defined in backend/models.py.
"""

import os
import shutil
import sqlite3
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import Base, engine
from models import DiaryEntry, FoodItem, HealthProfile, LabResult, User

DB_PATH = BACKEND_DIR.parent / "data" / "nutrisense.db"
BACKEND_DB_PATH = BACKEND_DIR / "data" / "nutrisense.db"


def fix_schemas():
    print("=" * 60)
    print("  ALIGNING ALL DATABASE SCHEMAS WITH BACKEND MODELS")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"Error: {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Fix health_profiles table if columns mismatch
    cur.execute("PRAGMA table_info(health_profiles);")
    hp_cols = [c[1] for c in cur.fetchall()]
    if "age_years" in hp_cols or "age" not in hp_cols:
        print("\n[1/4] Migrating 'health_profiles' table...")
        cur.execute("SELECT * FROM health_profiles;")
        old_hp = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS health_profiles;")
        conn.commit()

        # Re-create using SQLAlchemy metadata
        HealthProfile.__table__.create(bind=engine, checkfirst=True)

        for row in old_hp:
            # Row mapping based on old schema:
            # (id, user_id, age_years, gender, height_cm, weight_kg, activity_level, health_goal, diet_restrictions, conditions)
            try:
                row_id = row[0]
                user_id = row[1]
                age = row[2] if len(row) > 2 and row[2] else 25
                sex_val = row[3] if len(row) > 3 and row[3] else "Male"
                sex = "Male" if str(sex_val) in ["1", "Male", "male"] else "Female"
                height_cm = row[4] if len(row) > 4 and row[4] else 170.0
                weight_kg = row[5] if len(row) > 5 and row[5] else 70.0
                activity_level = row[6] if len(row) > 6 and row[6] else "Moderately active"
                health_goal = row[7] if len(row) > 7 and row[7] else "Improve overall health"
                dietary_restrictions = row[8] if len(row) > 8 and row[8] else '["None"]'

                cur.execute(
                    """
                    INSERT INTO health_profiles (id, user_id, age, sex, height_cm, weight_kg, activity_level, health_goal, dietary_restrictions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (row_id, user_id, age, sex, height_cm, weight_kg, activity_level, health_goal, dietary_restrictions),
                )
            except Exception as e:
                print("  Warning migrating health profile row:", e)

        conn.commit()
        print("  -> Migrated health_profiles table successfully!")

    # 2. Fix lab_results table
    cur.execute("PRAGMA table_info(lab_results);")
    lab_cols = [c[1] for c in cur.fetchall()]
    if "hemoglobin_g_dl" in lab_cols or "hemoglobin" not in lab_cols:
        print("\n[2/4] Migrating 'lab_results' table...")
        cur.execute("SELECT * FROM lab_results;")
        old_labs = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS lab_results;")
        conn.commit()

        LabResult.__table__.create(bind=engine, checkfirst=True)

        for row in old_labs:
            try:
                cur.execute(
                    """
                    INSERT INTO lab_results (id, user_id, hemoglobin, serum_vitamin_d, ferritin, vitamin_b12, calcium)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (row[0], row[1], row[2], row[4] if len(row)>4 else None, row[3] if len(row)>3 else None, row[7] if len(row)>7 else None, row[6] if len(row)>6 else None),
                )
            except Exception as e:
                print("  Warning migrating lab results row:", e)

        conn.commit()
        print("  -> Migrated lab_results table successfully!")

    # 3. Fix diary_entries table
    cur.execute("PRAGMA table_info(diary_entries);")
    de_cols = [c[1] for c in cur.fetchall()]
    if "entry_date" in de_cols or "date" not in de_cols or "energy_kcal" not in de_cols:
        print("\n[3/4] Migrating 'diary_entries' table...")
        cur.execute("SELECT * FROM diary_entries;")
        old_de = cur.fetchall()

        cur.execute("DROP TABLE IF EXISTS diary_entries;")
        conn.commit()

        DiaryEntry.__table__.create(bind=engine, checkfirst=True)

        for row in old_de:
            try:
                # Map old columns to new columns:
                # old: (id, user_id, entry_date, meal_type, food_id, food_name, portion_grams, calories_kcal, protein_g, ...)
                row_id = row[0]
                user_id = row[1]
                entry_date = row[2]
                meal_type = row[3]
                food_id = row[4]
                food_name = row[5]
                portion_grams = row[6]
                energy_kcal = row[7] if len(row) > 7 and row[7] else 0.0
                protein_g = row[8] if len(row) > 8 and row[8] else 0.0

                cur.execute(
                    """
                    INSERT INTO diary_entries (id, user_id, date, meal_type, food_item_id, food_name, portion_grams, energy_kcal, protein_g, fat_g, carb_g, iron_mg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (row_id, user_id, entry_date, meal_type, food_id, food_name, portion_grams, energy_kcal, protein_g, 0.0, 0.0, 0.0),
                )
            except Exception as e:
                print("  Warning migrating diary entry row:", e)

        conn.commit()
        print("  -> Migrated diary_entries table successfully!")

    # 4. Fix food_items table if missing columns
    cur.execute("PRAGMA table_info(food_items);")
    fi_cols = [c[1] for c in cur.fetchall()]
    if "energy_kcal" not in fi_cols or "vitc_mg" not in fi_cols:
        print("\n[4/4] Migrating 'food_items' table...")
        cur.execute("DROP TABLE IF EXISTS food_items;")
        conn.commit()
        FoodItem.__table__.create(bind=engine, checkfirst=True)
        conn.close()

        # Run 8734 food import script
        from import_exact_8734_foods import import_all
        import_all()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

    # Ensure all tables exist matching SQLAlchemy metadata
    Base.metadata.create_all(bind=engine)

    print(f"\n{'=' * 60}")
    print("  VERIFYING ALL TABLES IN DATABASE")
    print(f"{'=' * 60}")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]
    for t in sorted(tables):
        cur.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cur.fetchall()]
        cur.execute(f"SELECT count(*) FROM {t};")
        cnt = cur.fetchone()[0]
        print(f"  Table: {t:16s} ({cnt:5d} rows) -> Columns: {cols}")

    conn.close()

    # Sync to backend/data/nutrisense.db
    os.makedirs(BACKEND_DB_PATH.parent, exist_ok=True)
    shutil.copy(DB_PATH, BACKEND_DB_PATH)
    print(f"\nSynced {DB_PATH} -> {BACKEND_DB_PATH}")


if __name__ == "__main__":
    fix_schemas()
