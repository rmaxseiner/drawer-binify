"""add_user_settings

Revision ID: bdbe1aa5e6c7
Revises: 20250303231005
Create Date: 2025-03-16 10:57:12.848508

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdbe1aa5e6c7'
down_revision = '20250303231005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The user_settings table already exists, so we skip its creation
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_settings_id'), table_name='user_settings')
    op.drop_table('user_settings')
    # ### end Alembic commands ###