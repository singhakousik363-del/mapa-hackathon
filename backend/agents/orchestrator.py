"""
MAPA - Google ADK Orchestrator (Complete Rewrite)
Smart NLP extraction + multi-agent routing
"""
import os, json, asyncio, logging
from datetime import datetime
import google.generativeai as genai
from tools.mcp_base import MCPRegistry
from tools.calendar_tool import CalendarMCPTool
from tools.task_tool import TaskMCPTool
from tools.notes_tool import NotesMCPTool

logger = logging.getLogger(__name__)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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
- If user says "going to X on DATE" → create both a task "Trip to X" AND an event "Trip to X" on that date
- If user says "meeting/appointment/call on DATE" → create calendar event
- If user says "remind me to X" → create task
- If user says "note/write down/remember" → create note
- If user says "show/list/display" → operation=list
- Extract SHORT meaningful titles, NOT the full sentence
- Convert relative dates: "tomorrow", "next Monday" etc to YYYY-MM-DD based on today={today}
- If no clear action found, default to creating a task with a clean title"""

    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except:
        return {"tasks": [{"title": message[:60], "priority": "medium", "due_date": None}], "events": [], "notes": [], "operation": "create", "list_type": None}

class OrchestratorAgent:
    def __init__(self):
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
            "timestamp": datetime.utcnow().isoformat()
        })
        self._sessions[sid] = self._sessions[sid][-20:]

    async def run(self, user_message, session_id):
        self._add_history(session_id, "user", user_message)

        # Smart extraction
        extracted = smart_extract(user_message, self.model)
        operation = extracted.get("operation", "create")
        list_type = extracted.get("list_type")

        results = {}
        agents_called = []

        # Handle LIST operations
        if operation == "list":
            if list_type in ["tasks", "all", None]:
                from tools.firestore_client import FirestoreClient
                tasks = await FirestoreClient("tasks").list_all()
                results["task_agent"] = {"success": True, "message": f"{len(tasks)} tasks found", "data": tasks}
                agents_called.append("task_agent")
            if list_type in ["events", "all"]:
                from tools.firestore_client import FirestoreClient
                events = await FirestoreClient("events").list_all()
                results["calendar_agent"] = {"success": True, "message": f"{len(events)} events found", "data": events}
                agents_called.append("calendar_agent")
            if list_type in ["notes", "all"]:
                from tools.firestore_client import FirestoreClient
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
            # Create tasks
            for task_data in extracted.get("tasks", []):
                title = task_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create",
                    "title": title,
                    "priority": task_data.get("priority", "medium"),
                    "due_date": task_data.get("due_date") or "",
                    "session_id": session_id
                }
                result = await self.task_tool.call(params)
                results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("task_agent")

            # Create calendar events
            for event_data in extracted.get("events", []):
                title = event_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create",
                    "title": title,
                    "date": event_data.get("date", ""),
                    "time": event_data.get("time", "09:00"),
                    "description": event_data.get("description", ""),
                    "session_id": session_id
                }
                result = await self.calendar_tool.call(params)
                results["calendar_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("calendar_agent")

            # Create notes
            for note_data in extracted.get("notes", []):
                title = note_data.get("title", "").strip()
                if not title:
                    continue
                params = {
                    "operation": "create",
                    "title": title,
                    "content": note_data.get("content", ""),
                    "session_id": session_id
                }
                result = await self.notes_tool.call(params)
                results["notes_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("notes_agent")

            # Fallback if nothing was extracted
            if not agents_called:
                params = {"operation": "create", "title": user_message[:80], "priority": "medium", "due_date": "", "session_id": session_id}
                result = await self.task_tool.call(params)
                results["task_agent"] = {"success": result.success, "message": result.message, "data": result.data}
                agents_called.append("task_agent")

        # Handle DELETE
        elif operation == "delete":
            results["task_agent"] = {"success": False, "message": "Please use the task panel to delete tasks", "data": None}
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
- Confirm what was created/done
- If it's a list, summarize the items naturally
- If empty, say so helpfully and offer to help
- No JSON, no markdown, no bullet points
- Keep it conversational"""

        try:
            synthesis = self.model.generate_content(synthesis_prompt)
            response_text = synthesis.text.strip()
        except:
            response_text = list(results.values())[0].get("message", "Done!") if results else "Done!"

        self._add_history(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "agents_called": list(set(agents_called)),
            "results": results,
            "adk_version": "2.0",
            "session_id": session_id
        }
