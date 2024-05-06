from passlib.context import CryptContext
from pydantic import SecretStr

from app.core.constants import USERS_PAGE_LIMIT
from app.utils.generics import Password


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
