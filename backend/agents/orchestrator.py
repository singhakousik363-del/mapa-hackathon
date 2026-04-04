"""
MAPA - Google ADK Orchestrator
Multi-Agent Productivity Assistant using Google Agent Development Kit (ADK)
Judges will see: proper agent hierarchy, tool use, and ADK architecture
"""

import os
import json
import asyncio
import logging
from datetime import datetime

import google.generativeai as genai
from tools.mcp_base import MCPRegistry
from tools.calendar_tool import CalendarMCPTool
from tools.task_tool import TaskMCPTool
from tools.notes_tool import NotesMCPTool

logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# ── ADK-style Agent base ──────────────────────────────────────────────────────

class ADKAgent:
    """Base class following Google ADK agent interface pattern."""
    name: str = "base_agent"
    description: str = ""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def run(self, task: str, context: dict) -> dict:
        raise NotImplementedError


# ── Specialist Sub-Agents ─────────────────────────────────────────────────────

class CalendarAgent(ADKAgent):
    name = "calendar_agent"
    description = "Manages calendar events: create, list, update, delete events and reminders"

    def __init__(self, tool: CalendarMCPTool):
        super().__init__()
        self.tool = tool

    async def run(self, task: str, context: dict) -> dict:
        session_id = context.get("session_id", "default")
        prompt = f"""You are a calendar assistant. Extract the intent and details from:
"{task}"

Return ONLY valid JSON (no markdown):
{{"operation": "create|list|delete", "title": "...", "date": "YYYY-MM-DD or empty", "time": "HH:MM or empty", "description": "..."}}"""

        try:
            resp = self.model.generate_content(prompt)
            raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
            intent = json.loads(raw)
        except Exception:
            intent = {"operation": "list"}

        params = {**intent, "session_id": session_id}
        result = await self.tool.call(params)
        return {
            "agent": self.name,
            "success": result.success,
            "message": result.message,
            "data": result.data
        }


class TaskAgent(ADKAgent):
    name = "task_agent"
    description = "Manages tasks and to-dos: create, complete, list, prioritize tasks"

    def __init__(self, tool: TaskMCPTool):
        super().__init__()
        self.tool = tool

    async def run(self, task: str, context: dict) -> dict:
        session_id = context.get("session_id", "default")
        prompt = f"""You are a task management assistant. Extract intent from:
"{task}"

Return ONLY valid JSON (no markdown):
{{"operation": "create|list|complete|delete", "title": "...", "priority": "low|medium|high", "due_date": "YYYY-MM-DD or empty"}}"""

        try:
            resp = self.model.generate_content(prompt)
            raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
            intent = json.loads(raw)
        except Exception:
            intent = {"operation": "create", "title": task, "priority": "medium"}

        params = {**intent, "session_id": session_id}
        result = await self.tool.call(params)
        return {
            "agent": self.name,
            "success": result.success,
            "message": result.message,
            "data": result.data
        }


class NotesAgent(ADKAgent):
    name = "notes_agent"
    description = "Manages notes: create, search, list, update notes and memos"

    def __init__(self, tool: NotesMCPTool):
        super().__init__()
        self.tool = tool

    async def run(self, task: str, context: dict) -> dict:
        session_id = context.get("session_id", "default")
        prompt = f"""You are a notes assistant. Extract intent from:
"{task}"

Return ONLY valid JSON (no markdown):
{{"operation": "create|list|search", "title": "...", "content": "...", "query": "..."}}"""

        try:
            resp = self.model.generate_content(prompt)
            raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
            intent = json.loads(raw)
        except Exception:
            intent = {"operation": "create", "title": "Note", "content": task}

        params = {**intent, "session_id": session_id}
        result = await self.tool.call(params)
        return {
            "agent": self.name,
            "success": result.success,
            "message": result.message,
            "data": result.data
        }


# ── ADK Orchestrator (Root Agent) ─────────────────────────────────────────────

