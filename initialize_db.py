# vibe_check_backend/initialize_db.py

import asyncio
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import text # <-- Needed for raw SQL execution
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String

# Local imports from your app directory
from app.database import engine
# Import all models so SQLModel.metadata knows about them
from app.models import Report 

async def create_db_and_tables():
    """
    Asynchronously ensures the PostGIS extension is installed and then 
    creates all necessary database tables.
    """
    print("Database initialization starting...")
    
    async with engine.begin() as conn:
        
        # 1. CRITICAL FIX: Ensure PostGIS extension is created
        # We must run this DDL command explicitly before trying to create tables 
        # that use the 'geometry' type.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # 2. Create the tables using SQLModel's metadata
        # This runs the synchronous DDL (CREATE TABLE) commands within an async transaction.
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("Database initialization complete. Tables created successfully.")

if __name__ == "__main__":
    # This runs the async function synchronously when called from the terminal
    asyncio.run(create_db_and_tables())