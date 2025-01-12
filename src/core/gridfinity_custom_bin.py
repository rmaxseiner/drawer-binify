import os
import FreeCAD as App
import Part
from FreeCAD import Vector
import math
import logging

logger = logging.getLogger(__name__)


class GridfinityCustomBin:
    def __init__(self):
        self.knob_height = 4.75
        self.wall_thickness = 1.2
        self.bin_inset = 0.25
        self.corner_diameter = 8.0
        self.wall_height = 5.0
        self.lip_height = 1.5  # Height of the lip section
        self.bottom_thickness = 0.8  # Thickness of the bottom plate

    def create_straight_section(self, doc, start_point, end_point, height, name, layer_type="wall"):
        """Creates a straight section with specified profile type"""
        try:
            logger.info(f"Creating {layer_type} straight section '{name}':")
            logger.debug(f"  Start point: {start_point}")
            logger.debug(f"  End point: {end_point}")

            line = Part.makeLine(start_point, end_point)
            dx = end_point.x - start_point.x
            dy = end_point.y - start_point.y
            angle = math.degrees(math.atan2(dy, dx))
            logger.debug(f"  Line angle: {angle} degrees (dx={dx:.2f}, dy={dy:.2f})")

            # Create base profile

            if layer_type == "wall":
                profile = self.create_wall_base_profile()
            elif layer_type == "lip":
                profile = self.create_lip_base_profile()
            elif layer_type == "knob":
                profile = self.create_knob_profile()
            else:
                raise ValueError(f"Unknown layer type: {layer_type}")

            # Transform the profile
            profile_face = self.transform_profile(profile, start_point, angle)

            wire = Part.Wire([line])
            wall = wire.makePipe(profile_face)
            wall_obj = doc.addObject("Part::Feature", f"{layer_type.capitalize()}_{name}")
            wall_obj.Shape = wall

            return wall_obj
        except Exception as e:
            logger.error(f"Error creating straight section {name}: {e}")
            return None

    def create_corners(self, doc, width, depth, corner_radius, x_offset, y_offset, layer_type="wall", z_offset=0):
        """Creates corner sections for specified layer type at given z_offset"""
        created_objects = []

        # Select base profile based on layer type
        if layer_type == "wall":
            base_profile = self.create_wall_base_profile()
        elif layer_type == "lip":
            base_profile = self.create_lip_base_profile()
        elif layer_type == "knob":
            base_profile = self.create_knob_profile()
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

        corners = [
            ((corner_radius + x_offset, corner_radius + y_offset, z_offset),
             180, 270,
             Vector(corner_radius + x_offset, y_offset, z_offset),
             0, "BottomLeft"),
            ((width - corner_radius + x_offset, corner_radius + y_offset, z_offset),
             270, 0,
             Vector(width - corner_radius + x_offset, y_offset, z_offset),
             0, "BottomRight"),
            ((width - corner_radius + x_offset, depth - corner_radius + y_offset, z_offset),
             0, 90,
             Vector(width - corner_radius + x_offset, depth + y_offset, z_offset),
             180, "TopRight"),
            ((corner_radius + x_offset, depth - corner_radius + y_offset, z_offset),
             90, 180,
             Vector(corner_radius + x_offset, depth + y_offset, z_offset),
             180, "TopLeft")
        ]

        logger.info(f"Creating {layer_type} corners at z={z_offset}")

        for params in corners:
            try:
                center_point = Vector(*params[0])
                start_angle, end_angle = params[1], params[2]
                profile_point = params[3]
                profile_rotation = params[4]
                corner_name = params[5]

                # Create arc at z_offset with normal in z direction
                arc = Part.makeCircle(corner_radius, center_point, Vector(0, 0, 1),
                                      start_angle, end_angle)
                arc_wire = Part.Wire([arc])
                transformed_profile = self.transform_profile(base_profile, profile_point, profile_rotation)
                pipe = arc_wire.makePipe(transformed_profile)

                swept_obj = doc.addObject("Part::Feature", f"{layer_type.capitalize()}_Corner_{corner_name}")
                swept_obj.Shape = pipe
                created_objects.append(swept_obj)

            except Part.OCCError as e:
                logger.error(f"Error creating {layer_type} corner {corner_name}: {e}")
                continue

        return created_objects

    def create_wall_base_profile(self):
        """Creates the wall base profile at origin, oriented along Y axis"""
        profile_points = [
            Vector(0, 0, 0),
            Vector(0, self.wall_thickness, 0),  # Along Y axis
            Vector(0, self.wall_thickness, self.wall_height),
            Vector(0, 0, self.wall_height),
            Vector(0, 0, 0)
        ]
        return self.create_profile_from_points(profile_points)

    def create_lip_base_profile(self):
        """Creates the lip base profile at origin"""
        inner_extension = 0.6
        straight_extension = 1.8
        outer_extension = 1.9
        total_height = straight_extension + inner_extension + outer_extension


        profile_points = [
            Vector(0, 0, 0),
            Vector(0, 0, total_height),
            Vector(0, outer_extension, total_height - outer_extension),
            Vector(0, outer_extension, total_height - outer_extension - straight_extension ),
            Vector(0, outer_extension + inner_extension, 0 ),
            Vector(0, 0, 0)
        ]
        return self.create_profile_from_points(profile_points)


    def create_profile_from_points(self, points):
        """Helper method to create a profile face from points"""
        try:
            edges = []
            for i in range(len(points) - 1):
                edge = Part.makeLine(points[i], points[i + 1])
                edges.append(edge)

            wire = Part.Wire(edges)
            if not wire.isClosed():
                logger.error("Profile required closing.  May not be correct.")
                wire.fixWire()

            return Part.Face(wire)

        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            raise

    def transform_profile(self, profile, position, rotation_angle=0):
        """Transform profile to new position and rotation"""
        logger.info(f"Transforming profile:")
        logger.debug(f"  - Target position: {position}")
        logger.debug(f"  - Rotation angle: {rotation_angle} degrees")

        # Create transformation matrix
        mat = App.Matrix()

        # First rotate around Z
        if rotation_angle != 0:
            mat.rotateZ(math.radians(rotation_angle))

        # Then translate
        mat.move(position)

        transformed = profile.transformGeometry(mat)
        logger.debug("Transformation results:")
        logger.debug(
            f"  Before: X({profile.BoundBox.XMin:.2f},{profile.BoundBox.XMax:.2f}) Y({profile.BoundBox.YMin:.2f},{profile.BoundBox.YMax:.2f})")
        logger.debug(
            f"  After:  X({transformed.BoundBox.XMin:.2f},{transformed.BoundBox.XMax:.2f}) Y({transformed.BoundBox.YMin:.2f},{transformed.BoundBox.YMax:.2f})")

        return transformed

    def create_layer(self, doc, width, depth, z_offset=0, layer_type="wall"):
        """Creates complete layer (wall or lip) including straight sections and corners"""
        try:
            # Determine height based on layer type
            height = self.wall_height if layer_type == "wall" else self.lip_height

            # Calculate key positions with z_offset
            x_start = self.corner_diameter / 2
            x_end = width - self.corner_diameter / 2
            y_start = self.corner_diameter / 2
            y_end = depth - self.corner_diameter / 2

            # Define corner points with z_offset
            points = {
                'a': Vector(x_start, self.bin_inset, z_offset),  # Bottom edge start
                'b': Vector(x_end, self.bin_inset, z_offset),  # Bottom edge end
                'c': Vector(width - self.bin_inset, y_start, z_offset),  # Right edge start
                'd': Vector(width - self.bin_inset, y_end, z_offset),  # Right edge end
                'e': Vector(x_end, depth - self.bin_inset, z_offset),  # Top edge start
                'f': Vector(x_start, depth - self.bin_inset, z_offset),  # Top edge end
                'g': Vector(self.bin_inset, y_end, z_offset),  # Left edge start
                'h': Vector(self.bin_inset, y_start, z_offset)  # Left edge end
            }

            logger.info(f"Creating {layer_type} layer at z={z_offset}")

            # Create straight sections
            sections = []
            sections.append(self.create_straight_section(doc, points['a'], points['b'],
                                                         height, "Bottom", layer_type))
            sections.append(self.create_straight_section(doc, points['c'], points['d'],
                                                         height, "Right", layer_type))
            sections.append(self.create_straight_section(doc, points['e'], points['f'],
                                                         height, "Top", layer_type))
            sections.append(self.create_straight_section(doc, points['g'], points['h'],
                                                         height, "Left", layer_type))

            # Create corners at z_offset
            corners = self.create_corners(doc, width - (self.bin_inset) * 2,
                                          depth - (self.bin_inset) * 2,
                                          self.corner_diameter / 2 - (self.bin_inset),
                                          self.bin_inset, self.bin_inset, layer_type,
                                          z_offset=z_offset)

            # Combine all parts using multifuse
            all_parts = sections + corners
            layer_name = "Wall_Layer" if layer_type == "wall" else "Lip_Layer"
            fused = doc.addObject("Part::MultiFuse", layer_name)
            fused.Shapes = all_parts

            return fused

        except Exception as e:
            logger.error(f"Error creating {layer_type} layer: {e}")
            raise


    def create_bottom_plate(self, doc, width, depth):
        """Creates the bottom plate with rounded corners using explicit geometry construction"""
        try:
            # Calculate dimensions for the bottom plate
            length = width - (2 * self.bin_inset)
            plate_width = depth - (2 * self.bin_inset)
            corner_radius = self.corner_diameter / 2 - self.bin_inset

            # Calculate key points for the rounded rectangle
            x_start = self.bin_inset
            y_start = self.bin_inset
            x_end = x_start + length
            y_end = y_start + plate_width

            # Create the shape using a wire and face
            edges = []

            # Bottom edge with rounded corners
            p1 = Vector(x_start + corner_radius, y_start, 0)
            p2 = Vector(x_end - corner_radius, y_start, 0)
            edges.append(Part.makeLine(p1, p2))

            # Bottom right corner
            center1 = Vector(x_end - corner_radius, y_start + corner_radius, 0)
            edges.append(Part.makeCircle(corner_radius, center1, Vector(0, 0, 1), 270, 0))

            # Right edge
            p3 = Vector(x_end, y_start + corner_radius, 0)
            p4 = Vector(x_end, y_end - corner_radius, 0)
            edges.append(Part.makeLine(p3, p4))

            # Top right corner
            center2 = Vector(x_end - corner_radius, y_end - corner_radius, 0)
            edges.append(Part.makeCircle(corner_radius, center2, Vector(0, 0, 1), 0, 90))

            # Top edge
            p5 = Vector(x_end - corner_radius, y_end, 0)
            p6 = Vector(x_start + corner_radius, y_end, 0)
            edges.append(Part.makeLine(p5, p6))

            # Top left corner
            center3 = Vector(x_start + corner_radius, y_end - corner_radius, 0)
            edges.append(Part.makeCircle(corner_radius, center3, Vector(0, 0, 1), 90, 180))

            # Left edge
            p7 = Vector(x_start, y_end - corner_radius, 0)
            p8 = Vector(x_start, y_start + corner_radius, 0)
            edges.append(Part.makeLine(p7, p8))

            # Bottom left corner
            center4 = Vector(x_start + corner_radius, y_start + corner_radius, 0)
            edges.append(Part.makeCircle(corner_radius, center4, Vector(0, 0, 1), 180, 270))

            # Create wire from edges
            wire = Part.Wire(edges)
            face = Part.Face(wire)

            # Extrude the face to create the bottom plate
            bottom_plate = face.extrude(Vector(0, 0, self.bottom_thickness))

            # Add to document
            bottom_obj = doc.addObject("Part::Feature", "Bottom_Plate")
            bottom_obj.Shape = bottom_plate
            return bottom_obj

        except Exception as e:
            logger.error(f"Error creating bottom plate: {e}")
            raise

    def create_knob_profile(self):
        """Creates the knob profile in the Y-Z plane for the raised part"""
        profile_points = [
            Vector(0, 0, 4.75),  # A
            Vector(0, 3.75, 4.75),  # B
            Vector(0, 3.75, 0),  # C
            Vector(0, 2.95, 0),  # D
            Vector(0, 2.15, 0.8),  # E
            Vector(0, 2.15, 2.6),  # F
            Vector(0, 0, 4.75)  # G
        ]
        logger.info("Creating knob profile")
        return self.create_profile_from_points(profile_points)

    def grid_divider(self, width, depth, grid_size=42):
        """Divides the bin bottom into standard and non-standard units"""
        units = []

        # Calculate how many complete standard grids fit
        standard_squares_x = int(width / grid_size)
        standard_squares_y = int(depth / grid_size)

        # Calculate the actual remaining space
        remaining_width = width - (standard_squares_x * grid_size)
        remaining_depth = depth - (standard_squares_y * grid_size)

        # For each grid position
        for y in range(standard_squares_y + (1 if remaining_depth > 0 else 0)):
            for x in range(standard_squares_x + (1 if remaining_width > 0 else 0)):
                x_pos = x * grid_size
                y_pos = y * grid_size

                # Determine width for this unit
                if x < standard_squares_x:
                    unit_width = grid_size
                else:
                    unit_width = remaining_width

                # Determine depth for this unit
                if y < standard_squares_y:
                    unit_depth = grid_size
                else:
                    unit_depth = remaining_depth

                # Add unit with its dimensions and position
                units.append({
                    'width': unit_width,
                    'depth': unit_depth,
                    'x_pos': x_pos,
                    'y_pos': y_pos,
                    'is_standard': unit_width == grid_size and unit_depth == grid_size
                })

        return units

    def create_knob_unit(self, doc, width, depth, x_offset, y_offset):
        """Creates a single knob unit if dimensions are sufficient"""
        if width < 15 or depth < 15:
            logger.info(f"Unit too small for knob at ({x_offset}, {y_offset})")
            return None

        try:
            # Create the knob profile
            profile = self.create_knob_profile()

            # Calculate dimensions for the central box
            box_width = width - self.corner_diameter # Subtract corner diameter
            box_depth = depth - self.corner_diameter

            # Create the box at the center
            box = Part.makeBox(box_width, box_depth, self.knob_height,
                               Vector(x_offset + self.corner_diameter/2 - self.bin_inset, y_offset + self.corner_diameter/2 - self.bin_inset, 0))

            # Create the swept profile around the perimeter
            layer = self.create_layer(doc, width, depth, 0, "knob")

            # Create compound of all shapes
            shapes = [box]
            if layer:
                shapes.append(layer.Shape)

            compound = Part.makeCompound(shapes)

            # Add to document
            knob_obj = doc.addObject("Part::Feature", f"Knob_{x_offset}_{y_offset}")
            knob_obj.Shape = compound

            return knob_obj

        except Exception as e:
            logger.error(f"Error creating knob unit: {e}")
            return None

    def create_bin(self, width, depth, height, output_dir="generated_files"):
        """Creates a complete bin with all layers including knobs"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            doc_name = f"GrifinityBin_{width}x{depth}"
            doc = App.newDocument(doc_name)

            # Create knob layer first (at the bottom)
            knob_layer = self.create_knob_layer(doc, width, depth)

            # Create bottom plate with rounded corners above knobs
            bottom = self.create_bottom_plate(doc, width, depth)
            if bottom and hasattr(bottom, "Shape"):
                bottom.Placement.Base.z = self.knob_height

            # Calculate wall height and create wall layer
            wall_height = height - self.bottom_thickness - self.lip_height - self.knob_height
            wall_z_offset = self.bottom_thickness + self.knob_height
            wall_layer = self.create_layer(doc, width, depth, wall_z_offset, layer_type="wall")

            # Create lip layer
            lip_z_offset = wall_z_offset + self.wall_height
            lip_layer = self.create_layer(doc, width, depth, lip_z_offset, layer_type="lip")

            # Save files
            fcstd_path = os.path.join(output_dir, f"{doc_name}.FCStd")
            doc.saveAs(fcstd_path)

            # Export to STL
            import Mesh
            stl_path = os.path.join(output_dir, f"{doc_name}.stl")
            mesh = Mesh.Mesh()
            for obj in doc.Objects:
                if hasattr(obj, 'Shape'):
                    vertices, facets = obj.Shape.tessellate(0.05)
                    for f in facets:
                        mesh.addFacet(vertices[f[0]], vertices[f[1]], vertices[f[2]])
            mesh.write(stl_path)

            doc.recompute()
            return doc, fcstd_path, stl_path

        except Exception as e:
            logger.error(f"Error creating bin: {e}")
            raise

    def create_knob_layer(self, doc, width, depth):
        """Creates the complete knob layer with all units"""
        try:
            # Get all units based on the grid
            units = self.grid_divider(width - (2 * self.bin_inset),
                                      depth - (2 * self.bin_inset))

            knob_objects = []

            # Create knobs for each unit
            for unit in units:
                knob = self.create_knob_unit(
                    doc,
                    unit['width'],
                    unit['depth'],
                    unit['x_pos'] + self.bin_inset,
                    unit['y_pos'] + self.bin_inset
                )
                if knob:
                    knob_objects.append(knob)

            # Fuse all knobs together if there are any
            if knob_objects:
                fused_knobs = doc.addObject("Part::MultiFuse", "Knob_Layer")
                fused_knobs.Shapes = knob_objects
                return fused_knobs

            return None

        except Exception as e:
            logger.error(f"Error creating knob layer: {e}")
            raise


def main():
    try:
        logging.basicConfig(level=logging.INFO)
        bin_maker = GridfinityCustomBin()

        # Example usage
        width = 30.0  # mm
        depth = 42.0  # mm
        height = 35 # mm
        output_dir = "generated_files"

        doc, fcstd_path, stl_path = bin_maker.create_bin(width, depth, height, output_dir=output_dir)
        logger.info(f"Successfully created bin!")
        logger.info(f"FreeCAD file saved to: {fcstd_path}")
        logger.info(f"STL file saved to: {stl_path}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()