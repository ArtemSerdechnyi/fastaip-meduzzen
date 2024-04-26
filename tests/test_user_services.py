import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.user import (
    UserSignUpRequestScheme,
    UserUpdateRequestScheme, OAuth2RequestFormScheme, Auth0UserScheme,
)
from app.services.user import (
    Auth0Service,
    JWTService,
    PasswordManager,
    UserService,
)
from app.utils.exceptions.user import UserNotFoundException

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

oauth2password_requests_cheme = OAuth2RequestFormScheme(
    username=str(user1_scheme.email),
    password=user1_scheme.password.get_secret_value(),
)

auth0_user_scheme = Auth0UserScheme(email="auth0testmail@example.com")


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
    password = "12345678"
    manager = PasswordManager(password)
    hashed = manager.hash
    assert hashed != password
    assert manager.verify_password(hashed) is True


# Test UserService


async def test_create_user(service: UserService):
    scheme = user1_scheme
    with pytest.raises(NoResultFound):
        await get_user_by_username(scheme.username, service.session)
    await service.create_default_user(scheme)
    await service.session.flush()
    user = await get_user_by_username(scheme.username, service.session)
    assert isinstance(user, User)
    assert user.email == scheme.email
    assert user.username == scheme.username
    assert user.is_active is True
    assert user.hashed_password != scheme.password
    assert PasswordManager(scheme.password).verify_password(
        user.hashed_password
    )


async def test_get_user_by_attributes(service: UserService):
    scheme = user1_scheme
    user = await service.get_user_by_attributes(email=scheme.email)
    assert isinstance(user, User)
    assert user.email == scheme.email
    assert user.is_active is True
    user = await service.get_user_by_attributes(username="testuser")
    assert isinstance(user, User)
    assert user.username == scheme.username
    assert user.is_active is True


async def test_verify_user_by_email(service: UserService):
    scheme = user1_scheme
    user = await service.verify_user_by_email(scheme.email)
    assert isinstance(user, User)
    assert user.email == scheme.email
    with pytest.raises(UserNotFoundException):
        await service.verify_user_by_email("wrong_email@example.com")


async def test_update_user(service: UserService):
    scheme = user2_scheme_for_update
    update_scheme = user_update_scheme
    await service.create_default_user(scheme)
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
    assert users_count == 8
    res = await service.get_all_users(page=1, limit=limit)
    assert len(res.users) == limit
    res = await service.get_all_users(page=2, limit=limit)
    assert len(res.users) == limit
    res = await service.get_all_users(page=3, limit=limit)
    assert len(res.users) == 2
    res = await service.get_all_users(page=4, limit=limit)
    assert len(res.users) == 0

    with pytest.raises(AttributeError):
        await service.get_all_users(page=1, limit=0)
    with pytest.raises(AttributeError):
        await service.get_all_users(page=0, limit=1)


# JWT tests


async def test_user_get_access_token(service: UserService):
    scheme = oauth2password_requests_cheme
    token_scheme = await service.get_access_token(scheme=scheme)
    user_id = JWTService.get_user_email_from_token(token_scheme.access_token)
    user = await get_user_by_id(user_id, service.session)
    assert user.email == scheme.username


async def test_get_user_id_from_token(service: UserService):
    scheme = oauth2password_requests_cheme
    token_scheme = await service.get_access_token(scheme=scheme)
    user_id = JWTService.get_user_email_from_token(token_scheme.access_token)
    user = await get_user_by_id(user_id, service.session)
    assert user.email == scheme.username


async def test_get_current_user_from_token(service: UserService):
    scheme = oauth2password_requests_cheme
    token_scheme = await service.get_access_token(scheme=scheme)
    user = await JWTService.get_current_user_from_token(
        token=token_scheme.access_token, db=service.session
    )
    assert user.email == user1_scheme.email


# Auth0 tests


async def test_register_auth0_user(service: UserService):
    scheme = auth0_user_scheme
    with pytest.raises(UserNotFoundException):
        await service.get_user_by_attributes(email=scheme.email)
    await service.register_auth0_user(scheme)
    await service.get_user_by_attributes(email=scheme.email)
    await service.register_auth0_user(scheme)
    await service.register_auth0_user(scheme)
    await service.get_user_by_attributes(email=scheme.email)


async def test_get_user_scheme_from_auth0(service: UserService):
    scheme = auth0_user_scheme
    assert scheme.email
    user_scheme = await Auth0Service.get_user_scheme_from_auth0(
        auth0_user_scheme
    )
    assert isinstance(user_scheme, Auth0UserScheme)
    assert user_scheme.email == scheme.email
