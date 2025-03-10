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
    
def update_user(
    db: Session,
    user_id: int,
    user_update: schemas.UserUpdate
) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Check if username is being updated and it's not already taken
        if 'username' in update_data and update_data['username'] != db_user.username:
            existing_user = get_user_by_username(db, update_data['username'])
            if existing_user:
                return None  # Username already taken
        
        # Check if email is being updated and it's not already taken
        if 'email' in update_data and update_data['email'] != db_user.email:
            existing_user = get_user_by_email(db, update_data['email'])
            if existing_user:
                return None  # Email already taken
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
            
        db.commit()
        db.refresh(db_user)
        return db_user
    return None
    
def change_user_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str
) -> bool:
    from app.utils.password import verify_password, get_password_hash
    
    db_user = get_user(db, user_id)
    if not db_user:
        return False
        
    if not verify_password(current_password, db_user.hashed_password):
        return False
        
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

def update_drawer_bins(
    db: Session, 
    drawer_id: int, 
    bins_data: List[schemas.BinUpdate]
) -> List[models.Bin]:
    """Update all bins for a drawer - removes existing bins and creates new ones"""
    
    # Delete all existing bins for this drawer
    db.query(models.Bin).filter(models.Bin.drawer_id == drawer_id).delete()
    db.flush()
    
    # Create new bins based on the input data
    updated_bins = []
    for bin_data in bins_data:
        new_bin = models.Bin(
            drawer_id=drawer_id,
            width=bin_data.width,
            depth=bin_data.depth,
            height=50.0,  # Default height
            is_standard=True,  # Default to standard
            x_position=bin_data.x_position,
            y_position=bin_data.y_position
        )
        db.add(new_bin)
        updated_bins.append(new_bin)
    
    db.commit()
    
    # Refresh all the bin objects to get their IDs
    for bin_obj in updated_bins:
        db.refresh(bin_obj)
        
    return updated_bins