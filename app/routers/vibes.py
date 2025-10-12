# app/routers/vibes.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from typing import List, Optional
import random

from app.database import get_session
from app.models import Vibe, User
from app.schemas import VibeCreate, VibeRead
from app.dependencies.auth_user import get_current_user  # 🔐 import for ownership

router = APIRouter(tags=["Vibes"])

# Mock vibes list
MOCK_VIBES = [
    {"mood": "Calm & Cozy", "emoji": "🧘‍♂️", "description": "Peaceful energy around you."},
    {"mood": "Busy & Buzzing", "emoji": "🚀", "description": "The area is full of energy and activity — stay alert!"},
    {"mood": "Lively & Fun", "emoji": "🎉", "description": "People are having a good time nearby."},
    {"mood": "Focused & Chill", "emoji": "🎧", "description": "A quiet, productive vibe — great for work or study."},
    {"mood": "Romantic & Warm", "emoji": "💞", "description": "Love is in the air!"},
]


@router.get("/random", summary="Get a random demo vibe")
def get_random_vibe():
    return {"status": "success", "vibe": random.choice(MOCK_VIBES)}


# -------------------------------------------------
# ✅ CREATE (Authenticated)
# -------------------------------------------------
@router.post("/", response_model=VibeRead)
def create_vibe(
    vibe_data: VibeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    vibe = Vibe(
        user_id=current_user.id,
        place_name=vibe_data.place_name,
        decibel_level=vibe_data.decibel_level,
        crowd_status=vibe_data.crowd_status,
        vibe_tags=vibe_data.vibe_tags,
    )
    session.add(vibe)
    session.commit()
    session.refresh(vibe)
    return vibe


# -------------------------------------------------
# 🔍 FILTER + PAGINATION
# -------------------------------------------------
@router.get("/", response_model=List[VibeRead])
def list_vibes(
    session: Session = Depends(get_session),
    user_id: Optional[int] = Query(None),
    place: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
):
    query = select(Vibe)
    if user_id:
        query = query.where(Vibe.user_id == user_id)
    if place:
        query = query.where(Vibe.place_name.ilike(f"%{place}%"))
    return session.exec(query.offset(skip).limit(limit)).all()


# -------------------------------------------------
# ✏️ UPDATE (Owner only)
# -------------------------------------------------
@router.put("/{vibe_id}", response_model=VibeRead)
def update_vibe(
    vibe_id: int,
    vibe_data: VibeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    vibe = session.get(Vibe, vibe_id)
    if not vibe:
        raise HTTPException(status_code=404, detail="Vibe not found")

    if vibe.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own vibes")

    vibe.place_name = vibe_data.place_name
    vibe.decibel_level = vibe_data.decibel_level
    vibe.crowd_status = vibe_data.crowd_status
    vibe.vibe_tags = vibe_data.vibe_tags

    session.add(vibe)
    session.commit()
    session.refresh(vibe)
    return vibe


# -------------------------------------------------
# 🗑 DELETE (Owner only)
# -------------------------------------------------
@router.delete("/{vibe_id}")
def delete_vibe(
    vibe_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    vibe = session.get(Vibe, vibe_id)
    if not vibe:
        raise HTTPException(status_code=404, detail="Vibe not found")

    if vibe.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own vibes")

    session.delete(vibe)
    session.commit()
    return {"status": "success", "message": f"Vibe {vibe_id} deleted successfully"}
