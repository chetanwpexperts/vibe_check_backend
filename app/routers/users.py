from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select
from typing import List, Optional

from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(tags=["Users"])


# -------------------------------------------------
# 🧠 Helper: Convert relative avatar paths to full URLs
# -------------------------------------------------
def build_avatar_url(request: Request, avatar_path: Optional[str]) -> Optional[str]:
    """Convert stored relative avatar path to a full public URL."""
    if not avatar_path:
        return None

    # If it's already a complete URL, return it as-is
    if avatar_path.startswith("http"):
        return avatar_path

    # ✅ Use your ngrok domain if active, or fallback to request.base_url
    base_url = "https://slaphappy-sylas-museful.ngrok-free.dev"  # change to your active tunnel/domain
    return f"{base_url}/static/uploads/{avatar_path.split('/')[-1]}"


# -------------------------------------------------
# ✅ CREATE USER
# -------------------------------------------------
@router.post("/", response_model=UserRead)
def create_user(user_data: UserCreate, session: Session = Depends(get_session), request: Request = None):
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password,  # TODO: hash before production
        name=user_data.name,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # ✅ Attach full avatar URL for response
    new_user.avatar_url = build_avatar_url(request, new_user.avatar_url)
    return new_user


# -------------------------------------------------
# ✅ READ USERS
# -------------------------------------------------
@router.get("/", response_model=List[UserRead])
def list_users(
    session: Session = Depends(get_session),
    request: Request = None,
    search: Optional[str] = Query(None, description="Search by username or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100)
):
    query = select(User)
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    users = session.exec(query.offset(skip).limit(limit)).all()

    # ✅ Add full avatar URL to each user
    for u in users:
        u.avatar_url = build_avatar_url(request, u.avatar_url)
    return users


# -------------------------------------------------
# ✅ READ SINGLE USER
# -------------------------------------------------
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session), request: Request = None):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Format avatar URL before returning
    user.avatar_url = build_avatar_url(request, user.avatar_url)
    return user


# -------------------------------------------------
# ✏️ UPDATE USER (partial update, fully safe)
# -------------------------------------------------
@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    request: Request = None,
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_fields = user_data.dict(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    for key, value in update_fields.items():
        setattr(user, key, value)

    session.add(user)
    session.commit()
    session.refresh(user)

    # ✅ Format avatar URL for frontend display
    user.avatar_url = build_avatar_url(request, user.avatar_url)
    return user


# -------------------------------------------------
# 🗑 DELETE USER
# -------------------------------------------------
@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()
    return {"status": "success", "message": f"User {user.username} deleted successfully"}
