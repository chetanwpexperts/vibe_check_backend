# vibe_check_backend/app/crud.py

from sqlmodel import Session, select, func
from geoalchemy2 import WKTElement
from typing import List, Sequence

# Local Imports
from app.models import Report
from app.schemas import ReportCreate
from sqlalchemy.engine.result import ChunkedIteratorResult


# --- CREATE operation (Existing, verified working) ---
async def create_report(db: Session, report_in: ReportCreate):
    """
    Inserts a new report into the database, converting the lat/lon 
    into a PostGIS GEOMETRY point first.
    """
    wkt_point = f"POINT({report_in.lon} {report_in.lat})"
    location_point = WKTElement(wkt_point, srid=4326)
    
    db_report = Report(
        location=location_point,
        place_name=report_in.place_name,
        crowd_status=report_in.crowd_status,
        decibel_level=report_in.decibel_level,
        vibe_tags=report_in.vibe_tags,
        user_id=report_in.user_id 
    )
    
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    
    return db_report

# --- READ operation (FINAL FIX: Geo-Awarare Retrieval) ---
from geoalchemy2 import Geography  # ✅ Correct type import

async def get_reports_nearby(db: Session, lat: float, lon: float, radius_meters: int) -> List[Report]:
    """
    Queries the database for reports within a specified distance of the given (lat, lon).
    """

    user_location = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326).cast(Geography)

    statement = (
        select(Report)
        .where(
            func.ST_DWithin(
                Report.location.cast(Geography),  # Ensure Report.location is cast too
                user_location,
                radius_meters
            )
        )
        .limit(50)
    )

    result = await db.execute(statement)
    reports = result.scalars().all()

    return reports
