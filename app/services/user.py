import datetime
from logging import getLogger
from typing import NoReturn
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import app_settings, auth0_config, gwt_config
from app.db.models import (
    User,
    UserRequest,
    CompanyRequest,
    CompanyRequestStatus,
    CompanyMember,
    UserRequestStatus,
)
from app.db.postgres import get_async_session
from app.schemas.company import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
    CompanyMemberDetailResponseScheme,
)
from app.schemas.user import (
    TokenUserDataScheme,
    UserDetailResponseScheme,
    UserHTTPBearer,
    UserSignUpRequestScheme,
    UsersListResponseScheme,
    UserUpdateRequestScheme,
    UserRequestDetailResponseScheme,
    UserRequestListDetailResponseScheme,
)
from app.services.base import Service
from app.services.company import CompanyService
from app.utils.exceptions.company import CompanyRequestNotFoundException
from app.utils.exceptions.user import (
    DecodeUserTokenError,
    PasswordVerificationError,
    UserNotFoundException,
    UserRequestNotFoundException,
)
from app.utils.generics import Password
from app.utils.validators import UserValidator

logger = getLogger(__name__)


class PasswordManager:
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _hashed_password = None

    def __init__(self, password: str | Password):
        if isinstance(password, SecretStr):
            self.password = str(password.get_secret_value())
        else:
            self.password = password

    def _get_hash(self, var: str) -> str:
        return self._pwd_context.hash(var)

    @property
    def hash(self) -> str:
        if self._hashed_password is None:
            self._hashed_password = self._get_hash(self.password)
        return self._hashed_password

    def verify_password(self, hashed_password: str) -> bool:
        return self._pwd_context.verify(self.password, hashed_password)


