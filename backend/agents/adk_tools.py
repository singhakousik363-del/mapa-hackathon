"""ADK FunctionTool wrappers for MAPA's tools.

These wrap Firestore CRUD operations as plain Python functions that
ADK's Agent class can use as tools (via FunctionTool or directly via
Callable list in agent.tools).
"""
from datetime import datetime, timezone
from tools.firestore_client import FirestoreClient


# === TASK TOOLS ===

async def create_task(title: str, priority: str = "medium", due_date: str = None, notify_at: str = None, session_id: str = "default") -> dict:
    """Create a new task in Firestore.
    
    Args:
        title: Task title (required, non-empty)
        priority: One of low|medium|high (defaults to medium)
        due_date: YYYY-MM-DD format or None
        notify_at: ISO 8601 datetime for browser notification reminder (e.g. '2026-04-28T17:00:00'). Set this if user explicitly asks to be reminded at a specific time of day.
        session_id: User session ID
    
    Returns:
        dict with success status, id, and task data
    """
    title = (title or "").strip()
    if not title:
        return {"success": False, "message": "Task title cannot be empty", "data": None}
    
    db = FirestoreClient("tasks")
    
    # Duplicate check
    existing = await db.list_by_session(session_id)
    for t in existing:
        if (t.get("title") or "").strip().lower() == title.lower():
            return {"success": False, "message": f"Task '{title}' already exists", "data": None}
    
    if priority not in ("low", "medium", "high"):
        priority = "medium"
    
    doc_data = {
        "title": title,
        "priority": priority,
        "due_date": due_date or None,
        "notify_at": notify_at or None,
        "notified": False,
        "status": "pending",
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_id = await db.create(doc_data)
    msg = f"Task '{title}' created"
    if notify_at:
        msg += f" with reminder at {notify_at}"
    return {"success": True, "message": msg, "data": {**doc_data, "id": doc_id}}


async def list_tasks(session_id: str = "default") -> dict:
    """List all tasks across sessions (scope=all).
    
    Args:
        session_id: User session ID (currently shows all tasks)
    
    Returns:
        dict with task list and friendly count message
    """
    db = FirestoreClient("tasks")
    tasks = await db.list_all()
    if not tasks:
        return {"success": True, "message": "No tasks yet. Try saying 'remind me to call mom'.", "data": []}
    return {"success": True, "message": f"You have {len(tasks)} task{'s' if len(tasks) != 1 else ''}.", "data": tasks}


async def delete_task(title: str, session_id: str = "default") -> dict:
    """Delete a task by title (case-insensitive substring match).
    
    Args:
        title: Task title to delete
        session_id: User session ID
    
    Returns:
        dict with success status
    """
    title = (title or "").strip().lower()
    if not title:
        return {"success": False, "message": "Task title required", "data": None}
    
    db = FirestoreClient("tasks")
    tasks = await db.list_all()
    for t in tasks:
        if (t.get("title") or "").strip().lower() == title or title in (t.get("title") or "").strip().lower():
            await db.delete(t["id"])
            return {"success": True, "message": f"Task '{t.get('title')}' deleted", "data": {"id": t["id"]}}
    return {"success": False, "message": f"Task matching '{title}' not found", "data": None}


# === EVENT TOOLS ===

async def create_event(title: str, date: str, time: str = "09:00", description: str = "", session_id: str = "default") -> dict:
    """Create a calendar event in Firestore.
    
    Args:
        title: Event title
        date: YYYY-MM-DD format (required)
        time: HH:MM format (defaults to 09:00)
        description: Optional event description
        session_id: User session ID
    
    Returns:
        dict with success status, id, and event data
    """
    title = (title or "").strip()
    if not title:
        return {"success": False, "message": "Event title cannot be empty", "data": None}
    
    db = FirestoreClient("events")
    
    # Duplicate check within session
    existing = await db.list_by_session(session_id)
    for e in existing:
        if (e.get("title") or "").strip().lower() == title.lower():
            return {"success": False, "message": f"Event '{title}' already exists", "data": None}
    
    doc_data = {
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_id = await db.create(doc_data)
    return {"success": True, "message": f"Event '{title}' on {date}", "data": {**doc_data, "id": doc_id}}


async def list_events(session_id: str = "default") -> dict:
    """List all calendar events across sessions."""
    db = FirestoreClient("events")
    events = await db.list_all()
    if not events:
        return {"success": True, "message": "Your calendar is clear. Want to schedule something?", "data": []}
    return {"success": True, "message": f"You have {len(events)} event{'s' if len(events) != 1 else ''}.", "data": events}


async def delete_event(title: str, session_id: str = "default") -> dict:
    """Delete a calendar event by title."""
    title = (title or "").strip().lower()
    if not title:
        return {"success": False, "message": "Event title required", "data": None}
    
    db = FirestoreClient("events")
    events = await db.list_all()
    for e in events:
        if (e.get("title") or "").strip().lower() == title or title in (e.get("title") or "").strip().lower():
            await db.delete(e["id"])
            return {"success": True, "message": f"Event '{e.get('title')}' deleted", "data": {"id": e["id"]}}
    return {"success": False, "message": f"Event matching '{title}' not found", "data": None}


# === NOTE TOOLS ===

async def create_note(title: str, content: str, session_id: str = "default") -> dict:
    """Save a note in Firestore.
    
    Args:
        title: Note title
        content: Note body content
        session_id: User session ID
    
    Returns:
        dict with success status, id, and note data
    """
    title = (title or "").strip() or "Untitled"
    
    db = FirestoreClient("notes")
    
    # Duplicate check
    existing = await db.list_by_session(session_id)
    for n in existing:
        if (n.get("title") or "").strip().lower() == title.lower():
            return {"success": False, "message": f"Note '{title}' already exists", "data": None}
    
    doc_data = {
        "title": title,
        "content": content or "",
        "tags": [],
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_id = await db.create(doc_data)
    return {"success": True, "message": f"Note '{title}' saved", "data": {**doc_data, "id": doc_id}}


async def list_notes(session_id: str = "default") -> dict:
    """List all notes across sessions."""
    db = FirestoreClient("notes")
    notes = await db.list_all()
    if not notes:
        return {"success": True, "message": "No notes saved. Capture an idea anytime.", "data": []}
    return {"success": True, "message": f"You have {len(notes)} note{'s' if len(notes) != 1 else ''}.", "data": notes}


async def delete_note(title: str, session_id: str = "default") -> dict:
    """Delete a note by title."""
    title = (title or "").strip().lower()
    if not title:
        return {"success": False, "message": "Note title required", "data": None}
    
    db = FirestoreClient("notes")
    notes = await db.list_all()
    for n in notes:
        if (n.get("title") or "").strip().lower() == title or title in (n.get("title") or "").strip().lower():
            await db.delete(n["id"])
            return {"success": True, "message": f"Note '{n.get('title')}' deleted", "data": {"id": n["id"]}}
    return {"success": False, "message": f"Note matching '{title}' not found", "data": None}


# === SEARCH TOOLS ===

async def search_all(query: str, session_id: str = "default") -> dict:
    """Search across tasks, events, and notes by keyword.
    
    Performs case-insensitive substring match against titles and content.
    Returns categorized results.
    
    Args:
        query: Search query string (e.g., 'marketing', 'Kolkata', 'Q4')
        session_id: User session ID (currently searches all sessions)
    
    Returns:
        dict with tasks/events/notes lists and a friendly summary message
    """
    query = (query or "").strip()
    if not query or len(query) < 2:
        return {
            "success": False,
            "message": "Please provide a search query of at least 2 characters.",
            "data": {"tasks": [], "events": [], "notes": []}
        }
    
    q = query.lower()
    
    # Parallel-fetch all three collections
    tasks_db = FirestoreClient("tasks")
    events_db = FirestoreClient("events")
    notes_db = FirestoreClient("notes")
    
    all_tasks = await tasks_db.list_all()
    all_events = await events_db.list_all()
    all_notes = await notes_db.list_all()
    
    # Match against title (and content for notes)
    matched_tasks = [
        t for t in all_tasks
        if q in (t.get("title") or "").lower()
    ]
    matched_events = [
        e for e in all_events
        if q in (e.get("title") or "").lower()
        or q in (e.get("description") or "").lower()
    ]
    matched_notes = [
        n for n in all_notes
        if q in (n.get("title") or "").lower()
        or q in (n.get("content") or "").lower()
    ]
    
    total = len(matched_tasks) + len(matched_events) + len(matched_notes)
    
    if total == 0:
        return {
            "success": True,
            "message": f"No matches found for '{query}'.",
            "data": {"tasks": [], "events": [], "notes": []}
        }
    
    # Build a friendly summary
    parts = []
    if matched_tasks:
        parts.append(f"{len(matched_tasks)} task{'s' if len(matched_tasks) != 1 else ''}")
    if matched_events:
        parts.append(f"{len(matched_events)} event{'s' if len(matched_events) != 1 else ''}")
    if matched_notes:
        parts.append(f"{len(matched_notes)} note{'s' if len(matched_notes) != 1 else ''}")
    
    summary = f"Found {' and '.join(parts)} matching '{query}'."
    
    return {
        "success": True,
        "message": summary,
        "data": {
            "tasks": matched_tasks,
            "events": matched_events,
            "notes": matched_notes,
        }
    }
