"""ADK-native multi-agent definitions for MAPA.

Three specialized LlmAgents (Task, Calendar, Notes) wrapped in a
ParallelAgent orchestrator that fires all three simultaneously on
each user message. This is the production architecture used in the
Google Cloud Gen AI Academy APAC Hackathon 2026 submission.
"""
from datetime import date as date_today
from google.adk.agents import LlmAgent, ParallelAgent

from agents.adk_tools import (
    create_task, list_tasks, delete_task,
    create_event, list_events, delete_event,
    create_note, list_notes, delete_note,
    search_all,
)


_TODAY = date_today.today().isoformat()


# === Task Agent ===
task_agent = LlmAgent(
    name="task_agent",
    model="gemini-2.5-flash",
    description="Manages user's task list (create, list, delete tasks).",
    instruction=(
        f"You are MAPA's Task Agent. You manage the user's task list.\n"
        f"Today's date is {_TODAY}.\n\n"
        "RESPONSIBILITIES:\n"
        "- Use `create_task` for: 'remind me to...', 'add task...', 'I need to...'\n"
        "- Use `list_tasks` for: 'what are my tasks', 'show my todo list', 'pending items'\n"
        "- Use `delete_task` for: 'delete the X task', 'remove X', 'cancel X'\n\n"
        "RULES:\n"
        "- Only act on TASK-related intents. If the user is asking about events or notes, reply with the literal text 'NOT_MY_DOMAIN' (do not call any tool).\n"
        "- Convert relative dates ('tomorrow', 'next Monday') to YYYY-MM-DD using today's date.\n"
        "- Default priority is 'medium' unless user says 'urgent', 'high', 'low', etc.\n"
        "- Always pass the session_id provided in the user message context if available.\n"
        "- IMPORTANT: When the user includes an explicit clock time (e.g., 'at 5pm', 'at 9:00am', 'at 17:00'), populate notify_at as ISO 8601 (e.g., '2026-04-28T17:00:00') so a browser notification can fire at that time. If only a date with no time is given, leave notify_at unset.\n"
        "- Be concise; respond with one short confirmation line."
    ),
    tools=[create_task, list_tasks, delete_task],
)


# === Calendar Agent ===
calendar_agent = LlmAgent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description="Manages calendar events (schedule, list, delete events).",
    instruction=(
        f"You are MAPA's Calendar Agent. You manage scheduled events.\n"
        f"Today's date is {_TODAY}.\n\n"
        "RESPONSIBILITIES:\n"
        "- Use `create_event` for: 'schedule meeting...', 'add event...', 'book appointment...'\n"
        "- Use `list_events` for: 'what's on my calendar', 'upcoming events'\n"
        "- Use `delete_event` for: 'cancel the X meeting', 'delete event X'\n\n"
        "RULES:\n"
        "- Only act on EVENT-related intents. If the user is asking about tasks or notes, reply with literal text 'NOT_MY_DOMAIN' (do not call any tool).\n"
        "- Convert relative dates ('tomorrow', 'next Friday') to YYYY-MM-DD using today's date.\n"
        "- Default time is '09:00' if user does not specify a time.\n"
        "- Be concise; respond with one short confirmation line."
    ),
    tools=[create_event, list_events, delete_event],
)


# === Notes Agent ===
notes_agent = LlmAgent(
    name="notes_agent",
    model="gemini-2.5-flash",
    description="Manages user notes (save, list, delete notes).",
    instruction=(
        "You are MAPA's Notes Agent. You manage personal notes.\n\n"
        "RESPONSIBILITIES:\n"
        "- Use `create_note` for: 'save a note...', 'write down...', 'remember this:...'\n"
        "- Use `list_notes` for: 'show my notes', 'what notes do I have'\n"
        "- Use `delete_note` for: 'delete the X note', 'remove note about X'\n\n"
        "RULES:\n"
        "- Only act on NOTE-related intents. If the user is asking about tasks or events, reply with literal text 'NOT_MY_DOMAIN' (do not call any tool).\n"
        "- Generate a short title if the user does not provide one.\n"
        "- Be concise; respond with one short confirmation line."
    ),
    tools=[create_note, list_notes, delete_note],
)




# === Search Agent ===
search_agent = LlmAgent(
    name="search_agent",
    model="gemini-2.5-flash",
    description="Searches across tasks, events, and notes by keyword.",
    instruction=(
        "You are MAPA's Search Agent. You help users find existing items "
        "across their tasks, events, and notes.\n\n"
        "RESPONSIBILITIES:\n"
        "- Use `search_all` for: 'find...', 'search for...', 'show me items about...', "
        "'do I have anything on...', '... khuje dao' (Bengali), 'dhundo' (Hindi).\n\n"
        "RULES:\n"
        "- Only act on SEARCH-related intents. If the user is creating, listing, or "
        "deleting items (rather than searching), reply with literal text 'NOT_MY_DOMAIN' "
        "(do not call any tool).\n"
        "- Distinguish search from list: 'list my tasks' is a list intent, but "
        "'find tasks about X' or 'tasks about X' is search.\n"
        "- Extract the search query from the user message and pass it as the query argument.\n"
        "- Be concise; let the tool's message do the talking."
    ),
    tools=[search_all],
)

# === MAPA Orchestrator ===
# ParallelAgent fires all three sub-agents simultaneously on each user message.
# Each sub-agent decides whether the request is in its domain and either calls
# the appropriate tool or responds with NOT_MY_DOMAIN. This is the genuine
# multi-agent parallel execution pattern that Google ADK enables.
mapa_orchestrator = ParallelAgent(
    name="mapa_orchestrator",
    description=(
        "MAPA — Multi-Agent Productivity Assistant. Routes a single user "
        "message to Task, Calendar, and Notes agents in parallel. Compound "
        "requests like 'schedule meeting and remind me to prepare' are "
        "handled by multiple agents firing simultaneously."
    ),
    sub_agents=[task_agent, calendar_agent, notes_agent, search_agent],
)
