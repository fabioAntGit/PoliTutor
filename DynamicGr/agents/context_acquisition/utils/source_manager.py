import json
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from pydantic import BaseModel

from agents.infrastructure_agents.guardRail.context_acquisition.tools import (
    execute_csv,
    execute_db,
    execute_fl,
    execute_web,
    normalize_csv,
    normalize_db,
    normalize_fl,
    normalize_web,
)
from agents.infrastructure_agents.guardRail.context_acquisition.utils.context_budget import resolve_max_chars_from_model_profile


MAX_SOURCE_PART_CHARS = 16000


class SourceManager:
    """Handles source tool execution and normalization for ingestion."""

    def __init__(self, model: BaseModel, source_folder: Path | None = None):
        self.model = model
        self.source_folder = source_folder

    async def _call_fl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return execute_fl(self.source_folder)

    async def _call_web(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await execute_web(params)

    async def _call_db(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return execute_db(params)

    async def _call_csv(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return execute_csv(params)

    def _tool_handlers(self) -> Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]]:
        return {
            "FL": self._call_fl,
            "WEB": self._call_web,
            "DB": self._call_db,
            "CSV": self._call_csv,
        }

    @staticmethod
    def _normalizers() -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
        return {
            "FL": normalize_fl,
            "WEB": normalize_web,
            "DB": normalize_db,
            "CSV": normalize_csv,
        }

    async def call_tool(self, source_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._tool_handlers().get(source_type)
        if handler is None:
            raise ValueError(f"Unknown source_type: {source_type}")
        return await handler(params)

    @staticmethod
    def _normalize_default(tool_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": tool_result.get("status", "unknown"),
            "summary": {},
            "content": [{"data": tool_result}],
        }

    @classmethod
    def normalize_tool_output(cls, source_type: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        normalizer = cls._normalizers().get(source_type, cls._normalize_default)
        return normalizer(tool_result)

    @staticmethod
    def split_normalized_items(
        source_type: str,
        normalized_result: Dict[str, Any],
        model: BaseModel | None = None,
        max_chars: int = MAX_SOURCE_PART_CHARS,
    ) -> list[Dict[str, Any]]:
        max_chars = resolve_max_chars_from_model_profile(model, max_chars)

        content = normalized_result.get("content", [])
        summary = normalized_result.get("summary", {})
        status = normalized_result.get("status", "unknown")

        if not content:
            return [
                {
                    "part_index": 1,
                    "total_parts": 1,
                    "payload": {
                        "source_type": source_type,
                        "status": status,
                        "summary": summary,
                        "content": [],
                    },
                }
            ]

        parts: list[Dict[str, Any]] = []
        current_content: list[Dict[str, Any]] = []
        base_payload = {
            "source_type": source_type,
            "status": status,
            "summary": summary,
        }

        def payload_size(candidate_content: list[Dict[str, Any]]) -> int:
            payload = {**base_payload, "content": candidate_content}
            return len(json.dumps(payload, ensure_ascii=False))

        for content_item in content:
            candidate_content = [*current_content, content_item]
            if current_content and payload_size(candidate_content) > max_chars:
                parts.append(
                    {
                        "part_index": len(parts) + 1,
                        "total_parts": 0,
                        "payload": {**base_payload, "content": current_content},
                    }
                )
                current_content = [content_item]
            else:
                current_content = candidate_content

        if current_content:
            parts.append(
                {
                    "part_index": len(parts) + 1,
                    "total_parts": 0,
                    "payload": {**base_payload, "content": current_content},
                }
            )

        total_parts = len(parts)
        for part in parts:
            part["total_parts"] = total_parts

        return parts

    async def execute_source(self, source_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_result = await self.call_tool(source_type, params)
        normalized_result = self.normalize_tool_output(source_type, tool_result)
        split_parts = self.split_normalized_items(
            source_type,
            normalized_result,
            model=self.model,
        )
        return {
            "normalized_result": normalized_result,
            "split_parts": split_parts,
        }
