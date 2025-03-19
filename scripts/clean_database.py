#!/usr/bin/env python3
"""
Script to clean drawers, bins, baseplates, models and generated files from the database.
This will delete ALL data from these tables, so use with caution!
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Define default database connection string
DEFAULT_DB_URL = "postgresql://gridfinity:development@localhost/gridfinity_db"


def parse_arguments():
    parser = argparse.ArgumentParser(description='Clean database tables for Drawerfinity project.')
    parser.add_argument('--database-url', type=str, default=DEFAULT_DB_URL,
                        help=f'Database connection URL (default: {DEFAULT_DB_URL})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')
    parser.add_argument('--delete-files', action='store_true',
                        help='Also delete physical model files on disk')
    parser.add_argument('--output-dir', type=str,
                        default="/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output",
                        help='Path to model output directory to clean')
    return parser.parse_args()


def clean_database(db_url, dry_run=False, delete_files=False, output_dir=None):
    """Clean all relevant tables from the database."""
    print(f"Connecting to database: {db_url}")

    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get a count of rows in each table before deletion
        tables = ["generated_files", "bins", "baseplates", "drawers", "models"]
        counts = {}

        for table in tables:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            counts[table] = count
            print(f"Table {table}: {count} rows")

        if dry_run:
            print("\nDRY RUN: No changes will be made to the database or files")
            return

        # Get model file paths if we need to delete files
        file_paths = []
        if delete_files and output_dir:
            result = session.execute(text("SELECT file_path FROM generated_files"))
            file_paths = [row[0] for row in result]
            print(f"Found {len(file_paths)} file paths in database")

        # Delete from tables in the correct order to respect foreign key constraints
        print("\nDeleting data from tables...")

        # Now delete from tables in the proper order
        session.execute(text("DELETE FROM generated_files"))
        print(f"Deleted {counts['generated_files']} rows from generated_files table")

        session.execute(text("DELETE FROM bins"))
        print(f"Deleted {counts['bins']} rows from bins table")

        session.execute(text("DELETE FROM baseplates"))
        print(f"Deleted {counts['baseplates']} rows from baseplates table")

        session.execute(text("DELETE FROM drawers"))
        print(f"Deleted {counts['drawers']} rows from drawers table")

        session.execute(text("DELETE FROM models"))
        print(f"Deleted {counts['models']} rows from models table")

        # Reset all sequences/auto-increment counters
        print("\nResetting auto-increment sequences...")
        for table in tables:
            try:
                session.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1"))
                print(f"Reset sequence for {table}_id_seq")
            except Exception as e:
                print(f"Failed to reset sequence for {table}: {e}")

        # Commit the transaction
        session.commit()
        print("Database clean complete!")

        # Delete physical files if requested
        if delete_files and output_dir:
            delete_physical_files(output_dir, file_paths)

    except Exception as e:
        session.rollback()
        print(f"Error cleaning database: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def delete_physical_files(output_dir, file_paths):
    """Delete physical model files from disk."""
    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"Output directory {output_dir} does not exist, skipping file deletion")
        return

    print(f"\nCleaning model output directory: {output_dir}...")

    # Method 1: Delete specific files from database
    print("Deleting files listed in database...")
    deleted_count = 0
    error_count = 0

    for rel_path in file_paths:
        try:
            if rel_path:
                # Handle both absolute and relative paths
                if rel_path.startswith('/'):
                    # This is an absolute path
                    file_path = Path(rel_path)
                else:
                    # This is a relative path
                    file_path = output_path / rel_path

                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    if deleted_count % 100 == 0:  # Only print periodically for large numbers
                        print(f"Deleted {deleted_count} files...")
                else:
                    # Uncomment if you want to see missing files
                    # print(f"File not found: {file_path}")
                    pass
        except Exception as e:
            print(f"Error deleting file {rel_path}: {str(e)}")
            error_count += 1

    # Method 2: Clean the entire output directory
    print("\nPerforming complete directory cleanup...")
    removed_files = 0
    removed_dirs = 0

    # Create a list of standard directories to keep
    # Add any folders you want to preserve here
    dirs_to_preserve = []

    # Step 1: Loop through all first-level directories and files
    for item in output_path.iterdir():
        # Skip preserved directories
        if item.name in dirs_to_preserve:
            print(f"Preserving directory: {item.name}")
            continue

        try:
            if item.is_file():
                # Delete files directly in the output directory
                item.unlink()
                removed_files += 1
                print(f"Removed file: {item}")
            elif item.is_dir():
                # Recursively delete all contents first, then the directory
                file_count = 0
                for file_path in item.glob('**/*'):
                    if file_path.is_file():
                        file_path.unlink()
                        file_count += 1

                # Now remove all empty directories
                for dir_path in sorted([p for p in item.glob('**/*') if p.is_dir()], reverse=True):
                    try:
                        dir_path.rmdir()
                    except OSError:
                        # Directory might not be empty yet, which is fine
                        pass

                # Finally remove the top directory
                try:
                    item.rmdir()
                    removed_dirs += 1
                    print(f"Removed directory: {item} (containing {file_count} files)")
                except OSError as e:
                    print(f"Could not remove directory {item}: {e}")
        except Exception as e:
            print(f"Error processing {item}: {e}")

    print(f"\nDirectory cleanup complete:")
    print(f"- {deleted_count} specific files deleted from database records")
    print(f"- {removed_files} additional files and {removed_dirs} directories removed")
    print(f"- {error_count} errors encountered")

    # One more pass to clean up any remaining empty directories
    empty_dirs = 0
    for root, dirs, files in os.walk(output_path, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                # Check if directory is empty
                if dir_path.exists() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    empty_dirs += 1
            except Exception as e:
                print(f"Error removing directory {dir_path}: {str(e)}")

    if empty_dirs > 0:
        print(f"Removed {empty_dirs} empty directories")


def confirm_action():
    """Ask for confirmation before proceeding with potentially destructive action."""
    print("\n⚠️  WARNING ⚠️")
    print("This will delete ALL data from the database and potentially ALL files from the output directory.")
    print("This action CANNOT be undone!")

    response = input("\nAre you sure you want to proceed? (y/N): ").strip().lower()

    return response == 'y' or response == 'yes'


if __name__ == "__main__":
    args = parse_arguments()

    # Ask for confirmation unless in dry run mode
    if args.dry_run or confirm_action():
        clean_database(args.database_url, args.dry_run, args.delete_files, args.output_dir)
    else:
        print("Operation cancelled.")
        sys.exit(0)