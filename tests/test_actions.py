import pytest
from sqlalchemy import func, select, insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    User,
    Company,
    CompanyMember,
    CompanyRequest,
    UserRequest,
    UserRequestStatus,
    CompanyRequestStatus,
)
from app.schemas.company import (
    CompanyCreateRequestScheme,
    CompanyDetailResponseScheme,
    CompanyRequestDetailResponseScheme,
)
from app.schemas.user import (
    UserSignUpRequestScheme,
    UserUpdateRequestScheme,
    UserRequestDetailResponseScheme,
)
from app.services.company import CompanyService
from app.services.user import (
    Auth0Service,
    JWTService,
    PasswordManager,
    UserService,
    GenericAuthService,
)
from app.utils.exceptions.user import UserRequestNotFoundException

user_data = [
    {
        "username": "user1",
        "email": "user1@example.com",
        "is_active": True,
        "hashed_password": "1",
    },
    {
        "username": "user2",
        "email": "user2@example.com",
        "is_active": True,
        "hashed_password": "1",
    },
    {
        "username": "user3",
        "email": "user3@example.com",
        "is_active": True,
        "hashed_password": "1",
    },
    {
        "username": "user4",
        "email": "user4@example.com",
        "is_active": True,
        "hashed_password": "1",
    },
    {
        "username": "user5",
        "email": "user5@example.com",
        "is_active": True,
        "hashed_password": "1",
    },
]

company1_scheme = CompanyCreateRequestScheme(
    name="comapny1",
)

company2_scheme = CompanyCreateRequestScheme(
    name="comapny2",
)


async def test_add_users(company_service):
    for data in user_data:
        new_user = User(**data)
        company_service.session.add(new_user)
    await company_service.session.commit()


async def test_create_company(company_service: CompanyService):
    user = await company_service.session.execute(
        select(User).where(User.username == "user1")
    )
    user: User = user.scalar()
    company = await company_service.create_company(
        owner=user, scheme=company1_scheme
    )
    assert isinstance(company, CompanyDetailResponseScheme)
    assert company.name == company1_scheme.name
    assert company.owner_id == user.user_id

    user2 = await company_service.session.execute(
        select(User).where(User.username == "user2")
    )
    user2: User = user2.scalar()
    company = await company_service.create_company(
        owner=user2, scheme=company2_scheme
    )
    assert isinstance(company, CompanyDetailResponseScheme)
    assert company.name == company2_scheme.name


async def test_create_company_user_invite(company_service):
    owner = await company_service.session.execute(
        select(User).where(User.username == "user1")
    )
    owner = owner.scalar()
    company = await company_service.session.execute(
        select(Company).where(Company.name == "comapny1")
    )
    company = company.scalar()
    user = await company_service.session.execute(
        select(User).where(User.username == "user2")
    )
    user = user.scalar()

    company_request = await company_service.create_company_user_invite(
        user_id=user.user_id, company_id=company.company_id, owner=owner
    )

    assert isinstance(company_request, CompanyRequestDetailResponseScheme)
    assert company_request.user_id == user.user_id
    assert company_request.company_id == company.company_id
    assert company_request.status == CompanyRequestStatus.pending.value

    # send company request not owner
    with pytest.raises(PermissionError):
        error_owner = await company_service.session.execute(
            select(User).where(User.username == "user2")
        )
        error_owner = error_owner.scalar()

        company_error_request = (
            await company_service.create_company_user_invite(
                user_id=user.user_id,
                company_id=company.company_id,
                owner=error_owner,
            )
        )


async def test_user_accept_company_invitation(user_service):
    company = await user_service.session.execute(
        select(Company).where(Company.name == "comapny1")
    )
    company = company.scalar()
    user = await user_service.session.execute(
        select(User).where(User.username == "user2")
    )
    user = user.scalar()

    company_request = await user_service.session.execute(
        select(CompanyRequest).where(
            CompanyRequest.user_id == user.user_id,
            CompanyRequest.company_id == company.company_id,
        )
    )
    company_request = company_request.scalar()

    # wrong user accept invite check
    with pytest.raises(PermissionError):
        error_user = await user_service.session.execute(
            select(User).where(User.username == "user3")
        )
        error_user = error_user.scalar()
        await user_service.accept_invitation(
            request_id=company_request.request_id, user=error_user
        )

    accept_company_request = await user_service.accept_invitation(
        request_id=company_request.request_id, user=user
    )
    assert isinstance(
        accept_company_request, CompanyRequestDetailResponseScheme
    )
    assert accept_company_request.status == CompanyRequestStatus.accepted.value
    assert accept_company_request.user_id == user.user_id
    assert accept_company_request.company_id == company.company_id

    # invite is exist check error
    with pytest.raises(PermissionError):
        await user_service.accept_invitation(
            request_id=company_request.request_id, user=user
        )


async def test_create_user_request(user_service):
    company = await user_service.session.execute(
        select(Company).where(Company.name == "comapny1")
    )
    company = company.scalar()
    user = await user_service.session.execute(
        select(User).where(User.username == "user3")
    )
    user = user.scalar()

    user_request = await user_service.create_user_request(
        company_id=company.company_id, user=user
    )
    assert isinstance(user_request, UserRequestDetailResponseScheme)
    assert user_request.user_id == user.user_id
    assert user_request.company_id == company.company_id

    # error if request exist
    with pytest.raises(PermissionError):
        await user_service.create_user_request(
            company_id=company.company_id, user=user
        )


async def test_company_confirm_user_request(company_service):
    owner = await company_service.session.execute(
        select(User).where(User.username == "user1")
    )
    owner = owner.scalar()
    company = await company_service.session.execute(
        select(Company).where(Company.name == "comapny1")
    )
    company = company.scalar()
    user = await company_service.session.execute(
        select(User).where(User.username == "user3")
    )
    user = user.scalar()

    user_request = await company_service.session.execute(
        select(UserRequest).where(
            UserRequest.user_id == user.user_id,
            UserRequest.company_id == company.company_id,
        )
    )
    user_request = user_request.scalar()

    # error wrong owner
    with pytest.raises(PermissionError):
        error_owner = await company_service.session.execute(
            select(User).where(User.username == "user2")
        )
        error_owner = error_owner.scalar()
        await company_service.confirm_user_request(
            request_id=user_request.request_id, owner=error_owner
        )

    confirm_user_request = await company_service.confirm_user_request(
        request_id=user_request.request_id, owner=owner
    )
    assert isinstance(confirm_user_request, UserRequestDetailResponseScheme)
    assert confirm_user_request.status == UserRequestStatus.accepted.value
    assert confirm_user_request.user_id == user.user_id
    assert confirm_user_request.company_id == company.company_id

    # error if user request dont exist
    with pytest.raises(UserRequestNotFoundException):
        await company_service.confirm_user_request(
            request_id=user_request.request_id, owner=owner
        )
