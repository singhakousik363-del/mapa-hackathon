"""ADK-native orchestrator wrapper.

Provides the same async run(user_message, session_id) interface as the
legacy OrchestratorAgent so api/main.py needs only a single import swap.

Internally uses google.adk.runners.Runner with the ParallelAgent
mapa_orchestrator defined in adk_agents.py.
"""
import logging
import uuid
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.adk_agents import mapa_orchestrator

logger = logging.getLogger(__name__)


class ADKOrchestratorAgent:
    """Drop-in replacement for legacy OrchestratorAgent, powered by ADK."""

    APP_NAME = "mapa"

    def __init__(self):
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=mapa_orchestrator,
            session_service=self._session_service,
            app_name=self.APP_NAME,
        )
        # Track which (user_id, session_id) combos have been initialized
        self._initialized_sessions: set[tuple[str, str]] = set()
        logger.info("ADKOrchestratorAgent initialized with ParallelAgent")

    async def _ensure_session(self, user_id: str, session_id: str) -> None:
        """Create ADK session if not already created."""
        key = (user_id, session_id)
        if key in self._initialized_sessions:
            return
        try:
            await self._session_service.create_session(
                app_name=self.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            self._initialized_sessions.add(key)
        except Exception as e:
            # Session might already exist; that's fine
            logger.debug(f"create_session: {e}")
            self._initialized_sessions.add(key)

    @staticmethod
    def _is_greeting(message: str) -> bool:
        """Check if message is a short greeting that should bypass agents."""
        msg_norm = (message or "").strip().lower().rstrip("!.?,")
        if len(msg_norm) >= 30 or not msg_norm:
            return False
        greeting_words = {
            "hi", "hello", "hey", "yo", "sup",
            "namaste", "namaskar", "salaam", "salam",
            "kemon acho", "kemon achen", "kemon",
            "hola", "bonjour", "ciao",
            "good morning", "good afternoon", "good evening", "good night",
            "thanks", "thank you", "thx", "ok", "okay", "k",
            "bye", "goodbye", "see you", "see ya",
        }
        first_word = msg_norm.split()[0] if msg_norm else ""
        return msg_norm in greeting_words or first_word in {
            "hi", "hello", "hey", "namaste", "namaskar", "thanks", "ok", "bye"
        }

    async def run(self, user_message: str, session_id: str) -> dict[str, Any]:
        """Run a user message through the ADK ParallelAgent orchestrator.
        
        Returns a dict matching the legacy orchestrator's response shape:
            {
                "response": str,
                "agents_called": list[str],
                "results": dict[str, dict],
                "adk_version": str,
                "session_id": str,
            }
        """
        # Input validation
        if not user_message or not user_message.strip():
            return {
                "response": "Please type a message.",
                "agents_called": [],
                "results": {},
                "adk_version": "2.0",
                "session_id": session_id,
            }
        if len(user_message) > 2000:
            return {
                "response": "Message too long. Please keep it under 2000 characters.",
                "agents_called": [],
                "results": {},
                "adk_version": "2.0",
                "session_id": session_id,
            }

        # Greeting fast-path
        if self._is_greeting(user_message):
            return {
                "response": (
                    "Hi! I can help manage your tasks, calendar, and notes. "
                    "Try: 'remind me to call mom tomorrow' or "
                    "'schedule team meeting at 3pm'."
                ),
                "agents_called": [],
                "results": {},
                "adk_version": "2.0",
                "session_id": session_id,
            }

        # ADK runner expects a user_id; we use a synthetic one tied to session
        user_id = f"user_{session_id}"
        await self._ensure_session(user_id, session_id)

        # Annotate the message with session_id so tools can use it
        annotated = (
            f"{user_message}\n\n"
            f"[context] session_id={session_id}"
        )
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=annotated)],
        )

        # Collect events from the ParallelAgent run
        agent_responses: dict[str, str] = {}  # agent_name -> final text
        agent_tool_results: dict[str, dict] = {}  # agent_name -> last tool result
        agents_called: list[str] = []

        try:
            async for event in self._runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
            ):
                author = getattr(event, "author", None) or "unknown"
                # Capture text content (final response from each sub-agent)
                if hasattr(event, "content") and event.content:
                    parts = getattr(event.content, "parts", []) or []
                    for part in parts:
                        text = getattr(part, "text", None)
                        if text:
                            agent_responses[author] = text.strip()
                        # Capture tool call results
                        function_response = getattr(part, "function_response", None)
                        if function_response:
                            response_data = getattr(function_response, "response", None)
                            if isinstance(response_data, dict):
                                agent_tool_results[author] = response_data
                                if author not in agents_called:
                                    agents_called.append(author)
        except Exception as e:
            logger.exception(f"ADK run error: {e}")
            return {
                "response": "Sorry, I had trouble processing that. Please try again.",
                "agents_called": [],
                "results": {},
                "adk_version": "2.0",
                "session_id": session_id,
            }

        # Build response: prefer tool result messages over raw text
        # Filter out NOT_MY_DOMAIN responses
        relevant_messages: list[str] = []
        results: dict[str, dict] = {}
        for agent_name, tool_result in agent_tool_results.items():
            if isinstance(tool_result, dict) and tool_result.get("message"):
                msg = tool_result["message"]
                if "NOT_MY_DOMAIN" not in msg.upper():
                    relevant_messages.append(msg)
                    results[agent_name] = tool_result

        # Fallback: include text-only responses (e.g., simple "no action needed")
        for agent_name, text in agent_responses.items():
            if agent_name in results:
                continue
            if text and "NOT_MY_DOMAIN" not in text.upper() and len(text.strip()) > 0:
                # Only add if substantively informative
                relevant_messages.append(text)

        if not relevant_messages:
            response = (
                "I didn't quite catch that. Try saying something like "
                "'add a task to buy milk' or 'schedule a meeting tomorrow at 3pm'."
            )
        else:
            response = self._smart_join(relevant_messages)

        return {
            "response": response,
            "agents_called": agents_called,
            "results": results,
            "adk_version": "2.0",
            "session_id": session_id,
        }

    @staticmethod
    def _smart_join(msgs: list[str]) -> str:
        """Join messages with proper punctuation."""
        parts = [m.strip() for m in msgs if m and m.strip()]
        if not parts:
            return "Done!"
        result = parts[0]
        for p in parts[1:]:
            if result and result[-1] in "?!.":
                result = result + " " + p
            else:
                result = result + ". " + p
        if result and result[-1] not in ".?!":
            result = result + "."
        return result
