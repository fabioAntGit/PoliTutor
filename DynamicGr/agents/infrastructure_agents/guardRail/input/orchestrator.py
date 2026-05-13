import asyncio
import time
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.messages import BaseMessage
from agents.context_acquisition.company_context.models import DataSensitivityRules, EnterpriseTopicContext, StructCompanyContext, StructPolicies
from agents.infrastructure_agents.guardRail.core.base_agent import GuardrailAgent
from agents.infrastructure_agents.guardRail.input.context_agent.agent import get_context_agent_executer
from agents.infrastructure_agents.guardRail.input.threat_compliance_agent.agent import get_threat_compliance_agent_executer


async def build_input_guardrail_agents(llm, on_step=None):

    context_agent = await get_context_agent_executer(llm, on_step=(
        lambda msg: on_step("reasoning_update", msg, "context_agent")) if on_step else None)

    threat_agent = await get_threat_compliance_agent_executer(llm, on_step=(
        lambda msg: on_step("reasoning_update", msg, "threat_agent")) if on_step else None)

    return context_agent, threat_agent


def get_company_context(company_context: StructCompanyContext) -> tuple[EnterpriseTopicContext, StructPolicies, DataSensitivityRules]:
    enterpriseTopicContext: EnterpriseTopicContext = company_context.enterpriseTopicContext
    policies_attributes: StructPolicies = company_context.structPolicies
    data_sensitivity_rules: DataSensitivityRules = company_context.data_sensitivity_rules
    return enterpriseTopicContext, policies_attributes, data_sensitivity_rules


def _normalize_layer1_results(topic_result: Any, threat_result: Any) -> Dict[str, Any]:
    """Normalize agent outputs in one place to keep run_layer1 clean and predictable."""

    topic_check = getattr(topic_result, "topic", None)
    topic_reason = getattr(topic_result, "reasoning", None)

    threat_check = getattr(threat_result, "safety", None)
    threat_reason = getattr(threat_result, "reasoning", None)
    if threat_reason in (None, "None", ""):
        threat_reason = "No threats detected"

    print(
        f"[DEBUG _normalize_layer1_results] Extracted - topic_check: {topic_check}, threat_check: {threat_check}")

    return {
        "topic_check": topic_check,
        "topic_reason": topic_reason,
        "threat_check": threat_check,
        "threat_reason": threat_reason,
    }


async def run_layer1(
    prompt: str,
    company_context: StructCompanyContext,
    chat_history: List[BaseMessage],
    context_agent: GuardrailAgent,
    threat_agent: GuardrailAgent,
    strictness: int = 70,
    thread_id: str = "default-thread",
) -> Dict[str, Any]:

    enterpriseTopicContext, policies_attributes, _data_sensitivity_rules = get_company_context(
        company_context)

    start_time = time.time()
    tasks = {
        "topic": asyncio.create_task(
            context_agent.arun({
                "input": prompt,
                "enterpriseTopicContext": enterpriseTopicContext,
                "strictness": strictness,
                "config": {"thread_id": thread_id}
            })
        ),
        "threat": asyncio.create_task(
            threat_agent.arun({
                "input": prompt,
                "chat_history": chat_history,
                "default_policies": policies_attributes.default_policies,
                "custom_policies": policies_attributes.custom_policies,
                "strictness": strictness,
                "config": {"thread_id": thread_id}
            })
        ),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    results_map = dict(zip(tasks.keys(), results))

    # Handle async task failures in one centralized place.
    for task_name, task_result in results_map.items():
        if isinstance(task_result, Exception):
            print(
                f"[DEBUG run_layer1] Task {task_name} failed with exception: {task_result}")
            results_map[task_name] = None

    total_latency = time.time() - start_time

    topic_result = results_map.get("topic")
    threat_result = results_map.get("threat")
    normalized_results = _normalize_layer1_results(topic_result, threat_result)

    return {
        "topic_check": normalized_results["topic_check"],
        "topic_reason": normalized_results["topic_reason"],
        "threat_check": normalized_results["threat_check"],
        "threat_reason": normalized_results["threat_reason"],
        "overall_latency": total_latency,
    }


async def run_input_guardrails(
    prompt: str,
    company_context: StructCompanyContext,
    chat_history: List[BaseMessage],
    context_agent: GuardrailAgent,
    threat_agent: GuardrailAgent,
    sensitive_agent: Any,
    strictness: int = 70,
    data_masking: bool = False,
    thread_id: str = "default-thread",
    on_step: Optional[Any] = None,
) -> Dict[str, Any]:

    # Layer 1: Context and Threat Analysis
    layer1_results = await run_layer1(
        prompt,
        company_context,
        chat_history,
        context_agent,
        threat_agent,
        strictness,
        thread_id
    )
    return {**layer1_results,
            "layer0_passed": True}


def check_input_guardrail_response(result: Dict[str, Any], logs: bool = False) -> Tuple[bool, List[str]]:
    """Validates the output of input guardrails and collects rejection reasons."""

    is_allowed = True
    rejection_reasons = []

    if result.get("topic_check") == "OFF_TOPIC":
        is_allowed = False
        rejection_reasons.append(result.get("topic_reason"))

    if result.get("threat_check") == "UNSAFE":
        is_allowed = False
        rejection_reasons.append(result.get("threat_reason"))

    if logs and rejection_reasons:
        print(f"Guardrail rejected prompt: {rejection_reasons}")

    return is_allowed, rejection_reasons
