from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
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
    settings = relationship("UserSettings", back_populates="user", uselist=False)


class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    theme = Column(String, default="light")
    default_drawer_height = Column(Float, default=40.0)
    default_bin_height = Column(Float, default=25.0)
    notification_preferences = Column(JSON, default={})
    user = relationship("User", back_populates="settings")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)  # 'bin' or 'baseplate'
    model_metadata = Column(JSON)  # Store characteristics like {width, depth, height}
    created_at = Column(DateTime, default=datetime.utcnow)
    files = relationship("GeneratedFile", back_populates="model")
    bins = relationship("Bin", back_populates="model")
    baseplates = relationship("Baseplate", back_populates="model")


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
    baseplates = relationship("Baseplate", back_populates="drawer")


class Bin(Base):
    __tablename__ = "bins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    is_standard = Column(Boolean, default=True)
    drawer_id = Column(Integer, ForeignKey("drawers.id"))
    drawer = relationship("Drawer", back_populates="bins")
    created_at = Column(DateTime, default=datetime.utcnow)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    model = relationship("Model", back_populates="bins")
    # Position within drawer
    x_position = Column(Float, nullable=True)
    y_position = Column(Float, nullable=True)


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True, index=True)
    file_type = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)

    # Only keep the model relationship
    model = relationship("Model", back_populates="files")


class Baseplate(Base):
    __tablename__ = "baseplates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    width = Column(Float)
    depth = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    drawer_id = Column(Integer, ForeignKey("drawers.id"), nullable=True)
    model = relationship("Model", back_populates="baseplates")
    drawer = relationship("Drawer", back_populates="baseplates")