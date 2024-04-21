from pydantic import Field, SecretStr
from typing_extensions import Annotated

type Name = Annotated[str, Field(min_length=3, max_length=20)]
type Password = Annotated[SecretStr, Field(min_length=8, max_length=20)]
type Hash = str
