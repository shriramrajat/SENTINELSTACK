"""add_user_tier

Revision ID: abcd1234abcd
Revises: 951dc6153326
Create Date: 2026-07-22 17:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abcd1234abcd'
down_revision: Union[str, None] = '951dc6153326'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tier column with a default of 'free'
    op.add_column('users', sa.Column('tier', sa.String(), server_default='free', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'tier')
