
from pydantic import BaseModel


class TopicClassificationOutput(BaseModel):
    topic: str  # IN_TOPIC ou OFF_TOPIC
    reasoning: str


class ThreatComplianceOutput(BaseModel):
    safety: str  # SAFE ou UNSAFE
    reasoning: str


class IdentityAgentOutput(BaseModel):
    language: str  # en, pt, or ot
    tokens: int


class UserContextAcquisitionOutput(BaseModel):
    user_name: str
    general_context: str
    functional_context: str

