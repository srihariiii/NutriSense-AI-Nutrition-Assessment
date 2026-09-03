import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import joblib
import numpy as np
from fastapi import HTTPException
from sklearn.impute import SimpleImputer
from sqlalchemy import case
from sqlalchemy.orm import Session

from models import Assessment, DiaryEntry, FoodItem, HealthProfile, LabResult, User

# Monkey-patch SimpleImputer._fill_dtype for scikit-learn compatibility
if not hasattr(SimpleImputer, "_fill_dtype"):
    SimpleImputer._fill_dtype = property(
        lambda self: getattr(self, "_fit_dtype", None)
    )

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "deficiency_model.joblib"
PREPROCESS_PATH = MODEL_DIR / "preprocess.joblib"
META_PATH = MODEL_DIR / "meta.json"

_model = None
_preprocessor = None
_meta = None


def load_artifacts():
    global _model, _preprocessor, _meta
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    if _preprocessor is None and PREPROCESS_PATH.exists():
        _preprocessor = joblib.load(PREPROCESS_PATH)
    if _meta is None and META_PATH.exists():
        with open(META_PATH, "r") as f:
            _meta = json.load(f)
    return _model, _preprocessor, _meta


LABEL_DISPLAY_NAMES = {
    "label_iron": "Iron",
    "label_vitamin_d": "Vitamin D",
    "label_vitamin_b12": "Vitamin B12",
    "label_calcium": "Calcium",
    "label_folate": "Folate",
    "label_vitamin_a": "Vitamin A",
    "label_vitamin_c": "Vitamin C",
    "label_magnesium": "Magnesium",
    "label_zinc": "Zinc",
    "label_protein": "Protein",
}

NUTRIENT_COLUMN_MAP = {
    "iron": ("iron_mg", "Fe", "mg"),
    "calcium": ("calcium_mg", "Ca", "mg"),
    "vitamin_b12": ("vitamin_b12_mcg", "B12", "mcg"),
    "folate": ("folate_mcg", "Folate", "mcg"),
    "vitamin_a": ("vitamin_a_mcg", "Vit A", "mcg"),
    "vitamin_c": ("vitamin_c_mg", "Vit C", "mg"),
    "magnesium": ("magnesium_mg", "Mg", "mg"),
    "zinc": ("zinc_mg", "Zn", "mg"),
    "vitamin_d": ("vitamin_d_mcg", "Vit D", "mcg"),
    "protein": ("protein_g", "Protein", "g"),
}

RDA_THRESHOLDS = {
    "label_calcium": (1000.0, "Low calcium intake"),
    "label_zinc": (8.0, "Low zinc intake"),
    "label_vitamin_b12": (2.4, "Low B12 intake"),
    "label_folate": (400.0, "Low folate intake"),
    "label_magnesium": (320.0, "Low magnesium intake"),
    "label_vitamin_a": (700.0, "Low vitamin A intake"),
    "label_iron": (8.0, "Low iron intake"),
    "label_vitamin_d": (15.0, "Low vitamin D intake"),
    "label_protein": (50.0, "Low protein intake"),
    "label_vitamin_c": (75.0, "Low vitamin C intake"),
}

# --- PDF Diet Keyword Lists ---
USDA_SKIP = [
    "babyfood", "candies", "snacks", "pie", "puddings", "salad dressing",
    "refrigerated dough", "food distribution program", "artificial flavor",
    "infant formula", "frosting", "sweet snack", "liqueur", "whiskey",
    "distilled", "alcoholic", "fast foods, hamburger", "restaurant, "
]

NON_VEG_KEYWORDS = [
    "beef", "chicken", "meat", "pork", "mollusks", "fish", "liver", "clam", "oyster",
    "salmon", "tuna", "lamb", "veal", "whale", "turkey", "duck", "gelatin", "bacon",
    "sausage", "ham", "seafood", "anchovy", "sardine", "cod", "shrimp", "crab", "lobster"
]

ANIMAL_DERIVED_KEYWORDS = [
    "egg", "cheese", "milk", "paneer", "butter", "curd", "yogurt", "yoghurt", "cream",
    "whey", "ghee", "casein", "dairy", "honey", "lassi"
]

DAIRY_KEYWORDS = [
    "milk", "cheese", "yogurt", "yoghurt", "curd", "dahi", "paneer", "butter", "ghee",
    "cream", "whey", "casein", "lassi", "buttermilk", "custard"
]

