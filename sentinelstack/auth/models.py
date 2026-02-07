import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sentinelstack.database import Base

class User(Base):
    __tablename__ = "users"

    # UUID Primary Key (Better for security than 1, 2, 3...)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core Identity
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Authorization & Status
    role = Column(String, default="user", nullable=False)  # 'admin' or 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit Trail
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)