from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel


class ClothingMini(BaseModel):
    id: int
    item_type: str
    color: str
    image_url: str | None
    is_available: bool

    class Config:
        from_attributes = True


class OutfitCreate(BaseModel):
    date: date
    top_id: int
    bottom_id: int


class OutfitBase(BaseModel):
    date: date
    top: ClothingMini
    bottom: ClothingMini

    class Config:
        from_attributes = True


class WeeklyOutfitPlan(BaseModel):
    plan: List[OutfitBase]


class RecommendationRequest(BaseModel):
    city: Optional[str] = None
    average_temperature: Optional[str] = None
    previous_plan: Optional[WeeklyOutfitPlan] = None
