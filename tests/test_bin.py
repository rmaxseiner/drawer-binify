#!/usr/bin/env python3
import os
import sys
import pytest
from pathlib import Path
import math
import logging
import shutil

inset = 0.25

# Set up logging
def setup_logging():
    """Configure logging for tests"""
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create console handler and set level to DEBUG
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Create file handler and set level to DEBUG
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "test_bin.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure specific loggers
    freecad_logger = logging.getLogger('freecad_utils')
    freecad_logger.setLevel(logging.DEBUG)

    return root_logger


# Create logger
logger = setup_logging()

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add FreeCAD paths
freecad_paths = [
    '/usr/lib/freecad-python3/lib',
    '/usr/lib/freecad/lib',
    '/usr/lib/freecad/Mod',
    '/usr/share/freecad/Mod',
    '/usr/lib/python3/dist-packages'
]

for path in freecad_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# Set LD_LIBRARY_PATH
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/freecad-python3/lib'

# Define a permanent output directory relative to the project root
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "test_outputs"


def ensure_output_directory():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured at: {OUTPUT_DIR.absolute()}")


@pytest.fixture(scope="session", autouse=True)
def setup_output_directory():
    """Fixture to set up output directory before any tests"""
    ensure_output_directory()
    yield


def validate_freecad_file(file_path, width, depth, height):
    """Validate the FreeCAD file contents"""
    try:
        import FreeCAD
        doc = FreeCAD.openDocument(str(file_path))

        # Verify document contains objects
        assert len(doc.Objects) > 0, "FreeCAD document is empty"

        # Get overall bounds
        bbox = None
        for obj in doc.Objects:
            if hasattr(obj, 'Shape'):
                if bbox is None:
                    bbox = obj.Shape.BoundBox
                else:
                    bbox.add(obj.Shape.BoundBox)

        # Verify dimensions with tolerance
        tolerance = 0.1  # mm
        # assert abs(bbox.XLength + 2*inset - width) <= tolerance, \
        #     f"Width mismatch: expected {width}, got {bbox.XLength}"
        # assert abs(bbox.YLength + 2*inset - depth) <= tolerance, \
        #     f"Depth mismatch: expected {depth}, got {bbox.YLength}"
        # assert abs(bbox.ZLength - height) <= tolerance, \
        #     f"Height mismatch: expected {height}, got {bbox.ZLength}"

        FreeCAD.closeDocument(doc.Name)
    except Exception as e:
        logger.error(f"Error validating FreeCAD file: {e}")
        raise


def validate_stl_file(file_path):
    """Validate the STL file contents"""
    try:
        # Read STL file
        with open(file_path, 'rb') as f:
            # Verify file is not empty
            assert f.read(1), "STL file is empty"

        # Check file size is reasonable
        file_size = os.path.getsize(file_path)
#        assert file_size > 1000, f"STL file suspiciously small: {file_size} bytes"

    except Exception as e:
        logger.error(f"Error validating STL file: {e}")
        raise


@pytest.fixture(autouse=True, scope="session")
def cleanup_logs():
    log_file = Path("logs/test_bin.log")
    if log_file.exists():
        log_file.unlink()
    yield


@pytest.mark.parametrize("width,depth,height, description", [
    (42.0, 42.0, 42, "Standard 1x1 gridfinity")
    # (84.0, 42.0, 42,"2x1 gridfinity"),
    # (30.0, 42.0, 35,  "Custom width"),
    # (42.0, 30.0,76,  "Custom depth"),
    # (60.0, 60.0, 66, "Custom square"),
])
def test_bin(width, depth, height, description, tmp_path):
    """Test bin generation with comprehensive validation"""
    logger.info(f"\nTesting bin: {width}x{depth}mm ({description})")
    import FreeCAD
    try:
        from src.core.gridfinity_custom_bin import GridfinityCustomBin
        # Log test parameters
        logger.debug(f"Test parameters:")
        logger.debug(f"Width: {width}mm")
        logger.debug(f"Depth: {depth}mm")
        logger.debug(f"Description: {description}")
        logger.debug(f"Temporary path: {tmp_path}")

        # Create directories
        temp_output_dir = tmp_path / f"bin_{width}x{depth}"
        temp_output_dir.mkdir(exist_ok=True)
        logger.debug(f"Created temp directory: {temp_output_dir}")

        permanent_output_dir = OUTPUT_DIR / f"bin_{width}x{depth}"
        permanent_output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created permanent directory: {permanent_output_dir}")

        # Create bin
        logger.info("Creating bin instance...")
        bin_maker = GridfinityCustomBin()

        # Generate bin and files
        logger.info("Generating bin files...")
        doc, fcstd_path, stl_path = bin_maker.create_bin(width, depth, height, str(temp_output_dir))

        # Verify files exist in temp directory
        temp_fcstd_path = Path(fcstd_path)
        temp_stl_path = Path(stl_path)

        logger.debug(f"Checking temp files:")
        logger.debug(f"FCStd exists: {temp_fcstd_path.exists()}")
        logger.debug(f"STL exists: {temp_stl_path.exists()}")

        assert temp_fcstd_path.exists(), f"FreeCAD file not found at {temp_fcstd_path}"
        assert temp_stl_path.exists(), f"STL file not found at {temp_stl_path}"

        # Validate file contents
        validate_freecad_file(temp_fcstd_path, width, depth,
                              5.8 )
        validate_freecad_file(temp_fcstd_path, width, depth, bin_maker.bottom_thickness + bin_maker.wall_height+bin_maker.lip_height)
        validate_stl_file(temp_stl_path)

        # Copy files to permanent location
        permanent_fcstd_path = permanent_output_dir / temp_fcstd_path.name
        permanent_stl_path = permanent_output_dir / temp_stl_path.name

        logger.info("Copying files to permanent location...")
        shutil.copy2(temp_fcstd_path, permanent_fcstd_path)
        shutil.copy2(temp_stl_path, permanent_stl_path)

        # Verify permanent files exist
        logger.debug(f"Verifying permanent files:")
        logger.debug(f"FCStd exists: {permanent_fcstd_path.exists()}")
        logger.debug(f"STL exists: {permanent_stl_path.exists()}")

        assert permanent_fcstd_path.exists(), f"Failed to copy FCStd to {permanent_fcstd_path}"
        assert permanent_stl_path.exists(), f"Failed to copy STL to {permanent_stl_path}"

        # Verify wall thickness
        doc = FreeCAD.openDocument(str(permanent_fcstd_path))
        tolerance = 0.01  # mm

        for obj in doc.Objects:
            if obj.Name == "Wall_Left" or obj.Name == "Wall_Right" or obj.Name == "Wall_Bottom" or obj.Name == "Wall_Top" :
                bbox = obj.Shape.BoundBox
                # For vertical walls (Left/Right)
                if "Left" in obj.Name or "Right" in obj.Name:
                    thickness = bbox.XLength
                # For horizontal walls (Top/Bottom)
                else:
                    thickness = bbox.YLength

                assert abs(thickness - bin_maker.wall_thickness) <= tolerance, \
                    f"Wall thickness incorrect for {obj.Name}"

        FreeCAD.closeDocument(doc.Name)

        logger.info(f"All files successfully saved to: {permanent_output_dir}")

    except Exception as e:
        logger.error("Test failed with exception", exc_info=True)
        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])