"""update_baseplate_and_generated_files_models

Revision ID: 2a364316e95a
Revises: 231981aa7eff
Create Date: 2025-03-18 21:49:01.834644

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a364316e95a'
down_revision = '231981aa7eff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add drawer_id to baseplates table
    op.add_column('baseplates', sa.Column('drawer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'baseplates', 'drawers', ['drawer_id'], ['id'])

    # Remove bin_id and baseplate_id from generated_files
    op.drop_constraint('generated_files_bin_id_fkey', 'generated_files', type_='foreignkey')
    op.drop_constraint('generated_files_baseplate_id_fkey', 'generated_files', type_='foreignkey')
    op.drop_column('generated_files', 'bin_id')
    op.drop_column('generated_files', 'baseplate_id')


def downgrade() -> None:
    # Re-add bin_id and baseplate_id to generated_files
    op.add_column('generated_files', sa.Column('bin_id', sa.Integer(), nullable=True))
    op.add_column('generated_files', sa.Column('baseplate_id', sa.Integer(), nullable=True))
    op.create_foreign_key('generated_files_bin_id_fkey', 'generated_files', 'bins', ['bin_id'], ['id'])
    op.create_foreign_key('generated_files_baseplate_id_fkey', 'generated_files', 'baseplates', ['baseplate_id'],
                          ['id'])

    # Remove drawer_id from baseplates
    op.drop_constraint(None, 'baseplates', type_='foreignkey')
    op.drop_column('baseplates', 'drawer_id')