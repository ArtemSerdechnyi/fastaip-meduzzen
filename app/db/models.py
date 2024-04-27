import datetime
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    _repr_cols_num: int = 1
    _repr_cols: tuple[str, ...] = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self._repr_cols or idx < self._repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} : {', '.join(cols)}>"

    def __str__(self):
        return self.__repr__()


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    registered_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True, nullable=False)
    hashed_password = Column(String)

    companies = relationship(
        "Company", back_populates="owner", cascade="all, delete-orphan"
    )

    _repr_cols_num = 2
    _repr_cols = ("email", "is_active")


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    visibility = Column(Boolean(), default=True, nullable=False)
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active = Column(Boolean(), default=True, nullable=False)

    owner = relationship("User", back_populates="companies")

    _repr_cols_num = 2
    _repr_cols = ("visibility", "owner_id")
