# app/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from sqlmodel import SQLModel


class ReportCreate(BaseModel):
    lat: float = Field(..., description="Latitude of the report location.")
    lon: float = Field(..., description="Longitude of the report location.")
    place_name: str = Field(..., max_length=100)
    crowd_status: int = Field(..., ge=1, le=3)
    decibel_level: float = Field(...)
    vibe_tags: List[str] = Field(...)
    user_id: str = Field(..., max_length=50)


class ReportRead(BaseModel):
    id: int
    place_name: str
    crowd_status: int
    decibel_level: float
    vibe_tags: List[str]
    user_id: str
    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

# ============================================================
# 🧍 USER SCHEMAS
# ============================================================

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserRead(UserBase):
    id: int
    joined_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# IMPORTANT: make UserUpdate a regular Pydantic BaseModel so we can accept partial updates
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ============================================================
# 🎵 VIBE SCHEMAS
# ============================================================

class VibeBase(BaseModel):
    place_name: str
    decibel_level: float
    crowd_status: int
    vibe_tags: Optional[List[str]] = None


class VibeCreate(VibeBase):
    user_id: int


class VibeRead(VibeBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


# ============================================================
# 🖼 MEDIA SCHEMAS
# ============================================================

class VibeMediaBase(BaseModel):
    media_type: str
    file_url: str
    thumbnail_url: Optional[str] = None


class VibeMediaCreate(VibeMediaBase):
    vibe_id: int


class VibeMediaRead(VibeMediaBase):
    id: int
    vibe_id: int
    uploaded_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# 📊 METRICS SCHEMAS
# ============================================================

class VibeMetricsBase(BaseModel):
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    average_rating: Optional[float] = None


class VibeMetricsRead(VibeMetricsBase):
    id: int
    vibe_id: int
    updated_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# 👥 FOLLOWER SCHEMAS
# ============================================================

class FollowerBase(BaseModel):
    follower_id: int
    followed_id: int


class FollowerRead(FollowerBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ============================================================
# 🔑 SESSION SCHEMAS
# ============================================================

class SessionBase(BaseModel):
    token: str


class SessionRead(SessionBase):
    id: int
    user_id: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        orm_mode = True
