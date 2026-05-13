from langchain_core.runnables import RunnableSequence
from typing import Any, List, Optional

class AgentWrapper:
    def __init__(self, executor:RunnableSequence, callbacks: Optional[List[Any]] = None):
        self.executor = executor
        self.callbacks = callbacks or []
    
    def invoke(self, inputs: dict, config: dict = None):
        cfg = config or {}
        if "callbacks" in cfg:
            cfg["callbacks"] = self.callbacks + cfg["callbacks"]
        else:
            cfg["callbacks"] = self.callbacks
        return self.executor.invoke(inputs, config=cfg)
    
    async def ainvoke(self, inputs: dict, config: dict = None):
        cfg = config or {}
        if "callbacks" in cfg:
            cfg["callbacks"] = self.callbacks + cfg["callbacks"]
        else:
            cfg["callbacks"] = self.callbacks
        return await self.executor.ainvoke(inputs, config=cfg)
    

