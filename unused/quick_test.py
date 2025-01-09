#!/usr/bin/env python3
import os
import sys

# Add the paths explicitly in the script as well
freecad_paths = [
    '/usr/lib/freecad-python3/lib',
    '/usr/lib/freecad/lib',
    '/usr/lib/freecad/Mod',
    '/usr/share/freecad/Mod',
    '/usr/lib/python3/dist-packages'
]

for path in freecad_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

# Set LD_LIBRARY_PATH
os.environ['LD_LIBRARY_PATH'] = '/usr/lib/freecad-python3/lib'

print("Testing imports...")

try:
    import FreeCAD
    print("✓ FreeCAD imported successfully")
    print(f"  Version: {FreeCAD.Version()}")
except ImportError as e:
    print(f"✗ Failed to import FreeCAD: {e}")

try:
    import Draft
    print("✓ Draft module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Draft: {e}")
    print("\nSearching for Draft.py...")
    for path in sys.path:
        draft_path = os.path.join(path, 'Draft.py')
        if os.path.exists(draft_path):
            print(f"Found Draft.py at: {draft_path}")
        draft_path = os.path.join(path, 'Draft', '__init__.py')
        if os.path.exists(draft_path):
            print(f"Found Draft/__init__.py at: {draft_path}")