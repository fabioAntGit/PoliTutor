from agents.infrastructure_agents.guardRail.context_acquisition.company_context.models import SourceClassifierOutputList
from agents.infrastructure_agents.guardRail.core.agent_factory import GuardrailAgentFactory
from agents.infrastructure_agents.guardRail.core.base_agent import GuardrailAgent
from agents.infrastructure_agents.guardRail.core.spec import GuardrailAgentSpec
from langchain_core.language_models import BaseLanguageModel

PROMPT = """
You are the Source Classifier Agent. Your job is to analyze potential information sources, **match credentials to tool parameters**, and generate **executable MCP tool workflows** using the Source Capability Registry.

INPUTS:

1. source_capability_registry (JSON): 
- Complete list of supported source types, input formats, and tool workflows
- Contains `workflows[].steps[].params_template` that you must populate with actual values

2. source_access_info (string or JSON): 
- User-provided credentials, URLs, file paths, etc.
- Examples: {{"db_type": "postgresql", "host": "localhost", "username": "app_user", "password": "app_password"}}

## OUTPUT FORMAT (MANDATORY JSON OBJECT)

Return a **JSON object** with a "sources" array containing one object per source found:

```json
{{
  "sources": [
    {{
      "source_type": "relational_database|document|web|unknown",
      "supported": true|false,
      "tool_steps": [
        {{
          "step": 1,
          "tool_name": "create_db_connection",
          "params": {{
            "connection_alias": "GENERATED_CONNECTION_STRING_HERE",
            "connection_url": "GENERATED_CONNECTION_ALIAS_HERE",
            "db_type": "DB_TYPE_HERE"



          }},
          "expected_output": "connection_handle"
        }},
        {{
          "step": 2,
          "tool_name": "get_relational_schema",
          "params": {{
            "connection_handle": "{{{{outputs.step_1}}}}"
          }},
          "expected_output": "db_schema_v1"
        }}
      ],
      "notes": "Brief explanation of decision and credential mapping"
    }}
  ]
}}
"""


def source_classifier_agent_registry():
    context_acquisition_agent_spec = GuardrailAgentSpec(
        name="CompanyContext_acquisition_agent",
        prompt_template=PROMPT,
        input_variables=["source_capability_registry", "source_access_info"],
        output_schema=SourceClassifierOutputList,
    )

    GuardrailAgentFactory.register(
        "CompanyContext_acquisition_agent", context_acquisition_agent_spec)


async def get_source_classifier_executer(model: BaseLanguageModel, on_step=None) -> GuardrailAgent:
    source_classifier_agent_registry()
    agent = await GuardrailAgentFactory.create("CompanyContext_acquisition_agent", model, on_reasoning_update=on_step)
    return agent