NUTS_KEYWORDS = [
    "almond", "peanut", "cashew", "walnut", "pistachio", "hazelnut", "pecan",
    "groundnut", "tree nut", "nuts", "nut", "macadamia"
]

GLUTEN_KEYWORDS = [
    "wheat", "gluten", "bread", "atta", "maida", "seitan", "barley", "rye",
    "pasta", "noodle", "biscuit", "chapati", "roti", "paratha", "semolina",
    "vermicelli", "bulgur", "cracker", "couscous", "pastry"
]


def is_usda_noise(name: str) -> bool:
    """Drops USDA noise names matching USDA_SKIP (from PDF Section 5)."""
    n_lower = (name or "").lower()
    for skip_term in USDA_SKIP:
        if skip_term in n_lower:
            return True
    return False


def diet_flags(diet_restrictions: List[str]) -> Dict[str, bool]:
    """Parse diet_restrictions strings into booleans (from PDF Section 5)."""
    flags = {
        "vegan": False,
        "vegetarian": False,
        "gluten_free": False,
        "dairy_free": False,
        "nut_allergy": False,
    }
    if not diet_restrictions:
        return flags

    for r in diet_restrictions:
        clean = str(r).lower().strip()
        if "vegan" in clean:
            flags["vegan"] = True
            flags["vegetarian"] = True
            flags["dairy_free"] = True
        elif "vegetarian" in clean:
            flags["vegetarian"] = True
        elif "gluten" in clean:
            flags["gluten_free"] = True
        elif "dairy" in clean:
            flags["dairy_free"] = True
        elif "nut" in clean:
            flags["nut_allergy"] = True

    return flags


def food_allowed(food: FoodItem, flags: Dict[str, bool]) -> bool:
    """Applies strict database flags and keyword checks (from PDF Section 5)."""
    name_lower = (food.name or "").lower()
    text_content = f"{name_lower} {(food.ingredients or '').lower()} {(food.tags or '').lower()}"

    # Vegan check
    if flags["vegan"]:
        if not getattr(food, "is_vegan", False):
            for kw in NON_VEG_KEYWORDS + ANIMAL_DERIVED_KEYWORDS:
                if kw in text_content:
                    return False
        for kw in DAIRY_KEYWORDS:
            if kw in text_content:
                return False

    # Vegetarian check
    if flags["vegetarian"] and not flags["vegan"]:
        if not (getattr(food, "is_vegetarian", False) or getattr(food, "is_vegan", False)):
            for kw in NON_VEG_KEYWORDS:
                if kw in text_content:
                    return False

    # Dairy-free check
    if flags["dairy_free"]:
        for kw in DAIRY_KEYWORDS:
            if kw in text_content:
                return False

    # Nut allergy check
    if flags["nut_allergy"]:
        for kw in NUTS_KEYWORDS:
            if kw in text_content:
                return False

    # Gluten-free check
    if flags["gluten_free"]:
        for kw in GLUTEN_KEYWORDS:
            if kw in text_content:
                return False

    return True


def high_risk_nutrients(risks: List[Dict[str, Any]], cutoff: float = 0.45) -> List[str]:
    """Keeps every nutrient where probability >= 0.45 and has matching food_items column (from PDF Section 2)."""
    result = []
    for r in risks:
        prob = r.get("probability", 0.0)
        pct = r.get("percentage", 0)
        if prob >= cutoff or pct >= int(cutoff * 100):
            raw_key = r.get("label", "").replace("label_", "").lower()
            if raw_key in NUTRIENT_COLUMN_MAP:
                result.append(raw_key)
    return result


