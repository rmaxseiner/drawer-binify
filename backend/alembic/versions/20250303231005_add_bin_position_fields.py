"""add bin position fields

Revision ID: 20250303231005
Revises: f8f2e4b8f3b5
Create Date: 2025-03-03 23:10:05.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250303231005'
down_revision: Union[str, None] = 'f8f2e4b8f3b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add x_position and y_position columns to bins table
    op.add_column('bins', sa.Column('x_position', sa.Float(), nullable=True))
    op.add_column('bins', sa.Column('y_position', sa.Float(), nullable=True))
    
    # Make name column nullable for existing bins
    op.alter_column('bins', 'name', nullable=True)


def downgrade() -> None:
    # Remove x_position and y_position columns from bins table
    op.drop_column('bins', 'x_position')
    op.drop_column('bins', 'y_position')
    
    # Make name column non-nullable again
    op.alter_column('bins', 'name', nullable=False)