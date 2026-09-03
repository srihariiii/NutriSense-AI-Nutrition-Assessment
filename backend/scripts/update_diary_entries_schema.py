import os
import shutil
import sqlite3

db_path = "data/nutrisense.db"
backend_db_path = "backend/data/nutrisense.db"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found!")
    exit(1)

print(f"1. Migrating diary_entries table in {db_path}...")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get existing entries
cur.execute("SELECT * FROM diary_entries;")
old_entries = cur.fetchall()
cur.execute("PRAGMA table_info(diary_entries);")
old_cols = [c[1] for c in cur.fetchall()]
print(f"  Old columns ({len(old_cols)}): {old_cols}")
print(f"  Existing rows: {len(old_entries)}")

# Drop and recreate table with full nutrient columns matching food_items
cur.execute("DROP TABLE IF EXISTS diary_entries;")

create_sql = """
CREATE TABLE diary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date VARCHAR(10) NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    food_item_id INTEGER,
    food_name VARCHAR(500) NOT NULL,
    portion_grams FLOAT NOT NULL,
    calories_kcal FLOAT DEFAULT 0.0,
    protein_g FLOAT DEFAULT 0.0,
    iron_mg FLOAT DEFAULT 0.0,
    calcium_mg FLOAT DEFAULT 0.0,
    vitamin_d_mcg FLOAT DEFAULT 0.0,
    vitamin_b12_mcg FLOAT DEFAULT 0.0,
    folate_mcg FLOAT DEFAULT 0.0,
    vitamin_a_mcg FLOAT DEFAULT 0.0,
    vitamin_c_mg FLOAT DEFAULT 0.0,
    magnesium_mg FLOAT DEFAULT 0.0,
    zinc_mg FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(food_item_id) REFERENCES food_items(id)
);
"""
cur.execute(create_sql)
conn.commit()

# Re-populate existing diary entries calculating nutrients from food_items
print("\n2. Re-populating diary entries with updated nutrients...")
for row in old_entries:
    try:
        # map old row fields
        # old cols: ['id', 'user_id', 'date', 'meal_type', 'food_item_id', 'food_name', 'portion_grams', 'energy_kcal', 'protein_g', 'fat_g', 'carb_g', 'iron_mg', 'created_at']
        row_id = row[0]
        user_id = row[1]
        date_str = row[2]
        meal_type = row[3]
        food_item_id = row[4]
        food_name = row[5]
        portion_grams = row[6]
        created_at = row[12] if len(row) > 12 else None

        # Calculate nutrients from food_items if available
        calories_kcal = 0.0
        protein_g = 0.0
        iron_mg = 0.0
        calcium_mg = 0.0
        vitamin_d_mcg = 0.0
        vitamin_b12_mcg = 0.0
        folate_mcg = 0.0
        vitamin_a_mcg = 0.0
        vitamin_c_mg = 0.0
        magnesium_mg = 0.0
        zinc_mg = 0.0

        if food_item_id:
            cur.execute(
                """
                SELECT calories_kcal, protein_g, iron_mg, calcium_mg, vitamin_d_mcg, vitamin_b12_mcg, folate_mcg, vitamin_a_mcg, vitamin_c_mg, magnesium_mg, zinc_mg
                FROM food_items WHERE id = ?;
            """,
                (food_item_id,),
            )
            fi = cur.fetchone()
            if fi:
                mult = portion_grams / 100.0
                calories_kcal = round((fi[0] or 0.0) * mult, 2)
                protein_g = round((fi[1] or 0.0) * mult, 3)
                iron_mg = round((fi[2] or 0.0) * mult, 3)
                calcium_mg = round((fi[3] or 0.0) * mult, 3)
                vitamin_d_mcg = round((fi[4] or 0.0) * mult, 3)
                vitamin_b12_mcg = round((fi[5] or 0.0) * mult, 3)
                folate_mcg = round((fi[6] or 0.0) * mult, 3)
                vitamin_a_mcg = round((fi[7] or 0.0) * mult, 3)
                vitamin_c_mg = round((fi[8] or 0.0) * mult, 3)
                magnesium_mg = round((fi[9] or 0.0) * mult, 3)
                zinc_mg = round((fi[10] or 0.0) * mult, 3)

        cur.execute(
            """
            INSERT INTO diary_entries (id, user_id, date, meal_type, food_item_id, food_name, portion_grams, calories_kcal, protein_g, iron_mg, calcium_mg, vitamin_d_mcg, vitamin_b12_mcg, folate_mcg, vitamin_a_mcg, vitamin_c_mg, magnesium_mg, zinc_mg, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                row_id,
                user_id,
                date_str,
                meal_type,
                food_item_id,
                food_name,
                portion_grams,
                calories_kcal,
                protein_g,
                iron_mg,
                calcium_mg,
                vitamin_d_mcg,
                vitamin_b12_mcg,
                folate_mcg,
                vitamin_a_mcg,
                vitamin_c_mg,
                magnesium_mg,
                zinc_mg,
                created_at,
            ),
        )
    except Exception as e:
        print("  Error migrating row:", e)

conn.commit()

cur.execute("PRAGMA table_info(diary_entries);")
new_cols = [c[1] for c in cur.fetchall()]
cur.execute("SELECT COUNT(*) FROM diary_entries;")
cnt = cur.fetchone()[0]
print(
    f"\n3. Migration complete! diary_entries has {cnt} rows with {len(new_cols)} columns:"
)
print(" ", new_cols)

conn.close()

# Sync to backend/data/nutrisense.db
os.makedirs("backend/data", exist_ok=True)
shutil.copy(db_path, backend_db_path)
print(f"\nSynced {db_path} -> {backend_db_path}")
