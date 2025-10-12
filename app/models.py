# vibe_check_backend/app/models.py

from datetime import datetime
from typing import Optional, List

from sqlmodel import Field, SQLModel, Column, Relationship
# NOTE: Import String type for use in ARRAY below
from sqlalchemy import String 
from sqlalchemy import String, ForeignKey
from geoalchemy2 import Geometry  # GeoAlchemy for PostGIS integration
from sqlalchemy.dialects.postgresql import ARRAY  # For the list of Vibe Tags

class Report(SQLModel, table=True):
    """
    Represents a single Vibe Check report submitted by a user.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # --- Geospatial Data ---
    location: Geometry = Field(
        sa_column=Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True)),
        description="Geographic point (Lat/Lon) where the report was taken."
    )
    
    # --- Vibe Data ---
    place_name: str = Field(index=True, max_length=100)
    crowd_status: int  # 1=Empty, 2=Busy, 3=Packed
    decibel_level: float
    
    # FIX: Changed item_type=str to item_type=String (SQLAlchemy Type)
    # This resolves the "AttributeError: 'str' object has no attribute '_variant_mapping'"
    vibe_tags: List[str] = Field(sa_column=Column(ARRAY(item_type=String))) 
    
    # --- Metadata ---
    user_id: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # --- Pydantic Config to allow Geometry ---
    model_config = {
        "arbitrary_types_allowed": True
    }

# 🧍 User Table
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, unique=True)
    password_hash: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    # Relations
    vibes: List["Vibe"] = Relationship(back_populates="user")


# 🎵 Vibe Table
class Vibe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    location: Geometry = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True))
    )
    place_name: str = Field(max_length=150)
    crowd_status: int
    decibel_level: float
    vibe_tags: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(item_type=String))
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relations
    user: Optional[User] = Relationship(back_populates="vibes")
    media: List["VibeMedia"] = Relationship(back_populates="vibe")
    metrics: Optional["VibeMetrics"] = Relationship(back_populates="vibe")

    model_config = {"arbitrary_types_allowed": True}


# 🖼 Media Table
class VibeMedia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vibe_id: Optional[int] = Field(default=None, foreign_key="vibe.id")
    media_type: str = Field(max_length=10)
    file_url: str
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    vibe: Optional[Vibe] = Relationship(back_populates="media")


# 📊 Metrics Table
class VibeMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vibe_id: Optional[int] = Field(default=None, foreign_key="vibe.id", unique=True)
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    average_rating: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    vibe: Optional[Vibe] = Relationship(back_populates="metrics")


# 👥 Followers Table
class Follower(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    follower_id: int = Field(foreign_key="user.id")
    followed_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 🔑 Sessions Table
class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None