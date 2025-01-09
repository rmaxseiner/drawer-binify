#!/usr/bin/env python3
import sys
import os

# Set LD_LIBRARY_PATH
freecad_lib = '/usr/lib/freecad-python3/lib'
if 'LD_LIBRARY_PATH' in os.environ:
    os.environ['LD_LIBRARY_PATH'] = f"{freecad_lib}:{os.environ['LD_LIBRARY_PATH']}"
else:
    os.environ['LD_LIBRARY_PATH'] = freecad_lib

def print_paths():
    print("Python path:")
    for path in sys.path:
        print(f"  {path}")

print("Current environment:")
print(f"Python: {sys.version}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
print("\nChecking imports...")

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
    print("\nAttempting to locate Draft.py...")
    for path in sys.path:
        draft_path = os.path.join(path, 'Draft.py')
        if os.path.exists(draft_path):
            print(f"Found Draft.py at: {draft_path}")
    print("\nCurrent Python path:")
    print_paths()