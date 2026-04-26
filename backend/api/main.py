import uuid
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.orchestrator import OrchestratorAgent

# Structured logging config (single source of truth, picked up by Cloud Run)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mapa.api")

agent = None

@asynccontextmanager
async def lifespan(app):
    global agent
    agent = OrchestratorAgent()
    logger.info("MAPA Orchestrator initialized (lifespan startup)")
    yield

app = FastAPI(title="MAPA API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({elapsed_ms}ms)")
    return response

# Rate limiting: protect against abuse / runaway costs
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("20/minute")
async def chat(request: Request, req: ChatRequest):
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

@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("events")
    await db.delete(event_id)
    return {"success": True, "event_id": event_id}

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
@limiter.limit("30/minute")
async def create_task_direct(request: Request, req: TaskCreate):
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

class TaskUpdate(BaseModel):
    title: str | None = None
    priority: str | None = None
    due_date: str | None = None
    status: str | None = None

@app.patch("/tasks/{task_id}")
@limiter.limit("30/minute")
async def update_task(request: Request, task_id: str, req: TaskUpdate):
    """Update task fields. Only non-None fields are updated."""
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("tasks")

    existing = await db.get(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    if req.title is not None:
        title = req.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        existing_in_session = await db.list_by_session(existing.get("session_id", "default"))
        for t in existing_in_session:
            if t.get("id") != task_id and (t.get("title") or "").strip().lower() == title.lower():
                raise HTTPException(status_code=409, detail="Another task with this title exists in this session")
        updates["title"] = title
    if req.priority is not None and req.priority in ("low", "medium", "high"):
        updates["priority"] = req.priority
    if req.due_date is not None:
        updates["due_date"] = req.due_date or None
    if req.status is not None and req.status in ("pending", "completed"):
        updates["status"] = req.status

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db.update(task_id, updates)
    updated = await db.get(task_id)
    return {"success": True, "id": task_id, "data": updated}

class EventUpdate(BaseModel):
    title: str | None = None
    date: str | None = None
    time: str | None = None
    description: str | None = None

@app.patch("/events/{event_id}")
@limiter.limit("30/minute")
async def update_event(request: Request, event_id: str, req: EventUpdate):
    """Update event fields. Only non-None fields are updated."""
    from tools.firestore_client import FirestoreClient
    db = FirestoreClient("events")

    existing = await db.get(event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    updates = {}
    if req.title is not None:
        title = req.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        existing_in_session = await db.list_by_session(existing.get("session_id", "default"))
        for e in existing_in_session:
            if e.get("id") != event_id and (e.get("title") or "").strip().lower() == title.lower():
                raise HTTPException(status_code=409, detail="Another event with this title exists in this session")
        updates["title"] = title
    if req.date is not None:
        updates["date"] = req.date
    if req.time is not None:
        updates["time"] = req.time
    if req.description is not None:
        updates["description"] = req.description

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db.update(event_id, updates)
    updated = await db.get(event_id)
    return {"success": True, "id": event_id, "data": updated}
