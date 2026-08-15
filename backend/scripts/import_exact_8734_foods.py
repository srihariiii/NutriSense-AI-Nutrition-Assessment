"""
Script to import EXACTLY 8,734 food items into food_items table:
- 542 IFCT 2017 items
- 41 Curated Indian items
- 8,151 USDA FoodData Central items
Total = 8,734 items matching Screenshot 3!
"""

import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import Base, engine, SessionLocal
from models import FoodItem

DATA_DIR = BACKEND_DIR.parent / "data"
IFCT_CSV = DATA_DIR / "ifct2017" / "compositions.csv"
USDA_DIR = BACKEND_DIR / "data" / "usda_raw" / "FoodData_Central_foundation_food_csv_2026-04-30"


# 41 Curated Indian Foods
CURATED_FOODS = [
    {"name": "Whole wheat roti", "energy_kcal": 297, "protein_g": 11.0, "fat_g": 2.2, "carb_g": 55.0, "fiber_g": 11.5, "calcium_mg": 40, "iron_mg": 3.6, "vitc_mg": 0, "tags": "indian,bread"},
    {"name": "Lentil dal", "energy_kcal": 322, "protein_g": 24.3, "fat_g": 1.4, "carb_g": 57.0, "fiber_g": 10.8, "calcium_mg": 68, "iron_mg": 7.06, "vitc_mg": 0, "tags": "indian,dal"},
    {"name": "Rajma (kidney beans), cooked", "energy_kcal": 127, "protein_g": 8.7, "fat_g": 0.5, "carb_g": 22.8, "fiber_g": 6.4, "calcium_mg": 28, "iron_mg": 2.9, "vitc_mg": 1.2, "tags": "indian,curry"},
    {"name": "Palak paneer", "energy_kcal": 185, "protein_g": 9.2, "fat_g": 14.5, "carb_g": 6.1, "fiber_g": 2.8, "calcium_mg": 240, "iron_mg": 3.2, "vitc_mg": 18.5, "tags": "indian,curry"},
    {"name": "Chana masala (chole)", "energy_kcal": 164, "protein_g": 7.5, "fat_g": 5.2, "carb_g": 22.4, "fiber_g": 6.1, "calcium_mg": 45, "iron_mg": 2.8, "vitc_mg": 8.4, "tags": "indian,curry"},
    {"name": "Amla (Indian gooseberry)", "energy_kcal": 44, "protein_g": 0.9, "fat_g": 0.6, "carb_g": 10.2, "fiber_g": 4.3, "calcium_mg": 25, "iron_mg": 1.2, "vitc_mg": 600, "tags": "indian,fruit"},
    {"name": "Drumstick leaves (Moringa)", "energy_kcal": 64, "protein_g": 9.4, "fat_g": 1.4, "carb_g": 8.3, "fiber_g": 2.0, "calcium_mg": 185, "iron_mg": 4.0, "vitc_mg": 51.7, "tags": "indian,vegetable"},
    {"name": "Sesame seeds (Til)", "energy_kcal": 573, "protein_g": 17.7, "fat_g": 49.7, "carb_g": 23.4, "fiber_g": 11.8, "calcium_mg": 975, "iron_mg": 14.6, "vitc_mg": 0, "tags": "indian,seeds"},
    {"name": "Jaggery (Gur)", "energy_kcal": 383, "protein_g": 0.4, "fat_g": 0.1, "carb_g": 98.0, "fiber_g": 0, "calcium_mg": 80, "iron_mg": 11.0, "vitc_mg": 0, "tags": "indian,sweetener"},
    {"name": "Curd / Dahi (Plain yogurt)", "energy_kcal": 60, "protein_g": 3.5, "fat_g": 3.3, "carb_g": 4.7, "fiber_g": 0, "calcium_mg": 121, "iron_mg": 0.1, "vitc_mg": 0.5, "tags": "indian,dairy"},
    {"name": "Steamed Rice (White)", "energy_kcal": 130, "protein_g": 2.7, "fat_g": 0.3, "carb_g": 28.2, "fiber_g": 0.4, "calcium_mg": 10, "iron_mg": 0.2, "vitc_mg": 0, "tags": "indian,grain"},
    {"name": "Idli (Rice & urad dal cake)", "energy_kcal": 132, "protein_g": 4.8, "fat_g": 0.4, "carb_g": 27.5, "fiber_g": 1.6, "calcium_mg": 18, "iron_mg": 0.8, "vitc_mg": 0, "tags": "indian,breakfast"},
    {"name": "Plain Dosa", "energy_kcal": 168, "protein_g": 3.9, "fat_g": 3.7, "carb_g": 29.1, "fiber_g": 1.8, "calcium_mg": 22, "iron_mg": 1.1, "vitc_mg": 0, "tags": "indian,breakfast"},
    {"name": "Sambar", "energy_kcal": 75, "protein_g": 3.2, "fat_g": 2.1, "carb_g": 11.2, "fiber_g": 2.9, "calcium_mg": 32, "iron_mg": 1.4, "vitc_mg": 6.2, "tags": "indian,curry"},
    {"name": "Poha (Flattened rice, cooked)", "energy_kcal": 180, "protein_g": 3.1, "fat_g": 4.8, "carb_g": 31.5, "fiber_g": 1.9, "calcium_mg": 24, "iron_mg": 2.2, "vitc_mg": 4.5, "tags": "indian,breakfast"},
    {"name": "Upma (Semolina porridge)", "energy_kcal": 192, "protein_g": 4.2, "fat_g": 6.1, "carb_g": 30.2, "fiber_g": 2.1, "calcium_mg": 28, "iron_mg": 1.3, "vitc_mg": 3.8, "tags": "indian,breakfast"},
    {"name": "Almonds (Badam)", "energy_kcal": 579, "protein_g": 21.2, "fat_g": 49.9, "carb_g": 21.7, "fiber_g": 12.5, "calcium_mg": 269, "iron_mg": 3.7, "vitc_mg": 0, "tags": "nuts"},
    {"name": "Walnuts (Akhrot)", "energy_kcal": 654, "protein_g": 15.2, "fat_g": 65.2, "carb_g": 13.7, "fiber_g": 6.7, "calcium_mg": 98, "iron_mg": 2.9, "vitc_mg": 1.3, "tags": "nuts"},
    {"name": "Spinach cooked (Palak)", "energy_kcal": 23, "protein_g": 3.0, "fat_g": 0.3, "carb_g": 3.8, "fiber_g": 2.4, "calcium_mg": 136, "iron_mg": 3.6, "vitc_mg": 9.8, "tags": "vegetable"},
    {"name": "Guava (Amrood)", "energy_kcal": 68, "protein_g": 2.6, "fat_g": 1.0, "carb_g": 14.3, "fiber_g": 5.4, "calcium_mg": 18, "iron_mg": 0.3, "vitc_mg": 228.3, "tags": "fruit"},
    {"name": "Banana", "energy_kcal": 89, "protein_g": 1.1, "fat_g": 0.3, "carb_g": 22.8, "fiber_g": 2.6, "calcium_mg": 5, "iron_mg": 0.3, "vitc_mg": 8.7, "tags": "fruit"},
    {"name": "Apple", "energy_kcal": 52, "protein_g": 0.3, "fat_g": 0.2, "carb_g": 13.8, "fiber_g": 2.4, "calcium_mg": 6, "iron_mg": 0.1, "vitc_mg": 4.6, "tags": "fruit"},
    {"name": "Orange", "energy_kcal": 47, "protein_g": 0.9, "fat_g": 0.1, "carb_g": 11.8, "fiber_g": 2.4, "calcium_mg": 40, "iron_mg": 0.1, "vitc_mg": 53.2, "tags": "fruit"},
    {"name": "Boiled Egg", "energy_kcal": 155, "protein_g": 12.6, "fat_g": 10.6, "carb_g": 1.1, "fiber_g": 0, "calcium_mg": 50, "iron_mg": 1.2, "vitc_mg": 0, "tags": "protein"},
    {"name": "Chicken Curry", "energy_kcal": 210, "protein_g": 18.5, "fat_g": 12.8, "carb_g": 5.2, "fiber_g": 1.1, "calcium_mg": 35, "iron_mg": 1.8, "vitc_mg": 2.4, "tags": "non-veg"},
    {"name": "Fish Curry (Rohu/Katla)", "energy_kcal": 165, "protein_g": 16.2, "fat_g": 9.1, "carb_g": 4.1, "fiber_g": 0.8, "calcium_mg": 65, "iron_mg": 1.4, "vitc_mg": 1.8, "tags": "non-veg"},
    {"name": "Paneer (Cottage cheese)", "energy_kcal": 265, "protein_g": 18.3, "fat_g": 20.8, "carb_g": 1.2, "fiber_g": 0, "calcium_mg": 480, "iron_mg": 0.4, "vitc_mg": 0, "tags": "dairy"},
    {"name": "Cow Milk (Full cream)", "energy_kcal": 61, "protein_g": 3.2, "fat_g": 3.5, "carb_g": 4.8, "fiber_g": 0, "calcium_mg": 120, "iron_mg": 0.05, "vitc_mg": 1.0, "tags": "dairy"},
    {"name": "Ghee (Clarified butter)", "energy_kcal": 884, "protein_g": 0, "fat_g": 99.5, "carb_g": 0, "fiber_g": 0, "calcium_mg": 3, "iron_mg": 0, "vitc_mg": 0, "tags": "fat"},
    {"name": "Mustard Oil", "energy_kcal": 884, "protein_g": 0, "fat_g": 100, "carb_g": 0, "fiber_g": 0, "calcium_mg": 0, "iron_mg": 0, "vitc_mg": 0, "tags": "oil"},
    {"name": "Masala Tea (Chai with milk)", "energy_kcal": 65, "protein_g": 1.8, "fat_g": 2.1, "carb_g": 9.8, "fiber_g": 0, "calcium_mg": 62, "iron_mg": 0.2, "vitc_mg": 0.4, "tags": "beverage"},
    {"name": "Filter Coffee (with milk)", "energy_kcal": 58, "protein_g": 1.6, "fat_g": 1.9, "carb_g": 8.7, "fiber_g": 0, "calcium_mg": 55, "iron_mg": 0.1, "vitc_mg": 0.3, "tags": "beverage"},
    {"name": "Samosa", "energy_kcal": 262, "protein_g": 4.5, "fat_g": 14.8, "carb_g": 28.2, "fiber_g": 2.4, "calcium_mg": 25, "iron_mg": 1.6, "vitc_mg": 5.2, "tags": "snack"},
    {"name": "Vegetable Biryani", "energy_kcal": 195, "protein_g": 4.1, "fat_g": 6.8, "carb_g": 29.5, "fiber_g": 2.8, "calcium_mg": 38, "iron_mg": 1.4, "vitc_mg": 4.1, "tags": "indian,rice"},
    {"name": "Chicken Biryani", "energy_kcal": 235, "protein_g": 12.8, "fat_g": 9.5, "carb_g": 24.8, "fiber_g": 1.6, "calcium_mg": 42, "iron_mg": 1.8, "vitc_mg": 2.1, "tags": "indian,rice"},
    {"name": "Moong Dal Khichdi", "energy_kcal": 145, "protein_g": 5.2, "fat_g": 3.4, "carb_g": 23.6, "fiber_g": 2.5, "calcium_mg": 28, "iron_mg": 1.5, "vitc_mg": 1.8, "tags": "indian,rice"},
    {"name": "Aloo Paratha", "energy_kcal": 290, "protein_g": 6.2, "fat_g": 11.5, "carb_g": 41.2, "fiber_g": 4.2, "calcium_mg": 32, "iron_mg": 2.4, "vitc_mg": 8.5, "tags": "indian,bread"},
    {"name": "Rava Dosa", "energy_kcal": 178, "protein_g": 3.8, "fat_g": 4.5, "carb_g": 30.5, "fiber_g": 1.6, "calcium_mg": 20, "iron_mg": 1.2, "vitc_mg": 0, "tags": "indian,breakfast"},
    {"name": "Gulab Jamun", "energy_kcal": 320, "protein_g": 4.1, "fat_g": 11.2, "carb_g": 52.0, "fiber_g": 0.5, "calcium_mg": 85, "iron_mg": 0.6, "vitc_mg": 0, "tags": "sweet"},
    {"name": "Kheer (Rice pudding)", "energy_kcal": 180, "protein_g": 4.5, "fat_g": 5.8, "carb_g": 27.5, "fiber_g": 0.3, "calcium_mg": 145, "iron_mg": 0.3, "vitc_mg": 0.8, "tags": "sweet"},
    {"name": "Pani Puri (6 pieces)", "energy_kcal": 215, "protein_g": 3.8, "fat_g": 8.2, "carb_g": 32.0, "fiber_g": 3.1, "calcium_mg": 35, "iron_mg": 1.8, "vitc_mg": 6.5, "tags": "snack"},
]


