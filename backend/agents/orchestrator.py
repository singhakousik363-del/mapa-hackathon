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

def _detect_operation_keyword(message):
    """Pre-check for explicit operation keywords. Returns operation or None."""
    msg = message.lower().strip()
    delete_words = ["delete", "remove", "cancel", "drop", "discard"]
    complete_words = ["complete", "completed", "done", "finish", "finished", "mark done"]
    list_words = ["show", "list", "display", "view", "what are my", "what's on my", "see my"]
    # Word-boundary check (basic)
    for w in delete_words:
        if msg.startswith(w + " ") or f" {w} " in f" {msg} ":
            return "delete"
    for w in complete_words:
        if msg.startswith(w + " ") or f" {w} " in f" {msg} ":
            return "complete"
    for w in list_words:
        if msg.startswith(w + " ") or msg == w:
            return "list"
    return None


def smart_extract(message, model):
    """Use Gemini to extract intents. Has keyword override + verb stripping."""
    today = datetime.now().strftime("%Y-%m-%d")
    forced_op = _detect_operation_keyword(message)

    # Build the hint outside the prompt to avoid f-string backslash issues
    if forced_op:
        hint = f"CRITICAL: The user's message explicitly contains a {forced_op.upper()} keyword. You MUST set operation to {forced_op!r} and extract ONLY the TARGET item (the thing being acted on), NOT the action verb. For example, 'delete buy milk' has target='buy milk', not 'delete buy milk'."
    else:
        hint = "Intent should be inferred from context."

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
- If user says "delete/remove X" -> operation=delete, put X (just the target, NOT including the verb) in tasks/events/notes
- If user says "complete/done/finish X" -> operation=complete, put X in tasks
- Extract SHORT meaningful titles, NOT the full sentence. Strip action verbs from titles.
- Convert relative dates: "tomorrow", "next Monday" etc to YYYY-MM-DD based on today={today}
- If no clear action found, default to creating a task with a clean title

