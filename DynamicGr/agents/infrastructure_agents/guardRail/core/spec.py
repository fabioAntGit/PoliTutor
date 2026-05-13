from typing import  List, Optional, Type
from pydantic import BaseModel


class GuardrailAgentSpec:
    """Define prompt, schema, and allowed tools for an agent."""

    def __init__(
        self,
        name: str,
        input_variables: List[str],
        output_schema: Type[BaseModel],
        prompt_template: str = None,
        # Optional structured messages
        structured_prompt: Optional[List] = None,
    ):
        self.name = name
        self.prompt_template = prompt_template
        self.input_variables = input_variables
        self.output_schema = output_schema
        self.structured_prompt = structured_prompt


