from fastapi import HTTPException
from pathlib import Path
import shutil
import logging
from typing import Tuple, Optional, List, Dict, Any, Coroutine
from sqlalchemy.orm import Session

from app.models import Bin, GeneratedFile, Model
from app import crud
from core.gridfinity_custom_bin import GridfinityCustomBin
from utils.freecad_setup import setup_freecad
from core.gridfinity_config import GridfinityConfig
logger = logging.getLogger(__name__)


class BinGenerationService:
    def __init__(self, db: Session, base_output_dir: Path):
        self.db = db
        self.config = GridfinityConfig.from_env()
        if base_output_dir:
            self.config.BASE_OUTPUT_DIR = Path(base_output_dir)
        self.config.BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.FreeCAD = setup_freecad()

    async def generate_bin(self, name: str, width: float, depth: float, height: float, drawer_id: int) -> Tuple[
        Bin, List[GeneratedFile]]| None:
        """
        Generate a bin model, creating both the Model record and a Bin record in the database.
        Use this method when you need a standalone bin not associated with a drawer.
        """
        try:
            # Check if a model with these characteristics exists
            model_metadata = {
                "width": width,
                "depth": depth,
                "height": height
            }
            
            logger.info(f"Checking for existing model with metadata: {model_metadata}")
            existing_model = crud.get_model_by_metadata(self.db, "bin", model_metadata)
            
            if existing_model:
                logger.info(f"Found existing model with ID {existing_model.id} - will reuse")
                
                try:
                    # Create bin record linked to existing model
                    bin_record = Bin(
                        name=name,
                        width=width,
                        depth=depth,
                        height=height,
                        model_id=existing_model.id,
                        drawer_id=drawer_id
                    )
                    self.db.add(bin_record)
                    self.db.flush()  # Get ID without committing
                    
                    logger.info(f"Created bin {bin_record.id} linked to model {existing_model.id}")
                    
                    # Get the generated files associated with the model
                    model_files = self.db.query(GeneratedFile).filter(GeneratedFile.model_id == existing_model.id).all()
                    logger.info(f"Found {len(model_files)} existing files for model {existing_model.id}")
                    
                    # No need to create duplicate file records - the bin can access files through its model
                    # We can return the model's files directly since they're already in the database
                    
                    # Now commit all the changes
                    self.db.commit()
                    self.db.refresh(bin_record)
                    
                    logger.info(f"Successfully reused model {existing_model.id} for bin {bin_record.id}")
                    return bin_record, model_files
                    
                except Exception as e:
                    # If anything fails during model reuse, log, roll back, and raise the exception
                    error_msg = f"Failed to reuse model {existing_model.id}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self.db.rollback()
                    # Don't fall through - propagate the error to create a 500 response
                    raise HTTPException(status_code=500, detail=error_msg)
            else:
                logger.info("No existing model found, will create a new one")
            
            # Either no model exists or reuse failed, so create a new model and bin
            
            # Start a new transaction
            new_model = Model(
                type="bin",
                model_metadata=model_metadata
            )
            self.db.add(new_model)
            self.db.flush()  # Get model ID
            logger.info(f"Created new model with ID {new_model.id}")
            
            # Create bin record linked to the new model
            bin_record = Bin(
                name=name,
                width=width,
                depth=depth,
                height=height,
                model_id=new_model.id,
                drawer_id=drawer_id
            )
            self.db.add(bin_record)
            self.db.flush()  # Get bin ID
            logger.info(f"Created bin with ID {bin_record.id} linked to model {new_model.id}")

            # Generate model files
            generated_files = await self._generate_model_files(new_model.id, width, depth, height)
            
            # Commit all changes
            self.db.commit()
            logger.info("Committed all database changes")
            
            # Refresh records
            for file in generated_files:
                self.db.refresh(file)
            self.db.refresh(bin_record)
            
            logger.info(f"Bin generation completed successfully for bin {bin_record.id}")
            return bin_record, generated_files
        
        except Exception as e:
            logger.error("Bin generation failed", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate bin: {str(e)}"
            )
            
    async def get_or_create_bin_model(self, width: float, depth: float, height: float, drawer_id: int) -> Model:
        """
        Get or create a bin model without creating a Bin record.
        Use this method when you already have or will create the Bin record separately,
        such as in drawer generation.
        """
        try:
            # Check if a model with these characteristics exists
            model_metadata = {
                "width": width,
                "depth": depth,
                "height": height
            }
            
            logger.info(f"Checking for existing model with metadata: {model_metadata}")
            existing_model = crud.get_model_by_metadata(self.db, "bin", model_metadata)
            
            if existing_model:
                if isinstance(existing_model, list):
                    if len(existing_model) > 1:
                        logger.error(f"Found multiple existing model that match the meta data: {model_metadata}")
                        for model in existing_model:
                            logger.info(f"Found existing model with ID {model.id}")
                        raise
                    else:
                        return existing_model[0]
                return existing_model

            logger.info("No existing model found, will create a new one")
            
            # Create a new model record
            new_model = Model(
                type="bin",
                model_metadata=model_metadata
            )
            self.db.add(new_model)
            self.db.flush()  # Get model ID
            logger.info(f"Created new model with ID {new_model.id}")
            
            # Generate the model files
            await self._generate_model_files(new_model.id, width, depth, height)
            
            # No need to commit as this will be handled by the caller
            logger.info(f"Model generation completed for model {new_model.id}")

            return new_model
            
        except Exception as e:
            logger.error("Bin model generation failed", exc_info=True)
            # Don't roll back - let the caller handle transaction management
            raise
            
    async def _generate_model_files(self, model_id: int, width: float, depth: float, height: float) -> list[GeneratedFile] | None:
        """
        Helper method to generate model files for a given model ID.
        This handles the actual 3D model generation and file storage.
        """
        # Setup directories
        temp_dir = Path(f"/tmp/bin_{model_id}")
        temp_dir.mkdir(exist_ok=True)
        logger.info(f"Created temporary directory: {temp_dir}")

        # Initialize outside try block to ensure it's always defined
        generated_files = []
        
        try:
            # Generate files
            logger.info(f"Generating 3D model files for bin (width={width}, depth={depth}, height={height})")
            bin_maker = GridfinityCustomBin()
            doc, fcstd_path, stl_path = bin_maker.create_bin(
                width, depth, height, str(temp_dir)
            )
            logger.info(f"3D model generation completed: FCStd={fcstd_path}, STL={stl_path}")

            # Create permanent storage location using model_id
            relative_dir = f"bin_{model_id}"
            permanent_dir = self.config.BASE_OUTPUT_DIR / relative_dir
            permanent_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created permanent directory: {permanent_dir}")

            # Move files to permanent location and create records
            for temp_path, file_type in [(Path(fcstd_path), "FCStd"), (Path(stl_path), "STL")]:
                if not temp_path.exists():
                    error_msg = f"Failed to generate {file_type} file at {temp_path}"
                    logger.error(error_msg)
                    raise HTTPException(
                        status_code=500,
                        detail=error_msg
                    )

                relative_path = f"{relative_dir}/{temp_path.name}"
                permanent_path = permanent_dir / temp_path.name
                shutil.copy2(temp_path, permanent_path)
                logger.info(f"Copied {file_type} file to permanent location: {permanent_path}")

                #not sure why we are creating the files here
                # Create file record associated with the model only
                file_record = GeneratedFile(
                    file_type=file_type,
                    file_path=relative_path,  # Store relative path
                    model_id=model_id
                    # No bin_id - files should be associated with the model, not individual bins
                )
                self.db.add(file_record)
                generated_files.append(file_record)
                logger.info(f"Created file record for {file_type}")

            # The files have been created, we'll return them at the end of the function
            
        except Exception as e:
            logger.error(f"Error generating model files: {str(e)}", exc_info=True)
            # We don't rollback here - let the caller handle transaction management
            raise
            
        finally:
            # Always clean up the temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info(f"Removed temporary directory {temp_dir}")
        
        # This return is outside the try-except-finally blocks
        # If an exception occurs, this line will never be reached
        # If no exception occurs, this will return the generated files
        return generated_files