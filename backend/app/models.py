from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    drawers = relationship("Drawer", back_populates="owner")

class Drawer(Base):
    __tablename__ = "drawers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="drawers")
    bins = relationship("Bin", back_populates="drawer")

class Bin(Base):
    __tablename__ = "bins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    is_standard = Column(Boolean, default=True)
    drawer_id = Column(Integer, ForeignKey("drawers.id"))
    drawer = relationship("Drawer", back_populates="bins")
    created_at = Column(DateTime, default=datetime.utcnow)
    files = relationship("GeneratedFile", back_populates="bin")

class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True, index=True)
    file_type = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=True)
    baseplate_id = Column(Integer, ForeignKey("baseplates.id"), nullable=True)
    bin = relationship("Bin", back_populates="files")
    baseplate = relationship("Baseplate", back_populates="files")


class Baseplate(Base):
    __tablename__ = "baseplates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    width = Column(Float)
    depth = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    files = relationship("GeneratedFile", back_populates="baseplate")