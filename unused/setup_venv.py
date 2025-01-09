#!/usr/bin/env python3
import os
import site
import sys
from pathlib import Path


def setup_freecad_venv():
    """Setup FreeCAD in the current virtual environment"""
    venv_site_packages = site.getsitepackages()[0]
    print(f"Virtual environment site-packages: {venv_site_packages}")

    # FreeCAD paths to add
    freecad_paths = [
        '/usr/lib/freecad-python3/lib',
        '/usr/lib/freecad/lib',
        '/usr/lib/python3/dist-packages',
        '/usr/lib/python3.12/dist-packages'  # Adjust version if needed
    ]

    # Create .pth file
    pth_file = Path(venv_site_packages) / 'freecad.pth'

    print("\nChecking FreeCAD paths:")
    existing_paths = []
    for path in freecad_paths:
        if os.path.exists(path):
            print(f"✓ Found: {path}")
            existing_paths.append(path)
        else:
            print(f"✗ Not found: {path}")

    if existing_paths:
        print(f"\nCreating {pth_file}")
        with open(pth_file, 'w') as f:
            for path in existing_paths:
                f.write(path + '\n')
        print("FreeCAD paths added to virtual environment")
    else:
        print("\nError: No valid FreeCAD paths found!")
        return False

    # Try importing FreeCAD
    print("\nTesting FreeCAD import...")
    try:
        import FreeCAD
        print(f"Success! FreeCAD Version: {FreeCAD.Version()[0]}")
        return True
    except ImportError as e:
        print(f"Error importing FreeCAD: {e}")
        return False


if __name__ == "__main__":
    setup_freecad_venv()