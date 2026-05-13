import json
from typing import Any, Dict, List
from langchain_core.language_models import BaseLanguageModel
from agents.infrastructure_agents.guardRail.context_acquisition.utils.context_budget import resolve_max_chars_from_model_profile


MAX_CONTEXT_CHARS_PER_ITERATION = 48000


def _resolve_max_chars_per_iteration(
    model: BaseLanguageModel,
    default_max_chars: int,
) -> int:
    # This profile attribute is in beta, so we keep a safe fallback path.
    return resolve_max_chars_from_model_profile(model, default_max_chars)


def chunk_source_parts(
    parts: List[Dict[str, Any]],
    model: BaseLanguageModel,
    max_chars_per_iteration: int = MAX_CONTEXT_CHARS_PER_ITERATION,
) -> List[List[Dict[str, Any]]]:
    if not parts:
        return []
    max_chars_per_iteration = _resolve_max_chars_per_iteration(
        model,
        max_chars_per_iteration,
    )

    chunks: List[List[Dict[str, Any]]] = []
    current_chunk: List[Dict[str, Any]] = []
    current_size = 0

    for part in parts:
        part_size = len(json.dumps(part, ensure_ascii=False))

        if not current_chunk:
            current_chunk = [part]
            current_size = part_size
            continue

        if current_size + part_size <= max_chars_per_iteration:
            current_chunk.append(part)
            current_size += part_size
            continue

        chunks.append(current_chunk)
        current_chunk = [part]
        current_size = part_size

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def agent_input_preparation(company_id, current_context, idx, chunk, parts_chunks):
    source_classifier_plan_payload = {
        "company_id": company_id,
        "chunk_index": idx,
        "total_chunks": len(parts_chunks),
        "source_parts": chunk,
    }

    agent_inputs = {
        "company_information_batch": json.dumps(source_classifier_plan_payload, ensure_ascii=False),
    }
    debug_agent_inputs = {
        "company_information_batch": source_classifier_plan_payload,
    }

    if current_context is not None:
        agent_inputs["organization_context"] = json.dumps(
            current_context.model_dump(),
            ensure_ascii=False,
        )
        debug_agent_inputs["organization_context"] = current_context.model_dump(
        )

    else:
        agent_inputs["organization_context"] = json.dumps(
            {}, ensure_ascii=False)
        debug_agent_inputs["organization_context"] = {}
    return agent_inputs, debug_agent_inputs, source_classifier_plan_payload