def get_recommendations_for_nutrient(
    db: Session,
    nutrient_key: str,
    diet_restrictions: List[str],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """Query food_items for top rich foods for a specific nutrient with source priority and diet filtering (from PDF Step 5 & 6)."""
    if nutrient_key not in NUTRIENT_COLUMN_MAP:
        return []

    col_name, prefix, unit = NUTRIENT_COLUMN_MAP[nutrient_key]
    col_attr = getattr(FoodItem, col_name, None)
    if col_attr is None:
        return []

    flags = diet_flags(diet_restrictions)

    source_priority_expr = case(
        (FoodItem.data_type == "curated", 0),
        (FoodItem.data_type == "ifct2017", 1),
        else_=2,
    )

    pool_size = max(limit * 8, 48)

    query = db.query(FoodItem)
    if flags["vegan"]:
        query = query.filter(FoodItem.is_vegan == True)
    elif flags["vegetarian"]:
        query = query.filter((FoodItem.is_vegetarian == True) | (FoodItem.is_vegan == True))

    candidates = (
        query.order_by(source_priority_expr.asc(), col_attr.desc())
        .limit(pool_size)
        .all()
    )

    survived = []
    seen_names = set()

    for food in candidates:
        if is_usda_noise(food.name):
            continue
        if not food_allowed(food, flags):
            continue

        clean_name = food.name.strip()
        norm_name = clean_name.lower()
        if norm_name in seen_names:
            continue
        seen_names.add(norm_name)

        raw_val = getattr(food, col_name, 0.0) or 0.0
        val_formatted = str(int(raw_val)) if raw_val == int(raw_val) else f"{raw_val:.1f}"
        if unit == "g":
            target_display = f"{prefix} {val_formatted}g"
        else:
            target_display = f"{prefix} {val_formatted}"

        survived.append({
            "id": food.id,
            "name": clean_name,
            "display_name": clean_name,
            "nutrient_value": raw_val,
            "target_val": raw_val,
            "target_display": target_display,
            "unit": unit,
            "source": food.data_type or "",
            "is_vegan": bool(food.is_vegan),
            "is_vegetarian": bool(food.is_vegetarian),
            "iron_mg": float(getattr(food, "iron_mg", 0.0) or 0.0),
            "calcium_mg": float(getattr(food, "calcium_mg", 0.0) or 0.0),
            "protein_g": float(getattr(food, "protein_g", 0.0) or 0.0),
            "vitamin_c_mg": float(getattr(food, "vitamin_c_mg", 0.0) or 0.0),
            "vitamin_d_mcg": float(getattr(food, "vitamin_d_mcg", 0.0) or 0.0),
            "vitamin_b12_mcg": float(getattr(food, "vitamin_b12_mcg", 0.0) or 0.0),
            "folate_mcg": float(getattr(food, "folate_mcg", 0.0) or 0.0),
            "vitamin_a_mcg": float(getattr(food, "vitamin_a_mcg", 0.0) or 0.0),
            "magnesium_mg": float(getattr(food, "magnesium_mg", 0.0) or 0.0),
            "zinc_mg": float(getattr(food, "zinc_mg", 0.0) or 0.0),
            "tags": food.tags or "",
        })

        if len(survived) >= limit:
            break

    return survived


def get_recommended_foods_for_assessment(
    db: Session,
    risks_json_list: List[Dict[str, Any]],
    diet_restrictions: List[str],
) -> List[Dict[str, Any]]:
    """Builds the Recommended Foods blocks for all nutrients with probability >= 0.45 (from PDF Step 3 to Step 7)."""
    high_keys = high_risk_nutrients(risks_json_list, cutoff=0.45)
    
    if not high_keys and risks_json_list:
        sorted_risks = sorted(risks_json_list, key=lambda r: r.get("percentage", 0), reverse=True)
        for r in sorted_risks[:3]:
            k = r.get("label", "").replace("label_", "").lower()
            if k in NUTRIENT_COLUMN_MAP and k not in high_keys:
                high_keys.append(k)

    blocks = []
    for nut_key in high_keys:
        foods = get_recommendations_for_nutrient(db, nut_key, diet_restrictions, limit=6)
        label_key = f"label_{nut_key}"
        display_name = LABEL_DISPLAY_NAMES.get(label_key, nut_key.capitalize())
        if foods:
            blocks.append({
                "nutrient": nut_key,
                "nutrient_name": display_name,
                "foods": foods,
            })
    return blocks


def get_consecutive_days_status(
    db: Session, user_id: int
) -> Tuple[int, int, bool]:
    """Check user's diary entries for valid 4-meal days and max consecutive days.
    A valid day MUST contain at least one entry for all 4 meal types: breakfast, lunch, dinner, snack.
    """
    entries = (
        db.query(DiaryEntry.date, DiaryEntry.meal_type)
        .filter(DiaryEntry.user_id == user_id)
        .order_by(DiaryEntry.date)
        .all()
    )
    if not entries:
        return 0, 0, False

    day_meals: Dict[str, set] = {}
    for d_str, m_type in entries:
        d_clean = (d_str or "").strip()
        if d_clean not in day_meals:
            day_meals[d_clean] = set()
        day_meals[d_clean].add(m_type.lower().strip())

    required_meals = {"breakfast", "lunch", "dinner", "snack"}
    valid_dates = []
    for d_str, meals in day_meals.items():
        if required_meals.issubset(meals):
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d").date()
                valid_dates.append(dt)
            except ValueError:
                continue

    valid_dates = sorted(list(set(valid_dates)))
    distinct_count = len(valid_dates)
    if distinct_count == 0:
        return 0, 0, False

    max_streak = 1
    current_streak = 1
    for i in range(len(valid_dates) - 1):
        if valid_dates[i + 1] - valid_dates[i] == timedelta(days=1):
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 1

    return distinct_count, max_streak, (max_streak >= 4)


def get_diary_summary(db: Session, user_id: int) -> Dict[str, float]:
    """Sum nutrients per calendar day for logged meals, then average across logged days."""
    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == user_id)
        .order_by(DiaryEntry.date)
        .all()
    )
    if not entries:
        return {
            "calories_kcal": 0.0,
            "protein_g": 0.0,
            "iron_mg": 0.0,
            "calcium_mg": 0.0,
            "vitamin_d_mcg": 0.0,
            "vitamin_b12_mcg": 0.0,
            "folate_mcg": 0.0,
            "vitamin_a_mcg": 0.0,
            "vitamin_c_mg": 0.0,
            "magnesium_mg": 0.0,
            "zinc_mg": 0.0,
        }

    daily_sums: Dict[str, Dict[str, float]] = {}
    for e in entries:
        d = e.date.strip()
        if d not in daily_sums:
            daily_sums[d] = {
                "calories_kcal": 0.0,
                "protein_g": 0.0,
                "iron_mg": 0.0,
                "calcium_mg": 0.0,
                "vitamin_d_mcg": 0.0,
                "vitamin_b12_mcg": 0.0,
                "folate_mcg": 0.0,
                "vitamin_a_mcg": 0.0,
                "vitamin_c_mg": 0.0,
                "magnesium_mg": 0.0,
                "zinc_mg": 0.0,
            }
        daily_sums[d]["calories_kcal"] += getattr(e, "calories_kcal", 0.0) or 0.0
        daily_sums[d]["protein_g"] += getattr(e, "protein_g", 0.0) or 0.0
        daily_sums[d]["iron_mg"] += getattr(e, "iron_mg", 0.0) or 0.0
        daily_sums[d]["calcium_mg"] += getattr(e, "calcium_mg", 0.0) or 0.0
        daily_sums[d]["vitamin_d_mcg"] += getattr(e, "vitamin_d_mcg", 0.0) or 0.0
        daily_sums[d]["vitamin_b12_mcg"] += getattr(e, "vitamin_b12_mcg", 0.0) or 0.0
        daily_sums[d]["folate_mcg"] += getattr(e, "folate_mcg", 0.0) or 0.0
        daily_sums[d]["vitamin_a_mcg"] += getattr(e, "vitamin_a_mcg", 0.0) or 0.0
        daily_sums[d]["vitamin_c_mg"] += getattr(e, "vitamin_c_mg", 0.0) or 0.0
        daily_sums[d]["magnesium_mg"] += getattr(e, "magnesium_mg", 0.0) or 0.0
        daily_sums[d]["zinc_mg"] += getattr(e, "zinc_mg", 0.0) or 0.0

    n_days = max(1, len(daily_sums))
    avg_nutrients = {}
    for nut in [
        "calories_kcal", "protein_g", "iron_mg", "calcium_mg", "vitamin_d_mcg",
        "vitamin_b12_mcg", "folate_mcg", "vitamin_a_mcg", "vitamin_c_mg",
        "magnesium_mg", "zinc_mg",
    ]:
        total = sum(d[nut] for d in daily_sums.values())
        avg_nutrients[nut] = round(total / n_days, 3)

    return avg_nutrients


