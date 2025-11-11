"""ACP Agent implementation for Mini-Agent.

This module implements the ACP Agent protocol, bridging between
ACP clients and Mini-Agent's internal agent implementation.
"""

import logging
from typing import Any
from uuid import uuid4

from acp import (
    AgentSideConnection,
    InitializeRequest,
    InitializeResponse,
    NewSessionRequest,
    NewSessionResponse,
    PromptRequest,
    PromptResponse,
    LoadSessionRequest,
    LoadSessionResponse,
    SetSessionModeRequest,
    SetSessionModeResponse,
    CancelNotification,
    session_notification,
    text_block,
    update_agent_message,
    update_agent_thought,
    start_tool_call,
    update_tool_call,
    tool_content,
    PROTOCOL_VERSION,
)
from acp.schema import AgentCapabilities, Implementation

from mini_agent.acp.converter import acp_content_to_text, message_to_acp_content
from mini_agent.acp.session import SessionManager
from mini_agent.llm import LLMClient
from mini_agent.schema.schema import Message

logger = logging.getLogger(__name__)


class MiniMaxACPAgent:
    """ACP Agent implementation that wraps Mini-Agent.

    Implements the ACP Agent protocol, providing:
    - Multiple concurrent sessions
    - Real-time streaming updates
    - Tool execution with permission requests
    - MiniMax-specific features (thinking blocks, unique tool format)
    """

    def __init__(
        self,
        conn: AgentSideConnection,
        llm_client: LLMClient,
        tools: list[Any],
        system_prompt: str,
    ):
        """Initialize ACP agent.

        Args:
            conn: ACP connection for client communication
            llm_client: LLM client instance
            tools: Available tools
            system_prompt: System prompt
        """
        self._conn = conn
        self._session_manager = SessionManager(llm_client, tools, system_prompt)
        self._session_counter = 0

    async def initialize(self, params: InitializeRequest) -> InitializeResponse:
        """Handle ACP initialize request.

        Args:
            params: Initialize request parameters

        Returns:
            Initialize response with capabilities
        """
        logger.info("Initializing ACP agent (protocol v%s)", params.protocolVersion)

        return InitializeResponse(
            # Some versions of the ACP Python SDK expect a string here
            protocolVersion=str(PROTOCOL_VERSION),
            agentCapabilities=AgentCapabilities(
                supportsLoadSession=False,  # Session persistence not yet implemented
                supportsSetMode=False,  # Mode switching not yet implemented
            ),
            agentInfo=Implementation(
                name="mini-agent",
                title="Mini-Agent (MiniMax M2)",
                version="0.1.0",
            ),
        )

    async def newSession(self, params: NewSessionRequest) -> NewSessionResponse:
        """Create a new session.

        Args:
            params: New session request parameters

        Returns:
            New session response with session ID
        """
        # Generate unique session ID
        session_id = f"sess-{self._session_counter}-{uuid4().hex[:8]}"
        self._session_counter += 1

        logger.info("Creating new session: %s (cwd: %s)", session_id, params.cwd)

        # Create session
        await self._session_manager.create_session(
            session_id=session_id,
            cwd=params.cwd,
            mcp_servers=params.mcpServers or [],
        )

        return NewSessionResponse(sessionId=session_id)

    async def loadSession(
        self, params: LoadSessionRequest
    ) -> LoadSessionResponse | None:
        """Load an existing session (not implemented).

        Args:
            params: Load session request parameters

        Returns:
            None (not supported)
        """
        logger.info("Load session requested: %s (not implemented)", params.sessionId)
        return None

    async def setSessionMode(
        self, params: SetSessionModeRequest
    ) -> SetSessionModeResponse | None:
        """Set session mode (not implemented).

        Args:
            params: Set mode request parameters

        Returns:
            None (not supported)
        """
        logger.info(
            "Set mode requested: %s -> %s (not implemented)",
            params.sessionId,
            params.modeId,
        )
        return None

    async def prompt(self, params: PromptRequest) -> PromptResponse:
        """Process a user prompt.

        This is the main method that handles user input and generates responses.
        It streams updates in real-time via sessionUpdate notifications.

        Args:
            params: Prompt request with user message

        Returns:
            Prompt response with stop reason
        """
        session = await self._session_manager.get_session(params.sessionId)
        if not session:
            logger.error("Session not found: %s", params.sessionId)
            return PromptResponse(stopReason="refusal")

        logger.info("Processing prompt for session: %s", params.sessionId)

        try:
            # Convert ACP content to text
            user_text = acp_content_to_text(params.prompt)

            # Send user message update
            await self._send_update(
                params.sessionId, update_agent_message(text_block(f"User: {user_text}"))
            )

            # Add to message history
            user_message = Message(role="user", content=user_text)
            session.messages.append(user_message)

            # Run agent with streaming
            stop_reason = await self._run_agent_with_streaming(session)

            return PromptResponse(stopReason=stop_reason)

        except Exception as e:
            logger.exception("Error processing prompt: %s", e)
            await self._send_update(
                params.sessionId,
                update_agent_message(text_block(f"Error: {str(e)}")),
            )
            # 'error' is not a valid stopReason per ACP schema
            return PromptResponse(stopReason="refusal")

    async def cancel(self, params: CancelNotification) -> None:
        """Cancel ongoing operations for a session.

        Args:
            params: Cancel notification parameters
        """
        logger.info("Canceling session: %s", params.sessionId)
        await self._session_manager.cancel_session(params.sessionId)

    async def extMethod(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Handle extension methods.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Response data
        """
        logger.info("Extension method called: %s", method)
        return {}

    async def extNotification(self, method: str, params: dict[str, Any]) -> None:
        """Handle extension notifications.

        Args:
            method: Notification name
            params: Notification parameters
        """
        logger.info("Extension notification: %s", method)

    async def _send_update(self, session_id: str, update: Any) -> None:
        """Send a session update to the client.

        Args:
            session_id: Session identifier
            update: Update content (agent message, thought, tool call, etc.)
        """
        await self._conn.sessionUpdate(session_notification(session_id, update))

    async def _run_agent_with_streaming(self, session) -> str:
        """Run the agent with real-time streaming updates.

        Args:
            session: Session state

        Returns:
            Stop reason ("end_turn", "max_steps", "error")
        """
        agent = session.agent
        max_steps = 10  # TODO: Make configurable

        for step in range(max_steps):
            # Check for cancellation
            if session.cancel_event.is_set():
                logger.info("Session cancelled: %s", session.session_id)
                return "cancelled"

            # Generate LLM response
            # Note: Agent stores LLM client as 'llm' attribute
            try:
                # Convert tool objects to API schemas for LLM client
                tools_schema = [t.to_schema() for t in agent.tools.values()]
                response = await agent.llm.generate(
                    messages=session.messages, tools=tools_schema
                )
            except Exception as e:
                logger.exception("LLM generation error: %s", e)
                await self._send_update(
                    session.session_id,
                    update_agent_message(text_block(f"LLM Error: {str(e)}")),
                )
                # Map internal error to a valid ACP stopReason
                return "refusal"

            # Stream thinking content if present (MiniMax feature)
            if response.thinking:
                await self._send_update(
                    session.session_id,
                    update_agent_thought(text_block(response.thinking)),
                )

            # Stream assistant message
            if response.content:
                await self._send_update(
                    session.session_id,
                    update_agent_message(text_block(response.content)),
                )

            # Add assistant message to history
            assistant_message = Message(
                role="assistant",
                content=response.content,
                thinking=response.thinking,
                tool_calls=response.tool_calls,
            )
            session.messages.append(assistant_message)

            # If no tool calls, we're done
            if not response.tool_calls:
                return "end_turn"

            # Execute tool calls with streaming
            for tool_call in response.tool_calls:
                await self._execute_tool_with_streaming(session, tool_call)

            # Continue loop for next step

        # Max steps reached
        logger.warning("Max steps reached for session: %s", session.session_id)
        # Use ACP-compliant stop reason value
        return "max_turn_requests"

    async def _execute_tool_with_streaming(self, session, tool_call) -> None:
        """Execute a tool call with streaming updates.

        Args:
            session: Session state
            tool_call: Tool call to execute
        """
        tool_name = tool_call.function.name
        tool_id = tool_call.id

        # Start tool call (send raw_input to preserve structured args)
        await self._send_update(
            session.session_id,
            start_tool_call(
                tool_id,
                f"Executing {tool_name}",
                status="in_progress",
                raw_input=tool_call.function.arguments,
            ),
        )

        # Find and execute tool
        agent = session.agent
        tool = agent.tools.get(tool_name)

        if not tool:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)

            # Update tool call with error
            await self._send_update(
                session.session_id,
                update_tool_call(
                    tool_id,
                    status="failed",
                    content=[tool_content(text_block(error_msg))],
                ),
            )

            # Add error to message history
            session.messages.append(
                Message(
                    role="tool",
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )
            return

        # Execute tool
        try:
            result = await tool.execute(**tool_call.function.arguments)

            # Update tool call with result
            status = "completed" if result.success else "failed"
            result_text = result.content if result.success else result.error or "Unknown error"

            await self._send_update(
                session.session_id,
                update_tool_call(
                    tool_id,
                    status=status,
                    content=[tool_content(text_block(result_text))],
                    raw_output=(getattr(result, "model_dump", None) or getattr(result, "dict", None) or (lambda: None))() or {
                        "success": getattr(result, "success", None),
                        "content": getattr(result, "content", None),
                        "error": getattr(result, "error", None),
                    },
                ),
            )

            # Add to message history
            session.messages.append(
                Message(
                    role="tool",
                    content=result_text,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )

        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.exception(error_msg)

            # Update tool call with error
            await self._send_update(
                session.session_id,
                update_tool_call(
                    tool_id,
                    status="failed",
                    content=[tool_content(text_block(error_msg))],
                ),
            )

            # Add error to message history
            session.messages.append(
                Message(
                    role="tool",
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )
