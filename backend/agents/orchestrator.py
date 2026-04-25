"""
MAPA - Google ADK Orchestrator
Smart NLP extraction + multi-agent routing
"""
import os, json, logging
from datetime import datetime, timezone
import google.generativeai as genai
from tools.mcp_base import MCPRegistry
from tools.calendar_tool import CalendarMCPTool
from tools.task_tool import TaskMCPTool
from tools.notes_tool import NotesMCPTool

logger = logging.getLogger(__name__)

# Lazy configure - don't crash on import if env missing
_GEMINI_CONFIGURED = False
def _ensure_gemini():
    global _GEMINI_CONFIGURED
    if not _GEMINI_CONFIGURED:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        _GEMINI_CONFIGURED = True

def smart_extract(message, model):
    """Use Gemini to extract ALL intents from a natural language message."""
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Today is {today}. Analyze this message: "{message}"

Extract ALL actions the user wants. Return ONLY valid JSON:
{{
  "tasks": [
    {{"title": "short clear task title", "priority": "low|medium|high", "due_date": "YYYY-MM-DD or null"}}
  ],
  "events": [
    {{"title": "short event title", "date": "YYYY-MM-DD", "time": "HH:MM or 09:00", "description": ""}}
  ],
  "notes": [
    {{"title": "short title", "content": "full content"}}
  ],
  "operation": "create|list|delete|complete",
  "list_type": "tasks|events|notes|all or null"
}}

