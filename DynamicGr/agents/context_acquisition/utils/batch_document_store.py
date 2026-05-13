import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


DOC_TYPES = {
    "BATCH": "BATCH",
    "SOURCE_RUN": "SOURCE_RUN",
    "SOURCE_PART": "SOURCE_PART",
}


def generate_batch_id(company_id: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"batch_{company_id}_{timestamp}"


def generate_source_id(source_type: str, index: int) -> str:
    return f"{source_type.lower()}_{index:03d}"


def generate_source_part_id(source_id: str, part_index: int) -> str:
    return f"{source_id}_part_{part_index:02d}"


class BatchManager:
    """Single manager for batch lifecycle: build, store, read, and project."""
    @staticmethod
    def create_batch(company_id: str) -> Dict[str, Any]:
        return {
            "doc_type": DOC_TYPES["BATCH"],
            "batch_id": generate_batch_id(company_id),
            "company_id": company_id,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "source_runs": [],
        }

    @staticmethod
    def create_source_run(
        batch_id: str,
        company_id: str,
        source_type: str,
        params: Dict[str, Any],
        normalized_result: Dict[str, Any],
        source_index: int,
    ) -> Dict[str, Any]:
        return {
            "doc_type": DOC_TYPES["SOURCE_RUN"],
            "source_id": generate_source_id(source_type, source_index),
            "batch_id": batch_id,
            "company_id": company_id,
            "source_type": source_type,
            "params": params,
            "status": normalized_result.get("status", "unknown"),
            "summary": normalized_result.get("summary", {}),
            "processed": False,
            "source_parts": [],
        }
    @staticmethod
    def create_source_parts(source_id: str, parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "doc_type": DOC_TYPES["SOURCE_PART"],
                "source_part_id": generate_source_part_id(source_id, part["part_index"]),
                "source_id": source_id,
                "part_index": part["part_index"],
                "total_parts": part["total_parts"],
                "payload": part["payload"],
            }
            for part in parts
        ]
    @staticmethod
    def create_batch_documents(
        batch_doc: Dict[str, Any],
        source_runs: List[Dict[str, Any]],
        source_parts: List[Dict[str, Any]],
    ):

        batch_doc["source_runs"] = [source_run["source_id"]
                                    for source_run in source_runs]
        batch_doc["status"] = "pendingBatch"

        all_docs = [batch_doc, *source_runs, *source_parts]
        return all_docs

    @staticmethod
    def mark_batch_as_process_batch(batch_docs: Any) -> bool:
        """Mark first BATCH document status as processBatch. Returns True when updated."""
        docs = list(batch_docs)
        for doc in docs:
            if doc.get("doc_type") == DOC_TYPES["BATCH"]:
                doc["status"] = "processBatch"
                return True
        return False

    @staticmethod
    def collect_source_parts(batch_docs: Any) -> List[Dict[str, Any]]:
        docs = list(batch_docs)
        if not docs:
            return []

        source_run_by_id = {
            doc["source_id"]: doc
            for doc in docs
            if doc.get("doc_type") == DOC_TYPES["SOURCE_RUN"] and doc.get("source_id")
        }
        source_part_by_id = {
            doc["source_part_id"]: doc
            for doc in docs
            if doc.get("doc_type") == DOC_TYPES["SOURCE_PART"] and doc.get("source_part_id")
        }

        if not source_part_by_id:
            return []

        batch_doc = next((doc for doc in docs if doc.get(
            "doc_type") == DOC_TYPES["BATCH"]), None)
        ordered_source_ids = batch_doc.get(
            "source_runs", []) if batch_doc else list(source_run_by_id.keys())

        ordered_parts: List[Dict[str, Any]] = []
        for source_id in ordered_source_ids:
            source_run = source_run_by_id.get(source_id)
            if not source_run:
                continue
            for source_part_id in source_run.get("source_parts", []):
                part = source_part_by_id.get(source_part_id)
                if part:
                    ordered_parts.append(part)

        if ordered_parts:
            return ordered_parts

        return sorted(
            source_part_by_id.values(),
            key=lambda p: (p.get("source_id", ""), p.get("part_index", 0)),
        )

    @staticmethod
    def project_source_parts_for_agent(parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "source_part_id": part.get("source_part_id", ""),
                "source_id": part.get("source_id", ""),
                "part_index": part.get("part_index", 0),
                "total_parts": part.get("total_parts", 0),
                "payload": {
                    "content": part.get("payload", {}).get("content", []),
                },
            }
            for part in parts
        ]

    @staticmethod
    def collect_source_parts_for_agent(batch_docs: Any) -> List[Dict[str, Any]]:
        """Collect SOURCE_PART docs in order and return only agent-relevant fields."""
        collected_parts = BatchManager.collect_source_parts(batch_docs)
        return BatchManager.project_source_parts_for_agent(collected_parts)
