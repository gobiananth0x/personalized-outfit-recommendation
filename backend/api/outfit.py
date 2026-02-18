import os

import httpx
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models
from database import SessionLocal
from api.auth import get_current_user
from data import generate_dummy_outfits
from dotenv import load_dotenv
from helper.generator import OutfitRecommender
from helper.calendar import add_to_calendar
from schemas import (
    ClothingMini,
    OutfitCreate,
    OutfitBase,
    WeeklyOutfitPlan,
    RecommendationRequest,
)

load_dotenv()

router = APIRouter(dependencies=[Depends(get_current_user)])
recommender = OutfitRecommender(api_key=os.getenv("GEMINI_API_KEY"))


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def save_outfits(
    outfits: List[OutfitCreate],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    clothing_ids = set()
    for outfit in outfits:
        clothing_ids.add(outfit.top_id)
        clothing_ids.add(outfit.bottom_id)
    valid_items = (
        db.query(models.ClothingItem)
        .filter(
            models.ClothingItem.id.in_(clothing_ids),
            models.ClothingItem.user_id == current_user.id,
        )
        .all()
    )
    valid_ids = {item.id for item in valid_items}
    if clothing_ids != valid_ids:
        raise HTTPException(status_code=400, detail="Invalid clothing data(s)")
    calendar_data = []
    for outfit_data in outfits:
        existing = (
            db.query(models.Outfit)
            .filter_by(date=outfit_data.date, user_id=current_user.id)
            .first()
        )
        top_item = db.query(models.ClothingItem).get(outfit_data.top_id)
        bottom_item = db.query(models.ClothingItem).get(outfit_data.bottom_id)
        calendar_data.append(
            {
                "date": outfit_data.date,
                "top": f"{top_item.color} {top_item.item_type}",
                "bottom": f"{bottom_item.color} {bottom_item.item_type}",
            }
        )
        if existing:
            existing.top_id = outfit_data.top_id
            existing.bottom_id = outfit_data.bottom_id
        else:
            new_outfit = models.Outfit(
                date=outfit_data.date,
                top_id=outfit_data.top_id,
                bottom_id=outfit_data.bottom_id,
                user_id=current_user.id,
            )
            db.add(new_outfit)
    db.commit()
    if current_user.google_refresh_token:
        add_to_calendar(current_user, calendar_data)
    return {"message": "Outfits saved"}


@router.get("/week", response_model=List[OutfitBase])
def get_week_outfits(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    end_date = today + timedelta(days=6)
    outfits = (
        db.query(models.Outfit)
        .filter(
            models.Outfit.user_id == current_user.id,
            models.Outfit.date >= today,
            models.Outfit.date <= end_date,
        )
        .order_by(models.Outfit.date)
        .all()
    )
    return outfits


@router.post("/generate", response_model=List[OutfitBase])
async def generate_outfits(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    city: Optional[str] = request.city
    outfit_inventory = (
        db.query(models.ClothingItem).filter_by(user_id=current_user.id).all()
    )
    if not outfit_inventory:
        raise HTTPException(
            status_code=404, detail="No clothing items found in your wardrobe."
        )
    if city:
        weather_url = (
            "http://api.weatherapi.com/v1/forecast.json?key={}&q={}&days=7".format(
                os.getenv("WEATHER_API_KEY"), city
            )
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(weather_url)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Weather API Error")
        weather_data = response.json()
        try:
            forecast_list = weather_data["forecast"]["forecastday"]
            average_temp = sum(day["day"]["avgtemp_c"] for day in forecast_list) / len(
                forecast_list
            )
            print(f"Average Temperature for {city}: {average_temp:.1f}°C")
            request.average_temperature = f"Average Temperature: {average_temp:.1f}°C"
            request.city = None
        except KeyError:
            raise HTTPException(status_code=500, detail="Failed to parse weather data")
    else:
        request.average_temperature = None
    try:
        clean_wardrobe = [
            {
                "id": item.id,
                "item_type": item.item_type,
                "color": item.color,
                "image_url": item.image_url,
                "is_available": item.is_available,
            }
            for item in outfit_inventory
        ]
        recommendation = recommender.get_recommendation(clean_wardrobe, request)
        today = date.today()
        for i, outfit in enumerate(recommendation.plan):
            outfit.date = today + timedelta(days=i)
        return recommendation.plan
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate outfits: {str(e)}"
        )
