# main.py (root — the module you run with `uvicorn main:app`)
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.database import create_db_and_tables
from app.routers import reports

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Attempting to create database tables...")
    # create_db_and_tables is async — await it
    await create_db_and_tables()
    print("✅ Database tables and PostGIS geometry columns created successfully.")
    yield
    print("Application shutdown complete.")


app = FastAPI(
    title="The Vibe Check API (MVP)",
    version="1.0.0",
    description="Backend for real-time, hyper-local crowd and status reporting.",
    lifespan=lifespan,
)

# CORS if needed
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "The Vibe Check API is online!", "status": "ok"}

# mount reports router at /api/reports
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
