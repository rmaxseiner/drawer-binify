import sys
import os


def setup_freecad():
    freecad_paths = [
        "/usr/lib/freecad-python3/lib",
        "/usr/lib/freecad/lib",
        "/usr/lib/freecad/Mod",
        "/usr/share/freecad/Mod"
    ]

    for path in freecad_paths:
        if path not in sys.path and os.path.exists(path):
            sys.path.append(path)

    try:
        import FreeCAD
        return FreeCAD
    except ImportError as e:
        raise ImportError(f"Failed to import FreeCAD: {str(e)}")