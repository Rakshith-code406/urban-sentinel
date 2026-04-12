from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Sequence

from app.core.database import Base


class WorkerResetRequest(Base):
    __tablename__ = "worker_reset_requests"

    id = Column(Integer, Sequence("worker_reset_requests_seq"), primary_key=True)
    worker_id = Column(Integer, index=True, nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(50), default="Pending")
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
