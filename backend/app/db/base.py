"""
Shared declarative base. All models inherit from this.
Kept in its own module (separate from session.py) to avoid circular imports
when models need to import Base but session.py imports models for metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
