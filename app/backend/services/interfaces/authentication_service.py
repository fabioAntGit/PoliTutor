from typing import Protocol, runtime_checkable

@runtime_checkable
class IAuthenticationService(Protocol):
    async def login(self, username: str, password: str) -> str:
        ...

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        courses: list[str],
    ) -> bool:
        ...

    async def logout(self, access_token: str) -> bool:
        ...
