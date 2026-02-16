import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from api.auth import router as auth_router
from api.clothing import router as clothing_router
from api.outfit import router as outfit_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://personalized-outfit-recommendation.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Item-Type", "Color"],
)

models.Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {"message": "Alive"}


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(clothing_router, prefix="/clothing-items", tags=["Clothing"])
app.include_router(outfit_router, prefix="/outfits", tags=["Outfits"])
