import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import sqlalchemy as sa
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from app.models import User, Session
from app.utils import hash_password

@pytest.mark.asyncio
async def test_user_creation_success(test_db: AsyncSession):
    user_id = uuid4()
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        role=0,
        email="test_unique@example.com",
        password_hash=hash_password("strongpassword123"),
        name="Test User Full Name",
        country="Russia",
        is_active=True,
        last_login=None,
        created_at=created_at,
        updated_at=updated_at
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    assert user.id == user_id
    assert user.role == 0
    assert user.email == "test_unique@example.com"
    assert user.name == "Test User Full Name"
    assert user.country == "Russia"
    assert user.is_active is True
    assert user.created_at.replace(tzinfo=None) == created_at.replace(tzinfo=None)  # Tz-agnostic
    assert user.updated_at.replace(tzinfo=None) == updated_at.replace(tzinfo=None)

@pytest.mark.asyncio
async def test_user_unique_email_constraint(test_db: AsyncSession):
    user1 = User(
        id=uuid4(),
        role=0,
        email="duplicate@example.com",
        password_hash=hash_password("pass1"),
        name="User1",
        country="Russia",
        is_active=True
    )
    test_db.add(user1)
    await test_db.commit()

    user2 = User(
        id=uuid4(),
        role=1,
        email="duplicate@example.com",
        password_hash=hash_password("pass2"),
        name="User2",
        country="USA",
        is_active=False
    )
    test_db.add(user2)
    with pytest.raises(IntegrityError):
        await test_db.commit()

@pytest.mark.asyncio
async def test_session_creation_success(test_db: AsyncSession):
    user_id = uuid4()
    session_id = uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    created_at = datetime.now(timezone.utc)
    session = Session(
        id=session_id,
        user_id=user_id,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        device_name="Windows Desktop",
        ip="192.168.1.1",
        location="Moscow, Russia",
        revoked=False,
        refresh_fingerprint="hashed_fingerprint_123",
        expires_at=expires_at,
        created_at=created_at
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    assert session.id == session_id
    assert session.user_id == user_id
    assert session.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    assert session.device_name == "Windows Desktop"
    assert session.ip == "192.168.1.1"
    assert session.location == "Moscow, Russia"
    assert session.revoked is False
    assert session.refresh_fingerprint == "hashed_fingerprint_123"
    assert session.expires_at.replace(tzinfo=None) == expires_at.replace(tzinfo=None)  # Tz-agnostic
    assert session.created_at.replace(tzinfo=None) == created_at.replace(tzinfo=None)

@pytest.mark.asyncio
async def test_session_query_by_user_id_and_expiry(test_db: AsyncSession):
    user_id = uuid4()
    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="test",
        device_name="test",
        ip="127.0.0.1",
        location="test",
        revoked=False,
        refresh_fingerprint="test",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()

    query = select(Session).where(
        Session.user_id == user_id,
        Session.expires_at > datetime.now(timezone.utc),
        Session.revoked == sa.false()
    )
    result = await test_db.execute(query)
    fetched_session = result.scalar_one_or_none()
    assert fetched_session is not None
    assert fetched_session.user_id == user_id

@pytest.mark.asyncio
async def test_session_revoked_constraint(test_db: AsyncSession):
    user_id = uuid4()
    session = Session(
        id=uuid4(),
        user_id=user_id,
        user_agent="test",
        device_name="test",
        ip="127.0.0.1",
        location="test",
        revoked=False,
        refresh_fingerprint="test",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    assert session.revoked is False

    session.revoked = True
    await test_db.commit()
    await test_db.refresh(session)
    assert session.revoked is True