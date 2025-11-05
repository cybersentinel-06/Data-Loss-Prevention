"""
Policy Database Models (PostgreSQL)
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    compliance_tags = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Policy {self.name}>"
