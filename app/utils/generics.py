from pydantic import EmailStr, Field
from typing_extensions import Annotated

type Name = Annotated[str, Field(min_length=3, max_length=20)]
