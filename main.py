# main.py (root — the module you run with `uvicorn main:app`)
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi.middleware.cors import CORSMiddleware

# ✅ Import existing database init and routers
from app.database import create_db_and_tables
from app.routers import reports, users, vibes  # add new routers here
from app.routers import reports, users, vibes, auth

# Optional: include mock_vibes if you kept it
try:
    from app.routers import mock_vibes
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False


# =====================================================
# 🔹 Application Startup Lifecycle
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Attempting to create database tables...")
    await create_db_and_tables()  # ensure DB & PostGIS setup
    print("✅ Database tables and PostGIS geometry columns created successfully.")
    yield
    print("Application shutdown complete.")


# =====================================================
# 🔹 FastAPI Application Setup
# =====================================================
app = FastAPI(
    title="The Vibe Check API (MVP)",
    version="1.0.0",
    description="Backend for real-time, hyper-local crowd and status reporting.",
    lifespan=lifespan,
)

# =====================================================
# 🔹 Middleware (CORS)
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# 🔹 Root Route
# =====================================================
@app.get("/")
def read_root():
    return {"message": "The Vibe Check API is online!", "status": "ok"}


# =====================================================
# 🔹 Routers Mounting
# =====================================================
# Existing Reports API
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

# New Users API
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# New Vibes API (real data)
app.include_router(vibes.router, prefix="/api/vibes", tags=["Vibes"])

# Optional Mock Vibes API (random demo vibes)
if HAS_MOCK:
    app.include_router(mock_vibes.router, prefix="/api/mock_vibes", tags=["Mock Vibes"])

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

app.mount("/static", StaticFiles(directory="static"), name="static")


# =====================================================
# 🔹 Entry Point
# =====================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
