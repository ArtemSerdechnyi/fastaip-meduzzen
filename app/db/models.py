import datetime
import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    registered_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True, nullable=False)
    hashed_password = Column(String)
