import json
import re
from typing import List


def parse_guardrail_json_response(raw_text: str) -> dict:
    clean_text = re.sub(r"^```json\s*|```$", "",
                        raw_text.strip(), flags=re.MULTILINE)

    clean_text = re.sub(r",\s*([}\]])", r"\1", clean_text)

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", clean_text)
        raise e


def parse_guardrail_json_response(raw_text: str) -> dict:
    clean_text = re.sub(r"^```json\s*|```$", "",
                        raw_text.strip(), flags=re.MULTILINE)

    clean_text = re.sub(r",\s*([}\]])", r"\1", clean_text)

    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", clean_text)
        raise e


def build_llama_guard_prompt_dynamic(
    input_classifier: bool,
    unsafe_categories: List[str]
) -> str:
    """
    Builds a dynamic prompt compatible with Llama Guard 3 safety classification format.

    Args:
        input_classifier: True if the model should classify user input; False if it should classify assistant output.
        unsafe_categories: List of unsafe categories such as:
            ["S1: Violent Crimes", "S2: Non-Violent Crimes", "S3: Hate Speech", ...]

    Returns:
        str: Properly formatted prompt string for Llama Guard 3.
    """

    # Determine the correct role for the content being classified
    start_header = "user" if input_classifier else "assistant"

    # Build the unsafe categories section
    categories_block = "\n".join(f"- {cat}" for cat in unsafe_categories)

    prompt = f"""<|begin_of_text|>
    <|start_header_id|>system<|end_header_id|>
    You are Llama Guard 3, a large language model fine-tuned to classify text safety.
    You must identify whether the following message is SAFE or UNSAFE, according to Meta’s safety guidelines.

    Your task:
    1. Review the content within the provided conversation context.
    2. Determine if it violates any of the unsafe categories listed below.
    3. If unsafe, identify which categories apply.

    <BEGIN UNSAFE CONTENT CATEGORIES>
    {categories_block}
    <END UNSAFE CONTENT CATEGORIES>

    Return your response in this format:
    SAFE
    -- OR --
    UNSAFE: [comma-separated list of violated categories]

    Be concise and deterministic. Do not provide explanations unless explicitly asked.
    <|eot_id|>
    <|start_header_id|>{start_header}<|end_header_id|>
    {{input}}
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>"""

    return prompt
