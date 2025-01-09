#!/usr/bin/env python3
import os
import sys
import site


def fix_draft_import():
    """Add FreeCAD's Mod directory to Python path"""
    freecad_mod_paths = [
        '/usr/lib/freecad/Mod',
        '/usr/share/freecad/Mod',
        '/usr/share/freecad-python3/Mod'
    ]

    print("Checking FreeCAD Mod paths:")
    for path in freecad_mod_paths:
        if os.path.exists(path):
            print(f"Adding: {path}")
            sys.path.append(path)
        else:
            print(f"Not found: {path}")

    try:
        import Draft
        print("Successfully imported Draft module!")
        return True
    except ImportError as e:
        print(f"Error importing Draft: {e}")
        print("\nCurrent sys.path:")
        for p in sys.path:
            print(f"  {p}")
        return False


if __name__ == "__main__":
    fix_draft_import()