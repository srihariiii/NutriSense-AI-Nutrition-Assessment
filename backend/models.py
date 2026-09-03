import json

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    health_profile = relationship("HealthProfile", back_populates="user", uselist=False)
    lab_result = relationship("LabResult", back_populates="user", uselist=False)
    assessments = relationship("Assessment", back_populates="user")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    sex = Column(String(50), nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String(50), nullable=False)
    health_goal = Column(String(100), nullable=False)
    dietary_restrictions = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="health_profile")

    @property
    def dietary_restrictions_list(self) -> list[str]:
        return json.loads(self.dietary_restrictions)

    @dietary_restrictions_list.setter
    def dietary_restrictions_list(self, value: list[str]) -> None:
        self.dietary_restrictions = json.dumps(value)


class FoodItem(Base):
    __tablename__ = "food_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    tags = Column(Text, default="")
    calories_kcal = Column(Float, default=0)
    protein_g = Column(Float, default=0)
    iron_mg = Column(Float, default=0)
    calcium_mg = Column(Float, default=0)
    vitamin_d_mcg = Column(Float, default=0)
    vitamin_b12_mcg = Column(Float, default=0)
    folate_mcg = Column(Float, default=0)
    vitamin_a_mcg = Column(Float, default=0)
    vitamin_c_mg = Column(Float, default=0)
    magnesium_mg = Column(Float, default=0)
    zinc_mg = Column(Float, default=0)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    fdc_id = Column(String(32), nullable=True)
    data_type = Column(String(32), default="unknown")
    serving_description = Column(String(255), nullable=True)
    serving_gram_weight = Column(Float, nullable=True)
    ingredients = Column(Text, nullable=True)

    @property
    def energy_kcal(self) -> float:
        return self.calories_kcal or 0.0

    @property
    def vitc_mg(self) -> float:
        return self.vitamin_c_mg or 0.0

    @property
    def fat_g(self) -> float:
        return 0.0

    @property
    def carb_g(self) -> float:
        return 0.0

    @property
    def fiber_g(self) -> float:
        return 0.0

    @property
    def source(self) -> str:
        return self.data_type or ""



class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=True)
    food_name = Column(String(500), nullable=False)
    portion_grams = Column(Float, nullable=False)
    calories_kcal = Column(Float, default=0.0)
    protein_g = Column(Float, default=0.0)
    iron_mg = Column(Float, default=0.0)
    calcium_mg = Column(Float, default=0.0)
    vitamin_d_mcg = Column(Float, default=0.0)
    vitamin_b12_mcg = Column(Float, default=0.0)
    folate_mcg = Column(Float, default=0.0)
    vitamin_a_mcg = Column(Float, default=0.0)
    vitamin_c_mg = Column(Float, default=0.0)
    magnesium_mg = Column(Float, default=0.0)
    zinc_mg = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def energy_kcal(self) -> float:
        return self.calories_kcal or 0.0



class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    hemoglobin = Column(Float, nullable=True)
    serum_vitamin_d = Column(Float, nullable=True)
    ferritin = Column(Float, nullable=True)
    vitamin_b12 = Column(Float, nullable=True)
    calcium = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="lab_result")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    features_json = Column(Text, nullable=False)
    risks_json = Column(Text, nullable=False)
    wellness_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="assessments")


