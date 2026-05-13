
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from agents.context_acquisition.utils.company_context_loader import (
    company_context_from_json_file,
)
from agents.context_acquisition.utils.company_context_parser import (
    company_context_to_struct,
)
from agents.infrastructure_agents.guardRail.input.orchestrator import (
    build_input_guardrail_agents,
    check_input_guardrail_response,
    run_input_guardrails,
)
from utils.llms import getllmByName


DEFAULT_PROMPT = (
    "Write a Python function that takes a list of numbers and returns the sum of the squares of those numbers."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the guardrail workflow.")
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="User prompt to classify.",
    )
    parser.add_argument(
        "--context-file",
        default="projects_context/1.json",
        help="Path to the company context JSON file.",
    )
    parser.add_argument(
        "--llm",
        default="openrouter_gemini25",
        help="LLM key configured in utils.llms.getllmByName.",
    )
    parser.add_argument(
        "--strictness",
        type=int,
        default=70,
        help="Guardrail strictness from 0 to 100.",
    )
    return parser.parse_args()


async def run_workflow(prompt: str, context_file: str, llm_name: str, strictness: int) -> dict:
    llm = getllmByName(llm_name)
    if llm is None:
        raise RuntimeError(
            f"LLM '{llm_name}' is not available. Check your environment variables and utils/llms.py."
        )

    company_context = company_context_from_json_file(context_file)
    struct_context = company_context_to_struct(company_context)
    context_agent, threat_agent = await build_input_guardrail_agents(llm)

    result = await run_input_guardrails(
        prompt=prompt,
        company_context=struct_context,
        chat_history=[],
        context_agent=context_agent,
        threat_agent=threat_agent,
        sensitive_agent=None,
        strictness=strictness,
    )

    is_allowed, rejection_reasons = check_input_guardrail_response(result)
    return {
        "is_allowed": is_allowed,
        "rejection_reasons": rejection_reasons,
        "result": result,
    }


async def main() -> None:
    args = parse_args()
    output = await run_workflow(
        prompt=args.prompt,
        context_file=args.context_file,
        llm_name=args.llm,
        strictness=args.strictness,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())



