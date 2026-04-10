from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    incidents = relationship("Incident", back_populates="owner")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    location = Column(String(256), default="unknown", nullable=False)
    severity = Column(String(16), nullable=False)
    vehicles = Column(Integer, nullable=False, default=0)
    accident = Column(Boolean, default=False, nullable=False)
    annotated_frame = Column(LargeBinary, nullable=True)
    snapshot_path = Column(String(512), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    violations = relationship("Violation", back_populates="incident", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="incidents")

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    violation_type = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    incident = relationship("Incident", back_populates="violations")
