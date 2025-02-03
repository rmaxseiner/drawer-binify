from fastapi import HTTPException
from pathlib import Path
import shutil
import logging
from typing import Tuple
from sqlalchemy.orm import Session

from  app.models import Bin, GeneratedFile
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

    async def generate_bin(self, name: str, width: float, depth: float, height: float) -> Tuple[
        Bin, list[GeneratedFile]]:

        try:
            # Create bin record
            bin_record = Bin(
                name=name,
                width=width,
                depth=depth,
                height=height
            )
            self.db.add(bin_record)
            self.db.flush()  # Get ID without committing

            # Setup directories
            temp_dir = Path(f"/tmp/bin_{bin_record.id}")
            temp_dir.mkdir(exist_ok=True)

            # Generate files
            bin_maker = GridfinityCustomBin()
            doc, fcstd_path, stl_path = bin_maker.create_bin(
                width, depth, height, str(temp_dir)
            )

            relative_dir = f"bin_{bin_record.id}"
            permanent_dir = self.config.BASE_OUTPUT_DIR / relative_dir
            permanent_dir.mkdir(parents=True, exist_ok=True)

            generated_files = []
            for temp_path, file_type in [(Path(fcstd_path), "FCStd"), (Path(stl_path), "STL")]:
                if not temp_path.exists():
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to generate {file_type} file"
                    )

                relative_path = f"{relative_dir}/{temp_path.name}"
                permanent_path = permanent_dir / temp_path.name
                shutil.copy2(temp_path, permanent_path)

                file_record = GeneratedFile(
                    file_type=file_type,
                    file_path=relative_path,  # Store relative path
                    bin_id=bin_record.id
                )
                self.db.add(file_record)
                generated_files.append(file_record)

            # Cleanup and commit
            shutil.rmtree(temp_dir)
            self.db.commit()
            for file in generated_files:
                self.db.refresh(file)
            return bin_record, generated_files

        except Exception as e:
            logger.error("Bin generation failed", exc_info=True)
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate bin: {str(e)}"
            )