from enum import Enum

class Role(str, Enum):
    user = "user"
    assistant = "assistant"