{hint}"""

    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)

        # Force operation if keyword detected
        if forced_op:
            result["operation"] = forced_op
            # Always strip action verbs from titles for delete/complete
            if forced_op in ["delete", "complete"]:
                for task in result.get("tasks", []):
                    title = (task.get("title") or "").strip()
                    title_lower = title.lower()
                    for verb in ["delete ", "remove ", "cancel ", "drop ", "complete ", "completed ", "finish ", "finished ", "done ", "mark done "]:
                        if title_lower.startswith(verb):
                            task["title"] = title[len(verb):].strip()
                            break
                    # Strip trailing " task"
                    cur = task.get("title", "")
                    if cur.lower().endswith(" task"):
                        task["title"] = cur[:-5].strip()
        return result
    except Exception as e:
        logger.warning(f"smart_extract failed: {e}")
        # Fallback: also strip verbs from message for delete/complete
        fallback_title = message[:60]
        if forced_op in ["delete", "complete"]:
            ml = fallback_title.lower().strip()
            for verb in ["delete ", "remove ", "cancel ", "drop ", "complete ", "completed ", "finish ", "finished ", "done ", "mark done "]:
                if ml.startswith(verb):
                    fallback_title = fallback_title[len(verb):].strip()
                    break
            if fallback_title.lower().endswith(" task"):
                fallback_title = fallback_title[:-5].strip()
        return {
            "tasks": [{"title": fallback_title, "priority": "medium", "due_date": None}],
            "events": [],
            "notes": [],
            "operation": forced_op or "create",
            "list_type": None
        }



def _smart_join(msgs):
    """Join messages with proper punctuation, preserving ? and !."""
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

    def _synthesize_response(self, operation, agents_called, results, session_id):
        """Generate response. Skip Gemini for simple cases (50% latency saving)."""
        # Empty case
        if not results or not agents_called:
            return "I'm not sure what to do — try asking again?"

        result_values = [r for r in results.values() if isinstance(r, dict)]
        if not result_values:
            return "Done!"

        # Simple single-agent case: use agent's own message directly (NO Gemini call)
        if len(agents_called) == 1:
            return result_values[0].get("message", "Done!")

        # List operation with multiple agents: combine count messages
        if operation == "list":
            msgs = [r.get("message", "") for r in result_values if r.get("message")]
            if msgs:
                return _smart_join(msgs)
            return "Nothing found."

        # Compound intent (multiple agents) — use Gemini for natural synthesis
        history_lines = []
        for h in self._sessions.get(session_id, [])[-4:]:
            history_lines.append(h["role"] + ": " + h["content"])
        history_text = "\n".join(history_lines)

        synthesis_prompt = (
            "You are MAPA, a friendly AI productivity assistant for Indian users.\n\n"
            "Conversation:\n" + history_text + "\n\n"
            "Agent results:\n" + json.dumps(results, default=str, indent=2) + "\n\n"
            "Write a warm, friendly response in 1-3 sentences confirming all the actions taken across the different agents. "
            "No JSON, no markdown, no bullet points. Keep it conversational."
        )

        try:
            synthesis = self.model.generate_content(synthesis_prompt)
            return synthesis.text.strip()
        except Exception as e:
            logger.warning(f"synthesis failed: {e}")
            msgs = [r.get("message", "") for r in result_values if r.get("message")]
            return _smart_join(msgs) if msgs else "Done!"


    async def run(self, user_message, session_id):
        # Input validation
        if not user_message or not user_message.strip():
            return {"response": "Please type a message.", "agents_called": [], "results": {}, "adk_version": "2.0", "session_id": session_id}
        if len(user_message) > 2000:
            return {"response": "Message too long. Please keep it under 2000 characters.", "agents_called": [], "results": {}, "adk_version": "2.0", "session_id": session_id}

        self._add_history(session_id, "user", user_message)

        # Greeting fast-path: short conversational messages bypass Gemini extraction
        # Prevents "hi"/"hello"/"thanks" from being misinterpreted as task creation
        msg_norm = user_message.strip().lower().rstrip("!.?,")
        greeting_words = {
            "hi", "hello", "hey", "yo", "sup",
            "namaste", "namaskar", "salaam", "salam",
            "kemon acho", "kemon achen", "kemon",
            "hola", "bonjour", "ciao",
            "good morning", "good afternoon", "good evening", "good night",
            "thanks", "thank you", "thx", "ok", "okay", "k",
            "bye", "goodbye", "see you", "see ya"
        }
        first_word = msg_norm.split()[0] if msg_norm else ""
        is_greeting = (
            msg_norm in greeting_words or
            first_word in {"hi", "hello", "hey", "namaste", "namaskar", "thanks", "ok", "bye"}
        ) and len(msg_norm) < 30
        if is_greeting:
            response_msg = "Hi! I can help manage your tasks, calendar, and notes. Try: 'remind me to call mom tomorrow' or 'schedule team meeting at 3pm'."
            self._add_history(session_id, "assistant", response_msg)
            return {"response": response_msg, "agents_called": [], "results": {}, "adk_version": "2.0", "session_id": session_id}

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
                results["task_agent"] = {"success": True, "message": (f"You have {len(tasks)} task{'s' if len(tasks)!=1 else ''}." if tasks else "No tasks yet. Try saying 'remind me to call mom' to add one."), "data": tasks}
                agents_called.append("task_agent")
            if list_type in ["events", "all"]:
                events = await FirestoreClient("events").list_all()
                results["calendar_agent"] = {"success": True, "message": (f"You have {len(events)} event{'s' if len(events)!=1 else ''}." if events else "Your calendar is clear. Want to schedule something?"), "data": events}
                agents_called.append("calendar_agent")
            if list_type in ["notes", "all"]:
                notes = await FirestoreClient("notes").list_all()
                results["notes_agent"] = {"success": True, "message": (f"You have {len(notes)} note{'s' if len(notes)!=1 else ''}." if notes else "No notes saved. Capture an idea anytime."), "data": notes}
                agents_called.append("notes_agent")
            if not agents_called:
                from tools.firestore_client import FirestoreClient
                tasks = await FirestoreClient("tasks").list_all()
                results["task_agent"] = {"success": True, "message": (f"You have {len(tasks)} task{'s' if len(tasks)!=1 else ''}." if tasks else "No tasks yet. Try saying 'remind me to call mom' to add one."), "data": tasks}
                agents_called.append("task_agent")

        # Handle CREATE operations
        elif operation == "create":
            from tools.firestore_client import FirestoreClient
            for task_data in extracted.get("tasks", []):
                title = task_data.get("title", "").strip()
                if not title:
                    continue
                # Duplicate check: skip if same-titled task exists in this session
                existing = await FirestoreClient("tasks").list_by_session(session_id)
                if any((t.get("title") or "").strip().lower() == title.lower() for t in existing):
                    results["task_agent"] = {"success": False, "message": f"Task '{title}' already exists in this session", "data": None}
                    agents_called.append("task_agent")
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
                # Duplicate check: skip if same-titled event exists in this session
                existing = await FirestoreClient("events").list_by_session(session_id)
                if any((e.get("title") or "").strip().lower() == title.lower() for e in existing):
                    results["calendar_agent"] = {"success": False, "message": f"Event '{title}' already exists in this session", "data": None}
                    agents_called.append("calendar_agent")
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
                # Duplicate check: skip if same-titled note exists in this session
                existing = await FirestoreClient("notes").list_by_session(session_id)
                if any((n.get("title") or "").strip().lower() == title.lower() for n in existing):
                    results["notes_agent"] = {"success": False, "message": f"Note '{title}' already exists in this session", "data": None}
                    agents_called.append("notes_agent")
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

        # Smart synthesis: skip Gemini for simple cases (50% latency saving)
        response_text = self._synthesize_response(operation, list(set(agents_called)), results, session_id)

        self._add_history(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "agents_called": list(set(agents_called)),
            "results": results,
            "adk_version": "2.0",
            "session_id": session_id
        }
