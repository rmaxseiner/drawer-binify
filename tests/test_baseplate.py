#!/usr/bin/env python3
import os
import sys
import pytest
from pathlib import Path
import math
import logging
import shutil

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
    file_handler = logging.FileHandler(log_dir / "test_baseplate.log")
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


# @pytest.mark.parametrize("width,depth,description", [
#     (42, 42, "Basic 1x1"),
#     (42, 84, "1x2 rectangle"),
#     (84, 84, "2x2 square"),
#     (42, 64, "1x1.5 non-standard"),
#     (64, 42, "1.5x1 non-standard"),
#     (64, 64, "1.5x1.5 non-standard"),
#     (48,48, "slightly larger than 1x1 with solid fill"),
#     (250, 250, "Large multi-section")
# ])
# def test_baseplate(width, depth, description, tmp_path):
#     """Test baseplate generation with comprehensive validation"""
#     logger.info(f"\nTesting baseplate: {width}x{depth}mm ({description})")
#
#     try:
#         from src.core.gridfinity_baseplate import GridfinityBaseplate
#
#         # Log test parameters
#         logger.debug(f"Test parameters:")
#         logger.debug(f"Width: {width}mm")
#         logger.debug(f"Depth: {depth}mm")
#         logger.debug(f"Description: {description}")
#         logger.debug(f"Temporary path: {tmp_path}")
#
#         # Create directories
#         temp_output_dir = tmp_path / f"baseplate_{width}x{depth}"
#         temp_output_dir.mkdir(exist_ok=True)
#         logger.debug(f"Created temp directory: {temp_output_dir}")
#
#         permanent_output_dir = OUTPUT_DIR / f"baseplate_{width}x{depth}"
#         permanent_output_dir.mkdir(parents=True, exist_ok=True)
#         logger.debug(f"Created permanent directory: {permanent_output_dir}")
#
#         # Create baseplate
#         logger.info("Creating baseplate instance...")
#         baseplate = GridfinityBaseplate(width, depth, 220, 220)
#
#         # Generate units
#         logger.info("Generating grid units...")
#         units = baseplate.grid_divider()
#         logger.debug(f"Generated {len(units)} units")
#
#         # Get printable objects
#         logger.info("Creating printable objects...")
#         printable_objects = baseplate.printable_object_selector(units)
#         logger.debug(f"Created {len(printable_objects)} printable objects")
#
#         # Generate files
#         logger.info("Generating baseplate files...")
#         created_files = baseplate.generate_baseplate(str(temp_output_dir))
#         logger.debug(f"Created files: {created_files}")
#
#         # Extract doc names and dimensions from tuples
#         doc_names = [file_info[0] for file_info in created_files]
#         section_dimensions = [file_info[1] for file_info in created_files]
#
#         # Log grid information
#         standard_count = sum(1 for unit in units if unit.is_standard)
#         non_standard_count = len(units) - standard_count
#
#         standard_info = {
#             'num_x': baseplate.num_squares_x,
#             'num_y': baseplate.num_squares_y,
#             'size': baseplate.grid_size
#         }
#
#         non_standard_info = {
#             'count': non_standard_count
#         }
#
#         logger.info(f"Standard spaces: {standard_info}")
#         logger.info(f"Non-standard spaces: {non_standard_info}")
#         logger.info(f"Number of printable objects: {len(created_files)}")
#
#         # Validate the division calculations
#         validate_division_math(width, depth, standard_info, non_standard_info)
#
#         # Check each generated file
#         for i, (doc_name, dimensions) in enumerate(created_files):
#             # Check both STL and FCStd files
#             temp_stl_path = temp_output_dir / f"{doc_name}.stl"
#             temp_fcstd_path = temp_output_dir / f"{doc_name}.FCStd"
#
#             # Check if files exist in temp directory
#             logger.debug(f"Checking temp files for {doc_name}:")
#             logger.debug(f"STL exists: {temp_stl_path.exists()}")
#             logger.debug(f"FCStd exists: {temp_fcstd_path.exists()}")
#
#             assert temp_stl_path.exists(), f"STL file not found at {temp_stl_path}"
#             assert temp_fcstd_path.exists(), f"FreeCAD file not found at {temp_fcstd_path}"
#
#             # Verify dimensions are within print bed limits
#             assert dimensions['width'] <= 220, \
#                 f"Section {i + 1} width ({dimensions['width']}) exceeds print bed size"
#             assert dimensions['depth'] <= 220, \
#                 f"Section {i + 1} depth ({dimensions['depth']}) exceeds print bed size"
#
#             # Validate file contents
#             validate_freecad_file(temp_fcstd_path, width, depth)
#             validate_stl_file(temp_stl_path, width, depth)
#
#             # Copy files to permanent location
#             permanent_stl_path = permanent_output_dir / f"{doc_name}.stl"
#             permanent_fcstd_path = permanent_output_dir / f"{doc_name}.FCStd"
#
#             logger.info(f"Copying files to permanent location for {doc_name}...")
#             shutil.copy2(temp_stl_path, permanent_stl_path)
#             shutil.copy2(temp_fcstd_path, permanent_fcstd_path)
#
#             # Verify permanent files exist
#             logger.debug(f"Verifying permanent files for {doc_name}:")
#             logger.debug(f"STL exists: {permanent_stl_path.exists()}")
#             logger.debug(f"FCStd exists: {permanent_fcstd_path.exists()}")
#
#             assert permanent_stl_path.exists(), f"Failed to copy STL to {permanent_stl_path}"
#             assert permanent_fcstd_path.exists(), f"Failed to copy FCStd to {permanent_fcstd_path}"
#
#         logger.info(f"All files successfully saved to: {permanent_output_dir}")
#
#     except Exception as e:
#         logger.error("Test failed with exception", exc_info=True)
#         raise

