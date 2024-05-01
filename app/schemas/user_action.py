from abc import ABC

from pydantic import BaseModel


class _BaseUserActionScheme(BaseModel, ABC):
    pass
