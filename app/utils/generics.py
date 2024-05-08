from datetime import datetime
from typing import Literal

from pydantic import Field, SecretStr
from typing_extensions import Annotated

from app.utils.date import default_from_date, default_to_date

type Name = Annotated[str, Field(min_length=3, max_length=20)]
type Password = Annotated[SecretStr, Field(min_length=8, max_length=20)]

type ResponseFileType = Literal["json", "csv"]

# date types
type FromDate = Annotated[
    datetime,
    Field(
        default=default_from_date(),
        ge=default_from_date(),
        lt=default_to_date(),
    ),
]
type ToDate = Annotated[
    datetime,
    Field(
        default=datetime.now().date(),
        le=datetime.now().date(),
        gt=default_from_date(),
    ),
]
