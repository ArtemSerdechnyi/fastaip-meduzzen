from app.db.models import User


class UserNotFoundException(Exception):
    def __init__(self, message="User not found.", **kwargs):
        self.message = f"{message} Kwargs: {kwargs}" if kwargs else message
        super().__init__(self.message)


class PasswordVerificationError(Exception):
    def __init__(self, message="Password incorrect.", user: User = None):
        self.message = (
            f"{message} User: {user.email}" if user is not None else message
        )
        super().__init__(self.message)


class DecodeUserTokenError(Exception):
    def __init__(self, message="User token is not decoded."):
        super().__init__(message)
