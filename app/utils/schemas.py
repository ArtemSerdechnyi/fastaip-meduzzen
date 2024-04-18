from typing import Optional, Type, Any, Tuple
from copy import deepcopy

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo


def optionalise_fields(model: Type[BaseModel]):
    """
    Create a new model with all fields optional, base on input model.

    Source:
    https://stackoverflow.com/questions/67699451/make-every-field-as-optional-with-pydantic#:~:text=import%20FieldInfo%0A%0A%0Adef-,partial_model,-(model%3A
    """

    def make_field_optional(
        field: FieldInfo, default: Any = None
    ) -> Tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    return create_model(
        f"Optionalised{model.__name__}",
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(field_info)
            for field_name, field_info in model.model_fields.items()
        },
    )
