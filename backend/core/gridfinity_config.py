# backend/app/core/config/gridfinity_config.py
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class GridfinityConfig:
    # Printer settings
    PRINT_BED_WIDTH: float = 220.0
    PRINT_BED_DEPTH: float = 220.0

    # Grid settings
    GRID_SIZE: float = 42.0
    TOLERANCE: float = 0.5

    # Common dimensions
    WALL_THICKNESS: float = 1.2
    CORNER_RADIUS: float = 4.0
    CORNER_DIAMETER: float = 8.0
    BASE_HEIGHT: float = 5.0
    MIN_UNIT_SIZE: float = 15.0

    # Bin specific settings
    KNOB_HEIGHT: float = 4.75
    BIN_INSET: float = 0.25
    WALL_HEIGHT: float = 5.0
    LIP_HEIGHT: float = 4.3
    BOTTOM_THICKNESS: float = 0.8

    # File paths and storage
    BASE_OUTPUT_DIR: Path = Path(os.getenv(
        "GRIDFINITY_OUTPUT_DIR",
        "/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output"
    ))
    TEMP_DIR: Path = Path("/tmp")

    # Minimum dimensions
    MIN_WIDTH: float = 15.0
    MIN_DEPTH: float = 15.0
    MIN_HEIGHT: float = 10.0

    DIMENSION_TOLERANCE: float = 0.1 # Maximum allowed error in mm for unit dimensions
    STL_TESSELLATION_TOLERANCE: float = 0.05  # Controls STL mesh quality/resolution

    @classmethod
    def validate_dimensions(cls, width: float, depth: float, height: float = None) -> list[str]:
        """Validates dimensions against constraints"""
        errors = []
        if width < cls.MIN_WIDTH:
            errors.append(f"Width ({width}mm) must be at least {cls.MIN_WIDTH}mm")
        if depth < cls.MIN_DEPTH:
            errors.append(f"Depth ({depth}mm) must be at least {cls.MIN_DEPTH}mm")
        if height and height < cls.MIN_HEIGHT:
            errors.append(f"Height ({height}mm) must be at least {cls.MIN_HEIGHT}mm")
        if width > cls.PRINT_BED_WIDTH:
            errors.append(f"Width ({width}mm) exceeds print bed width ({cls.PRINT_BED_WIDTH}mm)")
        if depth > cls.PRINT_BED_DEPTH:
            errors.append(f"Depth ({depth}mm) exceeds print bed depth ({cls.PRINT_BED_DEPTH}mm)")
        return errors

    @classmethod
    def from_env(cls):
        """Creates instance with values from environment variables"""
        return cls(
            PRINT_BED_WIDTH=float(os.getenv("GRIDFINITY_PRINT_BED_WIDTH", cls.PRINT_BED_WIDTH)),
            PRINT_BED_DEPTH=float(os.getenv("GRIDFINITY_PRINT_BED_DEPTH", cls.PRINT_BED_DEPTH)),
            BASE_OUTPUT_DIR=Path(os.getenv("GRIDFINITY_OUTPUT_DIR", str(cls.BASE_OUTPUT_DIR))),
            # Add other env overrides as needed
        )

    @staticmethod
    def is_valid_grid_size(value) -> tuple[bool, str]:
        """
        Validates if a grid size is valid
        Returns (is_valid, error_message)
        """
        try:
            # Check if it can be converted to float
            grid_size = float(value)

            # Check if it's positive
            if grid_size <= 0:
                return False, "Grid size must be positive"

            # Check if it's greater than minimum size
            # Using 15mm as minimum since that's the minimum bin size
            if grid_size < 15:
                return False, f"Grid size ({grid_size}mm) must be at least 15mm"

            return True, ""

        except (TypeError, ValueError):
            return False, "Grid size must be a number"