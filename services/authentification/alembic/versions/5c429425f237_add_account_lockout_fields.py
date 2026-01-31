"""Add account lockout fields to users table

Revision ID: 9c463471c618
Revises: 5b429625f237
Create Date: 2025-01-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9c463471c618"
down_revision: Union[str, None] = "5b429625f237"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем флаг блокировки аккаунта
    op.add_column('users', sa.Column('is_locked', sa.Boolean(), nullable=False))
    
    # Добавляем время окончания блокировки
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    
    # Добавляем индекс для быстрого поиска заблокированных аккаунтов
    op.create_index('ix_users_is_locked', 'users', ['is_locked'])


def downgrade() -> None:
    # Удаляем индекс
    op.drop_index('ix_users_is_locked', table_name='users')
    
    # Удаляем столбцы
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
