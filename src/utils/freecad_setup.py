import os
import sys


def setup_freecad_path():
    """
    Set up the Python path for FreeCAD libraries
    Returns True if successful, False otherwise
    """
    # Add FreeCAD Python paths
    freecad_paths = [
        '/usr/lib/freecad-python3/lib',
        '/usr/lib/freecad/lib',
        '/usr/lib/python3/dist-packages',
        '/usr/lib/python3.12/dist-packages',
        '/usr/lib/freecad/Mod',  # Added Mod directory
        '/usr/share/freecad/Mod'  # Added shared Mod directory
    ]

    # Add paths to Python path if they exist
    for path in freecad_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)

    try:
        # Add lib directory to LD_LIBRARY_PATH
        os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([
            '/usr/lib/freecad-python3/lib',
            os.environ.get('LD_LIBRARY_PATH', '')
        ])

        import FreeCAD
        print(f"Successfully found FreeCAD {FreeCAD.Version()[0]}")

        # Verify Draft module import
        import Draft
        return True

    except ImportError as e:
        print(f"Error importing FreeCAD: {e}")
        print("\nCurrent Python path:")
        for p in sys.path:
            print(f"  {p}")
        return False


if __name__ == "__main__":
    setup_freecad_path()