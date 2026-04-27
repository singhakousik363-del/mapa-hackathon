# MAPA - Multi-Agent Productivity Assistant

> Build in APAC. Build for the world.
> A genuine multi-agent AI productivity system built on Google ADK for the Google Cloud Gen AI Academy APAC Hackathon 2026.

Live App: https://gen-lang-client-0349644995.web.app
API: https://mapa-api-637668641799.asia-south1.run.app
API Docs: https://mapa-api-637668641799.asia-south1.run.app/docs

---

## The Problem

APAC has hundreds of millions of professionals who think in Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati but operate productivity tools in English. They juggle 5+ disconnected apps daily.

MAPA replaces all of them with a single sentence in your own language.


---

## One Prompt. Four Agents. Zero Switching.

Powered by Google ADK ParallelAgent. Every user message fans out to four specialized LlmAgents simultaneously:

- Task Agent - To-do management (create_task, list_tasks, delete_task)
- Calendar Agent - Event scheduling (create_event, list_events, delete_event)
- Notes Agent - Knowledge capture (create_note, list_notes, delete_note)
- Search Agent - Cross-domain retrieval (search_all across all collections)

Each agent has a domain-scoped instruction prompt. Out-of-domain requests reply NOT_MY_DOMAIN and the orchestrator filters them out, so no wasted tool calls.

---

## Genuine Google ADK Multi-Agent Architecture

This is not a custom orchestrator wrapping Gemini. MAPA uses ADK's actual primitives:

- LlmAgent - each of the four sub-agents
- ParallelAgent - the mapa_orchestrator that fans out to sub-agents
- Runner - executes the orchestrator with session management
- InMemorySessionService - tracks per-session state
- FunctionTool - wraps async Python functions as agent tools

Code paths to inspect:

- backend/agents/adk_agents.py - the four LlmAgents and the ParallelAgent
- backend/agents/adk_tools.py - async tool functions wrapping Firestore CRUD + cross-domain search
- backend/agents/adk_orchestrator.py - Runner + InMemorySessionService integration


---

## Key Innovations

1. Genuine Google ADK - Real LlmAgent + ParallelAgent + Runner, not a custom wrapper
2. Compound-intent in one pass - "Schedule meeting tomorrow and add task to prepare" fires Calendar AND Task agents simultaneously
3. Voice-first multilingual - 8 Indian languages (EN HI BN TA TE MR GU PA) via Web Speech API
4. Cross-domain search - "find anything about Q4" returns matches across tasks, events, AND notes in one call
5. Production-hardened - min-instances=1, slowapi rate limiting, structured logging, greeting fast-path, duplicate detection
6. Inline Edit and Delete - Full CRUD UI on tasks, events, AND notes with PATCH/DELETE endpoints

---

## Architecture

USER (Voice + Text in 8 Indian languages)
  -> FRONTEND (React + Vite + Firebase Hosting)
  -> BACKEND (FastAPI on Cloud Run, asia-south1)
  -> google.adk.agents.ParallelAgent "mapa_orchestrator"
       -> Task Agent (LlmAgent + Gemini 2.5)
       -> Calendar Agent (LlmAgent + Gemini 2.5)
       -> Notes Agent (LlmAgent + Gemini 2.5)
       -> Search Agent (LlmAgent + Gemini 2.5)
  -> Firebase Firestore (tasks | events | notes)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | Google ADK 1.31 (LlmAgent, ParallelAgent, Runner, FunctionTool) |
| LLM | Gemini 2.5 Flash |
| Backend | Python 3.11, FastAPI, Uvicorn, slowapi |
| Database | Firebase Firestore |
| Frontend | React 18, Vite |
| Voice | Web Speech API |
| Hosting | Firebase Hosting + Cloud Run asia-south1 |


---

## API Endpoints

Live at https://mapa-api-637668641799.asia-south1.run.app. Interactive docs at /docs.

| Endpoint | Method | Description |
|---|---|---|
| /health | GET | Service health check |
| /tools | GET | List registered tool names |
| /chat | POST | Main conversation endpoint (runs ADK ParallelAgent) |
| /session/{id}/summary | GET | All tasks + events + notes for a session |
| /tasks | POST | Quick-add task (used by UI) |
| /tasks/{id} | PATCH | Edit a task |
| /tasks/{id} | DELETE | Delete a task |
| /tasks/{id}/complete | PATCH | Mark a task as completed |
| /events/{id} | PATCH | Edit a calendar event |
| /events/{id} | DELETE | Delete a calendar event |
| /notes/{id} | PATCH | Edit a note |
| /notes/{id} | DELETE | Delete a note |

---

## Try It Live

Visit https://gen-lang-client-0349644995.web.app and try:

- "Remind me to submit Q4 report by Friday" - Task Agent
- "Schedule a team standup tomorrow at 10 AM" - Calendar Agent
- "Save a note: Q1 priorities are mobile, search, onboarding" - Notes Agent
- "find tasks about Q4" - Search Agent (cross-domain)
- Bengali: "kal sokale dentist-er appointment ache"
- Hindi: "mujhe shaam ko groceries laani hai"
- Compound: "Schedule design review tomorrow at 3pm and add task to prepare slides"
- Hit the mic icon to speak instead of typing


---

## Performance

Measured on Cloud Run asia-south1 with min-instances=1 and 2 vCPU / 1 GiB RAM:

| Metric | Value |
|---|---|
| Cold start | n/a (kept warm with min-instances=1) |
| Warm request P50 latency | ~1.4 sec |
| Warm request P95 latency | ~2.3 sec |
| ParallelAgent fan-out | 4 sub-agents simultaneously |
| Region | asia-south1 (Mumbai) |

---

## Production Hardening

- Cold-start mitigation: min-instances=1, no-cpu-throttling, cpu=2
- Rate limiting: slowapi with 10/minute on /chat
- Structured JSON logging compatible with Cloud Run log explorer
- Greeting fast-path: detects "hi", "hello", "namaste", "thanks" and returns guidance without invoking any agent or DB write (prevents pollution)
- Duplicate writes blocked: per-session duplicate-title detection in every create-tool
- Input validation: 2000-char input cap; empty-input early return

---

## Local Development

Backend:

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    export GEMINI_API_KEY=your-gemini-key
    export GOOGLE_API_KEY=$GEMINI_API_KEY
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-admin-key.json
    uvicorn api.main:app --reload --port 8080

Frontend:

    cd frontend
    npm install
    echo "VITE_API_URL=http://localhost:8080" > .env.local
    npm run dev

---

## Why APAC Matters

India alone has ~500M non-English-first-language smartphone users. Southeast Asia adds ~300M. Most productivity tools treat these users as an afterthought. MAPA flips that: voice-first, multilingual-native, deployed in asia-south1 for sub-100ms latency to Indian users.

This isn't a hackathon-only demo. It's a usable productivity tool for the APAC region, running on Google Cloud, ready to be opened by anyone with a phone.

---

## Author

Kousik Singha
Google Cloud Gen AI Academy APAC Hackathon 2026 - Cohort 1

GitHub: https://github.com/singhakousik363-del
Repo: https://github.com/singhakousik363-del/mapa-hackathon

---

## License

MIT
