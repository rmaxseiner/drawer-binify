import sys
import subprocess


def test_freecad_python():
    """Test if FreeCAD Python modules are available"""
    try:
        # Try to find where FreeCAD is installed
        which_result = subprocess.run(['which', 'freecad'],
                                      capture_output=True,
                                      text=True)
        print(f"FreeCAD binary location: {which_result.stdout.strip()}")

        # Look for FreeCAD Python files
        dpkg_result = subprocess.run(['dpkg', '-L', 'freecad'],
                                     capture_output=True,
                                     text=True)

        print("\nPython-related FreeCAD files:")
        for line in dpkg_result.stdout.split('\n'):
            if 'python' in line.lower():
                print(line)
                # Add these paths to Python path
                if 'dist-packages' in line or 'site-packages' in line:
                    sys.path.append(line)

        # Try to import FreeCAD
        print("\nTrying to import FreeCAD...")
        import FreeCAD
        print(f"Success! FreeCAD Version: {FreeCAD.Version()[0]}")
        return True

    except ImportError as e:
        print(f"\nError importing FreeCAD: {e}")
        print("\nYou may need to install additional Python packages:")
        print("sudo apt install python3-freecad")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return False


if __name__ == "__main__":
    test_freecad_python()