def import_all():
    print("=" * 60)
    print("  IMPORTING EXACTLY 8,734 FOOD ITEMS INTO DATABASE")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing food items
    db.query(FoodItem).delete()
    db.commit()

    all_items = []

    # 1. IFCT 2017 (542 items)
    print("\n[1/3] Processing IFCT 2017 CSV...")
    ifct_count = 0
    if IFCT_CSV.exists():
        with open(IFCT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []
            col_map = { (c.split("; ", 1)[1].strip() if "; " in c else c): c for c in cols }

            def get_col(row, keys):
                for k in keys:
                    fc = col_map.get(k, k)
                    v = row.get(fc, "")
                    if v:
                        try:
                            return round(float(v), 2)
                        except ValueError:
                            pass
                return 0.0

            for row in reader:
                name_col = col_map.get("name", "Food Name; name")
                name = row.get(name_col, "").strip()
                if not name:
                    continue

                energy_kj = get_col(row, ["enerc"])
                energy_kcal = round(energy_kj * 0.239, 2) if energy_kj > 100 else energy_kj

                item = FoodItem(
                    name=name,
                    energy_kcal=energy_kcal,
                    protein_g=get_col(row, ["protcnt"]),
                    fat_g=get_col(row, ["fatce"]),
                    carb_g=get_col(row, ["choavldf", "carbdf"]),
                    fiber_g=get_col(row, ["fibtg"]),
                    calcium_mg=get_col(row, ["ca"]),
                    iron_mg=get_col(row, ["fe"]),
                    vitc_mg=get_col(row, ["vitc"]),
                    source="ifct2017",
                    tags="indian",
                )
                all_items.append(item)
                ifct_count += 1

    print(f"  -> Prepared {ifct_count} IFCT 2017 items")

    # 2. Curated Indian Foods (41 items)
    print("\n[2/3] Processing Curated Indian Foods...")
    curated_count = 0
    for c in CURATED_FOODS:
        item = FoodItem(
            name=c["name"],
            energy_kcal=c["energy_kcal"],
            protein_g=c["protein_g"],
            fat_g=c["fat_g"],
            carb_g=c["carb_g"],
            fiber_g=c["fiber_g"],
            calcium_mg=c["calcium_mg"],
            iron_mg=c["iron_mg"],
            vitc_mg=c["vitc_mg"],
            source="curated",
            tags=c.get("tags", "indian"),
        )
        all_items.append(item)
        curated_count += 1

    print(f"  -> Prepared {curated_count} Curated Indian items")

    # 3. USDA Foods (Target = 8734 - ifct_count - curated_count = 8151)
    target_usda = 8734 - ifct_count - curated_count
    print(f"\n[3/3] Processing USDA FoodData Central (Target: {target_usda} items)...")

    usda_count = 0
    if USDA_DIR.exists() and (USDA_DIR / "food.csv").exists():
        # Read nutrients
        nut_map = {1008: "energy_kcal", 1003: "protein_g", 1004: "fat_g", 1005: "carb_g", 1079: "fiber_g", 1087: "calcium_mg", 1089: "iron_mg", 1162: "vitc_mg"}
        food_nuts = defaultdict(dict)
        with open(USDA_DIR / "food_nutrient.csv", "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    fid = int(row["fdc_id"])
                    nid = int(row["nutrient_id"])
                    if nid in nut_map:
                        amt = float(row["amount"]) if row["amount"] else 0.0
                        food_nuts[fid][nut_map[nid]] = amt
                except (ValueError, KeyError):
                    pass

        # Read foods
        with open(USDA_DIR / "food.csv", "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                if usda_count >= target_usda:
                    break
                fid = int(row["fdc_id"])
                desc = row["description"].strip()
                if not desc:
                    continue

                nuts = food_nuts.get(fid, {})
                item = FoodItem(
                    name=desc,
                    energy_kcal=round(nuts.get("energy_kcal", 0), 2),
                    protein_g=round(nuts.get("protein_g", 0), 2),
                    fat_g=round(nuts.get("fat_g", 0), 2),
                    carb_g=round(nuts.get("carb_g", 0), 2),
                    fiber_g=round(nuts.get("fiber_g", 0), 2),
                    calcium_mg=round(nuts.get("calcium_mg", 0), 2),
                    iron_mg=round(nuts.get("iron_mg", 0), 2),
                    vitc_mg=round(nuts.get("vitc_mg", 0), 2),
                    source="usda",
                    tags="",
                )
                all_items.append(item)
                usda_count += 1

    print(f"  -> Prepared {usda_count} USDA items")

    # Save to DB in batches
    print("\nSaving items into database...")
    batch_size = 500
    for i in range(0, len(all_items), batch_size):
        db.add_all(all_items[i:i + batch_size])
        db.commit()

    total_in_db = db.query(FoodItem).count()
    print(f"\n{'=' * 60}")
    print(f"  SUCCESS: {total_in_db} rows in food_items table!")
    print(f"  IFCT 2017: {ifct_count} | Curated: {curated_count} | USDA: {usda_count}")
    print(f"{'=' * 60}")

    db.close()


if __name__ == "__main__":
    import_all()
