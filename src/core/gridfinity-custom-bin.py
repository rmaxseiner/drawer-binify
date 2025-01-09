import FreeCAD as App
import Part
from FreeCAD import Vector


class GridfinityBin:
    def __init__(self, width, depth, height):
        self.width = width
        self.depth = depth
        self.height = height
        self.wall_thickness = 1.2
        self.bottom_thickness = 1.8
        self.lip_height = 4.0
        self.lip_inset = 0.8

        # Create new document
        self.doc = App.newDocument("GridfinityBin")

    def create_bin(self):
        """Creates a custom-sized Gridfinity bin"""
        # Create outer shell
        outer = Part.makeBox(self.width, self.depth, self.height)

        # Create inner void
        inner = Part.makeBox(
            self.width - 2 * self.wall_thickness,
            self.depth - 2 * self.wall_thickness,
            self.height - self.bottom_thickness,
            Vector(self.wall_thickness, self.wall_thickness, self.bottom_thickness)
        )

        # Create lip
        lip_outer = Part.makeBox(
            self.width,
            self.depth,
            self.lip_height,
            Vector(0, 0, self.height - self.lip_height)
        )

        lip_inner = Part.makeBox(
            self.width - 2 * self.lip_inset,
            self.depth - 2 * self.lip_inset,
            self.lip_height,
            Vector(self.lip_inset, self.lip_inset, self.height - self.lip_height)
        )

        # Add reinforcement ribs if height is greater than 60mm
        bin_shape = outer.cut(inner)
        if self.height > 60:
            rib_thickness = 0.8
            rib_spacing = 30

            # Calculate number of ribs needed
            num_ribs_x = max(1, int(self.width / rib_spacing))
            num_ribs_y = max(1, int(self.depth / rib_spacing))

            # Create vertical ribs
            for x in range(1, num_ribs_x):
                pos_x = (x * self.width) / (num_ribs_x + 1)
                rib = Part.makeBox(
                    rib_thickness,
                    self.depth - 2 * self.wall_thickness,
                    self.height - self.bottom_thickness - self.lip_height,
                    Vector(pos_x - rib_thickness / 2, self.wall_thickness, self.bottom_thickness)
                )
                bin_shape = bin_shape.fuse(rib)

            for y in range(1, num_ribs_y):
                pos_y = (y * self.depth) / (num_ribs_y + 1)
                rib = Part.makeBox(
                    self.width - 2 * self.wall_thickness,
                    rib_thickness,
                    self.height - self.bottom_thickness - self.lip_height,
                    Vector(self.wall_thickness, pos_y - rib_thickness / 2, self.bottom_thickness)
                )
                bin_shape = bin_shape.fuse(rib)

        # Add lip
        lip = lip_outer.cut(lip_inner)
        final_shape = bin_shape.cut(lip)

        # Add magnet holes
        mag_positions = self.calculate_magnet_positions()
        for pos in mag_positions:
            mag_hole = Part.makeCylinder(3.5, self.bottom_thickness,
                                         Vector(pos[0], pos[1], 0))
            final_shape = final_shape.cut(mag_hole)

        # Create part
        Part.show(final_shape)

    def calculate_magnet_positions(self):
        """Calculate positions for magnet holes"""
        positions = []
        grid_size = 42.0

        # Calculate number of magnets needed
        num_x = max(1, int(self.width / grid_size))
        num_y = max(1, int(self.depth / grid_size))

        # If size is less than one grid, place magnet in