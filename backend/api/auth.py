import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import models
from database import SessionLocal

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRE_MINUTES = 60 * 24
security = HTTPBearer()

REDIRECT_URI = "postmessage"


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GoogleAuthRequest(BaseModel):
    code: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_jwt(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(credentials=Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/google", response_model=AuthResponse)
def google_login(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.events",
            ],
        )
        flow.redirect_uri = "postmessage"

        flow.fetch_token(code=data.code)
        credentials = flow.credentials

        idinfo = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
        )

    except Exception as e:
        print(f"GOOGLE AUTH ERROR: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google code")
    email = idinfo.get("email")
    name = idinfo.get("name")
    picture = idinfo.get("picture")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found")
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        user = models.User(email=email, name=name, picture=picture)
        db.add(user)
    else:
        user.name = name
        user.picture = picture
    if credentials.refresh_token:
        user.google_refresh_token = credentials.refresh_token
    db.commit()
    db.refresh(user)
    access_token = create_jwt({"user_id": user.id, "email": user.email})
    return {"access_token": access_token}


@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }
