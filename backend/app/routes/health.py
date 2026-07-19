"""
Health check endpoints.
GET /health         -> app is up (no DB dependency, for Render's health checks)
GET /health/db       -> app is up AND can reach Supabase
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    return {"status": "ok"}


@router.get("/db")
def health_db(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        table_count = db.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "AND table_name IN ('ocean_data', 'ingestion_log', 'query_log')"
            )
        ).scalar()
        return {
            "status": "ok",
            "database": "connected",
            "expected_tables_found": table_count,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {exc}") from exc
