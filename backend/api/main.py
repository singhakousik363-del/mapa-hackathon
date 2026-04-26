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
async def session_summary(session_id: str, scope: str = "all"):
    """Return data for a session. scope='all' returns everything, scope='session' filters by session_id."""
    from tools.firestore_client import FirestoreClient
    if scope == "session":
        tasks = await FirestoreClient("tasks").list_by_session(session_id)
        events = await FirestoreClient("events").list_by_session(session_id)
        notes = await FirestoreClient("notes").list_by_session(session_id)
    else:
        tasks = await FirestoreClient("tasks").list_all()
        events = await FirestoreClient("events").list_all()
        notes = await FirestoreClient("notes").list_all()
    return {"session_id": session_id, "scope": scope, "stats": {"tasks": len(tasks), "events": len(events), "notes": len(notes)}, "tasks": tasks, "events": events, "notes": notes}

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



class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    due_date: str | None = None
    session_id: str = "default"

@app.post("/tasks")
async def create_task_direct(req: TaskCreate):
    """Direct task creation. Bypasses Gemini for structured form input."""
    title = (req.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title required")

    from tools.firestore_client import FirestoreClient
    from datetime import datetime, timezone

    db = FirestoreClient("tasks")

    existing = await db.list_by_session(req.session_id)
    duplicate = False
    for t in existing:
        if (t.get("title") or "").strip().lower() == title.lower():
            duplicate = True
            break
    if duplicate:
        raise HTTPException(status_code=409, detail="Task '" + title + "' already exists in this session")

    priority = req.priority if req.priority in ("low", "medium", "high") else "medium"
    doc_data = {
        "title": title,
        "priority": priority,
        "due_date": req.due_date or None,
        "status": "pending",
        "session_id": req.session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_id = await db.create(doc_data)
    return {"success": True, "id": doc_id, "data": {**doc_data, "id": doc_id}}
