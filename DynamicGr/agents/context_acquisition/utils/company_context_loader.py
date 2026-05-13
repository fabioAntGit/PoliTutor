"""Helpers to build CompanyContext objects from JSON payloads.

The project stores company context in two closely related shapes:
- CompanyContext: the runtime model used by the guardrail logic.
- StructCompanyContext: a normalized/exported shape that often appears in JSON files.

This module accepts either shape, including the common wrapper used by pipeline
outputs: {"status": ..., "final_result": {...}}.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from agents.context_acquisition.company_context.models import (
    CompanyContext,
    PoliciesAttributes,
    StructCompanyContext,
    StructPolicies,
)


_DEFAULT_POLICY_ID_PATTERN = re.compile(r"^(S\d+)\s*[:\-]")
_CUSTOM_POLICY_PATTERN = re.compile(r"^C\d+\s*[:\-]\s*(.*)$")


def _extract_rule_id(policy: str) -> str | None:
    match = _DEFAULT_POLICY_ID_PATTERN.match(policy.strip())
    return match.group(1) if match else None


def _strip_custom_prefix(policy: str) -> str:
    match = _CUSTOM_POLICY_PATTERN.match(policy.strip())
    return match.group(1).strip() if match else policy.strip()


def _load_json_source(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)

    if isinstance(source, Path):
        return json.loads(source.read_text(encoding="utf-8"))

    if isinstance(source, str):
        text = source.strip()
        if text.startswith("{") or text.startswith("["):
            return json.loads(text)

        path = Path(source)
        return json.loads(path.read_text(encoding="utf-8"))

    raise TypeError(f"Unsupported JSON source type: {type(source)!r}")


def _unwrap_final_result(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    final_result = payload.get("final_result")
    if isinstance(final_result, Mapping):
        return final_result
    return payload


def _normalize_sensitivity_patterns(values: Any) -> list[dict[str, str]]:
    if not isinstance(values, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in values:
        if isinstance(item, str):
            normalized.append({"variable_name": item, "pattern": item})
        elif isinstance(item, Mapping):
            variable_name = str(item.get("variable_name", "")).strip()
            pattern = str(item.get("pattern", "")).strip()
            normalized.append({"variable_name": variable_name, "pattern": pattern})
    return normalized


def _normalize_data_sensitivity_rules(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {}

    normalized = dict(payload)
    normalized["pii"] = _normalize_sensitivity_patterns(payload.get("pii"))
    normalized["mnpi_keywords"] = _normalize_sensitivity_patterns(payload.get("mnpi_keywords"))
    return normalized


def _infer_policies_attributes(struct_policies: StructPolicies) -> PoliciesAttributes:
    default_policy_ids = {
        _extract_rule_id(policy)
        for policy in struct_policies.default_policies
    }

    excluded_safety_rules = [
        policy_id
        for policy_id in (f"S{i}" for i in range(1, 21))
        if policy_id not in default_policy_ids
    ]

    internal_policies = [
        _strip_custom_prefix(policy)
        for policy in struct_policies.custom_policies
    ]

    return PoliciesAttributes(
        internal_policies=internal_policies,
        excluded_safety_rules=excluded_safety_rules,
    )


def company_context_from_json(
    source: str | Path | Mapping[str, Any],
) -> CompanyContext:
    """Build a CompanyContext from a JSON file, JSON string, or loaded dict.

    The function accepts:
    - a path to a JSON file
    - a JSON string
    - an already loaded dict

    It understands both raw CompanyContext payloads and the StructCompanyContext
    format found under ``final_result`` in pipeline outputs.
    """

    payload = _load_json_source(source)
    root = _unwrap_final_result(payload)

    normalized_root = dict(root)
    if isinstance(normalized_root.get("data_sensitivity_rules"), Mapping):
        normalized_root["data_sensitivity_rules"] = _normalize_data_sensitivity_rules(
            normalized_root["data_sensitivity_rules"]
        )

    if "structPolicies" in normalized_root:
        struct_context = StructCompanyContext.model_validate(normalized_root)
        return CompanyContext(
            enterpriseTopicContext=struct_context.enterpriseTopicContext,
            policies_attributes=_infer_policies_attributes(struct_context.structPolicies),
            data_sensitivity_rules=struct_context.data_sensitivity_rules,
            reasoning=struct_context.reasoning,
        )

    if "policies_attributes" not in normalized_root and "policiesAttributes" in normalized_root:
        normalized_root["policies_attributes"] = normalized_root.pop("policiesAttributes")

    if isinstance(normalized_root.get("data_sensitivity_rules"), Mapping):
        normalized_root["data_sensitivity_rules"] = _normalize_data_sensitivity_rules(
            normalized_root["data_sensitivity_rules"]
        )

    return CompanyContext.model_validate(normalized_root)


def company_context_from_json_file(path: str | Path) -> CompanyContext:
    """Convenience wrapper for JSON files on disk."""

    return company_context_from_json(path)
