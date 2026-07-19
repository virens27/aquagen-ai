"""
Database engine + session management.

Uses the Session pooler connection string in production (Render is IPv4-only;
Supabase's direct connection is IPv6-only unless the IPv4 add-on is enabled).
Locally, either connection type works fine.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # avoids stale-connection errors after idle periods
    pool_size=5,
    max_overflow=10,
    echo=settings.debug and settings.app_env == "development",
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency. Yields a DB session and guarantees it's closed
    after the request, even if an exception is raised.

    Usage in a route:
        @router.get("/floats")
        def list_floats(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
