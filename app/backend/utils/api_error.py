from typing import Any

class APIError:
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data

def api_error(code: int, message: str, data: Any = None) -> APIError:
    return APIError(code, message, data)
