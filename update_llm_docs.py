#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


class LLMDocumentationUpdater:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.upload_dir = self.project_root / "upload"

        # Files/directories to exclude from copying
        self.exclude = {
            '.git', '.idea', '__pycache__', '.venv', 'venv',
            'output', 'generated_files', '.gitignore',
            '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.stl', '*.FCStd', '*.FCStd1'
        }

    def clean_directory(self):
        """Remove and recreate the upload directory"""
        if self.upload_dir.exists():
            shutil.rmtree(self.upload_dir)
        self.upload_dir.mkdir(parents=True)

    def should_copy(self, path):
        """Check if a file/directory should be copied"""
        path = Path(path)
        return not any(
            part.startswith('.') or part in self.exclude or
            any(part.endswith(ext[1:]) for ext in self.exclude if ext.startswith('*.'))
            for part in path.parts
        )

    def copy_project_files(self):
        """Copy relevant project files to upload directory"""
        for source_dir, dirs, files in os.walk(self.project_root):
            # Skip the upload directory itself
            if Path(source_dir) == self.upload_dir:
                continue

            # Filter directories
            dirs[:] = [d for d in dirs if self.should_copy(d)]

            for file in files:
                source_path = Path(source_dir) / file
                if self.should_copy(source_path):
                    # Calculate relative path from project root
                    rel_path = source_path.relative_to(self.project_root)
                    dest_path = self.upload_dir / rel_path

                    # Create parent directories if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy the file
                    shutil.copy2(source_path, dest_path)
                    print(f"Copied: {rel_path}")

    def create_file_reference(self):
        """Create XML file reference document for LLM consumption"""
        root = ET.Element("documents")

        for source_dir, dirs, files in os.walk(self.upload_dir):
            # Sort files for consistent ordering
            files.sort()

            for file in files:
                if file == 'file_reference.xml':
                    continue

                source_path = Path(source_dir) / file
                rel_path = source_path.relative_to(self.upload_dir)

                document = ET.SubElement(root, "document")

                # Add source path
                source = ET.SubElement(document, "source")
                source.text = str(rel_path)

                # Add file content
                content = ET.SubElement(document, "document_content")
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content.text = f.read()
                except Exception as e:
                    print(f"Warning: Could not read {rel_path}: {e}")
                    content.text = f"Error reading file: {e}"

        # Create pretty-printed XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

        # Write to file
        reference_path = self.upload_dir / "file_reference.xml"
        with open(reference_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        print(f"\nCreated file reference at: {reference_path}")

    def update_all(self):
        """Run the complete update process"""
        print("Starting LLM documentation update...")
        self.clean_directory()
        self.copy_project_files()
        self.create_file_reference()
        print("\nLLM documentation update complete!")


if __name__ == "__main__":
    updater = LLMDocumentationUpdater()
    updater.update_all()