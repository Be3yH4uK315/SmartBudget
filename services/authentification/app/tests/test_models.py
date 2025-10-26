import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Session
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
import sqlalchemy as sa

@pytest.mark.asyncio
async def test_user_creation(test_db: AsyncSession):
    user = User(
        id=uuid4(),
        role=0,
        email="test@example.com",
        password_hash="hashed_pw",
        name="Test User",
        country="Test Country",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    assert user.id is not None
    assert user.role == 0
    assert user.email == "test@example.com"

    # Test index/unique
    duplicate_user = User(
        id=uuid4(),
        role=1,
        email="test@example.com",
        password_hash="other",
        name="Duplicate",
        country="Other",
        is_active=False
    )
    test_db.add(duplicate_user)
    with pytest.raises(sa.exc.IntegrityError):
        await test_db.commit()

@pytest.mark.asyncio
async def test_session_creation(test_db: AsyncSession):
    user_id = uuid4()
    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="test_agent",
        device_name="test_device",
        ip="127.0.0.1",
        location="Test Location",
        revoked=False,
        refresh_fingerprint="fingerprint_hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    assert session.user_id == user_id
    assert session.revoked is False

    query = select(Session).where(Session.user_id == user_id, Session.expires_at > datetime.now(timezone.utc))
    result = await test_db.execute(query)
    assert result.scalar() == session