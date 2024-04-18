import datetime
import uuid

from sqlalchemy import Column, String, Boolean, MetaData
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    registered_at = Column(
        TIMESTAMP, default=datetime.datetime.now(datetime.timezone.utc)
    )
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True, nullable=False)
    hashed_password = Column(String, nullable=False)