#!/usr/bin/env python3
import sys

from unused.src.utils.freecad_setup import setup_freecad_path
from gridfinity_generator import GridfinityDrawerSystem


def main():
    # First, set up FreeCAD path
    if not setup_freecad_path():
        print("Failed to set up FreeCAD. Please check your installation.")
        return

    # Now proceed with the drawer system generation
    if len(sys.argv) != 3:
        print("Usage: python generate_drawer_system.py <drawer_width> <drawer_depth>")
        print("All dimensions should be in millimeters")
        sys.exit(1)

    drawer_width = float(sys.argv[1])
    drawer_depth = float(sys.argv[2])

    system = GridfinityDrawerSystem(drawer_width, drawer_depth)
    system.generate_system()


if __name__ == "__main__":
    main()