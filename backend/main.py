import json

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import auth
from database import Base, engine, get_db
from models import HealthProfile, User, FoodItem, DiaryEntry, LabResult
from schemas import (
    HealthProfileCreate,
    HealthProfileResponse,
    HealthProfileSaveResponse,
    TokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
    FoodSearchResult,
    DiaryEntryCreate,
    DiaryEntryResponse,
    LabResultCreate,
    LabResultResponse,
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
    profile_data: HealthProfileCreate,
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
def search_foods(q: str, limit: int = 15, db: Session = Depends(get_db)):
    foods = db.query(FoodItem).filter(FoodItem.name.ilike(f"%{q}%")).limit(limit).all()
    return foods


@app.post("/api/diary", response_model=DiaryEntryResponse)
def create_diary_entry(
    entry_data: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food_item = None
    energy_kcal = 0.0
    protein_g = 0.0
    fat_g = 0.0
    carb_g = 0.0
    iron_mg = 0.0

    if entry_data.food_item_id:
        food_item = db.query(FoodItem).filter(FoodItem.id == entry_data.food_item_id).first()
        if food_item:
            multiplier = entry_data.portion_grams / 100.0
            energy_kcal = (food_item.calories_kcal or 0.0) * multiplier
            protein_g = (food_item.protein_g or 0.0) * multiplier
            fat_g = 0.0
            carb_g = 0.0
            iron_mg = (food_item.iron_mg or 0.0) * multiplier

    new_entry = DiaryEntry(
        user_id=current_user.id,
        date=entry_data.date,
        meal_type=entry_data.meal_type,
        food_item_id=entry_data.food_item_id,
        food_name=entry_data.food_name,
        portion_grams=entry_data.portion_grams,
        energy_kcal=energy_kcal,
        protein_g=protein_g,
        fat_g=fat_g,
        carb_g=carb_g,
        iron_mg=iron_mg,
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

