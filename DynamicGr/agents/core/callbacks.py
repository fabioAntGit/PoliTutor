import time
from langchain_core.callbacks import BaseCallbackHandler


class StreamingReasoningCallback(BaseCallbackHandler):
    """Streams actual LLM reasoning + tool usage for Mongo agent."""

    def __init__(self, on_reasoning_update=None):
        self.on_reasoning_update = on_reasoning_update

    def on_llm_new_token(self, token, **kwargs):
        """Stream token-by-token real reasoning."""
        if self.on_reasoning_update and token.strip():
            self.on_reasoning_update(token)

    def on_tool_start(self, serialized, input_str, **kwargs):
        """When a tool is called, notify UI."""
        if self.on_reasoning_update:
            tool_name = serialized.get("name", "unknown")
            self.on_reasoning_update(
                f"\nUsing tool: {tool_name}\nInput: {input_str}\n")

    def on_tool_end(self, output, **kwargs):
        """When a tool finishes, show result summary."""
        if self.on_reasoning_update:
            self.on_reasoning_update(
                f"\nTool completed. Output snippet:\n{str(output)[:400]}\n")
    
    def on_llm_end(self, response, **kwargs):
        """Mark completion of reasoning."""
        if self.on_reasoning_update:
            self.on_reasoning_update("\nEnd of agent action.\n")


class StreamRelayCallback:
    def __init__(self, on_step, agent_name: str):
        self.on_step = on_step
        self.agent_name = agent_name
        self._buffer = ""
        self._last_flush = time.time()

    def __getattr__(self, name):
        def noop(*args, **kwargs):
            return None
        return noop

    def _flush(self):
        text = self._buffer.strip()
        if text and self.on_step:
            self.on_step("reasoning_update", text, self.agent_name)
        self._buffer = ""
        self._last_flush = time.time()

    def on_llm_new_token(self, token, **kwargs):
        if not self.on_step or not token or not token.strip():
            return
        self._buffer += token
        now = time.time()
        if any(p in token for p in (".", "!", "?", "\n")) or len(self._buffer) > 120 or (now - self._last_flush) > 0.6:
            self._flush()

    def on_llm_end(self, response, **kwargs):
        self._flush()
        if self.on_step:
            self.on_step("reasoning_update",
                         "\nAgent action ended.", self.agent_name)

    def on_tool_start(self, serialized, input_str, **kwargs):
        if self.on_step:
            tool_name = (serialized or {}).get("name", "unknown")
            self.on_step("reasoning_update",
                         f"\nUsing tool: {tool_name}", self.agent_name)

    def on_tool_end(self, output, **kwargs):
        if self.on_step:
            self.on_step("reasoning_update",
                         "\nTool completed. Summary received.", self.agent_name)
