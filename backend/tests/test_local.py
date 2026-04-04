import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestrator import OrchestratorAgent

TEST_MESSAGES = [
    "add a high priority task: submit hackathon by April 8",
    "schedule a team meeting tomorrow at 2pm",
    "save a note: use gemini-2.5-flash for the project",
    "what tasks do I have?",
    "show my calendar events",
]

async def main():
    print("MAPA Local Test")
    print("="*40)
    agent = OrchestratorAgent()
    session_id = "test-001"
    for msg in TEST_MESSAGES:
        print(f"\nUser: {msg}")
        result = await agent.run(msg, session_id)
        print(f"MAPA: {result['response']}")
        print(f"Tools: {result['agents_called']}")

asyncio.run(main())
