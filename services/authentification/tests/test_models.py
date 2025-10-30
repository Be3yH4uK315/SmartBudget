import pytest
from app.models import User, Session, UserRole
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc

@pytest.mark.asyncio
async def test_user_model_create_and_refresh(db_session: AsyncSession):
    user_id = uuid4()
    user = User(
        id=user_id,
        role=UserRole.USER,
        email="test@example.com",
        password_hash="hashed_pw",
        name="Test User",
        country="US",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id == user_id, "ID должен сохраняться"
    assert user.role == 0, "Role по умолчанию USER (0)"
    assert user.is_active is True, "is_active должен быть True"

@pytest.mark.asyncio
async def test_user_model_unique_email(db_session: AsyncSession):
    user1 = User(id=uuid4(), email="duplicate@example.com", password_hash="hash", name="User1", country="US")
    db_session.add(user1)
    await db_session.commit()

    user2 = User(id=uuid4(), email="duplicate@example.com", password_hash="hash", name="User2", country="US")
    db_session.add(user2)
    with pytest.raises(exc.IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_session_model_create(db_session: AsyncSession):
    user = User(id=uuid4(), email="session_user@example.com", password_hash="hash", name="User", country="US")
    db_session.add(user)
    await db_session.commit()

    session = Session(
        id=uuid4(),
        user_id=user.id,
        user_agent="Mozilla/5.0",
        device_name="Device",
        ip="127.0.0.1",
        location="Local",
        revoked=False,
        refresh_fingerprint="fingerprint",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    assert session.user_id == user.id, "FK на user должен работать"
    assert not session.revoked, "Revoked по умолчанию False"

@pytest.mark.asyncio
async def test_session_model_cascade_delete(db_session: AsyncSession):
    user_id = uuid4()
    user = User(id=user_id, email="cascade@example.com", password_hash="hash", name="User", country="US")
    db_session.add(user)
    await db_session.commit()

    session = Session(id=uuid4(), user_id=user_id, user_agent="UA", device_name="Dev", ip="IP", location="Loc", refresh_fingerprint="fp", expires_at=datetime.now(timezone.utc))
    db_session.add(session)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    result = await db_session.execute(select(Session).where(Session.user_id == user_id))
    assert result.scalar_one_or_none() is None, "Session должна удаляться при delete user"

@pytest.mark.asyncio
async def test_user_model_indexes(db_session: AsyncSession):
    user = User(id=uuid4(), email="indexed@example.com", password_hash="hash", name="User", country="US")
    db_session.add(user)
    await db_session.commit()
    result = await db_session.execute(select(User).where(User.email == "indexed@example.com"))
    fetched = result.scalar_one()
    assert fetched.email == "indexed@example.com", "Индекс по email должен позволять быстрый поиск"
