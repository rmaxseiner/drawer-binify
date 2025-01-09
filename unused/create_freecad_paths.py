#!/usr/bin/env python3
import site
import os
from pathlib import Path


def create_pth_file():
    # Get the site-packages directory of the current virtual environment
    site_packages = site.getsitepackages()[0]

    # FreeCAD paths to add
    freecad_paths = [
        '/usr/lib/freecad-python3/lib',
        '/usr/lib/freecad/lib',
        '/usr/lib/freecad/Mod',
        '/usr/share/freecad/Mod',
        '/usr/lib/python3/dist-packages',
        '/usr/lib/python3.12/dist-packages'
    ]

    # Create freecad.pth file
    pth_file = Path(site_packages) / 'freecad.pth'

    print(f"Creating {pth_file}")
    with open(pth_file, 'w') as f:
        for path in freecad_paths:
            if os.path.exists(path):
                print(f"Adding path: {path}")
                f.write(path + '\n')
            else:
                print(f"Path not found: {path}")


if __name__ == "__main__":
    create_pth_file()