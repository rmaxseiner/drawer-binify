"""convert_to_relative_paths

Revision ID: f8f2e4b8f3b5
Revises: 85e507dd8a08
Create Date: 2025-02-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pathlib import Path

# revision identifiers, used by Alembic
revision = 'f8f2e4b8f3b5'
down_revision = '85e507dd8a08'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Get connection
    conn = op.get_bind()

    # Select all generated files
    files = conn.execute(
        sa.text('SELECT id, file_path FROM generated_files')
    ).fetchall()

    # Update each file path to be relative
    for file_id, file_path in files:
        if file_path and file_path.startswith('/'):
            # Convert absolute path to relative
            relative_path = Path(file_path).name
            conn.execute(
                sa.text('UPDATE generated_files SET file_path = :path WHERE id = :id'),
                {"path": relative_path, "id": file_id}
            )

def downgrade() -> None:
    # Add downgrade logic if needed
    pass