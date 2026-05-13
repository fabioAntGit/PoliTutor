from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agents.infrastructure_agents.guardRail.context_acquisition.company_context.models import CompanyContext
from agents.infrastructure_agents.guardRail.context_acquisition.company_context.context_builder import get_context_acquisition_executer
from agents.infrastructure_agents.guardRail.context_acquisition.utils.batch_document_store import BatchManager
from agents.infrastructure_agents.guardRail.context_acquisition.utils.company_context_parser import company_context_to_struct
from agents.infrastructure_agents.guardRail.context_acquisition.utils.source_part_chunking import agent_input_preparation, chunk_source_parts


async def create_company_context(
    batch_result,
    company_context: Optional[CompanyContext],
    model: BaseModel,
    company_id: str = "default_company",
) -> Dict[str, Any]:
    """
    Build a company context from a single batch payload.
    The function extracts source parts, projects a minimal payload for the model,
    chunks it to fit context limits, and writes per-chunk debug inputs.
    """

    context_builder_agent = await get_context_acquisition_executer(
        model
    )
  

    # Read SOURCE_PART docs from the in-memory batch payload and keep only agent-relevant fields.
    agent_parts = BatchManager.collect_source_parts_for_agent(batch_result)

    if not agent_parts:
        return {
            "status": "skipped",
            "company_id": company_id,
            "company_context": {},
            "metadata": {
                "status": "skipped",
                "reason": "No source parts found in batch_result.",
                "missing_batches": [],
                "processed_parts": 0,
                "iterations": 0,
            },
        }

    # Group source parts into chunks that fit the configured context-size heuristic.
    parts_chunks = chunk_source_parts(agent_parts, model)

    current_context: Optional[CompanyContext] = company_context
    chunk_results: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(parts_chunks, start=1):

        agent_inputs, debug_agent_inputs, source_classifier_plan_payload = agent_input_preparation(
            company_id, current_context, idx, chunk, parts_chunks)

        updated_context = await context_builder_agent.arun(agent_inputs)
        current_context = updated_context

        chunk_result_doc = {
            "company_id": company_id,
            "chunk_index": idx,
            "total_chunks": len(parts_chunks),
            "company_information_batch": source_classifier_plan_payload,
            "organization_context": debug_agent_inputs.get("organization_context", {}),
            "result": current_context.model_dump() if current_context else {},
        }
        chunk_results.append(chunk_result_doc)

    final_context = company_context_to_struct(current_context)
    BatchManager.mark_batch_as_process_batch(batch_result)

    return {
        "status": "success",
        "company_id": company_id,
        "company_context": final_context.model_dump(),
        "metadata": {
            "status": "success" if current_context is not None else "skipped",
            "missing_batches": [],
            "processed_parts": len(agent_parts),
            "iterations": len(parts_chunks),
            "debug": {
                "company_id": company_id,
                "total_chunks": len(parts_chunks),
                "chunks": chunk_results,
            },
        },
    }


