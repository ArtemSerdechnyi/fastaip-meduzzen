import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.user import (
    UserSignUpRequestScheme,
    UserUpdateRequestScheme,
)
from app.services.user import (
    JWTService,
    PasswordManager,
    UserService,
    GenericAuthService,
)

user1_scheme = UserSignUpRequestScheme(
    user_id="db1eca0e-3110-4d78-bcbc-de50d04fae1d",
    email="test@example.com",
    username="testuser",
    password="password123",
    password_confirm="password123",
)

user2_scheme_for_update = UserSignUpRequestScheme(
    email="forupdate@example.com",
    username="forupdate",
    password="12345678",
    password_confirm="12345678",
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
    password = "12345678"
    manager = PasswordManager(password)
    hashed = manager.hash
    assert hashed != password
    assert manager.verify_password(hashed) is True


# Test UserService


async def test_create_user(user_service: UserService):
    scheme = user1_scheme
    with pytest.raises(NoResultFound):
        await get_user_by_username(scheme.username, user_service.session)
    await user_service.create_default_user(scheme)
    await user_service.session.flush()
    user = await get_user_by_username(scheme.username, user_service.session)
    assert isinstance(user, User)
    assert user.email == scheme.email
    assert user.username == scheme.username
    assert user.is_active is True
    assert user.hashed_password != scheme.password
    assert PasswordManager(scheme.password).verify_password(
        user.hashed_password
    )


async def test_get_user_by_attributes(user_service: UserService):
    scheme = user1_scheme
    user = await user_service.get_user_by_attributes(email=scheme.email)
    assert isinstance(user, User)
    assert user.email == scheme.email
    assert user.is_active is True
    user = await user_service.get_user_by_attributes(username="testuser")
    assert isinstance(user, User)
    assert user.username == scheme.username
    assert user.is_active is True


async def test_self_user_update(user_service: UserService):
    scheme = user2_scheme_for_update
    update_scheme = user_update_scheme
    await user_service.create_default_user(scheme)
    user = await get_user_by_username(scheme.username, user_service.session)
    assert user.email != update_scheme.email
    assert user.username != update_scheme.username
    assert user.last_name != update_scheme.last_name

    user = await user_service.self_user_update(user, update_scheme)
    assert user.email == update_scheme.email
    assert user.username == update_scheme.username
    assert user.last_name == update_scheme.last_name


async def test_self_user_delete(user_service: UserService):
    scheme = user_for_delete_scheme
    new_user = User(
        email=scheme.email,
        username=scheme.username,
        hashed_password=PasswordManager(scheme.password).hash,
    )

    user_service.session.add(new_user)
    await user_service.session.flush()
    user = await get_user_by_username(scheme.username, user_service.session)
    assert user.is_active is True
    await user_service.self_user_delete(user)
    await user_service.session.execute(user_service.queries.pop())
    await user_service.session.flush()
    deleted_user = await get_user_by_username(
        scheme.username, user_service.session
    )
    assert deleted_user.is_active is False


async def test_get_all_users(user_service: UserService):
    for scheme in user_list:
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=PasswordManager(scheme.password).hash,
        )
        user_service.session.add(new_user)
    await user_service.session.flush()
    limit = 5
    users_count_query = (
        select(func.count()).select_from(User).where(User.is_active == True)
    )
    users_count = (
        await user_service.session.execute(users_count_query)
    ).scalar()
    assert users_count == 13
    res = await user_service.get_all_users(page=1, limit=limit)
    assert len(res.users) == limit
    res = await user_service.get_all_users(page=2, limit=limit)
    assert len(res.users) == limit
    res = await user_service.get_all_users(page=3, limit=limit)
    assert len(res.users) == 3
    res = await user_service.get_all_users(page=4, limit=limit)
    assert len(res.users) == 0

    with pytest.raises(AttributeError):
        await user_service.get_all_users(page=1, limit=0)
    with pytest.raises(AttributeError):
        await user_service.get_all_users(page=0, limit=1)


# JWT tests


async def test_create_and_decode_access_token(user_service: UserService):
    data = {"email": user1_scheme.email}
    token = JWTService.create_access_token(data=data)
    token_data = JWTService.decode_token(token=token)
    assert token_data.email == user1_scheme.email


#  GenericAuthService


async def test_get_user_from_any_token(session: AsyncSession):
    data = {"email": user1_scheme.email}
    token = JWTService.create_access_token(data=data)
    credentials = type("Credentials", (object,), {"credentials": token})
    user = await GenericAuthService.get_user_from_any_token(
        credentials=credentials, db=session
    )
    assert isinstance(user, User)
    assert user.email == user1_scheme.email
