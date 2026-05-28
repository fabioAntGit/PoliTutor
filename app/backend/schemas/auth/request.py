from pydantic import BaseModel

class LogoutRequest(BaseModel):
    access_token: str
