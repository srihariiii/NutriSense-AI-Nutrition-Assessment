import csv
import sys
from pathlib import Path

# Add backend dir to sys.path to import from backend
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from database import SessionLocal
from models import FoodItem

USDA_RAW_DIR = backend_dir / "data" / "usda_raw" / "FoodData_Central_foundation_food_csv_2026-04-30"
FOOD_CSV = USDA_RAW_DIR / "food.csv"
NUTRIENT_CSV = USDA_RAW_DIR / "food_nutrient.csv"

def main():
    if not FOOD_CSV.exists() or not NUTRIENT_CSV.exists():
        print(f"Data files not found in {USDA_RAW_DIR}")
        return

    # 1. Read food.csv
    foods = {}  # fdc_id -> description
    with open(FOOD_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("data_type") == "foundation_food":
                fdc_id = int(row["fdc_id"])
                foods[fdc_id] = row["description"]

    print(f"Loaded {len(foods)} foundation foods.")

    # 2. Read food_nutrient.csv
    # target nutrient IDs
    NUTRIENTS = {
        1008: "energy_kcal",
        1003: "protein_g",
        1004: "fat_g",
        1005: "carb_g",
        1079: "fiber_g",
        1087: "calcium_mg",
        1089: "iron_mg",
        1162: "vitc_mg",
    }
    
    food_nutrients = {fdc_id: {k: 0.0 for k in NUTRIENTS.values()} for fdc_id in foods.keys()}

    with open(NUTRIENT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_id_str = row.get("fdc_id")
            if not fdc_id_str:
                continue
            fdc_id = int(fdc_id_str)
            if fdc_id in food_nutrients:
                nut_id_str = row.get("nutrient_id")
                amount_str = row.get("amount")
                if not nut_id_str or not amount_str:
                    continue
                nut_id = int(nut_id_str)
                if nut_id in NUTRIENTS:
                    try:
                        amount = float(amount_str)
                        field = NUTRIENTS[nut_id]
                        food_nutrients[fdc_id][field] = amount
                    except ValueError:
                        pass

    # 3. Insert into db
    db = SessionLocal()
    try:
        count = 0
        for fdc_id, desc in foods.items():
            nuts = food_nutrients[fdc_id]
            item = FoodItem(
                name=desc,
                energy_kcal=nuts["energy_kcal"],
                protein_g=nuts["protein_g"],
                fat_g=nuts["fat_g"],
                carb_g=nuts["carb_g"],
                fiber_g=nuts["fiber_g"],
                calcium_mg=nuts["calcium_mg"],
                iron_mg=nuts["iron_mg"],
                vitc_mg=nuts["vitc_mg"],
                source="usda"
            )
            db.add(item)
            count += 1
            if count % 100 == 0:
                print(f"Imported {count} foods...")
        db.commit()
        print(f"Successfully imported {count} USDA foods.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
