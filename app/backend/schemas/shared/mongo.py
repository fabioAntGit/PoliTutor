from bson import ObjectId
from pydantic import BeforeValidator
from typing_extensions import Annotated


def validate_object_id(value: object) -> str:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, str) and ObjectId.is_valid(value):
        return value

    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]
