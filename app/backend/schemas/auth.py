from pydantic import BaseModel, Field, ConfigDict

class IAEduBaseHeaders(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    x_iaedu_channel_id: str = Field(
        alias="X-IAEdu-Channel-ID",
        pattern=r"^[a-z0-9]+$",
        max_length=64
    )

class IAEduAuthHeaders(IAEduBaseHeaders):
    x_iaedu_api_key: str = Field(
        alias="X-IAEdu-API-Key",
        pattern=r"^sk-usr-",
        max_length=128
    )
    x_iaedu_endpoint: str = Field(
        alias="X-IAEdu-Endpoint",
        pattern=r"^https://api\.iaedu\.pt/agent-chat//api/v1/agent/[^/]+/stream$",
        max_length=256
    )
