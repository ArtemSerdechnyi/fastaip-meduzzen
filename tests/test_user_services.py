import pytest
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import PasswordManager, UserService
from app.db.models import User
from app.schemas.user import (
    UserSignUpRequestScheme,
    UserUpdateRequestScheme,
    UserDetailResponseScheme,
)

user1_scheme = UserSignUpRequestScheme(
    email="test@example.com",
    username="testuser",
    password="password123",
    password_confirm="password123",
)
user_update_scheme = UserUpdateRequestScheme(
    email="new@example.com", username="updatedname", last_name="lastname"
)
user_for_delete_scheme = UserSignUpRequestScheme(
    email="testdel@example.com",
    username="tdeluser",
    password="password123",
    password_confirm="password123",
)
user_list: list[UserSignUpRequestScheme] = [
    UserSignUpRequestScheme(
        email="test1@example.com",
        username="test1",
        password="password123",
        password_confirm="password123",
    ),
    UserSignUpRequestScheme(
        email="test2@example.com",
        username="test2",
        password="password123",
        password_confirm="password123",
    ),
    UserSignUpRequestScheme(
        email="test3@example.com",
        username="test3",
        password="password123",
        password_confirm="password123",
    ),
    UserSignUpRequestScheme(
        email="test4@example.com",
        username="test4",
        password="password123",
        password_confirm="password123",
    ),
    UserSignUpRequestScheme(
        email="test5@example.com",
        username="test5",
        password="password123",
        password_confirm="password123",
    ),
    UserSignUpRequestScheme(
        email="test6@example.com",
        username="test6",
        password="password123",
        password_confirm="password123",
    ),
]


@pytest.fixture(scope="function")
async def service(session: AsyncSession) -> UserService:
    async with UserService(session=session) as service:
        yield service


async def get_user_by_username(username: str, session: AsyncSession) -> User:
    query = select(User).where(User.username == username)
    result = await session.execute(query)
    await session.flush()
    return result.scalars().one()


async def get_user_by_id(user_id: str, session: AsyncSession) -> User:
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    await session.flush()
    return result.scalars().one()


# Test PasswordManager


def test_password_manager():
    password = "password123"
    manager = PasswordManager(password)
    hashed = manager.hash
    assert hashed != password
    assert manager.verify_password(password, hashed) is True


# Test UserService


async def test_create_user(service: UserService):
    scheme = user1_scheme
    with pytest.raises(NoResultFound):
        await get_user_by_username(scheme.username, service.session)
    await service.create_user(scheme)
    await service.session.flush()
    user = await get_user_by_username(scheme.username, service.session)
    assert isinstance(user, User)
    assert user.email == scheme.email
    assert user.username == scheme.username
    assert user.is_active is True
    assert user.hashed_password != scheme.password
    assert user.hashed_password != PasswordManager(scheme.password).hash


async def test_get_user_by_id(service: UserService):
    scheme = user1_scheme
    user = await get_user_by_username(scheme.username, service.session)
    user_id = user.user_id
    user_by_id = await service.get_user_by_id(user_id)
    assert isinstance(user_by_id, UserDetailResponseScheme)
    assert user_by_id.user_id == user_id
    assert user_by_id.email == scheme.email
    assert user_by_id.username == scheme.username

    wrong_id = uuid4()
    with pytest.raises(NoResultFound):
        await service.get_user_by_id(wrong_id)


async def test_update_user(service: UserService):
    scheme = user1_scheme
    update_scheme = user_update_scheme
    user = await get_user_by_username(scheme.username, service.session)
    assert user.email != update_scheme.email
    assert user.username != update_scheme.username
    assert user.last_name != update_scheme.last_name

    await service.update_user(user.user_id, update_scheme)
    await service.session.execute(service.queries.pop())
    await service.session.flush()
    updated_user = await get_user_by_username(
        update_scheme.username, service.session
    )
    assert updated_user.email == update_scheme.email
    assert updated_user.username == update_scheme.username
    assert updated_user.last_name == update_scheme.last_name


async def test_delete_user(service: UserService):
    scheme = user_for_delete_scheme
    new_user = User(
        email=scheme.email,
        username=scheme.username,
        hashed_password=PasswordManager(scheme.password).hash,
    )
    service.session.add(new_user)
    await service.session.flush()
    user = await get_user_by_username(scheme.username, service.session)
    assert user.is_active is True
    await service.delete_user(user.user_id)
    await service.session.execute(service.queries.pop())
    await service.session.flush()
    deleted_user = await get_user_by_username(scheme.username, service.session)
    assert deleted_user.is_active is False


async def test_get_all_users(service: UserService):
    for scheme in user_list:
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=PasswordManager(scheme.password).hash,
        )
        service.session.add(new_user)
    await service.session.flush()
    limit = 3
    users_count_query = (
        select(func.count()).select_from(User).where(User.is_active == True)
    )
    users_count = (await service.session.execute(users_count_query)).scalar()
    assert users_count == 7
    res = await service.get_all_users(page=1, limit=limit)
    assert len(res.users) == limit
    res = await service.get_all_users(page=2, limit=limit)
    assert len(res.users) == limit
    res = await service.get_all_users(page=3, limit=limit)
    assert len(res.users) == 1
    res = await service.get_all_users(page=4, limit=limit)
    assert len(res.users) == 0
