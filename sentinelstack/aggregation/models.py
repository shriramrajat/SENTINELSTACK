from sqlalchemy import Column, String, Integer, DateTime, Float, Index, BigInteger
from datetime import datetime
from sentinelstack.database import Base

class RequestMetric(Base):
    __tablename__ = "request_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Time Bucket (snapped to minute start, e.g., 2023-10-27 10:05:00)
    bucket_time = Column(DateTime, nullable=False, index=True)
    
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    
    # Aggregated Stats
    total_requests = Column(BigInteger, default=0)
    total_errors = Column(BigInteger, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)

    # Composite Index for fast lookups/deduplication
    __table_args__ = (
        Index('idx_metrics_bucket_path', 'bucket_time', 'path', 'method', 'status_code'),
    )
