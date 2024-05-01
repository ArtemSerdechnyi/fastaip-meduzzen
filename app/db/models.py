import datetime
import enum
import uuid

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    __repr_cols_num: int = 1
    __repr_cols: tuple[str, ...] = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.__repr_cols or idx < self.__repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} : {', '.join(cols)}>"

    def __str__(self):
        return self.__repr__()


class UserRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    denied = "denied"


class CompanyRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    denied = "denied"


class CompanyRole(str, enum.Enum):
    member = "member"


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
    employments = relationship("CompanyMember", back_populates="user")
    company_request = relationship(
        "CompanyRequest", back_populates="user", cascade="all, delete-orphan"
    )
    user_request = relationship(
        "UserRequest", back_populates="user", cascade="all, delete-orphan"
    )

    __repr_cols_num = 2
    __repr_cols = ("email", "is_active")


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
    members = relationship("CompanyMember", back_populates="company")
    company_request = relationship(
        "CompanyRequest",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    user_request = relationship(
        "UserRequest", back_populates="company", cascade="all, delete-orphan"
    )

    __repr_cols_num = 2
    __repr_cols = ("visibility", "is_active")


class CompanyMember(Base):
    __tablename__ = "company_members"

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role = Column(
        Enum(CompanyRole), default=CompanyRole.member, nullable=False
    )
    is_active = Column(Boolean(), default=True, nullable=False)

    company = relationship("Company", back_populates="members")
    user = relationship("User", back_populates="employments")

    __repr_cols_num = 3
    __repr_cols = ("is_active",)


class CompanyRequest(Base):
    __tablename__ = "company_request"

    request_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        Enum(CompanyRequestStatus), default=CompanyRequestStatus.pending
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    is_active = Column(Boolean(), default=True, nullable=False)

    company = relationship("Company", back_populates="company_request")
    user = relationship("User", back_populates="company_request")

    __repr_cols_num = 4
    __repr_cols = ("is_active",)


class UserRequest(Base):
    __tablename__ = "user_request"

    request_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(Enum(UserRequestStatus), default=UserRequestStatus.pending)
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    is_active = Column(Boolean(), default=True, nullable=False)

    company = relationship("Company", back_populates="user_request")
    user = relationship("User", back_populates="user_request")

    __repr_cols_num = 4
    __repr_cols = ("is_active",)

