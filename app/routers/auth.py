# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
import os
import shutil
from pathlib import Path
import secrets

from app.database import get_session
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# -------------------------------------------------
# 🧍 REGISTER  (unchanged)
# -------------------------------------------------
@router.post("/register", response_model=UserRead)
async def register_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_pw,
        name=user_data.name,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio,
    )

    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")

    return new_user


# -------------------------------------------------
# 🔐 LOGIN (unchanged)
# -------------------------------------------------
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.username}, expires_delta=token_expires)
    return {"access_token": token, "token_type": "bearer"}


# -------------------------------------------------
# 👤 GET CURRENT USER (unchanged)
# -------------------------------------------------
@router.get("/me", response_model=UserRead)
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload["sub"]
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -------------------------------------------------
# ✅ Update current user (multipart/form-data support)
# Accepts form fields (name, bio) and optionally an uploaded file named "avatar" or "avatar_url"
# -------------------------------------------------
@router.put("/me", response_model=UserRead)
async def update_current_user_profile(
    # Accept text fields from form
    name: str | None = Form(None),
    bio: str | None = Form(None),
    # Accept file (could be sent with form key "avatar" or "avatar_url")
    avatar: UploadFile | None = File(None),
    avatar_url: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # collect updates
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if bio is not None:
        update_data["bio"] = bio

    # handle file if provided (avatar or avatar_url)
    uploaded_file = avatar or avatar_url
    if uploaded_file is not None:
        # Save file to local static folder: ./static/uploads/
        upload_root = Path("static") / "uploads"
        upload_root.mkdir(parents=True, exist_ok=True)

        # use a random filename to avoid collisions
        ext = Path(uploaded_file.filename).suffix or ""
        safe_name = secrets.token_hex(12) + ext
        dest_path = upload_root / safe_name

        # write file
        try:
            with dest_path.open("wb") as f:
                contents = await uploaded_file.read()
                f.write(contents)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")

        # set avatar_url to a path the client can request (assumes StaticFiles mounted at /static)
        update_data["avatar_url"] = f"/static/uploads/{safe_name}"

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    # Apply updates to the SQLModel user instance and persist
    for key, value in update_data.items():
        setattr(current_user, key, value)

    # Because we're using AsyncSession we must add + commit via awaitable methods
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return current_user