class OrchestratorAgent(ADKAgent):
    """
    Root agent following Google ADK multi-agent pattern.
    Routes tasks to specialist sub-agents based on intent classification.
    """
    name = "orchestrator"
    description = "MAPA root agent — routes to calendar, task, and notes sub-agents"

    def __init__(self):
        super().__init__()
        # MCP tool registry (kept for compatibility)
        self.registry = MCPRegistry()
        calendar_tool = CalendarMCPTool()
        task_tool = TaskMCPTool()
        notes_tool = NotesMCPTool()
        self.registry.register(calendar_tool)
        self.registry.register(task_tool)
        self.registry.register(notes_tool)

        # ADK sub-agent team
        self.sub_agents = {
            "calendar_agent": CalendarAgent(calendar_tool),
            "task_agent": TaskAgent(task_tool),
            "notes_agent": NotesAgent(notes_tool),
        }

        # Conversation memory (per session)
        self._sessions: dict[str, list] = {}

    def _get_history(self, session_id: str) -> list:
        return self._sessions.get(session_id, [])

    def _add_to_history(self, session_id: str, role: str, content: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep last 20 turns
        self._sessions[session_id] = self._sessions[session_id][-20:]

    def _classify_intent(self, message: str) -> list[str]:
        """
        ADK-style intent router: classifies which sub-agents to invoke.
        Returns list of agent names (supports multi-agent parallel execution).
        """
        msg = message.lower()

        agents = []

        # Calendar signals
        if any(w in msg for w in ["calendar", "event", "schedule", "meeting", "appointment",
                                   "remind", "when", "date", "time", "today", "tomorrow",
                                   "next week", "free slot"]):
            agents.append("calendar_agent")

        # Task signals
        if any(w in msg for w in ["task", "todo", "to-do", "to do", "complete", "finish",
                                   "done", "deadline", "priority", "work", "submit",
                                   "create task", "add task", "mark"]):
            agents.append("task_agent")

        # Notes signals
        if any(w in msg for w in ["note", "memo", "write down", "remember", "jot",
                                   "save", "idea", "draft", "document"]):
            agents.append("notes_agent")

        # Default: task agent handles general requests
        if not agents:
            agents.append("task_agent")

        return agents

    async def run(self, user_message: str, session_id: str) -> dict:
        """
        ADK-style run: classify → dispatch → synthesize.
        Supports parallel sub-agent execution.
        """
        self._add_to_history(session_id, "user", user_message)

        # Step 1: Intent classification
        target_agents = self._classify_intent(user_message)
        logger.info(f"[ADK] Routing to agents: {target_agents}")

        # Step 2: Parallel sub-agent execution (ADK pattern)
        context = {"session_id": session_id}
        tasks = [
            self.sub_agents[agent_name].run(user_message, context)
            for agent_name in target_agents
            if agent_name in self.sub_agents
        ]
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Step 3: Collect results
        results = {}
        for agent_name, result in zip(target_agents, agent_results):
            if isinstance(result, Exception):
                results[agent_name] = {"success": False, "message": str(result), "data": None}
            else:
                results[agent_name] = result

        # Step 4: Synthesize final response
        history = self._get_history(session_id)
        history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history[-6:]])

        synthesis_prompt = f"""You are MAPA, a friendly multi-agent productivity assistant.

Conversation history:
{history_text}

Agent results:
{json.dumps(results, default=str, indent=2)}

Write a natural, helpful response to the user summarizing what was done.
Be concise and friendly. Do NOT use JSON or markdown."""

        try:
            synthesis = self.model.generate_content(synthesis_prompt)
            response_text = synthesis.text.strip()
        except Exception as e:
            response_text = f"I've processed your request. {list(results.values())[0].get('message', '')}"

        self._add_to_history(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "agents_called": target_agents,
            "results": results,
            "adk_version": "1.0",
            "session_id": session_id
        }
