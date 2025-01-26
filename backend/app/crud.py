# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from app.utils.password import get_password_hash
from typing import List, Optional

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_drawer(db: Session, drawer_id: int) -> Optional[models.Drawer]:
    return db.query(models.Drawer).filter(models.Drawer.id == drawer_id).first()

def get_user_drawers(db: Session, user_id: int) -> List[models.Drawer]:
    return db.query(models.Drawer).filter(models.Drawer.owner_id == user_id).all()

def create_drawer(db: Session, drawer: schemas.DrawerCreate, user_id: int) -> models.Drawer:
    db_drawer = models.Drawer(**drawer.model_dump(), owner_id=user_id)
    db.add(db_drawer)
    db.commit()
    db.refresh(db_drawer)
    return db_drawer

def create_bin(db: Session, bin: schemas.BinCreate) -> models.Bin:
    db_bin = models.Bin(**bin.model_dump())
    db.add(db_bin)
    db.commit()
    db.refresh(db_bin)
    return db_bin

def get_drawer_bins(db: Session, drawer_id: int) -> List[models.Bin]:
    return db.query(models.Bin).filter(models.Bin.drawer_id == drawer_id).all()

def delete_drawer(db: Session, drawer_id: int) -> bool:
    drawer = get_drawer(db, drawer_id)
    if drawer:
        db.delete(drawer)
        db.commit()
        return True
    return False

def update_drawer(
    db: Session,
    drawer_id: int,
    drawer_update: schemas.DrawerCreate
) -> Optional[models.Drawer]:
    db_drawer = get_drawer(db, drawer_id)
    if db_drawer:
        for key, value in drawer_update.model_dump().items():
            setattr(db_drawer, key, value)
        db.commit()
        db.refresh(db_drawer)
        return db_drawer
    return None