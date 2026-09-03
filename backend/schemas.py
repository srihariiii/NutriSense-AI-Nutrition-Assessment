from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

ALLOWED_RESTRICTIONS = {
    "Vegetarian",
    "Vegan",
    "Gluten-free",
    "Dairy-free",
    "Nut allergy",
    "None",
}

ACTIVITY_LEVELS = {
    "Sedentary",
    "Lightly active",
    "Moderately active",
    "Very active",
    "Extremely active",
}

SEX_OPTIONS = {"Female", "Male"}

HEALTH_GOALS = {
    "Improve energy",
    "Weight loss",
    "Weight gain",
    "Maintain weight",
    "Build muscle",
    "Improve overall health",
    "Improve nutrition",
}


class UserSignup(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one number")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserAccountUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    current_password: str | None = None
    new_password: str | None = None
    confirm_new_password: str | None = None



class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HealthProfileCreate(BaseModel):
    age: int = Field(..., ge=1, le=120)
    sex: str
    height_cm: float = Field(..., gt=0, le=300)
    weight_kg: float = Field(..., gt=0, le=500)
    activity_level: str
    health_goal: str
    dietary_restrictions: list[str] = Field(..., min_length=1)

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: str) -> str:
        if value not in SEX_OPTIONS:
            raise ValueError("Please select a valid sex option")
        return value

    @field_validator("activity_level")
    @classmethod
    def validate_activity(cls, value: str) -> str:
        if value not in ACTIVITY_LEVELS:
            raise ValueError("Please select a valid activity level")
        return value

    @field_validator("health_goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Please enter your health goal")
        return value.strip()

    @field_validator("dietary_restrictions", mode="before")
    @classmethod
    def validate_restrictions(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or len(value) == 0:
            value = ["None"]
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            return ["None"]
        if "None" in cleaned and len(cleaned) > 1:
            cleaned = [item for item in cleaned if item != "None"]
        return cleaned


class HealthProfileResponse(BaseModel):
    id: int
    user_id: int
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    activity_level: str
    health_goal: str
    dietary_restrictions: list[str]

    class Config:
        from_attributes = True


class HealthProfileSaveResponse(BaseModel):
    message: str
    profile: HealthProfileResponse


class FoodSearchResult(BaseModel):
    id: int
    name: str
    calories_kcal: float = 0.0
    protein_g: float = 0.0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    vitamin_c_mg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    data_type: str | None = ""
    tags: str | list[str] | None = ""

    @property
    def energy_kcal(self) -> float:
        return self.calories_kcal

    @property
    def vitc_mg(self) -> float:
        return self.vitamin_c_mg

    @property
    def source(self) -> str:
        return self.data_type or ""

    class Config:
        from_attributes = True



class DiaryEntryCreate(BaseModel):
    date: str
    meal_type: str
    food_item_id: int | None = None
    food_name: str
    portion_grams: float


class DiaryEntryResponse(BaseModel):
    id: int
    date: str
    meal_type: str
    food_name: str
    portion_grams: float
    calories_kcal: float = 0.0
    protein_g: float = 0.0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    folate_mcg: float = 0.0
    vitamin_a_mcg: float = 0.0
    vitamin_c_mg: float = 0.0
    magnesium_mg: float = 0.0
    zinc_mg: float = 0.0

    @property
    def energy_kcal(self) -> float:
        return self.calories_kcal

    class Config:
        from_attributes = True



class LabResultCreate(BaseModel):
    hemoglobin: float | None = None
    serum_vitamin_d: float | None = None
    ferritin: float | None = None
    vitamin_b12: float | None = None
    calcium: float | None = None


class LabResultResponse(BaseModel):
    id: int
    user_id: int
    hemoglobin: float | None = None
    serum_vitamin_d: float | None = None
    ferritin: float | None = None
    vitamin_b12: float | None = None
    calcium: float | None = None

    class Config:
        from_attributes = True


class AssessmentRiskItem(BaseModel):
    label: str
    nutrient_name: str
    probability: float
    percentage: int
    level: str
    tag: str
    lab_boosted: bool = False
    lab_notes: str | None = None


class RecommendedFoodItem(BaseModel):
    id: int
    name: str
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    protein_g: float = 0.0
    vitamin_c_mg: float = 0.0
    vitamin_d_mcg: float = 0.0
    vitamin_b12_mcg: float = 0.0
    target_val: float | None = None
    target_display: str | None = None
    tags: str | list[str] | None = ""


class RecommendedGroup(BaseModel):
    nutrient: str | None = None
    nutrient_name: str
    foods: list[Any]


class AssessmentResponse(BaseModel):
    id: int | None = None
    wellness_score: float
    distinct_days: int
    consecutive_days: int
    can_run_assessment: bool
    risk_items: list[AssessmentRiskItem]
    recommended_groups: list[RecommendedGroup]


class MealItemResponse(BaseModel):
    meal_type: str
    food_title: str
    target_summary: str


class DayMealPlanResponse(BaseModel):
    day_key: str
    day_name: str
    meals: list[MealItemResponse]


class MealPlanResponse(BaseModel):
    focus_nutrients: list[str]
    dietary_restrictions: list[str]
    days: list[DayMealPlanResponse]
    created_at: str | None = None


class ProgressAssessmentItem(BaseModel):
    id: int
    week_label: str
    wellness_score: float
    avg_risk: float
    top_risks_summary: str
    created_at: str | None = None


class ProgressResponse(BaseModel):
    history: list[ProgressAssessmentItem]
    current_wellness_score: float
    current_avg_risk: float



