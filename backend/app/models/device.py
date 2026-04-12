from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Sequence

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, Sequence("devices_seq"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    device_identifier = Column(String(120), unique=True, nullable=False)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(100), nullable=True)
    device_model = Column(String(255), nullable=True)
    platform = Column(String(100), nullable=True)
    os_version = Column(String(100), nullable=True)
    firmware_version = Column(String(100), nullable=True)
    app_version = Column(String(100), nullable=True)
    login_email = Column(String(255), nullable=True)
    login_phone = Column(String(20), nullable=True)
    ip_address = Column(String(64), nullable=True)
    mac_address = Column(String(64), nullable=True)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
