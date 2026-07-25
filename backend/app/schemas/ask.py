"""
Pydantic request/response models for /ask.

Kept separate from app/models/ on purpose — app/models/ holds SQLAlchemy ORM
models (the database tables), while these are API request/response shapes.
Mixing the two under one folder gets confusing fast once a project has more
than a couple of endpoints.
"""
from typing import Any

from pydantic import BaseModel

class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


class AskResponse(BaseModel):
    question: str | None = None
    sql: str | None = None
    data: list[dict[str, Any]] | None = None
    explanation: str
    error: str | None = None
    session_id: str | None = None