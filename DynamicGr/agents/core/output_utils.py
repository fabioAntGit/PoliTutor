
import json
import re
from typing import Dict, Any
from langchain_core.messages import AIMessage, BaseMessage


def parse_model_response(raw_response: str,) -> Dict[str, Any]:
    """
       {
         "content": "<json string without reasoning>",
         "reasoning": "<string or None>"
       }
    """
    result = extract_model_response(raw_response)

    parsed_result = parse_model_json_output(result)
    

    reasoning = parsed_result.pop("reasoning", None)

    content_json = json.dumps(parsed_result, ensure_ascii=False)

    return {
        "content": content_json,
        "reasoning": reasoning,
    }


def parse_model_json_output(text: str) -> dict:
    """
    Attempts to extract a valid JSON object from a model's output string.
    Handles cases where the response is inside markdown, 
    contains extra text, or is slightly malformed.
    """
    if not text:
        return {}

    json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    bracket_match = re.search(r"({.*})", text, re.DOTALL)
    if bracket_match:
        text = bracket_match.group(1)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.replace("'", '"')
        try:
            return json.loads(cleaned)
        except Exception:
            return {"raw_output": text.strip()}


def extract_model_response(result) -> str:
    """
    Extracts and normalizes the text content from a model response.
    Works for:
      - plain string outputs
      - AIMessage/BaseMessage objects
      - tool-calling agent outputs (dict with 'output' key)
    """
    if isinstance(result, str):
        return result

    if isinstance(result, (AIMessage, BaseMessage)):
        return str(result.content)

    if isinstance(result, dict) and "output" in result:
        return str(result["output"])
