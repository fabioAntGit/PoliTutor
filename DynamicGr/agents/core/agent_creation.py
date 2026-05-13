from __future__ import annotations

from typing import Any, Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser


def create_output_parser(output_schema: Optional[Any]) -> Optional[PydanticOutputParser]:
    if not output_schema:
        return None
    return PydanticOutputParser(pydantic_object=output_schema)

def to_state(inputs: dict) -> dict:
    if "messages" in inputs:
        return inputs
    if "input" in inputs:
        return {"messages": [HumanMessage(content=inputs["input"])]}

    return {
        "messages": [AIMessage(content=str(v)) for v in inputs.values()]
    }
