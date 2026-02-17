from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index
from datetime import datetime
from sentinelstack.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    
    # State
    status = Column(String, default="active") # active, resolved
    severity = Column(String, default="medium") # critical, high, medium, low
    
    # Timing
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    # Context
    description = Column(String, nullable=False) # e.g. "High Error Rate (>5%)"
    affected_endpoints = Column(String, nullable=True) # JSON string or comma-separated
    
    # Ai Analysis (Populated later by async job)
    ai_summary = Column(String, nullable=True)
    ai_action_items = Column(String, nullable=True)

    __table_args__ = (
        Index('idx_incidents_status', 'status'),
    )
