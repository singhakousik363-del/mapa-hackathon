from datetime import datetime, timezone
from tools.mcp_base import MCPTool, ToolResult
from tools.firestore_client import FirestoreClient

class CalendarMCPTool(MCPTool):
    name = "calendar"
    description = "Create and list calendar events and meetings"
    schema = {}

    def __init__(self):
        self.db = FirestoreClient("events")

    async def call(self, params: dict) -> ToolResult:
        op = params.get("operation")
        session_id = params.get("session_id", "default")
        try:
            if op == "create":
                event = {
                    "title": params.get("title", "Untitled Event"),
                    "date": params.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "time": params.get("time", "09:00"),
                    "description": params.get("description", ""),
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                doc_id = await self.db.create(event)
                return ToolResult(True, {**event, "id": doc_id}, f"Event '{event['title']}' on {event['date']}", self.name)
            elif op == "list":
                events = await self.db.list_all()
                return ToolResult(True, events, f"{len(events)} events found", self.name)
            else:
                events = await self.db.list_all()
                return ToolResult(True, events, f"{len(events)} events found", self.name)
        except Exception as e:
            return ToolResult(False, None, str(e), self.name)
