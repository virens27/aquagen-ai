"""ORM model for query_log — tracks natural-language queries from users."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user_query: Mapped[str] = mapped_column(String, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(String)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[str | None] = mapped_column(String)
    result_row_count: Mapped[int | None] = mapped_column(Integer)
    session_id: Mapped[str | None] = mapped_column(String, index=True)

    def __repr__(self) -> str:
        return f"<QueryLog id={self.id} success={self.success}>"
