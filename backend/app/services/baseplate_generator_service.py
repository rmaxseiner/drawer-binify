import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException
from core.gridfinity_baseplate import GridfinityBaseplate
from utils.freecad_setup import setup_freecad
from ..models import Baseplate, GeneratedFile
import logging
from core.gridfinity_config import GridfinityConfig
logger = logging.getLogger(__name__)

class BaseplateService:
    def __init__(self, db: Session, base_output_dir: Path = None):
        self.db = db
        self.config = GridfinityConfig.from_env()
        if base_output_dir:
            self.config.BASE_OUTPUT_DIR = Path(base_output_dir)
        self.config.BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.FreeCAD = setup_freecad()

    async def generate_baseplate(self, name: str, width: float, depth: float):
        try:
            # Create baseplate record
            baseplate_record = Baseplate(
                name=name,
                width=width,
                depth=depth
            )
            self.db.add(baseplate_record)
            self.db.flush()

            # Setup directories using relative paths
            temp_dir = Path(f"/tmp/baseplate_{baseplate_record.id}")
            temp_dir.mkdir(exist_ok=True)

            relative_dir = f"baseplate_{baseplate_record.id}"
            permanent_dir = self.config.BASE_OUTPUT_DIR / relative_dir
            permanent_dir.mkdir(parents=True, exist_ok=True)

            # Generate baseplate sections
            baseplate_maker = GridfinityBaseplate(drawer_depth=depth, drawer_width=width)
            logger.info(f"Starting baseplate generation for {width}x{depth}mm")
            sections = baseplate_maker.generate_baseplate(str(temp_dir))
            logger.info(f"Generated {len(sections)} baseplate sections")

            generated_files = []
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
                        baseplate_id=baseplate_record.id
                    )
                    self.db.add(file_record)
                    generated_files.append(file_record)
                    logger.debug(f"Created database record for {file_type} file")

            # Cleanup and commit
            shutil.rmtree(temp_dir)
            self.db.commit()

            return baseplate_record, generated_files

        except Exception as e:
            logger.error("Baseplate generation failed", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate baseplate: {str(e)}"
            )


