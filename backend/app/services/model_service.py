from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..utils import StorageManager, storage
import logging

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageManager()  # Initialize storage manager

    def retrieve_models(self) -> List[schemas.ModelResponse]:
        logger.info("Retrieving all models")
        bins = self.db.query(models.Bin).all()
        baseplates = self.db.query(models.Baseplate).all()

        models_list = []
        logger.info(f"Found {len(bins)} bins and {len(baseplates)} baseplates")

        # Process bins
        for bin in bins:
            # Check for STL files with both uppercase and lowercase
            stl_file = next((f for f in bin.files if f.file_type.upper() == "STL"), None)
            
            if not stl_file:
                logger.warning(f"Bin {bin.id} ({bin.name}) has no STL file")
                # Log all available files to help diagnose the issue
                if bin.files:
                    logger.info(f"Available files for bin {bin.id}: {[f.file_type for f in bin.files]}")
            else:
                logger.debug(f"Bin {bin.id} has STL file: {stl_file.file_path}")
                
            models_list.append(schemas.ModelResponse(
                id=str(bin.id),
                type="bin",
                name=bin.name or f"Bin_{bin.id}",  # Provide a fallback name if None
                date_created=bin.created_at,
                width=bin.width,
                depth=bin.depth,
                height=bin.height,
                file_path=stl_file.file_path if stl_file else None
            ))

        # Process baseplates
        for baseplate in baseplates:
            # Check for STL files with both uppercase and lowercase
            stl_file = next((f for f in baseplate.files if f.file_type.upper() == "STL"), None)
            
            if not stl_file:
                logger.warning(f"Baseplate {baseplate.id} ({baseplate.name}) has no STL file")
                # Log all available files to help diagnose the issue
                if baseplate.files:
                    logger.info(f"Available files for baseplate {baseplate.id}: {[f.file_type for f in baseplate.files]}")
            else:
                logger.debug(f"Baseplate {baseplate.id} has STL file: {stl_file.file_path}")
                
            models_list.append(schemas.ModelResponse(
                id=str(baseplate.id),
                type="baseplate",
                name=baseplate.name or f"Baseplate_{baseplate.id}",  # Provide a fallback name if None
                date_created=baseplate.created_at,
                width=baseplate.width,
                depth=baseplate.depth,
                height=0,  # Baseplates don't have height
                file_path=stl_file.file_path if stl_file else None
            ))

        return models_list

    def delete_model(self, model_id: str) -> bool:
        # Try to find and delete bin
        bin = self.db.query(models.Bin).filter(models.Bin.id == model_id).first()
        if bin:
            self.storage.delete_model_files("bins", bin.id)  # Use self.storage instead of storage
            self.db.delete(bin)
            self.db.commit()
            return True

        # Try to find and delete baseplate
        baseplate = self.db.query(models.Baseplate).filter(models.Baseplate.id == model_id).first()
        if baseplate:
            self.storage.delete_model_files("baseplates", baseplate.id)  # Use self.storage instead of storage
            self.db.delete(baseplate)
            self.db.commit()
            return True

        return False