class JWTService:
    @staticmethod
    def get_expires_delta() -> datetime.timedelta:
        return datetime.timedelta(
            minutes=gwt_config.GWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        expires_delta = cls.get_expires_delta()
        to_encode = data.copy()
        if expires_delta:
            expire = (
                datetime.datetime.now(datetime.timezone.utc) + expires_delta
            )
        else:
            expire = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(
                minutes=gwt_config.GWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            app_settings.SECRET_KEY,
            algorithm=gwt_config.GWT_ALGORITHMS,
        )
        return encoded_jwt

    @classmethod
    def decode_token(
        cls,
        token: str,
    ) -> TokenUserDataScheme:
        try:
            payload = jwt.decode(
                token,
                app_settings.SECRET_KEY,
                algorithms=[gwt_config.GWT_ALGORITHMS],
            )
        except JWTError:
            pass
        else:
            user_email = payload.get("email")
            return TokenUserDataScheme(email=user_email)


class Auth0Service:
    @classmethod
    def decode_token(
        cls,
        token: str,
    ) -> TokenUserDataScheme:
        try:
            payload = jwt.decode(
                token,
                auth0_config.AUTH0_API_SECRET,
                algorithms=[auth0_config.AUTH0_ALGORITHMS],
                audience=auth0_config.AUTH0_API_AUDIENCE,
            )
        except JWTError:
            pass
        else:
            user_email = payload.get("email")
            return TokenUserDataScheme(email=user_email)


class GenericAuthService:
    @classmethod
    async def get_user_from_any_token(
        cls,
        credentials: HTTPAuthorizationCredentials = Depends(UserHTTPBearer()),
        db: AsyncSession = Depends(get_async_session),
    ) -> User:
        token = credentials.credentials
        async with UserService(db) as service:
            if token_data := JWTService.decode_token(token=token):
                email = token_data.email
                user = await service.get_user_by_attributes(email=email)
            elif token_data := Auth0Service.decode_token(token=token):
                email = token_data.email
                try:
                    user = await service.get_user_by_attributes(email=email)
                except UserNotFoundException:
                    user = await service.create_and_get_auth0_user(email=email)
            else:
                raise DecodeUserTokenError()
            return user


class UserService(Service):
    validator = UserValidator()

    @staticmethod
    def verify_user_password(
        user: User,
        password: Password | str,
    ) -> NoReturn | None:
        hashed_password = user.hashed_password
        if PasswordManager(password).verify_password(hashed_password) is False:
            raise PasswordVerificationError(user=user)

    async def get_user_by_attributes(
        self,
        is_active=True,
        **kwargs,
    ) -> User:
        kwargs.update(is_active=is_active)

        query = select(User).where(
            and_(
                *(
                    getattr(User, attr) == value
                    for attr, value in kwargs.items()
                )
            )
        )
        result = await self.session.execute(query)
        if user := result.scalar():
            return user
        raise UserNotFoundException(**kwargs)

    async def create_default_user(self, scheme: UserSignUpRequestScheme):
        password_hash = PasswordManager(scheme.password).hash
        new_user = User(
            email=scheme.email,
            username=scheme.username,
            hashed_password=password_hash,
        )
        self.session.add(new_user)

    async def create_and_get_auth0_user(self, email: str) -> User:
        query = insert(User).values(email=email).returning(User)
        res = await self.session.execute(query)
        return res.scalar()

    async def self_user_update(
        self, user: User, scheme: UserUpdateRequestScheme
    ) -> UserDetailResponseScheme:
        if scheme.password:
            scheme.password = PasswordManager(scheme.password).hash

        query = (
            update(User)
            .where(and_(User.user_id == user.user_id, User.is_active == True))
            .values(scheme.dict(exclude_unset=True))
            .returning(User)
        )
        user = await self.session.execute(query)
        user = user.scalar()
        return UserDetailResponseScheme.from_orm(user)

    async def self_user_delete(self, user: User):
        query = (
            update(User)
            .where(and_(User.user_id == user.user_id, User.is_active == True))
            .values(is_active=False)
        )
        await self._add_query(query)

    async def get_all_users(self, page, limit) -> UsersListResponseScheme:
        query = (
            select(User).where(User.is_active == True).order_by(User.username)
        )
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_users = result.scalars().all()
        users = [UserDetailResponseScheme.from_orm(user) for user in raw_users]
        return UsersListResponseScheme(users=users)

    # user actions

    async def _update_user_request_status(
        self, request_id: UUID, status: UserRequestStatus
    ) -> UserRequest:
        query = (
            update(UserRequest)
            .where(
                and_(
                    UserRequest.request_id == request_id,
                    UserRequest.is_active == True,
                )
            )
            .values(status=status)
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        if request := result.scalar():
            return request
        raise UserRequestNotFoundException(
            request_id=request_id, status=status
        )

    @validator.validate_check_user_not_in_company
    @validator.validate_user_request_non_existing
    @validator.validate_exist_company_is_active
    async def create_user_request(
        self, company_id: UUID, user: User
    ) -> UserRequestDetailResponseScheme:
        query = (
            insert(UserRequest)
            .values(company_id=company_id, user_id=user.user_id)
            .returning(UserRequest)
        )

        result = await self.session.execute(query)
        request = result.scalar()
        return UserRequestDetailResponseScheme.from_orm(request)

    async def cancel_user_request(self, request_id: UUID, user: User):
        query = (
            update(UserRequest)
            .where(
                and_(
                    UserRequest.request_id == request_id,
                    UserRequest.user_id == user.user_id,
                    UserRequest.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(UserRequest)
        )
        result = await self.session.execute(query)
        request = result.scalar()
        return UserRequestDetailResponseScheme.from_orm(request)

    async def list_user_requests(self, user: User, page: int, limit: int):
        query = select(UserRequest).where(UserRequest.user_id == user.user_id)
        query = self.apply_pagination(query=query, page=page, limit=limit)

        result = await self.session.execute(query)
        raw_requests = result.scalars().all()
        requests = [
            UserRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return UserRequestListDetailResponseScheme(requests=requests)

    async def list_user_invitations(self, user: User, page: int, limit: int):
        query = select(CompanyRequest).where(
            and_(
                CompanyRequest.user_id == user.user_id,
                CompanyRequest.status == CompanyRequestStatus.pending.value,
                CompanyRequest.is_active == True,
            )
        )
        query = self.apply_pagination(query, page, limit)
        result = await self.session.execute(query)
        raw_requests = result.scalars().all()
        requests = [
            CompanyRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return CompanyRequestListDetailResponseScheme(requests=requests)

    @validator.validate_company_invitation
    async def accept_invitation(
        self, request_id: UUID, user: User
    ) -> CompanyRequestDetailResponseScheme:
        pending_status = CompanyRequestStatus.pending.value

        query = select(CompanyRequest).where(
            and_(
                CompanyRequest.request_id == request_id,
                CompanyRequest.user_id == user.user_id,
                CompanyRequest.status == pending_status,
                CompanyRequest.is_active == True,
            )
        )

        result = await self.session.execute(query)
        company_request = result.scalar()
        if not company_request:
            raise CompanyRequestNotFoundException(
                request_id=request_id, user_id=user.user_id
            )

        # company service logic
        cs = CompanyService(session=self.session)

        # add user to company
        await cs._add_user_to_company(
            company_id=company_request.company_id,
            user_id=user.user_id,
        )

        # update company request status
        accept_status = CompanyRequestStatus.accepted.value
        request = await cs._update_company_request_status(
            request_id=request_id,
            status=accept_status,
        )
        return CompanyRequestDetailResponseScheme.from_orm(request)

    @validator.validate_company_invitation
    async def reject_invitation(self, request_id: UUID, user: User):
        status = CompanyRequestStatus.denied.value
        cs = CompanyService(session=self.session)
        request = await cs._update_company_request_status(
            request_id=request_id,
            status=status,
        )
        return CompanyRequestDetailResponseScheme.from_orm(request)

    @validator.validate_user_leave_from_company
    async def leave_company(self, company_id: UUID, user: User):
        cs = CompanyService(session=self.session)
        member = await cs._remove_user_from_company(
            company_id=company_id,
            user_id=user.user_id,
        )
        return CompanyMemberDetailResponseScheme.from_orm(member)
