from datetime import datetime, timezone
from tools.mcp_base import MCPTool, ToolResult
from tools.firestore_client import FirestoreClient

class NotesMCPTool(MCPTool):
    name = "notes"
    description = "Save, search and list notes and information"
    schema = {}

    def __init__(self):
        self.db = FirestoreClient("notes")

    async def call(self, params: dict) -> ToolResult:
        op = params.get("operation")
        session_id = params.get("session_id", "default")
        try:
            if op == "create":
                note = {
                    "title": params.get("title", f"Note {datetime.now().strftime('%H:%M')}"),
                    "content": params.get("content", ""),
                    "tags": params.get("tags", []),
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                doc_id = await self.db.create(note)
                return ToolResult(True, {**note, "id": doc_id}, f"Note '{note['title']}' saved", self.name)
            elif op == "search":
                notes = await self.db.list_by_session(session_id)
                q = params.get("query", "").lower()
                results = [n for n in notes if q in n.get("title","").lower() or q in n.get("content","").lower()]
                return ToolResult(True, results, f"{len(results)} notes found", self.name)
            else:
                notes = await self.db.list_by_session(session_id)
                return ToolResult(True, notes, f"{len(notes)} notes found", self.name)
        except Exception as e:
            return ToolResult(False, None, str(e), self.name)
