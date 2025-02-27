import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import FreeCAD
import Part
from FreeCAD import Vector
import math
import logging
from core.gridfinity_config import GridfinityConfig
logger = logging.getLogger(__name__)

@dataclass
class BaseplateSection:
    doc_name: str
    fcstd_path: Path
    stl_path: Path
    width: float
    depth: float

class Unit:
    def __init__(self, width, depth, x_offset, y_offset, is_standard=True):
        self.width = width
        self.depth = depth
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.is_standard = is_standard


class PrintableObject:
    def __init__(self, units, index):
        self.units = units  # List of Unit objects
        self.index = index  # Index for naming


class GridfinityBaseplate:
    def __init__(self, drawer_width, drawer_depth, config: GridfinityConfig = None):
        self.config = config or GridfinityConfig()
        self.drawer_width = drawer_width
        self.drawer_depth = drawer_depth

        self.num_squares_x = math.ceil((drawer_width - 2 * self.config.TOLERANCE) / self.config.GRID_SIZE)
        self.num_squares_y = math.ceil((drawer_depth - 2 * self.config.TOLERANCE) / self.config.GRID_SIZE)

        self.total_width = self.num_squares_x * self.config.GRID_SIZE
        self.total_depth = self.num_squares_y * self.config.GRID_SIZE


    def grid_divider(self):
        """Divides the drawer into standard and non-standard units, with non-standard at the top"""
        units = []

        # Full width and depth of the space to be divided
        total_width = self.drawer_width
        total_depth = self.drawer_depth

        # Calculate how many complete standard grids fit
        standard_squares_x = int(total_width / self.config.GRID_SIZE)
        standard_squares_y = int(total_depth / self.config.GRID_SIZE)

        # Calculate the actual remaining space (could be negative)
        remaining_width = total_width - (standard_squares_x * self.config.GRID_SIZE)
        remaining_depth = total_depth - (standard_squares_y * self.config.GRID_SIZE)

        # Place non-standard depth units at the top (smaller y values)
        has_non_standard_depth = remaining_depth > 0 and remaining_depth < self.config.GRID_SIZE

        # For each grid position
        for y in range(self.num_squares_y):
            for x in range(self.num_squares_x):
                x_pos = x * self.config.GRID_SIZE
                
                # If we have non-standard depths, place them at the top by adjusting y_pos
                if has_non_standard_depth:
                    # First row (y=0) gets the non-standard depth
                    if y == 0:
                        y_pos = 0
                        depth = remaining_depth if remaining_depth > 0 else self.config.GRID_SIZE
                    else:
                        # Shift standard-sized units down to make room for the non-standard unit at the top
                        y_pos = remaining_depth + (y - 1) * self.config.GRID_SIZE
                        depth = self.config.GRID_SIZE
                else:
                    # Standard y positioning if no non-standard depths
                    y_pos = y * self.config.GRID_SIZE
                    
                    # Determine depth for this unit (standard case)
                    if y < standard_squares_y:
                        depth = self.config.GRID_SIZE  # Standard depth
                    else:
                        depth = remaining_depth if remaining_depth > 0 else self.config.GRID_SIZE

                # Determine width for this unit
                if x < standard_squares_x:
                    width = self.config.GRID_SIZE  # Standard width
                else:
                    width = remaining_width if remaining_width > 0 else self.config.GRID_SIZE

                # Only add unit if dimensions are sufficient
                is_standard = (width == self.config.GRID_SIZE and depth == self.config.GRID_SIZE)
                units.append(Unit(width, depth, x_pos, y_pos, is_standard))

        return units

    def printable_object_selector(self, units):
        """Divides units into printable objects based on print bed size"""
        printable_objects = []
        remaining_units = units.copy()
        object_index = 0

        # Initialize offsets
        y_printable_object_offset = 0

        while remaining_units:
            # Get units at current y offset
            y_units = [u for u in remaining_units if u.y_offset == y_printable_object_offset]
            if not y_units:
                break

            # Calculate max units in y direction that fit on print bed
            y_count = 0
            current_y_units = []
            for y in range(self.num_squares_y):
                y_row = [u for u in remaining_units if u.y_offset == y_printable_object_offset + (y * self.config.GRID_SIZE)]
                if not y_row or (y + 1) * self.config.GRID_SIZE > self.config.PRINT_BED_DEPTH:
                    break
                current_y_units.extend(y_row)
                y_count += 1

            # Process units in x direction for these y rows
            x_printable_object_offset = 0
            while current_y_units:
                # Get units at current x offset for all y rows
                x_units = [u for u in current_y_units if u.x_offset == x_printable_object_offset]
                if not x_units:
                    break

                # Calculate max units in x direction that fit on print bed
                x_count = 0
                printable_section_units = []
                for x in range(self.num_squares_x):
                    x_col = []
                    for y in range(y_count):
                        unit = next((u for u in current_y_units
                                     if u.x_offset == x_printable_object_offset + (x * self.config.GRID_SIZE)
                                     and u.y_offset == y_printable_object_offset + (y * self.config.GRID_SIZE)), None)
                        if unit:
                            x_col.append(unit)

                    if not x_col or (x + 1) * self.config.GRID_SIZE > self.config.PRINT_BED_WIDTH:
                        break
                    printable_section_units.extend(x_col)
                    x_count += 1

                if printable_section_units:
                    # Create adjusted units with zeroed offsets
                    adjusted_units = []
                    base_x = min(u.x_offset for u in printable_section_units)
                    base_y = min(u.y_offset for u in printable_section_units)

                    for unit in printable_section_units:
                        adjusted_unit = Unit(
                            width=unit.width,
                            depth=unit.depth,
                            x_offset=unit.x_offset - base_x,
                            y_offset=unit.y_offset - base_y,
                            is_standard=unit.is_standard
                        )
                        adjusted_units.append(adjusted_unit)

                    # Create printable object and update tracking
                    printable_objects.append(PrintableObject(adjusted_units, object_index))
                    object_index += 1

                    # Remove processed units from remaining sets
                    for unit in printable_section_units:
                        if unit in remaining_units:
                            remaining_units.remove(unit)
                        if unit in current_y_units:
                            current_y_units.remove(unit)

                    x_printable_object_offset += x_count * self.config.GRID_SIZE
                else:
                    break

            y_printable_object_offset += y_count * self.config.GRID_SIZE

        return printable_objects

    def create_printable_object(self, printable_object, output_dir="generated_files"):
        """Creates and validates a single printable object"""
        doc_name = f"BasePlate_{printable_object.index}"
        output_dir = Path(output_dir)
        logger = logging.getLogger(__name__)
        doc = None

        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            fcstd_path = output_dir / f"{doc_name}.FCStd"
            stl_path = output_dir / f"{doc_name}.stl"

            # Log intended dimensions
            logger.info(f"\nCreating printable object {doc_name}")
            logger.info("Intended dimensions:")
            for unit in printable_object.units:
                logger.info(f"  Unit: {unit.width}x{unit.depth} at position ({unit.x_offset}, {unit.y_offset})")

            # Create fresh document - only create once
            import FreeCAD
            # Close any existing document with this name
            if doc_name in FreeCAD.listDocuments():
                FreeCAD.closeDocument(doc_name)

            # Create new document
            doc = FreeCAD.newDocument(doc_name)

            # Create and validate individual units
            created_objects = []
            object_bounds = {'min_x': float('inf'), 'min_y': float('inf'),
                             'max_x': float('-inf'), 'max_y': float('-inf')}

            for unit in printable_object.units:
                # Pass doc reference instead of doc_name
                objects = self.create_unit(unit.width, unit.depth, self.config.CORNER_RADIUS,
                                           unit.x_offset, unit.y_offset, doc)

                # Validate each created object
                for obj in objects:
                    if hasattr(obj, 'Shape'):
                        bbox = obj.Shape.BoundBox

                        # Update overall bounds
                        object_bounds['min_x'] = min(object_bounds['min_x'], bbox.XMin)
                        object_bounds['min_y'] = min(object_bounds['min_y'], bbox.YMin)
                        object_bounds['max_x'] = max(object_bounds['max_x'], bbox.XMax)
                        object_bounds['max_y'] = max(object_bounds['max_y'], bbox.YMax)

                        # Validate individual unit dimensions
                        self._validate_unit_dimensions(unit, bbox)

                created_objects.extend(objects)
                doc.recompute()

            # Export files
            self._export_freecad_file(doc, fcstd_path)
            self._export_stl_file(doc, stl_path)

            # Calculate final dimensions
            final_dimensions = {
                'width': object_bounds['max_x'] - object_bounds['min_x'],
                'depth': object_bounds['max_y'] - object_bounds['min_y'],
                'height': self.config.BASE_HEIGHT,
                'position': (object_bounds['min_x'], object_bounds['min_y'])
            }

            # Close document after we're done with it
            FreeCAD.closeDocument(doc_name)

            return doc_name, final_dimensions

        except Exception as e:
            logger.error(f"Error creating printable object: {e}")
            # Make sure to close document even if there's an error
            if doc and doc_name in FreeCAD.listDocuments():
                FreeCAD.closeDocument(doc_name)
            raise

    def generate_baseplate(self, output_dir="generated_files"):
        """Main function to generate the complete baseplate"""
        try:
            # Divide grid into units
            units = self.grid_divider()

            # Divide into printable objects
            printable_objects = self.printable_object_selector(units)

            # Create each printable object
            created_files = []
            for printable_object in printable_objects:
                doc_name = self.create_printable_object(printable_object, output_dir)
                if doc_name:  # Only add if successfully created
                    created_files.append(doc_name)

            # Cleanup after all files are created
            self.cleanup_documents()

            return created_files

        except Exception as e:
            print(f"Error in generate_baseplate: {e}")
            raise

    def create_baseplate(self, width: float, depth: float, output_dir: str) -> List[BaseplateSection]:
        """Generate baseplate files and return file information"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create baseplate instance
        baseplate = GridfinityBaseplate(width, depth, 220, 220)

        # Generate grid and objects
        units = baseplate.grid_divider()
        printable_objects = baseplate.printable_object_selector(units)

        # Generate files for each section
        sections = []
        created_files = baseplate.generate_baseplate(str(output_path))

        for i, (doc_name, dimensions) in enumerate(created_files):
            section = BaseplateSection(
                doc_name=doc_name,
                fcstd_path=output_path / f"{doc_name}.FCStd",
                stl_path=output_path / f"{doc_name}.stl",
                width=dimensions['width'],
                depth=dimensions['depth']
            )
            sections.append(section)

        return sections

    def get_or_create_document(self, name="GridfinityTest"):
        """Creates a new document, closing any existing one with the same name"""
        import FreeCAD

        # Close existing document if it exists
        for doc in FreeCAD.listDocuments().values():
            if doc.Name == name:
                FreeCAD.closeDocument(doc.Name)

        # Create new document
        doc = FreeCAD.newDocument(name)
        return doc


    def clear_document(self, doc):
        """Clears all objects from the document"""
        for obj in doc.Objects:
            doc.removeObject(obj.Name)


    def create_base_profile(self):
        """Creates the base profile at origin"""
        profile_points = [
            Vector(0, 0, 0),
            Vector(0, 2.85, 0),  # Bottom width, centered
            Vector(0, 2.85, 0.35),  # First step
            Vector(0, 2.15, 1.05),  # Angled section
            Vector(0, 2.15, 2.85),  # Vertical section
            Vector(0, 0, 5.0),  # Top point
            Vector(0, 0, 0)  # Back to start
        ]

        try:
            # Create edges with precise vertex connections
            edges = []
            for i in range(len(profile_points) - 1):
                edge = Part.makeLine(profile_points[i], profile_points[i + 1])
                edges.append(edge)

            # Create wire and force it to be closed
            wire = Part.Wire(edges)
            if not wire.isClosed():
                logger.warning("Profile wire not naturally closed, forcing closure")
                wire.fixWire()

            # Create face
            face = Part.Face(wire)

            # Validate the profile
            if self.validate_shape(face, "base_profile"):
                return face
            else:
                raise ValueError("Failed to create valid base profile")

        except Exception as e:
            logger.error(f"Error creating base profile: {e}")
            raise


    def transform_profile(self, profile, position, rotation_angle=0):
        """
        Transform profile to new position and rotation
        position: Vector for new position
        rotation_angle: Angle in degrees to rotate around Z axis
        """
        # Create transformation matrix
        mat = FreeCAD.Matrix()

        # First rotate
        if rotation_angle != 0:
            mat.rotateZ(math.radians(rotation_angle))

        # Then translate
        mat.move(position)

        # Apply transformation
        return profile.transformGeometry(mat)


    def create_straight_sections(self, doc, width, depth, corner_radius, x_offset, y_offset):
        """Creates straight sections with validations"""
        created_objects = []
        base_profile = self.create_base_profile()

        # Define sections
        sections = [
            # (start, end, name)
            ((corner_radius + x_offset, y_offset, 0),
             (width - corner_radius + x_offset, y_offset, 0),
             "Bottom"),
            ((width + x_offset, corner_radius + y_offset, 0),
             (width + x_offset, depth - corner_radius + y_offset, 0),
             "Right"),
            ((width - corner_radius + x_offset, depth + y_offset, 0),
             (corner_radius + x_offset, depth + y_offset, 0),
             "Top"),
            ((x_offset, depth - corner_radius + y_offset, 0),
             (x_offset, corner_radius + y_offset, 0),
             "Left")
        ]

        for i, (start, end, section_name) in enumerate(sections):
            try:
                start_v = Vector(*start)
                end_v = Vector(*end)

                # Create and validate line
                line = Part.makeLine(start_v, end_v)
                if not self.validate_shape(line, f"{section_name}_line"):
                    continue

                line_wire = Part.Wire([line])
                if not self.validate_shape(line_wire, f"{section_name}_wire"):
                    continue

                # Calculate angle
                dx = end_v.x - start_v.x
                dy = end_v.y - start_v.y
                angle = math.degrees(math.atan2(dy, dx))

                # Transform profile
                transformed_profile = self.transform_profile(base_profile, start_v, angle)
                if not self.validate_shape(transformed_profile, f"{section_name}_profile"):
                    continue

                # Create pipe
                pipe = line_wire.makePipe(transformed_profile)
                if not self.validate_shape(pipe, f"{section_name}_pipe"):
                    continue

                # Add to document
                swept_obj = doc.addObject("Part::Feature", f"SweptProfile_{section_name}_{x_offset}_{y_offset}")
                swept_obj.Shape = pipe
                created_objects.append(swept_obj)

                logger.debug(f"Created {section_name} section successfully")

            except Part.OCCError as e:
                logger.error(f"Error creating {section_name} section: {e}")
                continue

        return created_objects


    def create_corners(self, doc, width, depth, corner_radius, x_offset, y_offset):
        """Creates corner sections with validations"""
        created_objects = []
        base_profile = self.create_base_profile()

        corners = [
            # (center, start_angle, end_angle, profile_point, profile_rotation, name)
            ((corner_radius + x_offset, corner_radius + y_offset, 0),
             180, 270,
             Vector(corner_radius + x_offset, y_offset, 0),
             0, "BottomLeft"),
            ((width - corner_radius + x_offset, corner_radius + y_offset, 0),
             270, 0,
             Vector(width - corner_radius + x_offset, y_offset, 0),
             0, "BottomRight"),
            ((width - corner_radius + x_offset, depth - corner_radius + y_offset, 0),
             0, 90,
             Vector(width - corner_radius + x_offset, depth + y_offset, 0),
             180, "TopRight"),
            ((corner_radius + x_offset, depth - corner_radius + y_offset, 0),
             90, 180,
             Vector(corner_radius + x_offset, depth + y_offset, 0),
             180, "TopLeft")
        ]

        for params in corners:
            corner_name = "Not set"
            try:
                center_point = Vector(*params[0])
                start_angle, end_angle = params[1], params[2]
                profile_point = params[3]
                profile_rotation = params[4]
                corner_name = params[5]

                # Create and validate arc
                arc = Part.makeCircle(corner_radius, center_point, Vector(0, 0, 1),
                                      start_angle, end_angle)
                if not self.validate_shape(arc, f"{corner_name}_arc"):
                    continue

                arc_wire = Part.Wire([arc])
                if not self.validate_shape(arc_wire, f"{corner_name}_wire"):
                    continue

                # Transform profile
                transformed_profile = self.transform_profile(base_profile, profile_point, profile_rotation)
                if not self.validate_shape(transformed_profile, f"{corner_name}_profile"):
                    continue

                # Create pipe
                pipe = arc_wire.makePipe(transformed_profile)
                if not self.validate_shape(pipe, f"{corner_name}_pipe"):
                    continue

                # Add to document
                swept_obj = doc.addObject("Part::Feature", f"SweptCorner_{corner_name}_{x_offset}_{y_offset}")
                swept_obj.Shape = pipe
                created_objects.append(swept_obj)

                logger.debug(f"Created {corner_name} corner successfully")

            except Part.OCCError as e:
                logger.error(f"Error creating {corner_name} corner: {e}")
                continue

        return created_objects


    def create_block(self, doc, width, depth, x_offset, y_offset):
        """
        Creates a simple rectangular block and translates it
        """
        try:
            # Create a box with width x depth x BASE_HEIGHT
            box = Part.makeBox(width, depth, self.config.BASE_HEIGHT)

            # Create translation
            translation = FreeCAD.Matrix()
            translation.move(Vector(x_offset, y_offset, 0))
            box = box.transformGeometry(translation)

            # Add to document with unique name including position
            block_obj = doc.addObject("Part::Feature", f"SimpleBlock_{x_offset}_{y_offset}")
            block_obj.Shape = box
            print(f"Created simple block {width}x{depth}x{self.config.BASE_HEIGHT}mm at position ({x_offset}, {y_offset})")
            return [block_obj]

        except Part.OCCError as e:
            print(f"Error creating block: {str(e)}")
            return []


    def validate_shape(self, shape, name="Unknown"):
        """Validate a shape and log any issues"""
        try:
            if not shape.isNull():
                logger.debug(f"Shape {name} is not null")
                if shape.isValid():
                    logger.debug(f"Shape {name} is valid")
                    logger.debug(f"Shape {name} bounds: {shape.BoundBox}")
                    return True
                else:
                    logger.error(f"Shape {name} is invalid")
                    return False
            else:
                logger.error(f"Shape {name} is null")
                return False
        except Exception as e:
            logger.error(f"Error validating shape {name}: {e}")
            return False


    def safe_fuse(self, base_shape, shape_to_add):
        """Safely fuse two shapes together"""
        try:
            # Try direct fusion first
            fused = base_shape.fuse(shape_to_add)
            if fused.isNull():
                logger.error("Direct fusion resulted in null shape")
                return base_shape
            return fused
        except Exception as e:
            logger.error(f"Direct fusion failed: {e}")
            try:
                # Try boolean operation as fallback
                bool_op = Part.BooleanOperations.booleanFuse(base_shape, shape_to_add)
                if bool_op.isNull():
                    logger.error("Boolean fusion resulted in null shape")
                    return base_shape
                return bool_op
            except Exception as e:
                logger.error(f"Boolean fusion failed: {e}")
                return base_shape


    def create_compound_shape(self, shapes):
        """Create a compound shape from a list of shapes"""
        try:
            # Create a compound of all input shapes
            compound = Part.Compound(shapes)
            if compound.isNull():
                logger.error("Created compound is null")
                return None
            return compound
        except Exception as e:
            logger.error(f"Error creating compound: {e}")
            return None

    def create_unit(self, width, depth, corner_radius, x_offset, y_offset, doc):
        """Creates a unified gridfinity unit
        Note: Now takes a document reference instead of doc_name
        """
        logger.debug(f"Creating unit: {width}x{depth} at ({x_offset},{y_offset})")

        try:
            if width < self.config.MIN_WIDTH or depth < self.config.MIN_DEPTH:
                shapes = self.create_block(doc, width, depth, x_offset, y_offset)
            else:
                # Create sections
                straight_shapes = self.create_straight_sections(doc, width, depth, corner_radius, x_offset, y_offset)
                corner_shapes = self.create_corners(doc, width, depth, corner_radius, x_offset, y_offset)

                # Combine all shapes
                all_shapes = [obj.Shape for obj in straight_shapes + corner_shapes]

                # Try compound fusion first
                logger.debug("Attempting compound fusion")
                compound = self.create_compound_shape(all_shapes)

                if compound and not compound.isNull():
                    try:
                        final_shape = compound
                        logger.debug("Using compound shape")
                    except Exception as e:
                        logger.warning(f"Compound handling failed: {e}, falling back to sequential fusion")
                        final_shape = all_shapes[0]
                        # Sequential fusion as fallback
                        for shape in all_shapes[1:]:
                            final_shape = self.safe_fuse(final_shape, shape)
                else:
                    logger.warning("Compound creation failed, using sequential fusion")
                    final_shape = all_shapes[0]
                    # Sequential fusion as fallback
                    for shape in all_shapes[1:]:
                        final_shape = self.safe_fuse(final_shape, shape)

                # Create final unified object
                unified_obj = doc.addObject("Part::Feature", f"UnifiedUnit_{x_offset}_{y_offset}")
                unified_obj.Shape = final_shape

                shapes = [unified_obj]

                # Validate final shape
                if self.validate_shape(unified_obj.Shape, unified_obj.Name):
                    logger.debug("Final unified shape is valid")
                else:
                    logger.error("Final unified shape is invalid")
            return shapes

        except Exception as e:
            logger.error(f"Error in create_unit: {e}")
            raise

    def _validate_unit_dimensions(self, unit, bbox):
        """Validates dimensions of a single unit"""
        actual_width = bbox.XMax - bbox.XMin
        actual_depth = bbox.YMax - bbox.YMin
        width_error = abs(actual_width - unit.width)
        depth_error = abs(actual_depth - unit.depth)

        if width_error > self.config.DIMENSION_TOLERANCE or depth_error > self.config.DIMENSION_TOLERANCE:
            raise ValueError(f"Unit dimensions mismatch - Expected: {unit.width}x{unit.depth}, "
                            f"Got: {actual_width:.2f}x{actual_depth:.2f}")

    def _export_freecad_file(self, doc, path):
        """Exports FreeCAD document"""
        doc.saveAs(str(path))
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise ValueError(f"Failed to create valid FreeCAD file at {path}")

    def _export_stl_file(self, doc, path):
        """Exports STL file"""
        import Mesh
        mesh = Mesh.Mesh()
        for obj in doc.Objects:
            if hasattr(obj, 'Shape'):
                vertices, facets = obj.Shape.tessellate(0.05)
                for f in facets:
                    mesh.addFacet(vertices[f[0]], vertices[f[1]], vertices[f[2]])
        mesh.write(str(path))
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise ValueError(f"Failed to create valid stl file at {path}")

    def cleanup_documents(self):
        """Close all open FreeCAD documents"""
        import FreeCAD
        for doc_name in FreeCAD.listDocuments():
            FreeCAD.closeDocument(doc_name)

def set_object_visible(obj):
    """Safely set an object's visibility to True"""
    try:
        import FreeCADGui
        if FreeCADGui.activeDocument():  # Only proceed if GUI is available
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                obj.ViewObject.Visibility = True
                logger.debug(f"Set {obj.Name} visible")
    except ImportError:
        logger.debug("FreeCADGui not available - skipping visibility setting")
    except Exception as e:
        logger.debug(f"Could not set visibility for {obj.Name}: {e}")

