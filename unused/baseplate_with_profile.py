import FreeCAD as App
import Part
from FreeCAD import Vector


def create_baseplate_with_profile():
    # Create a new document
    doc = App.newDocument("BaseplateProfile")

    # Create base block (42x42x5mm)
    block_width = 42.0
    block_height = 5.0
    base_block = Part.makeBox(block_width, block_width, block_height)

    # Create profile points according to dimensions
    # Starting from bottom, going counterclockwise
    points = [
        Vector(0, 0, 0),  # Start at bottom
        Vector(2.85, 0, 0),  # Bottom right
        Vector(2.85, 0.7, 0),  # First step right
        Vector(2.85, 2.5, 0),  # Vertical to before angle
        Vector(2.85, 4.65, 0),  # Top before 45° angle
        Vector(2.60, 4.90, 0),  # After 45° angle
        Vector(2.35, 4.90, 0),  # Top right
        Vector(0, 4.90, 0),  # Top left
        Vector(0, 0, 0)  # Back to start
    ]

    # Create wire from points
    wire = Part.makePolygon(points)

    # Create face from wire
    face = Part.Face(wire)

    # Extrude the face through the entire block width
    profile = face.extrude(Vector(0, 0, block_height))

    # Center the profile in the block
    profile.translate(Vector(
        (block_width - 2.85) / 2,  # Center in X
        (block_width - 4.90) / 2,  # Center in Y
        0  # No Z translation needed
    ))

    # Cut the profile from the block
    final_shape = base_block.cut(profile)

    # Create a part object
    part = doc.addObject("Part::Feature", "Baseplate")
    part.Shape = final_shape

    # Recompute the document
    doc.recompute()

    return doc


if __name__ == "__main__":
    doc = create_baseplate_with_profile()
    # Export if needed
    doc.saveAs("baseplate_profile.FCStd")