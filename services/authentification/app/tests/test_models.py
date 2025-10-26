import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from uuid import uuid4
from datetime import datetime

@pytest.mark.asyncio
async def test_user_creation(db_session: AsyncSession):
    user = User(
        id=uuid4(),
        role_id=uuid4(),
        email="test@example.com",
        password_hash="hashed",
        name="Test User",
        country="Test Country",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
    assert user.email == "test@example.com"