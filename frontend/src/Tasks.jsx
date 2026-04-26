import { useState, useEffect } from "react";

const API = "https://mapa-api-875352080719.asia-south1.run.app";

const CloseIcon = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>);
const PlusIcon = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>);
const CheckIcon = () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>);

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
  const [activeMenu, setActiveMenu] = useState(null);

  const fetchTasks = () => {
    fetch(`${API}/session/${sessionId || "default"}/summary?scope=all`)
      .then(r => r.json())
      .then(d => { setTasks(d.tasks || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchTasks(); }, [sessionId]);

  const saveTask = async () => {
    if (!newTitle.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${API}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle.trim(),
          priority: newPriority,
          due_date: newDueDate || null,
          session_id: sessionId || "default"
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to create task. Please try again.");
        setSaving(false);
        return;
      }
      setNewTitle(""); setNewPriority("medium"); setNewDueDate(""); setNewDesc("");
      setShowAdd(false);
      fetchTasks();
    } catch(e) {
      alert("Network error. Please check your connection.");
    }
    setSaving(false);
  };

  const completeTask = async (task) => {
    setActiveMenu(null);
    try { await fetch(`${API}/tasks/${task.id}/complete`, { method: "PATCH" }); setTimeout(fetchTasks, 500); } catch(e) {}
  };

  const deleteTask = async (task) => {
    setActiveMenu(null);
    try { await fetch(`${API}/tasks/${task.id}`, { method: "DELETE" }); setTimeout(fetchTasks, 500); } catch(e) {}
  };

  const pending = tasks.filter(t => t.status === "pending");
  const completed = tasks.filter(t => t.status === "completed");
  const shown = filter === "pending" ? pending : completed;
  const sorted = [...shown].sort((a,b) => (({high:0,medium:1,low:2}[a.priority]||1)-({high:0,medium:1,low:2}[b.priority]||1)));

  return (
    <div style={{position:"fixed",inset:0,zIndex:100,display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,0,0,0.6)",backdropFilter:"blur(8px)"}}
      onClick={e=>{if(e.target===e.currentTarget){onClose();setActiveMenu(null);}}}>
      <div style={{width:"min(500px,94vw)",background:"rgba(6,12,6,0.97)",backdropFilter:"blur(24px)",border:"1px solid rgba(100,220,100,0.2)",borderRadius:18,padding:"24px 20px 40px",boxShadow:"0 24px 80px rgba(0,0,0,0.5)"}}>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:18}}>
          <div>
            <div style={{fontFamily:"'Playfair Display',serif",fontSize:18,fontWeight:700,color:"#ffe082",marginBottom:4}}>✅ My Tasks</div>
            <div style={{fontSize:11,color:"rgba(255,200,100,0.45)",fontFamily:"'Lato',sans-serif"}}>{pending.length} pending · {completed.length} completed</div>
          </div>
          <div style={{display:"flex",gap:8}}>
            <button onClick={()=>setShowAdd(true)} style={{padding:"8px 16px",borderRadius:9,border:"1px solid rgba(100,220,100,0.3)",background:"rgba(100,220,100,0.15)",color:"rgba(180,240,180,0.9)",fontSize:12,cursor:"pointer",fontFamily:"'Lato',sans-serif",display:"flex",alignItems:"center",gap:6}}><PlusIcon/> New Task</button>
            <button onClick={onClose} style={{width:34,height:34,borderRadius:9,border:"1px solid rgba(255,255,255,0.1)",background:"rgba(255,255,255,0.05)",cursor:"pointer",color:"rgba(255,230,170,0.6)",display:"flex",alignItems:"center",justifyContent:"center"}}><CloseIcon/></button>
          </div>
        </div>

        <div style={{display:"flex",gap:8,marginBottom:16}}>
          {[["pending","Pending",pending.length],["completed","Completed",completed.length]].map(([val,lbl,count])=>(
            <button key={val} onClick={()=>setFilter(val)} style={{padding:"6px 16px",borderRadius:8,border:`1px solid ${filter===val?"rgba(100,220,100,0.8)":"rgba(255,255,255,0.05)"}`,background:filter===val?"rgba(100,220,100,0.15)":"rgba(255,255,255,0.04)",color:filter===val?"rgba(180,240,180,0.95)":"rgba(255,230,170,0.5)",fontSize:12,cursor:"pointer",fontFamily:"'Lato',sans-serif",display:"flex",alignItems:"center",gap:6,transition:"all 0.18s"}}>
              {lbl} <span style={{background:"rgba(255,255,255,0.08)",borderRadius:99,padding:"1px 7px",fontSize:11}}>{count}</span>
            </button>
          ))}
        </div>

        <div style={{maxHeight:"50vh",overflowY:"auto"}}>
          {loading ? (
            <div style={{textAlign:"center",padding:40,color:"rgba(255,200,100,0.4)",fontFamily:"'Lato',sans-serif"}}>Loading...</div>
          ) : sorted.length === 0 ? (
            <div style={{textAlign:"center",padding:40}}>
              <div style={{fontSize:40,marginBottom:12}}>📋</div>
              <div style={{color:"rgba(255,200,100,0.4)",fontFamily:"'Lato',sans-serif",fontSize:13}}>{filter==="pending"?"No pending tasks. Great job!":"No completed tasks yet."}</div>
              {filter==="pending" && <button onClick={()=>setShowAdd(true)} style={{marginTop:16,display:"inline-flex",alignItems:"center",gap:6,background:"rgba(100,220,100,0.15)",border:"1px solid rgba(100,220,100,0.3)",borderRadius:9,padding:"8px 16px",color:"rgba(180,240,180,0.9)",fontSize:12,cursor:"pointer",fontFamily:"'Lato',sans-serif"}}><PlusIcon/> Add Task</button>}
            </div>
          ) : sorted.map((task)=>{
            const pc = PRIORITY_CONFIG[task.priority]||PRIORITY_CONFIG.medium;
            const isOpen = activeMenu === task.id;
            return (
              <div key={task.id} style={{position:"relative",marginBottom:10}}>
                <div onClick={()=>setActiveMenu(isOpen?null:task.id)}
                  style={{background:"rgba(255,255,255,0.04)",border:"1px solid rgba(255,255,255,0.06)",borderLeft:`3px solid ${pc.color}`,borderRadius:11,padding:"12px 14px",display:"flex",alignItems:"flex-start",gap:12,cursor:"pointer",transition:"all 0.18s",userSelect:"none"}}
                  onMouseEnter={e=>e.currentTarget.style.background="rgba(255,255,255,0.07)"}
                  onMouseLeave={e=>e.currentTarget.style.background="rgba(255,255,255,0.04)"}>
                  <div style={{flex:1,minWidth:0}}>
                    <div style={{fontFamily:"'Lato',sans-serif",fontSize:14,fontWeight:400,color:filter==="completed"?"rgba(255,240,200,0.45)":"rgba(255,240,200,0.92)",textDecoration:filter==="completed"?"line-through":"none",marginBottom:4}}>{task.title}</div>
                    <div style={{display:"flex",gap:8,alignItems:"center",flexWrap:"wrap"}}>
                      <span style={{fontSize:11,padding:"2px 9px",borderRadius:99,background:pc.bg,border:`1px solid ${pc.border}`,color:pc.color,fontFamily:"'Lato',sans-serif"}}>{pc.label}</span>
                      {task.due_date && <span style={{fontSize:11,color:"rgba(255,180,60,0.55)",fontFamily:"'Lato',sans-serif"}}>📅 {task.due_date}</span>}
                    </div>
                  </div>
                  <div style={{fontSize:10,color:"rgba(255,255,255,0.2)",marginTop:4}}>•••</div>
                </div>
                {isOpen && (
                  <div style={{position:"absolute",right:0,top:"calc(100% + 4px)",zIndex:200,background:"rgba(10,20,10,0.98)",border:"1px solid rgba(100,220,100,0.2)",borderRadius:10,boxShadow:"0 8px 32px rgba(0,0,0,0.6)",overflow:"hidden",minWidth:160}}>
                    {filter==="pending" && (
                      <button onClick={()=>completeTask(task)} style={{width:"100%",padding:"10px 16px",background:"none",border:"none",cursor:"pointer",color:"rgba(100,220,100,0.9)",fontFamily:"'Lato',sans-serif",fontSize:13,textAlign:"left",display:"flex",alignItems:"center",gap:8}}
                        onMouseEnter={e=>e.currentTarget.style.background="rgba(100,220,100,0.1)"}
                        onMouseLeave={e=>e.currentTarget.style.background="none"}>✅ Mark Complete</button>
                    )}
                    <button onClick={()=>deleteTask(task)} style={{width:"100%",padding:"10px 16px",background:"none",border:"none",cursor:"pointer",color:"rgba(255,100,80,0.9)",fontFamily:"'Lato',sans-serif",fontSize:13,textAlign:"left",display:"flex",alignItems:"center",gap:8}}
                      onMouseEnter={e=>e.currentTarget.style.background="rgba(255,80,60,0.1)"}
                      onMouseLeave={e=>e.currentTarget.style.background="none"}>🗑️ Delete Task</button>
                    <button onClick={()=>setActiveMenu(null)} style={{width:"100%",padding:"8px 16px",background:"none",border:"none",borderTop:"1px solid rgba(255,255,255,0.05)",cursor:"pointer",color:"rgba(255,255,255,0.3)",fontFamily:"'Lato',sans-serif",fontSize:12,textAlign:"left"}}>Cancel</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {showAdd && (
          <div style={{position:"fixed",inset:0,zIndex:200,display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,0,0,0.5)"}}
            onClick={e=>{if(e.target===e.currentTarget)setShowAdd(false);}}>
            <div style={{width:"min(500px,94vw)",background:"rgba(6,12,6,0.97)",border:"1px solid rgba(100,220,100,0.2)",borderRadius:18,padding:"24px 20px 20px"}}>
              <div style={{fontFamily:"'Playfair Display',serif",fontSize:18,fontWeight:700,color:"#ffe082",marginBottom:18}}>✅ New Task</div>
              <div style={{display:"flex",flexDirection:"column",gap:11}}>
                <input value={newTitle} onChange={e=>setNewTitle(e.target.value)} onKeyDown={e=>e.key==="Enter"&&saveTask()} placeholder="Task title..." style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",borderRadius:10,padding:"10px 14px",color:"rgba(255,240,200,0.9)",fontSize:14,fontFamily:"'Lato',sans-serif",outline:"none"}}/>
                <div style={{display:"flex",gap:7}}>
                  {Object.entries(PRIORITY_CONFIG).map(([k,v])=>(
                    <button key={k} onClick={()=>setNewPriority(k)} style={{flex:1,padding:"8px",borderRadius:9,border:`1px solid ${newPriority===k?v.border:"rgba(255,255,255,0.08)"}`,background:newPriority===k?v.bg:"rgba(255,255,255,0.04)",color:newPriority===k?v.color:"rgba(255,230,170,0.4)",fontSize:12,cursor:"pointer",fontFamily:"'Lato',sans-serif"}}>{v.label}</button>
                  ))}
                </div>
                <input type="date" value={newDueDate} onChange={e=>setNewDueDate(e.target.value)} style={{background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",borderRadius:10,padding:"9px 14px",color:"rgba(255,240,200,0.8)",fontSize:13,fontFamily:"'Lato',sans-serif",width:"100%",colorScheme:"dark"}}/>
                <div style={{display:"flex",gap:8,justifyContent:"flex-end"}}>
                  <button onClick={()=>setShowAdd(false)} style={{padding:"9px 18px",borderRadius:9,border:"1px solid rgba(255,255,255,0.1)",background:"rgba(255,255,255,0.05)",color:"rgba(255,230,170,0.6)",fontSize:13,cursor:"pointer",fontFamily:"'Lato',sans-serif"}}>Cancel</button>
                  <button onClick={saveTask} disabled={saving||!newTitle.trim()} style={{padding:"9px 18px",borderRadius:9,border:"none",background:"linear-gradient(135deg,#81c784,#43a047)",color:"white",fontSize:13,cursor:"pointer",fontFamily:"'Lato',sans-serif"}}>
                    {saving?"Saving...":"Add Task"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
