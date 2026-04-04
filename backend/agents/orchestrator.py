"""
MAPA - Google ADK Orchestrator (Fixed)
"""
import os, json, asyncio, logging
from datetime import datetime
import google.generativeai as genai
from tools.mcp_base import MCPRegistry
from tools.calendar_tool import CalendarMCPTool
from tools.task_tool import TaskMCPTool
from tools.notes_tool import NotesMCPTool

logger = logging.getLogger(__name__)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

LIST_KEYWORDS = ["show","list","get","display","view","see","what are","what's","whats","fetch","all my","my tasks","my events","my notes","any tasks","any events","any notes"]
COMPLETE_KEYWORDS = ["complete","done","finished","mark as done","mark complete","check off"]
DELETE_KEYWORDS = ["delete","remove","cancel","clear"]

def detect_operation(message):
    msg = message.lower()
    if any(k in msg for k in COMPLETE_KEYWORDS): return "complete"
    if any(k in msg for k in DELETE_KEYWORDS): return "delete"
    if any(k in msg for k in LIST_KEYWORDS): return "list"
    return ""

class ADKAgent:
    name = "base_agent"
    def __init__(self): self.model = genai.GenerativeModel("gemini-2.5-flash")
    async def run(self, task, context): raise NotImplementedError

class CalendarAgent(ADKAgent):
    name = "calendar_agent"
    def __init__(self, tool): super().__init__(); self.tool = tool
    async def run(self, task, context):
        session_id = context.get("session_id","default")
        operation = detect_operation(task); intent = {}
        if not operation:
            try:
                resp = self.model.generate_content(f'Extract calendar intent from: "{task}"\nReturn ONLY JSON: {{"operation":"create|list|delete","title":"...","date":"YYYY-MM-DD or empty","time":"HH:MM or empty","description":"..."}} Default to list if unsure.')
                intent = json.loads(resp.text.strip().replace("```json","").replace("```","").strip())
                operation = intent.get("operation","list")
            except: operation = "list"
        if operation == "list": params = {"operation":"list","session_id":session_id}
        elif operation == "create": params = {"operation":"create","title":intent.get("title",task),"date":intent.get("date",""),"time":intent.get("time",""),"description":intent.get("description",""),"session_id":session_id}
        else: params = {"operation":operation,"session_id":session_id,**intent}
        result = await self.tool.call(params)
        return {"agent":self.name,"success":result.success,"message":result.message,"data":result.data}

class TaskAgent(ADKAgent):
    name = "task_agent"
    def __init__(self, tool): super().__init__(); self.tool = tool
    async def run(self, task, context):
        session_id = context.get("session_id","default")
        operation = detect_operation(task); intent = {}
        if not operation:
            try:
                resp = self.model.generate_content(f'Extract task intent from: "{task}"\nReturn ONLY JSON: {{"operation":"create|list|complete|delete","title":"...","priority":"low|medium|high","due_date":"YYYY-MM-DD or empty"}} Use create if adding, list if viewing.')
                intent = json.loads(resp.text.strip().replace("```json","").replace("```","").strip())
                operation = intent.get("operation","create")
            except: operation = "create"
        if operation == "list": params = {"operation":"list","session_id":session_id}
        elif operation == "complete": params = {"operation":"complete","session_id":session_id,**intent}
        elif operation == "delete": params = {"operation":"delete","session_id":session_id,**intent}
        else: params = {"operation":"create","title":intent.get("title",task),"priority":intent.get("priority","medium"),"due_date":intent.get("due_date",""),"session_id":session_id}
        result = await self.tool.call(params)
        return {"agent":self.name,"success":result.success,"message":result.message,"data":result.data}

class NotesAgent(ADKAgent):
    name = "notes_agent"
    def __init__(self, tool): super().__init__(); self.tool = tool
    async def run(self, task, context):
        session_id = context.get("session_id","default")
        operation = detect_operation(task); intent = {}
        if not operation:
            try:
                resp = self.model.generate_content(f'Extract notes intent from: "{task}"\nReturn ONLY JSON: {{"operation":"create|list|search","title":"...","content":"...","query":"..."}} Use create if saving, list if viewing.')
                intent = json.loads(resp.text.strip().replace("```json","").replace("```","").strip())
                operation = intent.get("operation","create")
            except: operation = "create"
        if operation == "list": params = {"operation":"list","session_id":session_id}
        elif operation == "search": params = {"operation":"search","query":intent.get("query",task),"session_id":session_id}
        else:
            content = task
            for p in ["note:","note -","note that","jot down","write down"]:
                if p in task.lower(): content = task[task.lower().index(p)+len(p):].strip(); break
            params = {"operation":"create","title":intent.get("title",content[:50] or "Note"),"content":intent.get("content",content),"session_id":session_id}
        result = await self.tool.call(params)
        return {"agent":self.name,"success":result.success,"message":result.message,"data":result.data}

class OrchestratorAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.registry = MCPRegistry()
        ct = CalendarMCPTool(); tt = TaskMCPTool(); nt = NotesMCPTool()
        self.registry.register(ct); self.registry.register(tt); self.registry.register(nt)
        self.sub_agents = {"calendar_agent":CalendarAgent(ct),"task_agent":TaskAgent(tt),"notes_agent":NotesAgent(nt)}
        self._sessions = {}

    def _add_history(self, sid, role, content):
        self._sessions.setdefault(sid,[]).append({"role":role,"content":content,"timestamp":datetime.utcnow().isoformat()})
        self._sessions[sid] = self._sessions[sid][-20:]

    def _classify_agents(self, message):
        msg = message.lower(); agents = []
        if any(w in msg for w in ["calendar","event","schedule","meeting","appointment","remind","today","tomorrow","next week","my events","any events"]): agents.append("calendar_agent")
        if any(w in msg for w in ["task","todo","to-do","to do","deadline","priority","submit","create task","add task","mark","my tasks","any tasks"]): agents.append("task_agent")
        if any(w in msg for w in ["note","memo","write down","jot","idea","draft","remember","my notes","any notes"]): agents.append("notes_agent")
        if not agents and any(w in msg for w in ["show","list","display","all","everything"]): agents = ["task_agent","calendar_agent","notes_agent"]
        return agents or ["task_agent"]

    async def run(self, user_message, session_id):
        self._add_history(session_id,"user",user_message)
        target_agents = self._classify_agents(user_message)
        logger.info(f"[ADK] '{user_message[:50]}' → {target_agents}")
        context = {"session_id":session_id}
        raw_results = await asyncio.gather(*[self.sub_agents[a].run(user_message,context) for a in target_agents], return_exceptions=True)
        results = {}
        for a, r in zip(target_agents, raw_results):
            results[a] = {"success":False,"message":str(r),"data":None} if isinstance(r,Exception) else r
        history_text = "\n".join([f"{h['role']}: {h['content']}" for h in self._sessions.get(session_id,[])[-4:]])
        try:
            synthesis = self.model.generate_content(f"""You are MAPA, a friendly AI productivity assistant.\nConversation:\n{history_text}\nAgent results:\n{json.dumps(results,default=str,indent=2)}\nWrite a clear friendly response. If list has items name them. If empty say so helpfully. No JSON. No markdown.""")
            response_text = synthesis.text.strip()
        except Exception as e:
            response_text = list(results.values())[0].get("message","Done!")
        self._add_history(session_id,"assistant",response_text)
        return {"response":response_text,"agents_called":target_agents,"results":results,"adk_version":"1.0","session_id":session_id}
