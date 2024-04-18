from typing_extensions import Annotated
from pydantic import EmailStr, Field

type Name = Annotated[str, Field(min_length=3, max_length=20)]
