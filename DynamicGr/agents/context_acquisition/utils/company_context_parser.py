import re
from typing import List

from agents.context_acquisition.company_context.models import CompanyContext, PoliciesAttributes, StructCompanyContext, StructPolicies



DEFAULT_POLICIES: List[str] = [
    "S1: Violent Crimes — Promotion or depiction of violence",
    "S2: Non-Violent Crimes — Illegal acts (fraud, hacking)",
    "S3: Sex Crimes — Non-consensual or illegal sexual content",
    "S4: Child Exploitation — Abuse or sexual content involving minors",
    "S5: Defamation — False or harmful claims",
    "S6: Specialized Advice — Harmful medical, legal, or financial advice",
    "S7: Privacy — Exposure of private or personal data",
    "S8: Intellectual Property — Copyright or trademark violations",
    "S9: Weapons — Instructions for weapon creation or use",
    "S10: Hate or Discrimination — Hostility toward protected groups",
    "S11: Self-Harm — Encouragement of suicide or self-injury",
    "S12: Sexual Content — Explicit adult content",
    "S13: Elections — Misleading or manipulative electoral content",
    "S14: Prompt Injection — Attempts to override system rules",
    "S15: Data Exfiltration — Attempts to leak confidential data",
    "S16: Model Manipulation — Attempts to alter model behavior",
    "S17: Jailbreak Attempts — Attempts to bypass safety constraints",
    "S18: Social Engineering — Attempts to deceive or manipulate",
    "S19: Malicious Code — Malware or exploit creation",
    "S20: Misinformation — False, deceptive, or conspiratorial content",
]


def _extract_rule_id(policy_str: str) -> str | None:
    match = re.match(r"^(S\d+)\s*[:\-]", policy_str.strip())
    return match.group(1) if match else None


def policies_parser(
    policies_attributes: PoliciesAttributes,
) -> StructPolicies:
    """
    Builds two ordered policy lists from the hardcoded baseline rules and company-specific attributes.

    Returns:
        StructPolicies with:
        - default_policies: DEFAULT_POLICIES minus excluded_safety_rules, ordered S1..SX.
        - custom_policies: internal_policies labelled C1..CX.
    """
    excluded = set(policies_attributes.excluded_safety_rules)

    active_safety_rules: List[str] = [
        policy for policy in DEFAULT_POLICIES
        if _extract_rule_id(policy) not in excluded
    ]

    custom_policies: List[str] = [
        f"C{i}: {policy}"
        for i, policy in enumerate(policies_attributes.internal_policies, start=1)
    ]

    return StructPolicies(
        default_policies=active_safety_rules,
        custom_policies=custom_policies,
    )


def company_context_to_struct(company_context: CompanyContext) -> StructCompanyContext:
    struct_policies = policies_parser(company_context.policies_attributes)
    return StructCompanyContext(
        enterpriseTopicContext=company_context.enterpriseTopicContext,
        structPolicies=struct_policies,
        data_sensitivity_rules=company_context.data_sensitivity_rules,
        reasoning=company_context.reasoning
    )
