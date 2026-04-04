from datetime import datetime, timezone
from tools.mcp_base import MCPTool, ToolResult
from tools.firestore_client import FirestoreClient

class TaskMCPTool(MCPTool):
    name = "task_manager"
    description = "Create, list, complete, and delete tasks with priorities"
    schema = {}

    def __init__(self):
        self.db = FirestoreClient("tasks")

    async def call(self, params: dict) -> ToolResult:
        op = params.get("operation")
        session_id = params.get("session_id", "default")
        try:
            if op == "create":
                task = {
                    "title": params.get("title", "Untitled"),
                    "priority": params.get("priority", "medium"),
                    "due_date": params.get("due_date") or None,
                    "status": "pending",
                    "session_id": session_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                doc_id = await self.db.create(task)
                return ToolResult(True, {**task, "id": doc_id}, f"Task '{task['title']}' created", self.name)
            elif op == "list":
                tasks = await self.db.list_all()
                return ToolResult(True, tasks, f"{len(tasks)} tasks found", self.name)
            elif op == "complete":
                tasks = await self.db.list_all()
                title = params.get("title", "").lower()
                match = next((t for t in tasks if title and title in t.get("title","").lower()), None)
                if match:
                    await self.db.update(match["id"], {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()})
                    return ToolResult(True, match, f"Task '{match['title']}' marked complete", self.name)
                return ToolResult(False, None, "Task not found", self.name)
            elif op == "delete":
                tasks = await self.db.list_all()
                title = params.get("title", "").lower()
                match = next((t for t in tasks if title and title in t.get("title","").lower()), None)
                if match:
                    await self.db.delete(match["id"])
                    return ToolResult(True, None, f"Task '{match['title']}' deleted", self.name)
                return ToolResult(False, None, "Task not found", self.name)
            else:
                tasks = await self.db.list_all()
                return ToolResult(True, tasks, f"{len(tasks)} tasks found", self.name)
        except Exception as e:
            return ToolResult(False, None, str(e), self.name)
