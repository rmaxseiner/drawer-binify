import os
from pathlib import Path
from datetime import datetime, UTC


class StorageManager:
    def __init__(self, base_path: str = "generated_files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _generate_filepath(self, model_type: str, model_id: int, file_type: str) -> Path:
        # Creates path like: generated_files/bins/123/model.stl
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        model_dir = self.base_path / model_type / str(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir / f"{timestamp}.{file_type}"

    def save_file(self, model_type: str, model_id: int, file_type: str, file_content: bytes) -> str:
        filepath = self._generate_filepath(model_type, model_id, file_type)
        with open(filepath, "wb") as f:
            f.write(file_content)
        return str(filepath)

    def delete_model_files(self, model_type: str, model_id: int):
        model_dir = self.base_path / model_type / str(model_id)
        if model_dir.exists():
            for file in model_dir.glob("*"):
                file.unlink()
            model_dir.rmdir()