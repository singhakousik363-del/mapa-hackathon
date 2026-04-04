import { useState, useEffect } from "react";

const API = "http://localhost:8080";

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
);
const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
);
const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
);

const PRIORITY_CONFIG = {
  high:   { color:"rgba(255,100,80,0.9)",  bg:"rgba(255,80,60,0.15)",  border:"rgba(255,80,60,0.3)",  label:"High"   },
  medium: { color:"rgba(255,180,60,0.9)",  bg:"rgba(255,160,40,0.12)", border:"rgba(255,160,40,0.3)", label:"Medium" },
  low:    { color:"rgba(100,200,120,0.9)", bg:"rgba(80,190,100,0.12)", border:"rgba(80,190,100,0.3)", label:"Low"    },
};

export default function TasksPage({ sessionId, onClose }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [filter, setFilter] = useState("pending");
  const [newTitle, setNewTitle] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const [newDueDate, setNewDueDate] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [saving, setSaving] = useState(false);

  const fetchTasks = () => {
    if (!sessionId) { setLoading(false); return; }
    fetch(`${API}/session/${sessionId}/summary`)
      .then(r => r.json())
      .then(d => { setTasks(d.tasks || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchTasks(); }, [sessionId]);

  const saveTask = async () => {
    if (!newTitle.trim()) return;
    setSaving(true);
    try {
      await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Add a ${newPriority} priority task: ${newTitle}${newDueDate?` due on ${newDueDate}`:""}${newDesc?`. Description: ${newDesc}`:""}`,
          session_id: sessionId,
        }),
      });
      setNewTitle(""); setNewPriority("medium"); setNewDueDate(""); setNewDesc("");
      setShowAdd(false);
      setTimeout(fetchTasks, 800);
    } catch(e) {}
    setSaving(false);
  };

  const completeTask = async (task) => {
    try {
      await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `Mark task "${task.title}" as complete`, session_id: sessionId }),
      });
      setTimeout(fetchTasks, 800);
    } catch(e) {}
  };

  const pending = tasks.filter(t => t.status === "pending");
  const completed = tasks.filter(t => t.status === "completed");
  const shown = filter === "pending" ? pending : completed;
  const priorityOrder = { high:0, medium:1, low:2 };
  const sorted = [...shown].sort((a,b) => (priorityOrder[a.priority]||1) - (priorityOrder[b.priority]||1));

  return (
    <div style={{ position:"fixed", inset:0, zIndex:100, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.6)", backdropFilter:"blur(8px)" }}
      onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400&display=swap');
        .task-card:hover{background:rgba(255,255,255,0.07)!important}
        .task-card{transition:all 0.18s}
        .tadd-input::placeholder{color:rgba(255,230,170,0.3)}
        .tadd-input:focus{outline:none;border-color:rgba(100,220,120,0.5)!important}
        .filter-btn:hover{background:rgba(255,255,255,0.1)!important}
      `}</style>

      <div style={{ width:"min(720px,96vw)", height:"88vh", background:"rgba(6,12,6,0.94)", backdropFilter:"blur(24px)", border:"1px solid rgba(100,220,100,0.12)", borderRadius:20, overflow:"hidden", boxShadow:"0 24px 80px rgba(0,0,0,0.7)", display:"flex", flexDirection:"column" }}>

        {/* Header */}
        <div style={{ padding:"16px 22px", borderBottom:"1px solid rgba(100,220,100,0.08)", display:"flex", alignItems:"center", gap:12, flexShrink:0 }}>
          <div style={{ width:36, height:36, borderRadius:10, background:"rgba(100,220,100,0.12)", border:"1px solid rgba(100,220,100,0.3)", display:"flex", alignItems:"center", justifyContent:"center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#81c784" strokeWidth="2" strokeLinecap="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          </div>
          <div>
            <div style={{ fontFamily:"'Playfair Display',serif", fontSize:18, fontWeight:700, color:"#ffe082" }}>My Tasks</div>
            <div style={{ fontSize:11, color:"rgba(100,220,100,0.5)", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>{pending.length} pending · {completed.length} completed</div>
          </div>
          <div style={{ marginLeft:"auto", display:"flex", gap:8, alignItems:"center" }}>
            <button onClick={()=>setShowAdd(true)} style={{ display:"flex", alignItems:"center", gap:6, background:"rgba(100,220,100,0.15)", border:"1px solid rgba(100,220,100,0.3)", borderRadius:9, padding:"7px 14px", color:"rgba(180,240,180,0.9)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>
              <PlusIcon/> New Task
            </button>
            <button onClick={onClose} style={{ width:34, height:34, borderRadius:9, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", cursor:"pointer", color:"rgba(255,230,170,0.6)", display:"flex", alignItems:"center", justifyContent:"center" }}><CloseIcon/></button>
          </div>
        </div>

        {/* Filter tabs */}
        <div style={{ padding:"10px 22px", borderBottom:"1px solid rgba(255,255,255,0.04)", display:"flex", gap:8, flexShrink:0 }}>
          {[["pending","Pending",pending.length],["completed","Completed",completed.length]].map(([val,lbl,count])=>(
            <button key={val} className="filter-btn" onClick={()=>setFilter(val)} style={{ padding:"6px 16px", borderRadius:8, border:`1px solid ${filter===val?"rgba(100,220,100,0.4)":"rgba(255,255,255,0.08)"}`, background:filter===val?"rgba(100,220,100,0.15)":"rgba(255,255,255,0.04)", color:filter===val?"rgba(180,240,180,0.95)":"rgba(255,230,170,0.5)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif", display:"flex", alignItems:"center", gap:6, transition:"all 0.18s" }}>
              {lbl}
              <span style={{ background:filter===val?"rgba(100,220,100,0.25)":"rgba(255,255,255,0.08)", borderRadius:99, padding:"1px 7px", fontSize:11 }}>{count}</span>
            </button>
          ))}
          {/* Priority legend */}
          <div style={{ marginLeft:"auto", display:"flex", gap:10, alignItems:"center" }}>
            {Object.entries(PRIORITY_CONFIG).map(([k,v])=>(
              <span key={k} style={{ fontSize:11, color:v.color, fontFamily:"'Lato',sans-serif", display:"flex", alignItems:"center", gap:4 }}>
                <span style={{ width:7, height:7, borderRadius:"50%", background:v.color, display:"inline-block" }}/>{v.label}
              </span>
            ))}
          </div>
        </div>

        {/* Task list */}
        <div style={{ flex:1, overflow:"auto", padding:"14px 16px", display:"flex", flexDirection:"column", gap:7 }}>
          {loading ? (
            <div style={{ textAlign:"center", padding:40, color:"rgba(100,220,100,0.4)", fontFamily:"'Lato',sans-serif", fontSize:13 }}>Loading...</div>
          ) : sorted.length === 0 ? (
            <div style={{ textAlign:"center", padding:40 }}>
              <div style={{ fontSize:40, marginBottom:12 }}>{filter==="pending"?"📋":"✅"}</div>
              <div style={{ color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif", fontSize:13, fontWeight:300 }}>
                {filter==="pending" ? "No pending tasks. Great job!" : "No completed tasks yet."}
              </div>
              {filter==="pending" && <button onClick={()=>setShowAdd(true)} style={{ marginTop:16, display:"inline-flex", alignItems:"center", gap:6, background:"rgba(100,220,100,0.15)", border:"1px solid rgba(100,220,100,0.3)", borderRadius:9, padding:"8px 16px", color:"rgba(180,240,180,0.9)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif" }}><PlusIcon/> Add Task</button>}
            </div>
          ) : sorted.map((task, i) => {
            const pc = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
            return (
              <div key={task.id||i} className="task-card" style={{ background:"rgba(255,255,255,0.04)", border:`1px solid rgba(255,255,255,0.06)`, borderLeft:`3px solid ${pc.color}`, borderRadius:11, padding:"12px 14px", display:"flex", alignItems:"flex-start", gap:12 }}>
                {/* Complete button */}
                {filter==="pending" && (
                  <button onClick={()=>completeTask(task)} title="Mark complete" style={{ width:26, height:26, borderRadius:"50%", border:`1.5px solid ${pc.border}`, background:"transparent", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", color:pc.color, flexShrink:0, marginTop:1, transition:"all 0.18s" }}
                    onMouseEnter={e=>{e.currentTarget.style.background=pc.bg;}}
                    onMouseLeave={e=>{e.currentTarget.style.background="transparent";}}>
                    <CheckIcon/>
                  </button>
                )}
                {filter==="completed" && (
                  <div style={{ width:26, height:26, borderRadius:"50%", border:`1.5px solid rgba(100,220,100,0.4)`, background:"rgba(100,220,100,0.15)", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:1 }}>
                    <CheckIcon/>
                  </div>
                )}

                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontFamily:"'Lato',sans-serif", fontSize:14, fontWeight:400, color: filter==="completed"?"rgba(255,240,200,0.45)":"rgba(255,240,200,0.92)", textDecoration:filter==="completed"?"line-through":"none", marginBottom:task.description||task.due_date?4:0 }}>{task.title}</div>
                  {task.description && <div style={{ fontSize:12, color:"rgba(255,220,150,0.4)", fontFamily:"'Lato',sans-serif", fontWeight:300, marginBottom:task.due_date?4:0 }}>{task.description}</div>}
                  <div style={{ display:"flex", gap:8, alignItems:"center", flexWrap:"wrap" }}>
                    <span style={{ fontSize:11, padding:"2px 9px", borderRadius:99, background:pc.bg, border:`1px solid ${pc.border}`, color:pc.color, fontFamily:"'Lato',sans-serif" }}>{pc.label}</span>
                    {task.due_date && <span style={{ fontSize:11, color:"rgba(255,180,60,0.55)", fontFamily:"'Lato',sans-serif" }}>📅 {task.due_date}</span>}
                    {task.completed_at && <span style={{ fontSize:11, color:"rgba(100,220,100,0.45)", fontFamily:"'Lato',sans-serif" }}>✓ {new Date(task.completed_at).toLocaleDateString("en-IN",{day:"numeric",month:"short"})}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Task modal */}
      {showAdd && (
        <div style={{ position:"fixed", inset:0, zIndex:200, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.5)" }}
          onClick={e=>{if(e.target===e.currentTarget)setShowAdd(false);}}>
          <div style={{ width:"min(500px,94vw)", background:"rgba(6,12,6,0.97)", backdropFilter:"blur(24px)", border:"1px solid rgba(100,220,100,0.2)", borderRadius:18, padding:"24px", boxShadow:"0 24px 80px rgba(0,0,0,0.8)" }}>
            <div style={{ fontFamily:"'Playfair Display',serif", fontSize:18, fontWeight:700, color:"#ffe082", marginBottom:18 }}>✅ New Task</div>
            <div style={{ display:"flex", flexDirection:"column", gap:11 }}>
              <input value={newTitle} onChange={e=>setNewTitle(e.target.value)} onKeyDown={e=>e.key==="Enter"&&saveTask()} placeholder="Task title..." className="tadd-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:14, fontFamily:"'Lato',sans-serif", fontWeight:300 }}/>
              <textarea value={newDesc} onChange={e=>setNewDesc(e.target.value)} placeholder="Description (optional)..." rows={2} className="tadd-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:13, fontFamily:"'Lato',sans-serif", fontWeight:300, resize:"vertical", outline:"none" }}/>

              {/* Priority selector */}
              <div>
                <div style={{ fontSize:11, color:"rgba(255,200,100,0.45)", fontFamily:"'Lato',sans-serif", letterSpacing:"0.08em", marginBottom:7 }}>PRIORITY</div>
                <div style={{ display:"flex", gap:7 }}>
                  {Object.entries(PRIORITY_CONFIG).map(([k,v])=>(
                    <button key={k} onClick={()=>setNewPriority(k)} style={{ flex:1, padding:"8px", borderRadius:9, border:`1px solid ${newPriority===k?v.border:"rgba(255,255,255,0.08)"}`, background:newPriority===k?v.bg:"rgba(255,255,255,0.04)", color:newPriority===k?v.color:"rgba(255,230,170,0.4)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif", transition:"all 0.18s" }}>{v.label}</button>
                  ))}
                </div>
              </div>

              <div>
                <div style={{ fontSize:11, color:"rgba(255,200,100,0.45)", fontFamily:"'Lato',sans-serif", letterSpacing:"0.08em", marginBottom:7 }}>DUE DATE (OPTIONAL)</div>
                <input type="date" value={newDueDate} onChange={e=>setNewDueDate(e.target.value)} className="tadd-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"9px 14px", color:"rgba(255,240,200,0.8)", fontSize:13, fontFamily:"'Lato',sans-serif", fontWeight:300, width:"100%", colorScheme:"dark" }}/>
              </div>

              <div style={{ display:"flex", gap:8, justifyContent:"flex-end", marginTop:4 }}>
                <button onClick={()=>setShowAdd(false)} style={{ padding:"9px 18px", borderRadius:9, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", color:"rgba(255,230,170,0.6)", fontSize:13, cursor:"pointer", fontFamily:"'Lato',sans-serif" }}>Cancel</button>
                <button onClick={saveTask} disabled={saving||!newTitle.trim()} style={{ padding:"9px 20px", borderRadius:9, border:"none", background:saving||!newTitle.trim()?"rgba(100,220,100,0.15)":"linear-gradient(135deg,#81c784,#43a047)", color:"white", fontSize:13, cursor:saving||!newTitle.trim()?"not-allowed":"pointer", fontFamily:"'Lato',sans-serif", fontWeight:400, display:"flex", alignItems:"center", gap:6 }}>
                  {saving?"Saving...":<><PlusIcon/> Add Task</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
