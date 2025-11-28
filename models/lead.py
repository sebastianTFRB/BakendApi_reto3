import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from db.session import Base


class LeadUrgency(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadCategory(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True, index=True)
    preferred_area = Column(String(255), nullable=True)
    budget = Column(Numeric(12, 2), nullable=True)
    urgency = Column(Enum(LeadUrgency), default=LeadUrgency.medium)
    category = Column(Enum(LeadCategory), default=LeadCategory.C)
    intent_score = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship("Agency", back_populates="leads")
    interactions = relationship("LeadInteraction", back_populates="lead", cascade="all, delete-orphan")
