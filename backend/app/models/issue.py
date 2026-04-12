from sqlalchemy import Column, Integer, String, DateTime, Text, Sequence
from app.core.database import Base
from datetime import datetime

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, Sequence("issues_seq"), primary_key=True)
    user_id = Column(Integer, index=True, nullable=True)
    complaint_number = Column(String(50), unique=True)
    title = Column(String(255))
    description = Column(Text)
    location = Column(String(255))
    category = Column(String(100), default="General")
    
    # Store uploaded media names as comma-separated text for Oracle compatibility.
    media_urls = Column(Text, nullable=True)

    status = Column(String(50), default="Pending")
    assigned_department = Column(String(100), nullable=True)
    assigned_worker_id = Column(String(100), nullable=True)
    assignment_deadline = Column(DateTime, nullable=True)
    assignment_duration_label = Column(String(100), nullable=True)
    assigned_by_admin_id = Column(Integer, nullable=True)
    worker_status = Column(String(50), nullable=True)
    worker_resolution_requested_at = Column(DateTime, nullable=True)
    admin_deleted = Column(Integer, default=0, nullable=False)
    admin_deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    