def validate_division_math(width, depth, standard_info, non_standard_info):
    """Validate the mathematics of the grid division"""
    # Calculate expected number of standard squares
    expected_squares_x = math.ceil(width / standard_info['size'])
    expected_squares_y = math.ceil(depth / standard_info['size'])

    assert standard_info['num_x'] == expected_squares_x, \
        f"Incorrect number of X squares. Expected {expected_squares_x}, got {standard_info['num_x']}"
    assert standard_info['num_y'] == expected_squares_y, \
        f"Incorrect number of Y squares. Expected {expected_squares_y}, got {standard_info['num_y']}"


def validate_freecad_file(file_path, width, depth):
    """Validate the FreeCAD file contents"""
    try:
        import FreeCAD
        doc = FreeCAD.openDocument(str(file_path))

        # Verify document contains objects
        assert len(doc.Objects) > 0, "FreeCAD document is empty"

        # Basic size validation could be added here
        # Note: Exact validation would require analyzing the shapes

        FreeCAD.closeDocument(doc.Name)
    except Exception as e:
        logger.error(f"Error validating FreeCAD file: {e}")
        raise


def validate_stl_file(file_path, width, depth):
    """Validate the STL file contents"""
    try:
        # Read STL file
        with open(file_path, 'rb') as f:
            # Verify file is not empty
            assert f.read(1), "STL file is empty"

        # Additional STL validation could be added here
        # Note: Full STL validation would require parsing the binary format
    except Exception as e:
        logger.error(f"Error validating STL file: {e}")
        raise

@pytest.fixture(autouse=True, scope="session")
def cleanup_logs():
    log_file = Path("logs/test_baseplate.log")
    if log_file.exists():
        log_file.unlink()
    yield

