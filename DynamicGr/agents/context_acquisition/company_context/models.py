
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict


class WeakField(BaseModel):
    field_path: str
    issue: str  # "missing_evidence | low_confidence | partially_inferred"
    comment: str


class Conflict(BaseModel):
    field_path: str
    sources_involved: List[str]
    conflict_description: str
    # "prefer_new_evidence | prefer_existing_context | undecided_requires_human_review"
    resolution_strategy: str


class ManualReviewRecommendation(BaseModel):
    field_path: str
    reason: str


class Reasoning(BaseModel):
    weak_fields: List[WeakField] = []
    conflicts: List[Conflict] = []
    manual_review_recommendations: List[ManualReviewRecommendation] = []

# Models for TechnicalContext


class RolePermission(BaseModel):
    role: str
    allowed_actions: List[str]


class Relations(BaseModel):
    references: str = ""


class TableInfo(BaseModel):
    name: str
    type: str = ""
    description: str = ""
    description_metadata: str = Field(
        default="Represents the automatically inferred characterization of the table,"
        " derived from the statistical and semantic features of its columns (e.g., data types, naming patterns, relational structure, "
        "and usage frequency). The description conveys the functional and contextual role of the table within the broader database schema."
    )
    roles_permissions: List[RolePermission] = []
    relations: Relations = Relations()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: Any) -> str:
        if value is None:
            return ""
        return value


class DatabaseInfo(BaseModel):
    name: str
    tables: List[TableInfo] = []

    @field_validator("tables", mode="before")
    @classmethod
    def normalize_tables(cls, value: Any) -> List[Dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in value:
            if isinstance(item, str):
                normalized.append({"name": item})
            elif isinstance(item, dict):
                normalized.append(item)
        return normalized


class TechnicalContext(BaseModel):
    databases: List[DatabaseInfo] = []

    @field_validator("databases", mode="before")
    @classmethod
    def normalize_databases(cls, value: Any) -> List[Dict[str, Any]]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in value:
            if isinstance(item, str):
                normalized.append({"name": item, "tables": []})
            elif isinstance(item, dict):
                # Ensure minimum shape so partial model outputs still parse.
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    normalized.append(item)
                else:
                    normalized.append({"name": "unknown", **item})
        return normalized

# Models  business_context


class BorderlineTopic(BaseModel):
    topic: str
    decision: str  # "allow_with_review | redirect | block"
    reason: str


class ScopeDefinitions(BaseModel):
    in_scope_topics: List[str] = []
    out_of_scope_topics: List[str] = []
    borderline_topics: List[BorderlineTopic] = []


class VocabularyClassification(BaseModel):
    common_entities: List[str] = []
    common_entities_description: str = Field(
        default="terms with high frequency in general business vocabulary but also high frequency in company sources"
    )
    company_specific_terms: List[str] = []
    company_specific_terms_description: str = Field(
        default="terms with low frequency in general vocabulary but high frequency in company sources"
    )
    description: str = Field(
        default="Vocabulary automatically extracted from knowledge sources for context classification"
    )


class BusinessContext(BaseModel):
    departments: List[str] = []
    roles: List[str] = []
    scope_definitions: ScopeDefinitions = ScopeDefinitions()
    vocabulary_classification: VocabularyClassification = VocabularyClassification()


class OrgProfile(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    regions: List[str] = []
    size: Optional[str] = None
    core_mission: Optional[str] = None
    public_description: Optional[str] = None


class PoliciesAttributes(BaseModel):
    internal_policies: List[str] = Field(
        default_factory=list,
        description="Company-specific internal policies identified from organizational sources.",
    )
    excluded_safety_rules: List[str] = Field(
        default_factory=list,
        description="Baseline guardrail rules (e.g., S1-S20) explicitly excluded or overridden by company policy when conflict is documented.",
    )


class SensitivityPattern(BaseModel):
    variable_name: str = ""
    pattern: str = ""


class DataClassification(BaseModel):
    high_sensitivity: List[str] = []
    low_sensitivity: List[str] = []


class DataSensitivityRules(BaseModel):
    pii: List[SensitivityPattern] = []
    mnpi_keywords: List[SensitivityPattern] = []
    data_classification: DataClassification = DataClassification()


class EnterpriseTopicContext(BaseModel):
    org_profile: OrgProfile = OrgProfile()
    technical_context: TechnicalContext = TechnicalContext()
    business_context: BusinessContext = BusinessContext()


class CompanyContext(BaseModel):
    enterpriseTopicContext: EnterpriseTopicContext = EnterpriseTopicContext()
    policies_attributes: PoliciesAttributes = PoliciesAttributes()
    data_sensitivity_rules: DataSensitivityRules = DataSensitivityRules()
    reasoning: Reasoning = Reasoning()


class StructPolicies(BaseModel):
    default_policies: List[str] = Field(
        default_factory=list
    )
    custom_policies: List[str] = Field(
        default_factory=list
    )


class StructCompanyContext(BaseModel):
    enterpriseTopicContext: EnterpriseTopicContext = EnterpriseTopicContext()
    structPolicies: StructPolicies = StructPolicies()
    data_sensitivity_rules: DataSensitivityRules = DataSensitivityRules()
    reasoning: Reasoning = Reasoning()
