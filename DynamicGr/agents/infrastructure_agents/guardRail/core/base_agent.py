from typing import Any, List, Optional
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel
from agents.core.callbacks import StreamingReasoningCallback
from agents.core.agent_creation import create_output_parser, to_state
from agents.infrastructure_agents.core.agent_wrapper import AgentWrapper

from agents.infrastructure_agents.guardRail.core.spec import GuardrailAgentSpec


class GuardrailAgent:
    TOOL_CALL_RUN_LIMIT = 4

    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        spec: GuardrailAgentSpec,
        tools: Optional[List[Any]] = None,
        on_reasoning_update=None,
        executor: AgentWrapper = None,

    ):
        self.name = name
        self.model = model
        self.spec = spec
        self.on_reasoning_update = on_reasoning_update
        self.callback = StreamingReasoningCallback(on_reasoning_update)
        self.output_parser = create_output_parser(self.spec.output_schema)
        self.executor: AgentWrapper = executor

    @classmethod
    async def ainit(
        cls,
        name: str,
        model: BaseLanguageModel,
        spec: GuardrailAgentSpec,
        tools: Optional[List[Any]] = None,
        on_reasoning_update=None,
    ):
        self = cls(
            name=name,
            model=model,
            spec=spec,
            tools=tools,
            on_reasoning_update=on_reasoning_update,
        )
        self.executor = await self._create_executor()
        return self
    

   

    # ------------------------------
    # Modular executor creation
    # ------------------------------
    async def _create_executor(self):
       
        return self._create_standard_agent()

   
    # ------------------------------
    # MCP agent
    # ------------------------------

    

    # ------------------------------
    # Standard agent (without tools)
    # ------------------------------

    def _create_standard_agent(self):
        prompt, _ = self._build_prompt()
        runnable = RunnableSequence(prompt | self.model | self.output_parser)
        return AgentWrapper(runnable, callbacks=[self.callback])

    # ------------------------------
    # Build dynamic prompt
    # ------------------------------
    def _build_prompt(self):
        if self.spec.structured_prompt:
            return ChatPromptTemplate.from_messages(self.spec.structured_prompt)
        else:
            messages = [
                ("system", self.spec.prompt_template or "You are an assistant.")]
            for var_name in self.spec.input_variables:
                if var_name in ["input", "chat_history"]:
                    messages.append(("human", f"{{{var_name}}}"))
                else:
                    messages.append(("assistant", f"{{{var_name}}}"))
            return ChatPromptTemplate.from_messages(messages), messages

    # ------------------------------
    # Run / Async Run
    # ------------------------------

    def run(self, inputs: dict, config: dict = None):
        state = inputs
        return self.executor.invoke(state, config=config)

    async def arun(self, inputs: dict, config: dict = None):
        state = inputs
        return await self.executor.ainvoke(state, config=config)