Rules:
- If user says "going to X on DATE" -> create both a task "Trip to X" AND an event "Trip to X" on that date
- If user says "meeting/appointment/call on DATE" -> create calendar event
- If user says "remind me to X" -> create task
- If user says "note/write down/remember" -> create note
- If user says "show/list/display" -> operation=list
- If user says "delete/remove X" -> operation=delete, put X title in tasks/events/notes array based on context
- If user says "complete/done/finish X" -> operation=complete, put X title in tasks array
- Extract SHORT meaningful titles, NOT the full sentence
- Convert relative dates: "tomorrow", "next Monday" etc to YYYY-MM-DD based on today={today}
- If no clear action found, default to creating a task with a clean title"""

    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"smart_extract failed: {e}")
        return {"tasks": [{"title": message[:60], "priority": "medium", "due_date": None}], "events": [], "notes": [], "operation": "create", "list_type": None}


class OrchestratorAgent:
    def __init__(self):
        _ensure_gemini()
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.registry = MCPRegistry()
        self.calendar_tool = CalendarMCPTool()
        self.task_tool = TaskMCPTool()
        self.notes_tool = NotesMCPTool()
        self.registry.register(self.calendar_tool)
        self.registry.register(self.task_tool)
        self.registry.register(self.notes_tool)
        self._sessions = {}

    def _add_history(self, sid, role, content):
        self._sessions.setdefault(sid, []).append({
            "role": role, "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._sessions[sid] = self._sessions[sid][-20:]

    async def run(self, user_message, session_id):
        # Input validation
        if not user_message or not user_message.strip():
            return {"response": "Please type a message.", "agents_called": [], "results": {}, "adk_version": "2.0", "session_id": session_id}
        if len(user_message) > 2000:
            return {"response": "Message too long. Please keep it under 2000 characters.", "agents_called": [], "results": {}, "adk_version": "2.0", "session_id": session_id}

        self._add_history(session_id, "user", user_message)

        extracted = smart_extract(user_message, self.model)
        operation = extracted.get("operation", "create")
        list_type = extracted.get("list_type")

        results = {}
        agents_called = []

        # Handle LIST operations
        if operation == "list":
            from tools.firestore_client import FirestoreClient
            if list_type in ["tasks", "all", None]:
                tasks = await FirestoreClient("tasks").list_all()
                results["task_agent"] = {"success": True, "message": f"{len(tasks)} tasks found", "data": tasks}
                agents_called.append("task_agent")
            if list_type in ["events", "all"]:
                events = await FirestoreClient("events").list_all()
                results["calendar_agent"] = {"success": True, "message": f"{len(events)} events found", "data": events}
                agents_called.append("calendar_agent")
            if list_type in ["notes", "all"]:
                notes = await FirestoreClient("notes").list_all()
                results["notes_agent"] = {"success": True, "message": f"{len(notes)} notes found", "data": notes}
                agents_called.append("notes_agent")
            if not agents_called:
                from tools.firestore_client import FirestoreClient
                tasks = await FirestoreClient("tasks").list_all()
                results["task_agent"] = {"success": True, "message": f"{len(tasks)} tasks found", "data": tasks}
                agents_called.append("task_agent")

        # Handle CREATE operations
        elif operation == "create":
            for task_data in extracted.get("tasks", []):
                title = task_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create", "title": title,
                    "priority": task_data.get("priority", "medium"),
                    "due_date": task_data.get("due_date") or "",
                    "session_id": session_id
                }
                result = await self.task_tool.call(params)
                results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("task_agent")

            for event_data in extracted.get("events", []):
                title = event_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create", "title": title,
                    "date": event_data.get("date", ""),
                    "time": event_data.get("time", "09:00"),
                    "description": event_data.get("description", ""),
                    "session_id": session_id
                }
                result = await self.calendar_tool.call(params)
                results["calendar_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("calendar_agent")

            for note_data in extracted.get("notes", []):
                title = note_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create", "title": title,
                    "content": note_data.get("content", ""),
                    "session_id": session_id
                }
                result = await self.notes_tool.call(params)
                results["notes_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("notes_agent")

            if not agents_called:
                params = {"operation": "create", "title": user_message[:80], "priority": "medium", "due_date": "", "session_id": session_id}
                result = await self.task_tool.call(params)
                results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("task_agent")

        # Handle DELETE — actually call tools, with title matching
        elif operation == "delete":
            from tools.firestore_client import FirestoreClient
            handled = False

            # Delete tasks
            for task_data in extracted.get("tasks", []):
                title = (task_data.get("title") or "").strip().lower()
                if not title:
                    continue
                result = await self.task_tool.call({"operation": "delete", "title": title, "session_id": session_id})
                results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("task_agent")
                handled = True

            # Delete events (no built-in delete in calendar_tool, do it directly)
            for event_data in extracted.get("events", []):
                title = (event_data.get("title") or "").strip().lower()
                if not title:
                    continue
                db = FirestoreClient("events")
                events = await db.list_all()
                match = next((e for e in events if title in (e.get("title") or "").lower()), None)
                if match:
                    await db.delete(match["id"])
                    results["calendar_agent"] = {"success": True, "message": f"Event '{match.get('title')}' deleted", "data": match}
                else:
                    results["calendar_agent"] = {"success": False, "message": f"Event matching '{title}' not found", "data": None}
                agents_called.append("calendar_agent")
                handled = True

            # Delete notes
            for note_data in extracted.get("notes", []):
                title = (note_data.get("title") or "").strip().lower()
                if not title:
                    continue
                db = FirestoreClient("notes")
                notes = await db.list_all()
                match = next((n for n in notes if title in (n.get("title") or "").lower()), None)
                if match:
                    await db.delete(match["id"])
                    results["notes_agent"] = {"success": True, "message": f"Note '{match.get('title')}' deleted", "data": match}
                else:
                    results["notes_agent"] = {"success": False, "message": f"Note matching '{title}' not found", "data": None}
                agents_called.append("notes_agent")
                handled = True

            if not handled:
                results["task_agent"] = {"success": False, "message": "Please specify what to delete (e.g. 'delete meeting task')", "data": None}
                agents_called.append("task_agent")

        # Handle COMPLETE
        elif operation == "complete":
            title_to_complete = ""
            if extracted.get("tasks"):
                title_to_complete = extracted["tasks"][0].get("title", "")
            params = {"operation": "complete", "title": title_to_complete, "session_id": session_id}
            result = await self.task_tool.call(params)
            results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
            agents_called.append("task_agent")

        # Synthesize response
        history_text = "\n".join([f"{h['role']}: {h['content']}" for h in self._sessions.get(session_id, [])[-4:]])
        synthesis_prompt = f"""You are MAPA, a friendly AI productivity assistant for Indian users.

Conversation:
{history_text}

Agent results:
{json.dumps(results, default=str, indent=2)}

Write a warm, friendly response in 1-3 sentences:
- Confirm what was created/done/deleted
- If it's a list, summarize the items naturally
- If empty, say so helpfully and offer to help
- No JSON, no markdown, no bullet points
- Keep it conversational"""

        try:
            synthesis = self.model.generate_content(synthesis_prompt)
            response_text = synthesis.text.strip()
        except Exception as e:
            logger.warning(f"synthesis failed: {e}")
            if results:
                first = next(iter(results.values()), None)
                if isinstance(first, dict):
                    response_text = first.get("message", "Done!")
                else:
                    response_text = "Done!"
            else:
                response_text = "Done!"

        self._add_history(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "agents_called": list(set(agents_called)),
            "results": results,
            "adk_version": "2.0",
            "session_id": session_id
        }
