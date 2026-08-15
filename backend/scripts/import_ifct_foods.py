"""
Import IFCT 2017 (Indian Food Composition Tables) into the food_items table.
Uses a curated list of ~100 common Indian foods with nutritional data per 100g.
Run from project root: python backend/scripts/import_ifct_foods.py
"""

import csv
import io
import sys
import urllib.request
from pathlib import Path

# Allow importing from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database import Base, engine, SessionLocal
from models import FoodItem

# Curated Indian food dataset (per 100g) sourced from IFCT 2017
# Fields: name, energy_kcal, protein_g, fat_g, carb_g, fiber_g, calcium_mg, iron_mg, vitc_mg
INDIAN_FOODS = [
    ("Rice, raw, milled", 356, 6.8, 0.5, 78.2, 0.2, 10, 0.7, 0),
    ("Rice, cooked", 130, 2.7, 0.3, 28.2, 0.4, 10, 0.2, 0),
    ("Wheat flour, whole", 341, 12.1, 1.7, 71.2, 12.5, 48, 4.9, 0),
    ("Wheat, bread (chapati)", 297, 8.7, 2.2, 56.6, 3.6, 25, 2.7, 0),
    ("Whole wheat roti", 297, 8.7, 2.2, 56.6, 3.6, 25, 2.7, 0),
    ("Bajra (Pearl millet)", 361, 11.6, 5.0, 67.5, 1.2, 42, 8.0, 0),
    ("Jowar (Sorghum)", 349, 10.4, 1.9, 72.6, 1.6, 25, 4.1, 0),
    ("Ragi (Finger millet)", 328, 7.3, 1.3, 72.0, 3.6, 344, 3.9, 0),
    ("Maize, dry", 342, 11.5, 3.6, 66.2, 2.7, 10, 2.3, 0),
    ("Oats", 389, 16.9, 6.9, 66.3, 10.6, 54, 4.7, 0),
    ("Bengal gram dal (Chana dal)", 360, 17.1, 5.3, 60.9, 3.9, 56, 4.6, 0),
    ("Red gram dal (Toor dal)", 335, 22.3, 1.7, 57.6, 1.5, 73, 2.7, 0),
    ("Green gram dal (Moong dal)", 348, 24.0, 1.3, 59.9, 0.8, 75, 3.9, 0),
    ("Black gram dal (Urad dal)", 347, 24.0, 1.4, 59.6, 0.9, 154, 3.8, 0),
    ("Masoor dal (Red lentil)", 343, 25.1, 0.7, 59.0, 0.7, 69, 7.6, 0),
    ("Rajma (Kidney beans)", 346, 22.9, 1.3, 60.6, 4.8, 260, 5.1, 0),
    ("Soyabean", 432, 43.2, 19.5, 20.9, 3.7, 240, 10.4, 0),
    ("Chickpeas (Kabuli chana)", 364, 17.1, 5.3, 61.0, 3.9, 202, 4.6, 0),
    ("Groundnut (Peanut)", 567, 25.3, 49.2, 16.1, 8.5, 90, 2.5, 0),
    ("Coconut, fresh", 354, 3.4, 33.5, 15.2, 9.0, 10, 1.7, 1),
    ("Almond", 655, 20.8, 58.9, 10.5, 1.7, 230, 5.1, 0.5),
    ("Cashew nut", 596, 21.2, 46.9, 22.3, 1.0, 50, 5.8, 0),
    ("Milk, whole (cow)", 67, 3.2, 4.1, 4.4, 0, 120, 0.2, 1),
    ("Milk, whole (buffalo)", 117, 4.3, 6.5, 5.2, 0, 210, 0.2, 1),
    ("Milk, toned", 58, 3.0, 3.0, 4.6, 0, 120, 0.1, 1),
    ("Curd (Yogurt)", 60, 3.1, 4.0, 3.0, 0, 149, 0.2, 1),
    ("Paneer (Cottage cheese)", 265, 18.3, 20.8, 1.2, 0, 208, 1.3, 0),
    ("Butter", 729, 0.6, 81.0, 0.1, 0, 15, 0, 0),
    ("Ghee (Clarified butter)", 897, 0.1, 99.5, 0, 0, 0, 0, 0),
    ("Egg, hen, whole", 173, 13.3, 13.3, 0, 0, 58, 2.1, 0),
    ("Chicken, breast", 110, 25.0, 1.2, 0, 0, 12, 0.4, 0),
    ("Chicken, leg", 158, 18.0, 9.0, 0, 0, 11, 0.7, 0),
    ("Mutton (Goat meat)", 118, 21.4, 3.6, 0, 0, 12, 2.5, 0),
    ("Fish, Rohu", 97, 16.6, 1.4, 4.4, 0, 650, 1.0, 0),
    ("Prawns (Shrimp)", 89, 19.1, 1.0, 0, 0, 323, 5.3, 0),
    ("Potato", 97, 1.6, 0.1, 22.6, 0.4, 10, 0.5, 17),
    ("Onion", 50, 1.2, 0.1, 11.1, 0.6, 47, 0.7, 2),
    ("Tomato", 23, 0.9, 0.2, 3.6, 0.8, 48, 0.4, 27),
    ("Brinjal (Eggplant)", 24, 1.4, 0.3, 4.0, 1.3, 18, 0.4, 12),
    ("Cauliflower", 30, 2.6, 0.4, 4.0, 1.2, 33, 1.2, 56),
    ("Cabbage", 27, 1.8, 0.1, 4.6, 0.6, 39, 0.8, 124),
    ("Carrot", 48, 0.9, 0.2, 10.6, 1.2, 80, 1.0, 3),
    ("Beans, French", 26, 1.7, 0.1, 4.5, 1.8, 60, 1.7, 24),
    ("Ladies finger (Okra)", 35, 1.9, 0.2, 6.4, 1.2, 66, 0.4, 13),
    ("Spinach (Palak)", 26, 2.0, 0.7, 2.9, 0.6, 73, 1.1, 28),
    ("Methi leaves (Fenugreek)", 49, 4.4, 0.9, 6.3, 1.1, 395, 1.9, 52),
    ("Bitter gourd (Karela)", 25, 1.6, 0.2, 4.2, 0.8, 20, 0.6, 88),
    ("Bottle gourd (Lauki)", 15, 0.2, 0.1, 2.5, 0.6, 20, 0.5, 6),
    ("Ridge gourd (Tori)", 18, 0.5, 0.1, 3.4, 0.5, 18, 0.4, 5),
    ("Pumpkin", 25, 1.4, 0.1, 4.6, 0.5, 10, 0.4, 2),
    ("Drumstick (Moringa)", 26, 2.5, 0.1, 3.7, 0.8, 30, 0.4, 120),
    ("Radish (Mooli)", 17, 0.7, 0.1, 3.4, 0.6, 35, 0.4, 15),
    ("Beetroot", 43, 1.7, 0.1, 8.8, 0.9, 19, 1.0, 10),
    ("Sweet potato", 120, 1.2, 0.3, 28.2, 0.8, 46, 0.2, 24),
    ("Green peas", 93, 7.2, 0.1, 15.9, 4.0, 20, 1.5, 9),
    ("Mushroom", 18, 3.6, 0.1, 0.5, 2.0, 6, 1.5, 0),
    ("Banana, ripe", 116, 1.2, 0.3, 27.2, 0.4, 17, 0.4, 7),
    ("Apple", 59, 0.2, 0.5, 13.7, 1.0, 10, 0.7, 1),
    ("Mango, ripe", 74, 0.6, 0.4, 16.9, 0.7, 14, 1.3, 16),
    ("Papaya, ripe", 32, 0.6, 0.1, 7.2, 0.6, 17, 0.5, 57),
    ("Guava", 51, 0.9, 0.3, 11.2, 5.4, 10, 0.3, 212),
    ("Orange", 48, 0.7, 0.2, 11.3, 0.3, 26, 0.3, 30),
    ("Grapes", 71, 0.5, 0.3, 16.5, 2.4, 20, 0.5, 1),
    ("Watermelon", 20, 0.2, 0.2, 3.3, 0.2, 11, 0.2, 1),
    ("Pomegranate", 65, 1.6, 1.2, 14.5, 2.3, 10, 0.3, 14),
    ("Lemon", 57, 1.0, 0.9, 11.1, 1.7, 70, 2.3, 39),
    ("Coconut water", 24, 0.1, 0.1, 4.7, 0, 29, 0.3, 2),
    ("Jaggery", 383, 0.4, 0.1, 95.0, 0, 80, 11.0, 0),
    ("Sugar, refined", 398, 0, 0, 99.4, 0, 12, 0.2, 0),
    ("Honey", 319, 0.3, 0, 79.5, 0, 5, 0.7, 0.5),
    ("Tea, black (brewed)", 1, 0.1, 0, 0.3, 0, 0, 0.1, 0),
    ("Coffee, brewed", 0, 0.1, 0, 0, 0, 2, 0, 0),
    ("Turmeric powder", 312, 6.3, 5.1, 69.4, 6.7, 150, 41.4, 0),
    ("Chili powder, red", 246, 15.9, 6.2, 31.6, 30.2, 160, 2.3, 50),
    ("Cumin seeds (Jeera)", 375, 17.8, 22.3, 44.2, 10.5, 931, 66.4, 7.7),
    ("Coriander seeds (Dhaniya)", 298, 12.4, 17.8, 55.0, 41.9, 630, 16.3, 0),
    ("Mustard oil", 884, 0, 100, 0, 0, 0, 0, 0),
    ("Sunflower oil", 884, 0, 100, 0, 0, 0, 0, 0),
    ("Olive oil", 884, 0, 100, 0, 0, 1, 0.6, 0),
    ("Idli (steamed rice cake)", 156, 3.9, 0.4, 33.1, 0.6, 12, 0.6, 0),
    ("Dosa (rice & lentil crepe)", 175, 4.1, 2.4, 33.1, 0.5, 15, 0.8, 0),
    ("Sambar", 69, 3.8, 1.2, 11.0, 1.6, 38, 1.4, 5),
    ("Upma", 146, 3.6, 3.8, 24.6, 0.8, 13, 0.6, 0),
    ("Poha (Flattened rice, cooked)", 130, 2.1, 0.6, 28.4, 0.3, 8, 2.8, 0),
    ("Dal fry", 120, 6.5, 3.8, 15.2, 1.8, 35, 1.8, 2),
    ("Chole (Chickpea curry)", 140, 5.8, 4.5, 19.5, 3.2, 60, 2.1, 3),
    ("Aloo gobi (Potato cauliflower)", 85, 2.2, 3.5, 12.0, 1.5, 25, 0.6, 15),
    ("Palak paneer", 170, 9.5, 12.0, 5.8, 1.2, 180, 2.3, 10),
    ("Raita (Yogurt with cucumber)", 45, 2.2, 2.5, 3.5, 0.2, 80, 0.2, 2),
    ("Biryani (Chicken)", 180, 8.5, 6.2, 23.0, 0.6, 20, 0.8, 1),
    ("Pulao (Vegetable)", 150, 3.0, 3.5, 26.5, 0.8, 15, 0.5, 2),
    ("Paratha (Plain)", 326, 6.2, 11.5, 49.0, 2.0, 22, 2.0, 0),
    ("Naan", 310, 8.7, 5.2, 55.0, 2.1, 30, 2.4, 0),
    ("Puri (Deep fried bread)", 391, 7.6, 15.0, 56.0, 1.8, 20, 2.0, 0),
    ("Vada (Fried lentil donut)", 290, 7.8, 14.5, 33.5, 1.2, 25, 1.6, 0),
    ("Uttapam", 170, 4.2, 3.0, 31.0, 0.8, 16, 0.7, 1),
    ("Rasam", 25, 0.8, 0.5, 4.5, 0.5, 12, 0.4, 8),
    ("Coconut chutney", 130, 2.5, 10.0, 8.5, 2.5, 15, 0.6, 1),
    ("Pickle, mango", 182, 1.0, 11.0, 20.5, 0.8, 30, 1.0, 3),
    ("Papad (Roasted)", 328, 22.5, 0.6, 57.0, 1.5, 85, 8.0, 0),
    ("Kheer (Rice pudding)", 128, 3.2, 4.0, 20.0, 0.1, 100, 0.3, 0),
    ("Gulab Jamun", 320, 4.0, 14.0, 46.0, 0.1, 60, 0.4, 0),
    ("Ladoo (Besan)", 480, 8.5, 22.0, 62.0, 2.0, 25, 2.0, 0),
    ("Jalebi", 370, 2.0, 10.0, 68.0, 0.1, 8, 0.3, 0),
]


def main():
    print("=== IFCT 2017 Indian Foods Importer ===")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing IFCT entries
    deleted = db.query(FoodItem).filter(FoodItem.source == "ifct2017").delete()
    db.commit()
    if deleted:
        print(f"  Cleared {deleted} existing IFCT entries")

    count = 0
    for name, energy, protein, fat, carb, fiber, calcium, iron, vitc in INDIAN_FOODS:
        item = FoodItem(
            name=name,
            energy_kcal=energy,
            protein_g=protein,
            fat_g=fat,
            carb_g=carb,
            fiber_g=fiber,
            calcium_mg=calcium,
            iron_mg=iron,
            vitc_mg=vitc,
            source="ifct2017",
            tags="indian",
        )
        db.add(item)
        count += 1

    db.commit()
    db.close()

    print(f"\nDone! Imported {count} Indian foods (IFCT 2017) into food_items table.")


if __name__ == "__main__":
    main()
