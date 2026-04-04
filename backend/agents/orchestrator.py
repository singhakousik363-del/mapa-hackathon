import os
import json
import google.generativeai as genai
from tools.mcp_base import MCPRegistry
from tools.calendar_tool import CalendarMCPTool
from tools.task_tool import TaskMCPTool
from tools.notes_tool import NotesMCPTool

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

class OrchestratorAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.registry = MCPRegistry()
        self.registry.register(CalendarMCPTool())
        self.registry.register(TaskMCPTool())
        self.registry.register(NotesMCPTool())

    def _system_prompt(self):
        manifest = self.registry.tool_manifest()
        return manifest + "\n\nGiven user message return ONLY valid JSON:\n{\"plan\": [{\"tool\": \"task_manager\", \"params\": {\"operation\": \"create\", \"title\": \"...\", \"priority\": \"high\"}}]}\nNo explanation. No markdown."

    async def run(self, user_message, session_id):
        plan_response = self.model.generate_content(self._system_prompt() + " User: " + user_message)
        try:
            raw = plan_response.text.strip()
            raw = raw.replace("```json","").replace("```","").strip()
            plan = json.loads(raw).get("plan", [])
        except Exception:
            plan = [{"tool": "task_manager", "params": {"operation": "create", "title": user_message, "priority": "medium"}}]

        results = {}
        for step in plan:
            tool_name = step.get("tool")
            params = step.get("params", {})
            params["session_id"] = session_id
            tool = self.registry.get(tool_name)
            if tool:
                result = await tool.call(params)
                results[tool_name] = {"success": result.success, "message": result.message, "data": result.data}

        msg = "User said: " + user_message + ". Results: " + json.dumps(results, default=str) + ". Reply friendly. Return ONLY JSON with keys response and agents_called."
        synthesis = self.model.generate_content(msg)
        try:
            raw = synthesis.text.strip().replace("```json","").replace("```","").strip()
            parsed = json.loads(raw)
            return {"response": parsed.get("response", synthesis.text), "agents_called": parsed.get("agents_called", list(results.keys())), "results": results}
        except Exception:
            return {"response": synthesis.text, "agents_called": list(results.keys()), "results": results}
