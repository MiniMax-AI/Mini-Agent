"""Tests for Agent interrupt/pause behavior."""

import asyncio

from mini_agent.agent import Agent
from mini_agent.schema import FunctionCall, LLMResponse, ToolCall
from mini_agent.tools.base import Tool, ToolResult


class StubLLM:
    """Fake LLM client returning predetermined responses."""

    def __init__(self):
        self.call_count = 0

        tool_calls = [
            ToolCall(
                id="call-1",
                type="function",
                function=FunctionCall(name="tool_a", arguments={}),
            ),
            ToolCall(
                id="call-2",
                type="function",
                function=FunctionCall(name="tool_b", arguments={}),
            ),
        ]
        self.tool_response = LLMResponse(
            content="",
            thinking=None,
            tool_calls=tool_calls,
            finish_reason="tool_calls",
        )
        self.final_response = LLMResponse(
            content="All done!",
            thinking=None,
            tool_calls=None,
            finish_reason="stop",
        )

    async def generate(self, messages, tools=None):
        if self.call_count == 0:
            self.call_count += 1
            return self.tool_response
        return self.final_response


class NotifyingTool(Tool):
    """Simple tool that records executions and can trigger an event."""

    def __init__(self, name: str, event: asyncio.Event | None = None):
        self._name = name
        self._event = event
        self.executions = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Test tool {self._name}"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        self.executions += 1
        if self._event and not self._event.is_set():
            self._event.set()
            await asyncio.sleep(0)  # Ensure the caller can observe the event
        return ToolResult(success=True, content=f"{self._name}-result")


async def _run_interrupt_preserves_tool_results(tmp_path):
    """Requesting stop mid-tool loop should still record all tool outputs."""

    llm = StubLLM()
    first_tool_event = asyncio.Event()

    tool_a = NotifyingTool("tool_a", event=first_tool_event)
    tool_b = NotifyingTool("tool_b")

    agent = Agent(
        llm_client=llm,
        system_prompt="System prompt",
        tools=[tool_a, tool_b],
        max_steps=3,
        workspace_dir=str(tmp_path),
    )

    agent.add_user_message("Run tools")

    run_task = asyncio.create_task(agent.run())

    # Wait until the first tool has executed, then request a stop
    await first_tool_event.wait()
    agent.request_stop()

    result = await run_task
    assert "interrupted" in result.lower()

    # Ensure both tool results exist in message history
    tool_messages = [m for m in agent.messages if m.role == "tool"]
    assert len(tool_messages) == 2
    assert {m.name for m in tool_messages} == {"tool_a", "tool_b"}


async def _run_agent_can_resume_after_interrupt(tmp_path):
    """Agent should continue the same run after being interrupted."""

    llm = StubLLM()
    tool_a_event = asyncio.Event()

    tool_a = NotifyingTool("tool_a", event=tool_a_event)
    tool_b = NotifyingTool("tool_b")

    agent = Agent(
        llm_client=llm,
        system_prompt="System prompt",
        tools=[tool_a, tool_b],
        max_steps=3,
        workspace_dir=str(tmp_path),
    )
    agent.add_user_message("Run tools")

    first_run = asyncio.create_task(agent.run())
    await tool_a_event.wait()
    agent.request_stop()
    await first_run

    # Resume run without adding new messages
    final_result = await agent.run()
    assert final_result == "All done!"

    tool_messages = [m for m in agent.messages if m.role == "tool"]
    assert len(tool_messages) == 2
    assert agent.current_step == 0  # Run completed and reset


def test_interrupt_preserves_tool_results(tmp_path):
    asyncio.run(_run_interrupt_preserves_tool_results(tmp_path))


def test_agent_can_resume_after_interrupt(tmp_path):
    asyncio.run(_run_agent_can_resume_after_interrupt(tmp_path))
