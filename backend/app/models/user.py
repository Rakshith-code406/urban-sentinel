from sqlalchemy import Column, Integer, String, DateTime, Boolean, Sequence
from app.core.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence("users_seq"), primary_key=True)
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(155), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    registration_source = Column(String(100), nullable=True)
    registered_device_identifier = Column(String(120), nullable=True)
    registered_device_name = Column(String(255), nullable=True)
    registered_device_type = Column(String(100), nullable=True)
    registered_device_model = Column(String(255), nullable=True)
    registered_device_platform = Column(String(100), nullable=True)
    registered_device_os_version = Column(String(100), nullable=True)
    registered_app_version = Column(String(100), nullable=True)
    registered_ip_address = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    reset_code_hash = Column(String(255), nullable=True)
    reset_code_expires_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_code_hash = Column(String(255), nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
