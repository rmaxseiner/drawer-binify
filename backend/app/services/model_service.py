from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..utils import StorageManager, storage


class ModelService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = StorageManager()  # Initialize storage manager

    def retrieve_models(self) -> List[schemas.ModelResponse]:
        bins = self.db.query(models.Bin).all()
        baseplates = self.db.query(models.Baseplate).all()

        models_list = []

        for bin in bins:
            stl_file = next((f for f in bin.files if f.file_type == "STL"), None)
            models_list.append(schemas.ModelResponse(
                id=str(bin.id),
                type="bin",
                name=bin.name,
                date_created=bin.created_at,
                width=bin.width,
                depth=bin.depth,
                height=bin.height,
                file_path=stl_file.file_path if stl_file else None
            ))

        for baseplate in baseplates:
            stl_file = next((f for f in baseplate.files if f.file_type == "stl"), None)
            models_list.append(schemas.ModelResponse(
                id=str(baseplate.id),
                type="baseplate",
                name=baseplate.name,
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