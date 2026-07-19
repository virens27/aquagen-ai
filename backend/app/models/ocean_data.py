"""
ORM model for ocean_data — core ARGO float measurements.
Mirrors the table created in schema.sql. The `location` geography column
is managed by a DB trigger (ocean_data_set_location), so it's not written
to directly from the app — SQLAlchemy just needs to know it exists for reads.
"""
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import BigInteger, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OceanData(Base):
    __tablename__ = "ocean_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    float_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    cycle_number: Mapped[int | None] = mapped_column(Integer)
    profile_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    pressure_dbar: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    salinity_psu: Mapped[float | None] = mapped_column(Float)
    data_mode: Mapped[str | None] = mapped_column(String)
    source_file: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<OceanData float_id={self.float_id} cycle={self.cycle_number} date={self.profile_date}>"