@pytest.mark.parametrize("width,depth,description,expected_sections", [
    (42, 42, "Basic 1x1", 1),
    (42, 64, "1x1.5 non-standard", 1),
    (64, 42, "1.5x1 non-standard", 1),
    ()
    (250, 250, "Large multi-section", 4)  # Will need 2x2 sections
])
def test_baseplate(width, depth, description, expected_sections, tmp_path):
    """Test baseplate generation with comprehensive validation"""
    logger.info(f"\nTesting baseplate: {width}x{depth}mm ({description})")

    try:
        from src.core.gridfinity_baseplate import GridfinityBaseplate

        # Log test parameters
        logger.debug(f"Test parameters:")
        logger.debug(f"Width: {width}mm")
        logger.debug(f"Depth: {depth}mm")
        logger.debug(f"Description: {description}")
        logger.debug(f"Expected sections: {expected_sections}")
        logger.debug(f"Temporary path: {tmp_path}")

        # Create directories
        temp_output_dir = tmp_path / f"baseplate_{width}x{depth}"
        temp_output_dir.mkdir(exist_ok=True)
        logger.debug(f"Created temp directory: {temp_output_dir}")

        permanent_output_dir = OUTPUT_DIR / f"baseplate_{width}x{depth}"
        permanent_output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created permanent directory: {permanent_output_dir}")

        # Create baseplate instance
        logger.info("Creating baseplate instance...")
        baseplate = GridfinityBaseplate(width, depth, 220, 220)

        # Generate units
        logger.info("Generating grid units...")
        units = baseplate.grid_divider()
        logger.debug(f"Generated {len(units)} units")

        # Get printable objects
        logger.info("Creating printable objects...")
        printable_objects = baseplate.printable_object_selector(units)
        logger.debug(f"Created {len(printable_objects)} printable objects")

        # Verify number of printable objects matches expected sections
        assert len(printable_objects) == expected_sections, \
            f"Expected {expected_sections} sections, but got {len(printable_objects)}"

        # Generate files - using the instance we created
        logger.info("Generating baseplate files...")
        created_files = baseplate.generate_baseplate(str(temp_output_dir))
        logger.debug(f"Created files: {created_files}")

        # Verify number of created files matches expected sections
        assert len(created_files) == expected_sections, \
            f"Expected {expected_sections} files, but got {len(created_files)}"

        doc_names = [file_info[0] for file_info in created_files]
        dimensions_info = dict(created_files)

        # For each section, verify files and dimensions

        for i, doc_name in enumerate(doc_names):
            # Verify both STL and FCStd files exist
            temp_stl_path = temp_output_dir / f"{doc_name}.stl"
            temp_fcstd_path = temp_output_dir / f"{doc_name}.FCStd"

            logger.debug(f"Checking section {i + 1}/{expected_sections}:")
            logger.debug(f"STL exists: {temp_stl_path.exists()}")
            logger.debug(f"FCStd exists: {temp_fcstd_path.exists()}")

            assert temp_stl_path.exists(), f"STL file not found for section {i + 1}"
            assert temp_fcstd_path.exists(), f"FreeCAD file not found for section {i + 1}"

            # Get dimensions for this section
            dimensions = dimensions_info[doc_name]
            # Verify dimensions are within print bed limits
            assert dimensions['width'] <= 220, \
                f"Section {i + 1} width ({dimensions['width']}) exceeds print bed size"
            assert dimensions['depth'] <= 220, \
                f"Section {i + 1} depth ({dimensions['depth']}) exceeds print bed size"

            # Verify each section's dimensions are within print bed limits
            section = printable_objects[i]
            max_section_width = max(unit.width for unit in section.units)
            max_section_depth = max(unit.depth for unit in section.units)

            assert max_section_width <= 220, \
                f"Section {i + 1} width ({max_section_width}) exceeds print bed size"
            assert max_section_depth <= 220, \
                f"Section {i + 1} depth ({max_section_depth}) exceeds print bed size"

            # Copy files to permanent location
            permanent_stl_path = permanent_output_dir / f"{doc_name}.stl"
            permanent_fcstd_path = permanent_output_dir / f"{doc_name}.FCStd"

            logger.info(f"Copying files for section {i + 1}...")
            shutil.copy2(temp_stl_path, permanent_stl_path)
            shutil.copy2(temp_fcstd_path, permanent_fcstd_path)

            # Verify permanent files exist
            assert permanent_stl_path.exists(), f"Failed to copy STL for section {i + 1}"
            assert permanent_fcstd_path.exists(), f"Failed to copy FCStd for section {i + 1}"

        # Log final counts
        logger.info(f"Successfully generated {len(created_files)} sections:")
        for i, section in enumerate(printable_objects):
            logger.info(f"Section {i + 1}: {len(section.units)} units")

    except Exception as e:
        logger.error("Test failed with exception", exc_info=True)
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])