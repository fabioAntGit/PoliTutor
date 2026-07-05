from pydantic import BaseModel

class TutorSource(BaseModel):
    filename: str
    pages: list[int]

class TutorResponse(BaseModel):
    answer: str
    sources: list[TutorSource]
    is_fallback: bool
    is_guardrail: bool = False
    is_output_guardrail: bool = False
    is_retrieval_fallback: bool = False
