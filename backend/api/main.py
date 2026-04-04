import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.orchestrator import OrchestratorAgent

agent = None

@asynccontextmanager
async def lifespan(app):
    global agent
    agent = OrchestratorAgent()
    print("MAPA Orchestrator initialized")
    yield

app = FastAPI(title="MAPA API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MAPA", "version": "2.0.0"}

@app.get("/tools")
async def list_tools():
    return {"tools": agent.registry.list_tools()}

@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        result = await agent.run(req.message, session_id)
        return {"session_id": session_id, "response": result.get("response",""), "agents_called": result.get("agents_called",[]), "results": result.get("results",{})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/summary")
async def session_summary(session_id: str):
    from tools.firestore_client import FirestoreClient
    # Return ALL data (not filtered by session) so UI always shows everything
    tasks = await FirestoreClient("tasks").list_all()
    events = await FirestoreClient("events").list_all()
    notes = await FirestoreClient("notes").list_all()
    return {"session_id": session_id, "stats": {"tasks": len(tasks), "events": len(events), "notes": len(notes)}, "tasks": tasks, "events": events, "notes": notes}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("tasks")
    doc = await db.get(task_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task_id)
    return {"success": True, "deleted": task_id}

@app.patch("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("tasks")
    await db.update(task_id, {"status": "completed"})
    return {"success": True, "task_id": task_id}

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("notes")
    await db.delete(note_id)
    return {"success": True, "deleted": note_id}
