from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Sequence

from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, Sequence("workers_seq"), primary_key=True)
    worker_id = Column(String(100), unique=True, nullable=False)
    department = Column(String(100), index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_plaintext = Column(String(255), nullable=True)
    created_by_admin_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
