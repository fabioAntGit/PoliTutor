from typing import Any

from bson import ObjectId
from pydantic import BeforeValidator, PlainSerializer
from pydantic import SerializationInfo
from typing_extensions import Annotated


def validate_object_id(value: object) -> str:
    """Accept an ObjectId or a valid hex string, keep it as a ``str`` in Python."""
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, str) and ObjectId.is_valid(value):
        return value

    raise ValueError("Invalid ObjectId")


def _serialize_object_id(value: str, info: SerializationInfo) -> Any:
    return value if info.mode == "json" else ObjectId(value)


PyObjectId = Annotated[
    str,
    BeforeValidator(validate_object_id),
    PlainSerializer(_serialize_object_id, return_type=Any, when_used="unless-none"),
]
