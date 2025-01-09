#!/usr/bin/env python3
import os
import sys
import json
import math
import subprocess
from pathlib import Path


class GridfinityDrawerSystem:
    def __init__(self, drawer_width, drawer_depth, output_dir="generated_files"):
        self.drawer_width = float(drawer_width)
        self.drawer_depth = float(drawer_depth)
        # Ender 3 V2 build volume limitations
        self.max_print_width = 220
        self.max_print_depth = 220

        # Calculate bin height based on drawer depth
        # Using 75% of drawer depth as default bin height, with minimum of 42mm (standard Gridfinity)
        self.bin_height = max(42, math.floor(self.drawer_depth * 0.75))

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.baseplate_dir = self.output_dir / "baseplates"
        self.bins_dir = self.output_dir / "bins"
        self.baseplate_dir.mkdir(exist_ok=True)
        self.bins_dir.mkdir(exist_ok=True)

        # Store computed dimensions
        self.dimensions = []

    def calculate_baseplate_sections(self):
        """Calculates how to split the baseplate into printable sections"""
        grid_size = 42.0  # Standard Gridfinity size

        # Calculate total number of full grid squares
        total_squares_x = int(self.drawer_width / grid_size)
        total_squares_y = int(self.drawer_depth / grid_size)

        # Calculate maximum squares per section based on printer limits
        max_squares_x = int(self.max_print_width / grid_size)
        max_squares_y = int(self.max_print_depth / grid_size)

        # Calculate number of sections needed
        sections_x = math.ceil(total_squares_x / max_squares_x)
        sections_y = math.ceil(total_squares_y / max_squares_y)

        sections = []
        remaining_width = self.drawer_width
        remaining_depth = self.drawer_depth

        for section_y in range(sections_y):
            for section_x in range(sections_x):
                # Calculate section dimensions
                section_width = min(self.max_print_width, remaining_width)
                section_depth = min(self.max_print_depth, remaining_depth)

                # Calculate position in overall grid
                x_offset = section_x * self.max_print_width
                y_offset = section_y * self.max_print_depth

                sections.append({
                    'width': section_width,
                    'depth': section_depth,
                    'x_offset': x_offset,
                    'y_offset': y_offset,
                    'index': len(sections)
                })

                remaining_width -= self.max_print_width
            remaining_width = self.drawer_width
            remaining_depth -= self.max_print_depth

        return sections

    def generate_freecad_script(self, script_content):
        """Creates a temporary FreeCAD script file"""
        script_path = self.output_dir / "temp_script.py"
        with open(script_path, "w") as f:
            f.write(script_content)
        return script_path

    def run_freecad_headless(self, script_path):
        """Runs FreeCAD in headless mode with the given script"""
        try:
            freecad_executables = ['FreeCAD', 'freecad', 'freecadcmd']

            for executable in freecad_executables:
                try:
                    subprocess.run([executable, '-c', str(script_path)],
                                   check=True,
                                   capture_output=True,
                                   text=True)
                    return True
                except FileNotFoundError:
                    continue

            raise Exception("FreeCAD executable not found")

        except subprocess.CalledProcessError as e:
            print(f"Error running FreeCAD: {e}")
            print(f"Error output: {e.stderr}")
            return False

    def generate_baseplate_section(self, section):
        """Generates a single baseplate section"""
        script_content = f"""
import sys
sys.path.append("{self.output_dir}")
from gridfinity_baseplate import create_baseplate

# Generate baseplate section
dimensions = create_baseplate({section['width']}, {section['depth']})

# Export to STL
import Mesh
objects = FreeCAD.ActiveDocument.Objects
mesh = Mesh.Mesh()
for obj in objects:
    if hasattr(obj, "Shape"):
        mesh.addFacets(obj.Shape.tessellate(0.1))
mesh.write("{self.baseplate_dir}/baseplate_section_{section['index']}.stl")

# Save dimensions for bin generation
import json
with open("{self.output_dir}/dimensions_{section['index']}.json", "w") as f:
    json.dump(dimensions, f)
"""
        script_path = self.generate_freecad_script(script_content)
        success = self.run_freecad_headless(script_path)

        if success:
            # Load the dimensions for bin generation
            with open(self.output_dir / f"dimensions_{section['index']}.json", "r") as f:
                dimensions = json.load(f)
                self.dimensions.append({
                    'section': section,
                    'grid': dimensions
                })

        return success

    def generate_custom_bins(self):
        """Generates custom-sized bins for non-standard spaces"""
        for section_dims in self.dimensions:
            standard, non_standard = section_dims['grid']
            section = section_dims['section']

            # Generate bins for non-standard edges
            bins_to_generate = []

            if non_standard['right_edge'] > 10:
                bins_to_generate.append({
                    'width': non_standard['right_edge'],
                    'depth': standard['size'],
                    'name': f'right_edge_bin_section_{section["index"]}'
                })

            if non_standard['top_edge'] > 10:
                bins_to_generate.append({
                    'width': standard['size'],
                    'depth': non_standard['top_edge'],
                    'name': f'top_edge_bin_section_{section["index"]}'
                })

            if non_standard['right_edge'] > 10 and non_standard['top_edge'] > 10:
                bins_to_generate.append({
                    'width': non_standard['right_edge'],
                    'depth': non_standard['top_edge'],
                    'name': f'corner_bin_section_{section["index"]}'
                })

            for bin_spec in bins_to_generate:
                script_content = f"""
import sys
sys.path.append("{self.output_dir}")
from gridfinity_custom_bin import create_custom_bin

# Generate bin with calculated height
create_custom_bin({bin_spec['width']}, {bin_spec['depth']}, {self.bin_height})

# Export to STL
import Mesh
objects = FreeCAD.ActiveDocument.Objects
mesh = Mesh.Mesh()
for obj in objects:
    if hasattr(obj, "Shape"):
        mesh.addFacets(obj.Shape.tessellate(0.1))
mesh.write("{self.bins_dir}/{bin_spec['name']}.stl")
"""
                script_path = self.generate_freecad_script(script_content)
                self.run_freecad_headless(script_path)

    def generate_standard_bin(self):
        """Generates a standard-sized bin with the calculated height"""
        script_content = f"""
import sys
sys.path.append("{self.output_dir}")
from gridfinity_custom_bin import create_custom_bin

# Generate standard bin with calculated height
create_custom_bin(42, 42, {self.bin_height})

# Export to STL
import Mesh
objects = FreeCAD.ActiveDocument.Objects
mesh = Mesh.Mesh()
for obj in objects:
    if hasattr(obj, "Shape"):
        mesh.addFacets(obj.Shape.tessellate(0.1))
mesh.write("{self.bins_dir}/standard_bin.stl")
"""
        script_path = self.generate_freecad_script(script_content)
        self.run_freecad_headless(script_path)

    def generate_system(self):
        """Generates the complete drawer system"""
        print(f"Calculating bin height based on drawer depth: {self.bin_height}mm")

        # Calculate baseplate sections
        sections = self.calculate_baseplate_sections()
        print(f"Drawer will be split into {len(sections)} baseplate sections")

        # Generate each baseplate section
        for section in sections:
            print(f"Generating baseplate section {section['index'] + 1}/{len(sections)}...")
            if self.generate_baseplate_section(section):
                print(f"Section {section['index'] + 1} generated successfully")
            else:
                print(f"Failed to generate section {section['index'] + 1}")

        # Generate bins
        print("Generating standard bin...")
        self.generate_standard_bin()

        print("Generating custom bins for non-standard spaces...")
        self.generate_custom_bins()

        # Save system information
        system_info = {
            'drawer_dimensions': {
                'width': self.drawer_width,
                'depth': self.drawer_depth
            },
            'bin_height': self.bin_height,
            'baseplate_sections': sections,
            'section_dimensions': self.dimensions
        }

        with open(self.output_dir / "system_info.json", "w") as f:
            json.dump(system_info, f, indent=2)

        print(f"\nAll files generated in: {self.output_dir}")
        print(f"Assembly instructions saved in system_info.json")
        return True


def main():
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