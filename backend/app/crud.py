# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from app.utils.password import get_password_hash
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

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


def get_model_by_metadata(db: Session, model_type: str, metadata: Dict[str, Any]) -> Optional[models.Model]:
    """
    Find a model with matching type and metadata.

    Returns:
        - A matching Model if found
        - None if no matching model exists

    Raises:
        - DatabaseError if a database error occurs
        - ValueError if invalid parameters are provided
    """
    logger.info(f"Searching for {model_type} model with metadata: {metadata}")

    # Input validation
    if not model_type or not metadata:
        raise ValueError("Model type and metadata are required")

    # Query models with same type
    models_query = db.query(models.Model).filter(models.Model.type == model_type)

    try:
        # Handle bin models with specific dimension matching
        if model_type == "bin" and all(k in metadata for k in ["width", "depth", "height"]):
            # Get all models of this type
            all_models = models_query.all()

            # Extract dimensions we're looking for
            width = metadata["width"]
            depth = metadata["depth"]
            height = metadata["height"]

            logger.info(f"Searching for bin with dimensions: width={width}, depth={depth}, height={height}")

            # Find matching models
            matching_models = []
            for model in all_models:
                model_metadata = model.model_metadata
                if (model_metadata.get("width") == width and
                        model_metadata.get("depth") == depth and
                        model_metadata.get("height") == height):
                    matching_models.append(model)
                    logger.info(f"Found matching bin model: id={model.id}")

            if matching_models:
                return matching_models[0]

        # Handle baseplate models with specific dimension matching
        elif model_type == "baseplate" and all(k in metadata for k in ["width", "depth"]):
            # Get all models of this type
            all_models = models_query.all()

            # Extract dimensions we're looking for
            width = metadata["width"]
            depth = metadata["depth"]

            logger.info(f"Searching for baseplate with dimensions: width={width}, depth={depth}")

            # Find matching models
            matching_models = []
            for model in all_models:
                model_metadata = model.model_metadata
                if (model_metadata.get("width") == width and
                        model_metadata.get("depth") == depth):
                    matching_models.append(model)
                    logger.info(f"Found matching baseplate model: id={model.id}")

            if matching_models:
                return matching_models[0]

        # For other model types, try direct metadata comparison
        else:
            for model in models_query.all():
                if model.model_metadata == metadata:
                    return model

        # No matching model found
        logger.info(f"No matching {model_type} model found")
        return None

    except Exception as e:
        # This catch should only handle unexpected errors, not normal "not found" cases
        logger.error(f"Error searching for {model_type} model: {e}", exc_info=True)
        # Re-raise the exception rather than hiding it
        raise

    except Exception as e:
        # Log the error but don't fail - just return None to create a new model
        logger.error(f"Error in get_model_by_metadata: {str(e)}")
        return None

def create_model(db: Session, model: schemas.ModelCreate) -> models.Model:
    """Create a new model"""
    db_model = models.Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_or_create_model(db: Session, model_type: str, metadata: Dict[str, Any]) -> models.Model:
    """Get an existing model or create a new one if it doesn't exist"""
    # Check if model already exists
    existing_model = get_model_by_metadata(db, model_type, metadata)
    if existing_model:
        return existing_model
    
    # If not, create a new model
    model_create = schemas.ModelCreate(type=model_type, model_metadata=metadata)
    return create_model(db, model_create)

def create_bin(db: Session, bin: schemas.BinCreate) -> models.Bin:
    # Create the bin
    bin_data = bin.model_dump()
    
    # If model_id is provided, use it; otherwise, we'll set it later
    model_id = bin_data.pop('model_id', None)
    
    db_bin = models.Bin(**bin_data, model_id=model_id)
    db.add(db_bin)
    db.commit()
    db.refresh(db_bin)
    return db_bin

def update_bin_model(db: Session, bin_id: int, model_id: int) -> Optional[models.Bin]:
    """Update a bin's model reference"""
    db_bin = db.query(models.Bin).filter(models.Bin.id == bin_id).first()
    if db_bin:
        db_bin.model_id = model_id
        db.commit()
        db.refresh(db_bin)
        return db_bin
    return None

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

def get_user_settings(db: Session, user_id: int) -> Optional[models.UserSettings]:
    """Get user settings for a specific user"""
    return db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()

def create_user_settings(db: Session, user_id: int, settings: schemas.UserSettingsCreate) -> models.UserSettings:
    """Create new user settings"""
    db_settings = models.UserSettings(**settings.model_dump(), user_id=user_id)
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def update_user_settings(db: Session, user_id: int, settings: schemas.UserSettingsUpdate) -> Optional[models.UserSettings]:
    """Update user settings"""
    db_settings = get_user_settings(db, user_id)
    
    if not db_settings:
        # If settings don't exist yet, create them
        return create_user_settings(db, user_id, settings)
    
    # Update existing settings
    for key, value in settings.model_dump(exclude_unset=True).items():
        setattr(db_settings, key, value)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings