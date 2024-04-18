from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.utils.generics import Hash, Name, Password


class PasswordManager:
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _hashed_password = None

    def __init__(self, password: Password | str):
        self.password = password

    def _get_hash(self, var: Password | str) -> Hash:
        return self._pwd_context.hash(var)

    @property
    def hashed_password(self) -> Hash:
        if not self._hashed_password:
            self._hashed_password = self._get_hash(self.password)
        return self._hashed_password

    def verify_password(
        self, plain_password: Password, hashed_password: Hash
    ) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self, email: EmailStr, username: Name, password: Password
    ):
        password_hash = PasswordManager(password).hashed_password
        new_user = User(
            email=email,
            username=username,
            password=password_hash,
        )
        self.session.add(new_user)
        await self.session.commit()
        return new_user
