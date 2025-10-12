import json
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_session
from app.schemas import ReportCreate, ReportRead

# ✅ Import the JWT helper to verify users
from app.dependencies.auth_user import get_current_user
from app.models import User

router = APIRouter()


# ---------------------------------------------------------------------
# 🔐 POST - Submit a new Vibe Check Report (Authenticated)
# ---------------------------------------------------------------------
@router.post("/", response_model=ReportRead, summary="Submit a new Vibe Check Report")
async def submit_report(
    report: ReportCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # 👈 require valid token
):
    """
    Insert a new vibe check report with PostGIS point geometry and Postgres array (vibe_tags[]).
    Only accessible to authenticated users.
    """
    try:
        params = {
            "place_name": report.place_name,
            "crowd_status": report.crowd_status,
            "decibel_level": report.decibel_level,
            "vibe_tags": report.vibe_tags,
            "user_id": current_user.id,  # 👈 user_id comes from JWT
            "lon": report.lon,
            "lat": report.lat,
        }

        insert_sql = text("""
            INSERT INTO report (place_name, crowd_status, decibel_level, vibe_tags, user_id, location)
            VALUES (:place_name, :crowd_status, :decibel_level, :vibe_tags, :user_id,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            RETURNING id, place_name, crowd_status, decibel_level, vibe_tags, user_id, "timestamp",
                      ST_Y(location::geometry) AS latitude,
                      ST_X(location::geometry) AS longitude;
        """)

        result = await session.execute(insert_sql, params)
        await session.commit()

        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=500, detail="Insert returned no row.")

        return {
            "id": row["id"],
            "place_name": row["place_name"],
            "crowd_status": row["crowd_status"],
            "decibel_level": float(row["decibel_level"]) if row["decibel_level"] is not None else None,
            "vibe_tags": row["vibe_tags"],
            "user_id": row["user_id"],
            "timestamp": row["timestamp"],
            "latitude": float(row["latitude"]) if row["latitude"] is not None else None,
            "longitude": float(row["longitude"]) if row["longitude"] is not None else None,
        }

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error inserting report: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------
# 🌍 GET - Retrieve Nearby Reports (Public)
# ---------------------------------------------------------------------
@router.get("/nearby", summary="Retrieve latest Vibe Check per place (sorted by distance)")
async def get_nearby_reports(
    lat: float = Query(..., description="User's current latitude"),
    lon: float = Query(..., description="User's current longitude"),
    radius_km: float = Query(100.0, description="Search radius in kilometers (default 100 km)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Return the most recent report for each unique place within the radius.
    Public endpoint — no authentication required.
    """
    try:
        query = text("""
            SELECT DISTINCT ON (place_name)
                id,
                place_name,
                crowd_status,
                decibel_level,
                vibe_tags,
                user_id,
                "timestamp",
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_Distance(
                    location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) / 1000 AS distance_km
            FROM report
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_meters
            )
            ORDER BY place_name, "timestamp" DESC;
        """)

        params = {"lon": lon, "lat": lat, "radius_meters": radius_km * 1000}
        result = await session.execute(query, params)
        rows = result.mappings().all()

        out = []
        for r in rows:
            vt = r["vibe_tags"]
            if isinstance(vt, (str, bytes)):
                try:
                    vt = json.loads(vt)
                except Exception:
                    pass
            out.append(
                {
                    "id": r["id"],
                    "place_name": r["place_name"],
                    "crowd_status": r["crowd_status"],
                    "decibel_level": r["decibel_level"],
                    "vibe_tags": vt,
                    "user_id": r["user_id"],
                    "timestamp": r["timestamp"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "distance_km": round(r["distance_km"], 2),
                }
            )

        return {
            "status": "success",
            "count": len(out),
            "radius_km": radius_km,
            "data": out,
        }

    except Exception as exc:
        print(f"❌ Error fetching nearby reports: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    
# ---------------------------------------------------------------------
# 🗑 DELETE - Remove a report (Owner only)
# ---------------------------------------------------------------------
@router.delete("/{report_id}", summary="Delete a report (owner only)")
async def delete_report(
    report_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a report if it belongs to the current user.
    """
    try:
        # 1️⃣ Fetch report owner
        check_owner_sql = text("SELECT user_id FROM report WHERE id = :rid")
        owner_result = await session.execute(check_owner_sql, {"rid": report_id})
        owner_row = owner_result.mappings().first()

        if not owner_row:
            raise HTTPException(status_code=404, detail="Report not found")

        if owner_row["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own reports")

        # 2️⃣ Delete report
        delete_sql = text("DELETE FROM report WHERE id = :rid")
        await session.execute(delete_sql, {"rid": report_id})
        await session.commit()

        return {"status": "success", "message": f"Report {report_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ Error deleting report: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
