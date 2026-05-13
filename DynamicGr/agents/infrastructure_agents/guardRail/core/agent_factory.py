
from agents.infrastructure_agents.guardRail.core.base_agent import GuardrailAgent


class GuardrailAgentFactory:
    """ Regist the agents"""

    _registry = {}  # simple registry

    @classmethod
    def register(cls, name, spec):
        """Regist a new GuardrailAgent spec."""
        cls._registry[name] = spec

    @classmethod
    async def create(cls, name, model, tools=None, on_reasoning_update=None):
        """Create an instance of a registered GuardrailAgent."""
        if name not in cls._registry:
            raise ValueError("Agent '{}' not registered.".format(name))

        spec = cls._registry[name]
        return await GuardrailAgent.ainit(
            name=name,
            model=model,
            tools=tools,
            spec=spec,
            on_reasoning_update=on_reasoning_update
        )
