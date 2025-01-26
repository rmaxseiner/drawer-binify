#!/usr/bin/env python3
import json
import os
from pathlib import Path


class ProjectDocumentationGenerator:
    def __init__(self, project_root="/home/ron-maxseiner/PycharmProjects/drawerfinity"):
        self.project_root = Path(project_root)
        self.included_dirs = {'backend', 'frontend', 'docker', 'scripts'}

        # Files/directories to exclude
        self.exclude = {
            '.git', '.idea', '__pycache__', '.venv', 'venv',
            'node_modules', 'output', 'generated_files', '.gitignore',
            '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd',
            '*.so', '*.stl', '*.FCStd', '*.FCStd1', 'test_outputs',
            'tests', 'unused', 'docs', 'package-lock.json', '*.svg',
            'file_reference.json'
        }

    def should_process(self, path):
        """Check if a file/directory should be processed"""
        path = Path(path)
        rel_path = path.relative_to(self.project_root)

        # Check if any parent directory is in included_dirs
        if not any(part in self.included_dirs for part in rel_path.parts):
            return False

        return not any(
            part.startswith('.') or part in self.exclude or
            any(part.endswith(ext[1:]) for ext in self.exclude if ext.startswith('*.'))
            for part in rel_path.parts
        )

    def read_file_content(self, file_path):
        """Read and return file content, with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def create_file_reference(self):
        """Create JSON file reference document"""
        documents = []

        for included_dir in self.included_dirs:
            dir_path = self.project_root / included_dir
            if not dir_path.exists():
                continue

            for source_dir, dirs, files in os.walk(dir_path):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if self.should_process(Path(source_dir) / d)]

                # Sort files for consistent ordering
                files.sort()

                for file in files:
                    source_path = Path(source_dir) / file
                    if not self.should_process(source_path):
                        continue

                    rel_path = source_path.relative_to(self.project_root)

                    document = {
                        "source": str(rel_path),
                        "document_content": self.read_file_content(source_path)
                    }
                    documents.append(document)
                    print(f"Processed: {rel_path}")

        # Write to JSON file
        output_path = self.project_root / "scripts" / "file_reference.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"documents": documents}, f, indent=2)

        print(f"\nCreated file reference at: {output_path}")

    def generate_documentation(self):
        """Run the documentation generation process"""
        print("Starting project documentation generation...")
        self.create_file_reference()
        print("\nDocumentation generation complete!")


if __name__ == "__main__":
    generator = ProjectDocumentationGenerator()
    generator.generate_documentation()