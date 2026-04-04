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
    tasks = await FirestoreClient("tasks").list_by_session(session_id)
    events = await FirestoreClient("events").list_by_session(session_id)
    notes = await FirestoreClient("notes").list_by_session(session_id)
    return {"session_id": session_id, "stats": {"tasks": len(tasks), "events": len(events), "notes": len(notes)}, "tasks": tasks, "events": events, "notes": notes}
