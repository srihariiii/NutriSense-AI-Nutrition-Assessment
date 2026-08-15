"""
Download IFCT 2017 compositions CSV from npm registry + re-import into food_items.
Also re-imports USDA foundation foods from existing CSVs.
Clears old data and creates fresh entries.
Run: backend\venv\Scripts\python.exe backend/scripts/reimport_all_foods.py
"""

import csv
import io
import os
import sys
import tarfile
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import Base, engine, SessionLocal
from models import FoodItem

# ── Paths ──
DATA_DIR = BACKEND_DIR.parent / "data"
BACKEND_DATA_DIR = BACKEND_DIR / "data"
IFCT_DIR = DATA_DIR / "ifct2017"
USDA_DIR = BACKEND_DATA_DIR / "usda_raw"

IFCT_CSV = IFCT_DIR / "compositions.csv"

IFCT_NPM_URL = "https://registry.npmjs.org/@ifct2017/compositions/-/compositions-2.0.9.tgz"

# USDA nutrient IDs
NUTRIENT_MAP = {
    1008: "energy_kcal",
    1003: "protein_g",
    1004: "fat_g",
    1005: "carb_g",
    1079: "fiber_g",
    1087: "calcium_mg",
    1089: "iron_mg",
    1162: "vitc_mg",
}


def download_ifct_csv():
    """Download IFCT 2017 compositions.csv from npm."""
    IFCT_DIR.mkdir(parents=True, exist_ok=True)
    if IFCT_CSV.exists():
        print(f"  IFCT CSV already present at {IFCT_CSV}")
        return

    print(f"  Downloading IFCT 2017 from {IFCT_NPM_URL} ...")
    req = urllib.request.Request(IFCT_NPM_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        tgz_data = resp.read()

    # Extract index.csv from tarball
    with tempfile.TemporaryDirectory() as tmpdir:
        tgz_path = Path(tmpdir) / "pkg.tgz"
        tgz_path.write_bytes(tgz_data)

        with tarfile.open(tgz_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("index.csv"):
                    f = tar.extractfile(member)
                    if f:
                        IFCT_CSV.write_bytes(f.read())
                        break

    if IFCT_CSV.exists():
        lines = len(IFCT_CSV.read_text(encoding="utf-8").splitlines())
        print(f"  Saved IFCT CSV ({lines} lines)")
    else:
        print("  ERROR: Could not extract index.csv from tarball")


def import_ifct(db):
    """Import IFCT 2017 compositions CSV into food_items."""
    if not IFCT_CSV.exists():
        print("  IFCT CSV not found, skipping.")
        return 0

    count = 0
    with open(IFCT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        print(f"  IFCT CSV columns (first 5): {cols[:5]}")

        # Build a lookup: short_name -> full_column_name
        # Columns are like "Food Name; name", "Energy; enerc"
        col_map = {}
        for c in cols:
            if "; " in c:
                short = c.split("; ", 1)[1].strip()
                col_map[short] = c
            else:
                col_map[c] = c

        def get_col(row, short_names):
            """Get float value from row using short column name(s)."""
            for sn in short_names:
                full_col = col_map.get(sn, sn)
                v = row.get(full_col, "")
                if v:
                    try:
                        return round(float(v), 2)
                    except ValueError:
                        pass
            return 0.0

        for row in reader:
            # Get name using short key
            name_col = col_map.get("name", "Food Name; name")
            name = row.get(name_col, "").strip()
            if not name:
                continue

            # Energy in IFCT is in kJ, convert to kcal (1 kJ = 0.239 kcal)
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
            db.add(item)
            count += 1

    db.commit()
    return count


def find_usda_csv_dir():
    """Find the USDA CSV directory (may have different date suffixes)."""
    if not USDA_DIR.exists():
        return None
    # Check for food.csv directly in usda_raw
    if (USDA_DIR / "food.csv").exists():
        return USDA_DIR
    # Check subdirectories
    for d in sorted(USDA_DIR.iterdir()):
        if d.is_dir() and (d / "food.csv").exists():
            return d
    return None


def import_usda(db):
    """Import USDA FoodData Central foundation foods."""
    csv_dir = find_usda_csv_dir()
    if not csv_dir:
        print("  USDA CSV directory not found, skipping.")
        return 0

    print(f"  Reading USDA CSVs from {csv_dir}")

    # 1. Read foods
    foods = {}
    with open(csv_dir / "food.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dtype = row.get("data_type", "")
            if dtype == "foundation_food":
                fdc_id = int(row["fdc_id"])
                foods[fdc_id] = row["description"].strip()

    print(f"  Found {len(foods)} foundation foods")

    # 2. Read nutrients per food
    food_nuts = defaultdict(dict)
    with open(csv_dir / "food_nutrient.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fdc_id = int(row["fdc_id"])
            nid = int(row["nutrient_id"])
            if fdc_id in foods and nid in NUTRIENT_MAP:
                try:
                    amount = float(row["amount"]) if row["amount"] else 0.0
                except ValueError:
                    amount = 0.0
                food_nuts[fdc_id][NUTRIENT_MAP[nid]] = amount

    # 3. Insert
    count = 0
    batch = []
    for fdc_id, name in foods.items():
        nuts = food_nuts.get(fdc_id, {})
        item = FoodItem(
            name=name,
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
        batch.append(item)
        count += 1
        if len(batch) >= 500:
            db.add_all(batch)
            db.commit()
            print(f"    Imported {count} USDA foods...")
            batch = []

    if batch:
        db.add_all(batch)
        db.commit()

    return count


def main():
    print("=" * 60)
    print("  FOOD DATABASE RE-IMPORT (IFCT 2017 + USDA)")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear ALL existing food items
    deleted = db.query(FoodItem).delete()
    db.commit()
    print(f"\nCleared {deleted} existing food items.")

    # 1. Download & import IFCT 2017
    print("\n[1/2] IFCT 2017 Indian Foods")
    download_ifct_csv()
    ifct_count = import_ifct(db)
    print(f"  -> Imported {ifct_count} IFCT foods")

    # 2. Import USDA
    print("\n[2/2] USDA FoodData Central")
    usda_count = import_usda(db)
    print(f"  -> Imported {usda_count} USDA foods")

    # Summary
    total = db.query(FoodItem).count()
    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total} foods in food_items table")
    print(f"  IFCT: {ifct_count} | USDA: {usda_count}")
    print(f"{'=' * 60}")

    db.close()


if __name__ == "__main__":
    main()