def center_view(doc_name):
    """Centers the view on all objects in the document"""
    try:
        import FreeCADGui
        if FreeCADGui.activeDocument():  # Only proceed if GUI is available
            # Get the active view
            view = FreeCADGui.getDocument(doc_name).activeView()

            # Set to axonometric view
            view.viewAxonometric()

            # Fit all objects
            view.fitAll()

            # Optional: set view direction to isometric
            view.viewIsometric()

            logger.debug("View centered successfully")
    except ImportError:
        logger.debug("FreeCADGui not available - skipping view centering")
    except Exception as e:
        logger.debug(f"Error centering view: {e}")

def ensure_objects_visible(doc_name):
    """Ensures all objects in the document are visible"""
    try:
        import FreeCADGui
        if FreeCADGui.activeDocument():  # Only proceed if GUI is available
            # Get the document
            gui_doc = FreeCADGui.getDocument(doc_name)

            # Make all objects visible
            for obj in gui_doc.Document.Objects:
                set_object_visible(obj)

            # Update the view
            gui_doc.Document.recompute()

            logger.debug("All objects set to visible")
    except ImportError:
        logger.debug("FreeCADGui not available - skipping visibility control")
    except Exception as e:
        logger.debug(f"Error setting object visibility: {e}")

def check_freecad_version(self):
    """Check FreeCAD version and log compatibility information"""
    try:
        version = FreeCAD.Version()
        version_str = '.'.join(version[0:3])
        logger.info(f"FreeCAD Version: {version_str}")
        logger.info(f"Build type: {version[3]}")
        logger.info(f"Build date: {version[4]}")
        logger.info(f"Branch: {version[5]}")
        logger.info(f"Hash: {version[6]}")

        # Parse major.minor version
        major, minor = map(int, version_str.split('.')[:2])
        logger.info(f"Parsed version: {major}.{minor}")

        if major == 0 and minor >= 20:
            logger.info("FreeCAD version is compatible")
        else:
            logger.warning(f"FreeCAD version {major}.{minor} might not be fully compatible")

        return version
    except Exception as e:
        logger.error(f"Error checking FreeCAD version: {e}")
        return None