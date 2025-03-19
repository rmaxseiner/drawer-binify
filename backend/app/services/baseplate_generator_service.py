import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException
from core.gridfinity_baseplate import GridfinityBaseplate
from utils.freecad_setup import setup_freecad
from ..models import Baseplate, GeneratedFile, Model
from app import crud
import logging
from core.gridfinity_config import GridfinityConfig
from typing import Tuple, List
logger = logging.getLogger(__name__)

class BaseplateService:
    def __init__(self, db: Session, base_output_dir: Path = None):
        self.db = db
        self.config = GridfinityConfig.from_env()
        if base_output_dir:
            self.config.BASE_OUTPUT_DIR = Path(base_output_dir)
        self.config.BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.FreeCAD = setup_freecad()

    async def generate_baseplate(self, name: str, drawer_id: int, width: float, depth: float) -> Tuple[
        Baseplate, List[GeneratedFile]]:
        try:
            # Check if a model with these characteristics exists or create a new one
            model = await self.get_or_create_baseplate_model(width=width, depth=depth)

            # Create baseplate record linked to the model
            baseplate_record = Baseplate(
                name=name,
                width=width,
                depth=depth,
                drawer_id=drawer_id,
                model_id=model.id
            )
            self.db.add(baseplate_record)
            self.db.flush()

            logger.info(f"Created baseplate {baseplate_record.id} linked to model {model.id}")

            # Get the generated files associated with the model
            model_files = self.db.query(GeneratedFile).filter(GeneratedFile.model_id == model.id).all()
            logger.info(f"Found {len(model_files)} existing files for model {model.id}")

            # Commit all changes
            self.db.commit()
            self.db.refresh(baseplate_record)

            logger.info(f"Baseplate generation completed successfully for baseplate {baseplate_record.id}")
            return baseplate_record, model_files

        except Exception as e:
            logger.error("Baseplate generation failed", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate baseplate: {str(e)}"
            )


    async def get_or_create_baseplate_model(self, width: float, depth: float) -> Model:
        """
        Get or create a baseplate model without creating a Baseplate record.
        Use this method when you already have or will create the Baseplate record separately.
        """
        try:
            # Check if a model with these characteristics exists
            model_metadata = {
                "width": width,
                "depth": depth
            }

            logger.info(f"Checking for existing model with metadata: {model_metadata}")
            existing_model = crud.get_model_by_metadata(self.db, "baseplate", model_metadata)

            if existing_model:
                if isinstance(existing_model, list):
                    if len(existing_model) > 1:
                        logger.error(f"Found multiple existing models that match the metadata: {model_metadata}")
                        for model in existing_model:
                            logger.info(f"Found existing model with ID {model.id}")
                        raise ValueError("Multiple matching models found")
                    else:
                        return existing_model[0]
                return existing_model

            logger.info("No existing model found, will create a new one")

            # Create a new model record
            new_model = Model(
                type="baseplate",
                model_metadata=model_metadata
            )
            self.db.add(new_model)
            self.db.flush()  # Get model ID
            logger.info(f"Created new model with ID {new_model.id}")

            # Setup directories using relative paths
            temp_dir = Path(f"/tmp/baseplate_model_{new_model.id}")
            temp_dir.mkdir(exist_ok=True)

            relative_dir = f"baseplate_{new_model.id}"
            permanent_dir = self.config.BASE_OUTPUT_DIR / relative_dir
            permanent_dir.mkdir(parents=True, exist_ok=True)

            # Generate baseplate sections
            baseplate_maker = GridfinityBaseplate(drawer_depth=depth, drawer_width=width)
            logger.info(f"Starting baseplate generation for {width}x{depth}mm")
            sections = baseplate_maker.generate_baseplate(str(temp_dir))
            logger.info(f"Generated {len(sections)} baseplate sections")

            for section_name, dimensions in sections:
                for file_type in ["FCStd", "stl"]:
                    temp_path = temp_dir / f"{section_name}.{file_type}"
                    if not temp_path.exists():
                        error_msg = f"Failed to generate {file_type} file for section {section_name}"
                        logger.error(error_msg)
                        logger.error(f"Expected file not found: {temp_path}")
                        raise HTTPException(status_code=500, detail=error_msg)

                    relative_path = f"{relative_dir}/{section_name}.{file_type}"
                    permanent_path = permanent_dir / f"{section_name}.{file_type}"

                    try:
                        shutil.copy2(temp_path, permanent_path)
                        logger.debug(f"Copied {file_type} file to: {permanent_path}")
                    except Exception as e:
                        error_msg = f"Failed to copy {file_type} file for section {section_name}"
                        logger.error(error_msg, exc_info=True)
                        raise HTTPException(status_code=500, detail=error_msg)

                    file_record = GeneratedFile(
                        file_type=file_type,
                        file_path=relative_path,  # Store relative path
                        model_id=new_model.id
                    )
                    self.db.add(file_record)
                    logger.debug(f"Created database record for {file_type} file")

            # Cleanup temporary directory
            shutil.rmtree(temp_dir)

            # No need to commit as this will be handled by the caller
            logger.info(f"Model generation completed for model {new_model.id}")

            return new_model

        except Exception as e:
            logger.error("Baseplate model generation failed", exc_info=True)
            # Don't roll back - let the caller handle transaction management
            raise