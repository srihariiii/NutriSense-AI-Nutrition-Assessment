import json
import math

from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import auth
from database import Base, engine, get_db
from models import Assessment, DiaryEntry, FoodItem, HealthProfile, LabResult, User
from schemas import (
    HealthProfileCreate,
    HealthProfileResponse,
    HealthProfileSaveResponse,
    TokenResponse,
    UserAccountUpdate,
    UserLogin,
    UserResponse,
    UserSignup,
    FoodSearchResult,
    DiaryEntryCreate,
    DiaryEntryResponse,
    LabResultCreate,
    LabResultResponse,
    MealPlanResponse,
    ProgressResponse,
    ProgressAssessmentItem,
    RecommendedGroup,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriSense AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = auth.decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


@app.get("/")
def root():
    return {"message": "NutriSense AI backend is running"}


@app.post("/api/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        first_name=user_data.first_name.strip(),
        last_name=user_data.last_name.strip(),
        email=user_data.email.lower(),
        hashed_password=auth.hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth.create_access_token({"sub": str(new_user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(new_user),
    )


@app.post("/api/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.lower()).first()

    if user is None or not auth.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth.create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@app.get("/api/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@app.put("/api/user/account", response_model=UserResponse)
def update_user_account(
    data: UserAccountUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parts = data.full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    if data.email.lower() != current_user.email.lower():
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already registered by another account")
        current_user.email = data.email.lower()

    current_user.first_name = first_name
    current_user.last_name = last_name

    if data.new_password and data.new_password.strip():
        if not data.current_password or not data.current_password.strip():
            raise HTTPException(status_code=400, detail="Current password is required to set a new password")
        if not auth.verify_password(data.current_password.strip(), current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if data.new_password != data.confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")
        if len(data.new_password.strip()) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        current_user.hashed_password = auth.hash_password(data.new_password.strip())

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)



def _profile_to_response(profile: HealthProfile) -> HealthProfileResponse:
    return HealthProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        health_goal=profile.health_goal,
        dietary_restrictions=json.loads(profile.dietary_restrictions),
    )


@app.get("/api/health-profile", response_model=HealthProfileResponse)
def get_health_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found",
        )
    return _profile_to_response(profile)


@app.post("/api/health-profile", response_model=HealthProfileSaveResponse)
def save_health_profile(
    profile_data: HealthProfileCreate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()

    if profile is None:
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)

    profile.age = profile_data.age
    profile.sex = profile_data.sex
    profile.height_cm = profile_data.height_cm
    profile.weight_kg = profile_data.weight_kg
    profile.activity_level = profile_data.activity_level
    profile.health_goal = profile_data.health_goal
    profile.dietary_restrictions = json.dumps(profile_data.dietary_restrictions)

    db.commit()
    db.refresh(profile)

    return HealthProfileSaveResponse(
        message="Health profile saved successfully",
        profile=_profile_to_response(profile),
    )


@app.get("/api/foods/search", response_model=list[FoodSearchResult])
def search_foods(q: str, limit: int = 50, db: Session = Depends(get_db)):
    if not q or not q.strip():
        return []

    query = q.strip().lower()
    candidates = (
        db.query(FoodItem)
        .filter(FoodItem.name.ilike(f"%{query}%"))
        .limit(300)
        .all()
    )

    def score_food(food: FoodItem):
        name_lower = food.name.lower()
        if name_lower == query:
            rank = 1
        elif name_lower.startswith(query):
            rank = 2
        elif any(w.startswith(query) for w in name_lower.replace(",", " ").replace("-", " ").split()):
            rank = 3
        else:
            rank = 4
        return (rank, len(name_lower), name_lower)

    candidates.sort(key=score_food)

    def clean_num(val):
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return 0.0
        return float(val)

    results = []
    for f in candidates[:limit]:
        results.append(
            FoodSearchResult(
                id=f.id,
                name=f.name,
                energy_kcal=clean_num(f.energy_kcal),
                protein_g=clean_num(f.protein_g),
                fat_g=clean_num(f.fat_g),
                carb_g=clean_num(f.carb_g),
                fiber_g=clean_num(f.fiber_g),
                calcium_mg=clean_num(f.calcium_mg),
                iron_mg=clean_num(f.iron_mg),
                vitc_mg=clean_num(f.vitc_mg),
                source=f.source or "",
                tags=f.tags or "",
            )
        )

    return results


@app.post("/api/diary", response_model=DiaryEntryResponse)
def create_diary_entry(
    entry_data: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    if entry_data.food_item_id:
        food_item = db.query(FoodItem).filter(FoodItem.id == entry_data.food_item_id).first()
        if food_item:
            multiplier = entry_data.portion_grams / 100.0
            calories_kcal = round((food_item.calories_kcal or 0.0) * multiplier, 2)
            protein_g = round((food_item.protein_g or 0.0) * multiplier, 3)
            iron_mg = round((food_item.iron_mg or 0.0) * multiplier, 3)
            calcium_mg = round((food_item.calcium_mg or 0.0) * multiplier, 3)
            vitamin_d_mcg = round((food_item.vitamin_d_mcg or 0.0) * multiplier, 3)
            vitamin_b12_mcg = round((food_item.vitamin_b12_mcg or 0.0) * multiplier, 3)
            folate_mcg = round((food_item.folate_mcg or 0.0) * multiplier, 3)
            vitamin_a_mcg = round((food_item.vitamin_a_mcg or 0.0) * multiplier, 3)
            vitamin_c_mg = round((food_item.vitamin_c_mg or 0.0) * multiplier, 3)
            magnesium_mg = round((food_item.magnesium_mg or 0.0) * multiplier, 3)
            zinc_mg = round((food_item.zinc_mg or 0.0) * multiplier, 3)

    new_entry = DiaryEntry(
        user_id=current_user.id,
        date=entry_data.date,
        meal_type=entry_data.meal_type,
        food_item_id=entry_data.food_item_id,
        food_name=entry_data.food_name,
        portion_grams=entry_data.portion_grams,
        calories_kcal=calories_kcal,
        protein_g=protein_g,
        iron_mg=iron_mg,
        calcium_mg=calcium_mg,
        vitamin_d_mcg=vitamin_d_mcg,
        vitamin_b12_mcg=vitamin_b12_mcg,
        folate_mcg=folate_mcg,
        vitamin_a_mcg=vitamin_a_mcg,
        vitamin_c_mg=vitamin_c_mg,
        magnesium_mg=magnesium_mg,
        zinc_mg=zinc_mg,
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@app.get("/api/diary", response_model=list[DiaryEntryResponse])
def get_diary_entries(
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.user_id == current_user.id, DiaryEntry.date == date)
        .order_by(DiaryEntry.created_at)
        .all()
    )
    return entries


@app.delete("/api/diary/{entry_id}")
def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == current_user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"message": "Deleted"}


@app.get("/api/lab-results", response_model=LabResultResponse)
def get_lab_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = db.query(LabResult).filter(LabResult.user_id == current_user.id).first()
    if lab is None:
        return LabResultResponse(
            id=0,
            user_id=current_user.id,
            hemoglobin=None,
            serum_vitamin_d=None,
            ferritin=None,
            vitamin_b12=None,
            calcium=None,
        )
    return lab


@app.post("/api/lab-results", response_model=LabResultResponse)
def save_lab_results(
    lab_data: LabResultCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = db.query(LabResult).filter(LabResult.user_id == current_user.id).first()
    if lab is None:
        lab = LabResult(user_id=current_user.id)
        db.add(lab)

    lab.hemoglobin = lab_data.hemoglobin
    lab.serum_vitamin_d = lab_data.serum_vitamin_d
    lab.ferritin = lab_data.ferritin
    lab.vitamin_b12 = lab_data.vitamin_b12
    lab.calcium = lab_data.calcium

    db.commit()
    db.refresh(lab)
    return lab


@app.get("/api/assess/status")
def get_assessment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import get_consecutive_days_status
    distinct_cnt, streak, is_valid = get_consecutive_days_status(db, current_user.id)
    return {
        "distinct_days": distinct_cnt,
        "consecutive_days": streak,
        "can_run_assessment": is_valid,
        "message": "Valid 4 consecutive days logged with all 4 meal types" if is_valid else "Enter the atlest 4 concecutive days",
    }


@app.get("/api/assess/latest")
def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import get_consecutive_days_status, get_recommended_foods_for_assessment
    distinct_cnt, streak, is_valid = get_consecutive_days_status(db, current_user.id)
    latest = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    if not latest:
        return {
            "id": None,
            "wellness_score": 0.0,
            "distinct_days": distinct_cnt,
            "consecutive_days": streak,
            "can_run_assessment": is_valid,
            "risk_items": [],
            "recommended_groups": [],
            "created_at": None,
        }

    risk_items = json.loads(latest.risks_json) if latest.risks_json else []
    for item in risk_items:
        lvl = (item.get("level") or "").upper()
        nut = item.get("nutrient_name") or item.get("label", "").replace("label_", "").title()
        if lvl == "LOW":
            item["tag"] = f"Adequate {nut.lower()} intake"
        elif lvl == "MODERATE":
            item["tag"] = f"Moderate {nut.lower()} intake"
        elif lvl == "HIGH":
            item["tag"] = f"Low {nut.lower()} intake"

    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    user_restrictions = []
    if profile and profile.dietary_restrictions:
        try:
            user_restrictions = json.loads(profile.dietary_restrictions)
        except Exception:
            user_restrictions = [profile.dietary_restrictions]

    recommended_groups = get_recommended_foods_for_assessment(db, risk_items, user_restrictions)

    return {
        "id": latest.id,
        "wellness_score": latest.wellness_score,
        "distinct_days": distinct_cnt,
        "consecutive_days": streak,
        "can_run_assessment": is_valid,
        "risk_items": risk_items,
        "recommended_groups": recommended_groups,
        "created_at": latest.created_at.isoformat() if latest.created_at else None,
    }


@app.get("/api/recommendations")
def get_recommendations_endpoint(
    assessment_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import get_recommended_foods_for_assessment
    if assessment_id:
        assessment = (
            db.query(Assessment)
            .filter(Assessment.id == assessment_id, Assessment.user_id == current_user.id)
            .first()
        )
    else:
        assessment = (
            db.query(Assessment)
            .filter(Assessment.user_id == current_user.id)
            .order_by(Assessment.created_at.desc())
            .first()
        )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment yet — Run an assessment first",
        )

    risks = json.loads(assessment.risks_json) if assessment.risks_json else []
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    user_restrictions = []
    if profile and profile.dietary_restrictions:
        try:
            user_restrictions = json.loads(profile.dietary_restrictions)
        except Exception:
            user_restrictions = [profile.dietary_restrictions]

    return get_recommended_foods_for_assessment(db, risks, user_restrictions)


@app.get("/api/progress", response_model=ProgressResponse)
def get_progress_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.asc())
        .all()
    )

    history_items = []
    for idx, a in enumerate(assessments):
        score = a.wellness_score or 60.7
        avg_risk = round(100.0 - score, 1)
        risks = []
        if a.risks_json:
            try:
                risks = json.loads(a.risks_json)
            except Exception:
                pass

        top_parts = []
        if risks:
            sorted_r = sorted(risks, key=lambda r: r.get("percentage", 0), reverse=True)
            for r in sorted_r[:2]:
                n_name = r.get("nutrient_name") or r.get("label", "").replace("label_", "").capitalize()
                if "vitamin" in n_name.lower():
                    n_name = n_name.replace("Vitamin ", "Vit ").replace("vitamin ", "Vit ")
                top_parts.append(f"{n_name} {r.get('percentage', 0)}%")
        summary_str = " · ".join(top_parts) if top_parts else "Balanced"

        history_items.append(
            ProgressAssessmentItem(
                id=a.id,
                week_label=f"W{idx + 1}",
                wellness_score=score,
                avg_risk=avg_risk,
                top_risks_summary=summary_str,
                created_at=a.created_at.strftime("%Y-%m-%d") if a.created_at else None,
            )
        )

    if not history_items:
        current_score = 60.7
        current_risk = 39.3
    else:
        current_score = history_items[-1].wellness_score
        current_risk = history_items[-1].avg_risk

    return ProgressResponse(
        history=history_items,
        current_wellness_score=current_score,
        current_avg_risk=current_risk,
    )


@app.post("/api/assess")
def run_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import run_assessment_for_user
    return run_assessment_for_user(db, current_user, enforce_4_days=True)


@app.get("/api/meal-plan", response_model=MealPlanResponse)
def get_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import generate_7day_meal_plan
    return generate_7day_meal_plan(db, current_user)


@app.post("/api/meal-plan/generate", response_model=MealPlanResponse)
def regenerate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from assessment_service import generate_7day_meal_plan
    return generate_7day_meal_plan(db, current_user)





