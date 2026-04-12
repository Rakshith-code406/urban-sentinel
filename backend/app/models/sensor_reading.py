from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Sequence

from app.core.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, Sequence("sensor_readings_seq"), primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    device_identifier = Column(String(120), index=True, nullable=False)
    sensor_name = Column(String(100), index=True, nullable=False)
    sensor_label = Column(String(255), nullable=True)
    current_reading = Column(Float, nullable=True)
    reading_text = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
