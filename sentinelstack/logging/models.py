import uuid
import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sentinelstack.database import Base

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Who
    client_ip = Column(String, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    
    # What
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    
    # Context
    error_flag = Column(Boolean, default=False)