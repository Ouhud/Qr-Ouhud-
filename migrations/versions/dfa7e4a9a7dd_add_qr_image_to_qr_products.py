"""add qr_image to qr_products

Revision ID: dfa7e4a9a7dd
Revises: ddf59cd8f80f
Create Date: 2025-11-08 18:13:12.051424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfa7e4a9a7dd'
down_revision: Union[str, Sequence[str], None] = 'ddf59cd8f80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