def run_assessment_for_user(
    db: Session, user: User, enforce_4_days: bool = True
) -> Dict[str, Any]:
    """Execute complete Random Forest Assessment model pipeline."""
    profile = (
        db.query(HealthProfile)
        .filter(HealthProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Please complete your health profile before running assessment.",
        )

    distinct_count, max_consecutive, is_valid_4 = get_consecutive_days_status(
        db, user.id
    )

    if enforce_4_days and not is_valid_4:
        raise HTTPException(
            status_code=400,
            detail="Enter the atlest 4 concecutive days",
        )

    model, preprocessor, meta = load_artifacts()
    if not model or not preprocessor or not meta:
        raise HTTPException(
            status_code=500,
            detail="Assessment machine learning model artifacts missing.",
        )

    diary_avg = get_diary_summary(db, user.id)

    gender_val = 1 if str(profile.sex).lower() in ["male", "1", "m"] else 2
    age_val = float(profile.age)

    features_dict = {
        "gender": gender_val,
        "age_years": age_val,
        "calories_kcal": diary_avg["calories_kcal"],
        "protein_g": diary_avg["protein_g"],
        "iron_mg": diary_avg["iron_mg"],
        "calcium_mg": diary_avg["calcium_mg"],
        "vitamin_d_mcg": diary_avg["vitamin_d_mcg"],
        "vitamin_b12_mcg": diary_avg["vitamin_b12_mcg"],
        "folate_mcg": diary_avg["folate_mcg"],
        "vitamin_a_mcg": diary_avg["vitamin_a_mcg"],
        "vitamin_c_mg": diary_avg["vitamin_c_mg"],
        "magnesium_mg": diary_avg["magnesium_mg"],
        "zinc_mg": diary_avg["zinc_mg"],
    }

    X_raw = np.array([[features_dict[f] for f in meta["features"]]])
    X_prep = preprocessor.transform(X_raw)

    raw_probs = model.predict_proba(X_prep)

    probs_dict = {}
    for i, label_col in enumerate(meta["label_columns"]):
        p = (
            raw_probs[i][0][1]
            if raw_probs[i].shape[1] > 1
            else raw_probs[i][0][0]
        )
        probs_dict[label_col] = float(p)

    lab = db.query(LabResult).filter(LabResult.user_id == user.id).first()
    boosted_labels = {}

    if lab:
        if lab.hemoglobin is not None:
            cutoff = 13.0 if gender_val == 1 else 12.0
            if lab.hemoglobin < cutoff:
                probs_dict["label_iron"] = max(probs_dict["label_iron"], 0.75)
                boosted_labels["label_iron"] = f"Boosted by Hb ({lab.hemoglobin} g/dL)"

        if lab.ferritin is not None and lab.ferritin < 30.0:
            probs_dict["label_iron"] = max(probs_dict["label_iron"], 0.70)
            boosted_labels["label_iron"] = f"Boosted by Ferritin ({lab.ferritin} ng/mL)"

        if lab.serum_vitamin_d is not None and lab.serum_vitamin_d < 50.0:
            probs_dict["label_vitamin_d"] = max(probs_dict["label_vitamin_d"], 0.65)
            boosted_labels["label_vitamin_d"] = f"Boosted by Serum Vit D ({lab.serum_vitamin_d} nmol/L)"

        if lab.vitamin_b12 is not None and lab.vitamin_b12 < 200.0:
            probs_dict["label_vitamin_b12"] = max(probs_dict["label_vitamin_b12"], 0.60)
            boosted_labels["label_vitamin_b12"] = f"Boosted by Vit B12 ({lab.vitamin_b12} pg/mL)"

        if lab.calcium is not None and lab.calcium < 8.5:
            probs_dict["label_calcium"] = max(probs_dict["label_calcium"], 0.55)
            boosted_labels["label_calcium"] = f"Boosted by Calcium ({lab.calcium} mg/dL)"

    risk_values = list(probs_dict.values())
    avg_risk = sum(risk_values) / len(risk_values)
    wellness_score = round((1.0 - avg_risk) * 100.0, 1)

    risk_items = []
    sorted_labels = sorted(
        meta["label_columns"], key=lambda l: probs_dict[l], reverse=True
    )

    for label in sorted_labels:
        prob = probs_dict[label]
        pct = int(round(prob * 100))

        if pct > 65:
            level = "HIGH"
        elif pct >= 35:
            level = "MODERATE"
        else:
            level = "LOW"

        nut_name = LABEL_DISPLAY_NAMES.get(label, label)
        thresh, default_tag = RDA_THRESHOLDS.get(
            label, (0.0, f"Low {nut_name.lower()} intake")
        )
        tag = default_tag

        is_boosted = label in boosted_labels
        boost_note = boosted_labels.get(label, None)

        risk_items.append(
            {
                "label": label,
                "nutrient_name": nut_name,
                "probability": round(prob, 4),
                "percentage": pct,
                "level": level,
                "tag": tag,
                "lab_boosted": is_boosted,
                "lab_notes": boost_note,
            }
        )

    user_restrictions = []
    if profile and profile.dietary_restrictions:
        try:
            user_restrictions = json.loads(profile.dietary_restrictions)
        except Exception:
            user_restrictions = [profile.dietary_restrictions]

    recommended_groups = get_recommended_foods_for_assessment(db, risk_items, user_restrictions)

    new_assessment = Assessment(
        user_id=user.id,
        features_json=json.dumps(features_dict),
        risks_json=json.dumps(risk_items),
        wellness_score=wellness_score,
    )
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    return {
        "id": new_assessment.id,
        "wellness_score": wellness_score,
        "distinct_days": distinct_count,
        "consecutive_days": max_consecutive,
        "can_run_assessment": True,
        "risk_items": risk_items,
        "recommended_groups": recommended_groups,
        "created_at": new_assessment.created_at.isoformat() if new_assessment.created_at else None,
    }


def generate_7day_meal_plan(db: Session, user: User) -> Dict[str, Any]:
    """Generates a complete 7-day meal plan (Sunday to Saturday) with 4 meals/day and exactly 2 foods/meal.
    Guarantees 56 UNIQUE foods with zero repeats across all meals and days.
    """
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user.id).first()
    dietary_restrictions = []
    if profile and profile.dietary_restrictions:
        try:
            dietary_restrictions = json.loads(profile.dietary_restrictions)
        except Exception:
            dietary_restrictions = [profile.dietary_restrictions]
    if not dietary_restrictions or "none" in [r.lower() for r in dietary_restrictions]:
        dietary_restrictions = ["Vegetarian", "Dairy-free"]

    latest_assessment = (
        db.query(Assessment)
        .filter(Assessment.user_id == user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )

    focus_nutrients = []
    if latest_assessment and latest_assessment.risks_json:
        try:
            risks = json.loads(latest_assessment.risks_json)
            high_keys = high_risk_nutrients(risks, cutoff=0.45)
            if high_keys:
                focus_nutrients = high_keys
            else:
                sorted_risks = sorted(risks, key=lambda r: r.get("percentage", 0), reverse=True)
                focus_nutrients = [r["label"].replace("label_", "").lower() for r in sorted_risks[:4]]
        except Exception:
            pass

    if not focus_nutrients:
        focus_nutrients = ["calcium", "vitamin_b12", "vitamin_a", "vitamin_d", "iron", "protein"]

    flags = diet_flags(dietary_restrictions)

    all_target_keys = list(focus_nutrients)
    for k in ["iron", "calcium", "protein", "vitamin_c", "folate", "vitamin_a", "magnesium", "zinc", "vitamin_d", "vitamin_b12"]:
        if k not in all_target_keys:
            all_target_keys.append(k)

    unique_food_candidates: List[FoodItem] = []
    seen_candidate_names = set()

    source_priority_expr = case(
        (FoodItem.data_type == "curated", 0),
        (FoodItem.data_type == "ifct2017", 1),
        else_=2,
    )

    for nut_key in all_target_keys:
        if nut_key not in NUTRIENT_COLUMN_MAP:
            continue
        col_name, _, _ = NUTRIENT_COLUMN_MAP[nut_key]
        col_attr = getattr(FoodItem, col_name, None)
        if col_attr is None:
            continue

        q = db.query(FoodItem)
        if flags["vegan"]:
            q = q.filter(FoodItem.is_vegan == True)
        elif flags["vegetarian"]:
            q = q.filter((FoodItem.is_vegetarian == True) | (FoodItem.is_vegan == True))

        foods = q.order_by(source_priority_expr.asc(), col_attr.desc()).limit(60).all()
        for f in foods:
            if is_usda_noise(f.name):
                continue
            if not food_allowed(f, flags):
                continue
            norm = f.name.strip().lower()
            if norm not in seen_candidate_names and len(f.name.strip()) <= 65:
                seen_candidate_names.add(norm)
                unique_food_candidates.append(f)

    if len(unique_food_candidates) < 56:
        extra_q = db.query(FoodItem)
        if flags["vegan"]:
            extra_q = extra_q.filter(FoodItem.is_vegan == True)
        elif flags["vegetarian"]:
            extra_q = extra_q.filter((FoodItem.is_vegetarian == True) | (FoodItem.is_vegan == True))
        extras = extra_q.order_by(source_priority_expr.asc(), FoodItem.calories_kcal.desc()).limit(200).all()
        for f in extras:
            if is_usda_noise(f.name):
                continue
            if not food_allowed(f, flags):
                continue
            norm = f.name.strip().lower()
            if norm not in seen_candidate_names and len(f.name.strip()) <= 65:
                seen_candidate_names.add(norm)
                unique_food_candidates.append(f)

    fallback_pool = [
        "Fenugreek leaves (Methi)", "Fortified breakfast cereal", "Pippali", "Amaranth leaves (Chaulai)",
        "Curry leaves", "Ponnaganni leaves", "Gingelly seeds (White sesame)", "Betel leaves",
        "Almonds (Badam)", "Spinach (Palak)", "Chickpeas (Kabuli Chana)", "Firm Tofu",
        "Fortified Soy Milk", "Finger Millet flour (Ragi)", "Red Lentils (Masoor Dal)",
        "Chia Seeds", "Flaxseed meal", "Moringa leaves (Drumstick leaves)", "Black Gram (Urad Dal)",
        "Green Gram (Moong Dal)", "Brown Rice", "Oats (Rolled)", "Pomegranate",
        "Papaya", "Guava", "Indian Gooseberry (Amla)", "Pumpkin Seeds", "Sunflower Seeds",
        "Kidney Beans (Rajma)", "Horse Gram (Kulthi)", "Colocasia leaves", "Mustard greens (Sarson)",
        "Lotus stem (Kamal Kakdi)", "Walnuts", "Soybeans (Whole)", "Sprouted Mung",
        "Sesame Laddu", "Amaranth Seeds (Rajgira)", "Fox Nuts (Makhana)", "Pearl Millet (Bajra)",
        "Sorghum (Jowar)", "Barnyard Millet (Sanwa)", "Black Chana (Kala Chana)", "Cowpeas (Lobia)",
        "Moth Beans", "Pistachios", "Cashew kernels", "Dates (Khajoor)", "Dry Figs (Anjeer)",
        "Raisins (Kishmish)", "Apricots (Khubani)", "Peanuts (Roasted)", "Flaxseed Chutney",
        "Watermelon Seeds", "Barley flakes (Jau)", "Coconut water, fresh"
    ]
    for fb in fallback_pool:
        norm = fb.lower()
        if norm not in seen_candidate_names:
            dummy = FoodItem(name=fb, is_vegan=True, is_vegetarian=True)
            if food_allowed(dummy, flags):
                seen_candidate_names.add(norm)
                unique_food_candidates.append(dummy)

    selected_foods = unique_food_candidates[:56]
    
    days_meta = [
        ("Sun", "Sunday"),
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
    ]

    meal_types = ["breakfast", "lunch", "snack", "dinner"]
    focus_str = ", ".join(focus_nutrients)

    days_plan = []
    food_ptr = 0

    for day_key, day_name in days_meta:
        meals_plan = []
        for m_type in meal_types:
            food_item_1 = selected_foods[food_ptr]
            food_ptr += 1
            food_item_2 = selected_foods[food_ptr]
            food_ptr += 1

            f1_name = food_item_1.name.strip()
            f2_name = food_item_2.name.strip()

            w1 = "30g" if any(s in f1_name.lower() for s in ["seed", "sesame", "flax", "chia", "nut", "powder", "oil", "leaf", "leaves"]) else "100g"
            w2 = "30g" if any(s in f2_name.lower() for s in ["seed", "sesame", "flax", "chia", "nut", "powder", "oil", "leaf", "leaves"]) else "100g"

            title = f"{f1_name} ({w1}) + {f2_name} ({w2})"
            summary = f"Targets {focus_str}. Compliant nutrient sources: {f1_name} ({w1}), {f2_name} ({w2})."

            meals_plan.append({
                "meal_type": m_type,
                "food_title": title,
                "target_summary": summary,
            })

        days_plan.append({
            "day_key": day_key,
            "day_name": day_name,
            "meals": meals_plan,
        })

    return {
        "focus_nutrients": focus_nutrients,
        "dietary_restrictions": dietary_restrictions,
        "days": days_plan,
    }


