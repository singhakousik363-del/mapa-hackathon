import { useState, useEffect } from "react";

const API = "https://mapa-api-875352080719.asia-south1.run.app";

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
);
const ChevronLeft = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="15 18 9 12 15 6"/></svg>
);
const ChevronRight = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
);

export default function CalendarPage({ sessionId, onClose }) {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [selectedDay, setSelectedDay] = useState(null);
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editTime, setEditTime] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  const fetchData = () => {
    if (!sessionId) { setLoading(false); return; }
    fetch(`${API}/session/${sessionId || "default"}/summary?scope=all`)
      .then(r => r.json())
      .then(data => {
        setEvents(data.events || []);
        setTasks(data.tasks || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [sessionId]);

  const deleteEvent = async (event) => {
    if (!confirm(`Delete event "${event.title}"?`)) return;
    try {
      await fetch(`${API}/events/${event.id}`, { method: "DELETE" });
      fetchData();
    } catch(e) {
      alert("Could not delete event. Please try again.");
    }
  };

  const startEditEvent = (event) => {
    setEditingEvent(event);
    setEditTitle(event.title || "");
    setEditDate(event.date || "");
    setEditTime(event.time || "09:00");
  };

  const cancelEditEvent = () => {
    setEditingEvent(null);
    setEditTitle("");
    setEditDate("");
    setEditTime("");
  };

  const saveEditEvent = async () => {
    if (!editTitle.trim()) return;
    setSavingEdit(true);
    try {
      const res = await fetch(`${API}/events/${editingEvent.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: editTitle.trim(),
          date: editDate || null,
          time: editTime || null
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Could not update event.");
        setSavingEdit(false);
        return;
      }
      cancelEditEvent();
      fetchData();
    } catch(e) {
      alert("Network error. Please try again.");
    }
    setSavingEdit(false);
  };

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  // Build calendar grid
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrev = new Date(year, month, 0).getDate();
  const cells = [];
  for (let i = firstDay - 1; i >= 0; i--) cells.push({ day: daysInPrev - i, current: false });
  for (let d = 1; d <= daysInMonth; d++) cells.push({ day: d, current: true });
  while (cells.length % 7 !== 0) cells.push({ day: cells.length - daysInMonth - firstDay + 1, current: false });

  // Get items for a date string YYYY-MM-DD
  const getItemsForDate = (dateStr) => {
    const dayEvents = events.filter(e => e.date === dateStr);
    const dayTasks = tasks.filter(t => t.due_date === dateStr);
    return { events: dayEvents, tasks: dayTasks };
  };

  const formatDate = (d) => {
    const mm = String(month + 1).padStart(2, "0");
    const dd = String(d).padStart(2, "0");
    return `${year}-${mm}-${dd}`;
  };

  const selectedDateStr = selectedDay ? formatDate(selectedDay) : null;
  const selectedItems = selectedDateStr ? getItemsForDate(selectedDateStr) : null;

  const isToday = (d) => d === today.getDate() && month === today.getMonth() && year === today.getFullYear();

  return (
    <div style={{ position:"fixed", inset:0, zIndex:100, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.6)", backdropFilter:"blur(8px)" }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>

      <div style={{ width:"min(820px,96vw)", maxHeight:"92vh", background:"rgba(8,15,8,0.92)", backdropFilter:"blur(24px)", border:"1px solid rgba(255,200,100,0.15)", borderRadius:20, overflow:"hidden", boxShadow:"0 24px 80px rgba(0,0,0,0.7)", display:"flex", flexDirection:"column" }}>

        {/* Header */}
        <div style={{ padding:"18px 24px", borderBottom:"1px solid rgba(255,200,100,0.1)", display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ width:36, height:36, borderRadius:10, background:"rgba(255,180,60,0.15)", border:"1px solid rgba(255,180,60,0.3)", display:"flex", alignItems:"center", justifyContent:"center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffb300" strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <div>
            <div style={{ fontFamily:"'Playfair Display',serif", fontSize:18, fontWeight:700, color:"#ffe082" }}>Calendar</div>
            <div style={{ fontSize:11, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>Your schedule at a glance</div>
          </div>
          <button onClick={onClose} style={{ marginLeft:"auto", width:34, height:34, borderRadius:9, border:"1px solid rgba(255,255,255,0.12)", background:"rgba(255,255,255,0.06)", cursor:"pointer", color:"rgba(255,230,170,0.7)", display:"flex", alignItems:"center", justifyContent:"center" }}>
            <CloseIcon/>
          </button>
        </div>

        <div style={{ display:"flex", flex:1, overflow:"hidden" }}>

          {/* Calendar grid */}
          <div style={{ flex:1, padding:"20px 24px", overflow:"auto" }}>

            {/* Month nav */}
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
              <button onClick={prevMonth} style={{ width:34, height:34, borderRadius:9, border:"1px solid rgba(255,200,100,0.2)", background:"rgba(255,255,255,0.06)", cursor:"pointer", color:"rgba(255,230,170,0.8)", display:"flex", alignItems:"center", justifyContent:"center" }}><ChevronLeft/></button>
              <div style={{ textAlign:"center" }}>
                <div style={{ fontFamily:"'Playfair Display',serif", fontSize:22, fontWeight:700, color:"#ffe082" }}>{MONTHS[month]}</div>
                <div style={{ fontSize:13, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif" }}>{year}</div>
              </div>
              <button onClick={nextMonth} style={{ width:34, height:34, borderRadius:9, border:"1px solid rgba(255,200,100,0.2)", background:"rgba(255,255,255,0.06)", cursor:"pointer", color:"rgba(255,230,170,0.8)", display:"flex", alignItems:"center", justifyContent:"center" }}><ChevronRight/></button>
            </div>

            {/* Day headers */}
            <div style={{ display:"grid", gridTemplateColumns:"repeat(7,1fr)", gap:4, marginBottom:6 }}>
              {DAYS.map(d => (
                <div key={d} style={{ textAlign:"center", fontSize:11, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif", fontWeight:400, padding:"4px 0", letterSpacing:"0.05em" }}>{d}</div>
              ))}
            </div>

            {/* Day cells */}
            <div style={{ display:"grid", gridTemplateColumns:"repeat(7,1fr)", gap:4 }}>
              {cells.map((cell, idx) => {
                const dateStr = cell.current ? formatDate(cell.day) : null;
                const items = dateStr ? getItemsForDate(dateStr) : { events:[], tasks:[] };
                const hasItems = items.events.length > 0 || items.tasks.length > 0;
                const isSelected = selectedDay === cell.day && cell.current;
                const isTod = cell.current && isToday(cell.day);

                return (
                  <div key={idx} onClick={() => cell.current && setSelectedDay(cell.day)}
                    style={{
                      aspectRatio:"1", borderRadius:10, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", cursor:cell.current?"pointer":"default", position:"relative", transition:"all 0.18s",
                      background: isSelected ? "rgba(255,180,60,0.25)" : isTod ? "rgba(255,180,60,0.12)" : hasItems ? "rgba(100,200,120,0.1)" : "rgba(255,255,255,0.04)",
                      border: isSelected ? "1.5px solid rgba(255,180,60,0.6)" : isTod ? "1.5px solid rgba(255,180,60,0.35)" : hasItems ? "1px solid rgba(100,220,120,0.3)" : "1px solid rgba(255,255,255,0.05)",
                      opacity: cell.current ? 1 : 0.25,
                    }}>

                    <span style={{ fontSize:14, fontFamily:"'Lato',sans-serif", fontWeight: isTod||isSelected ? 400 : 300, color: isSelected ? "#ffe082" : isTod ? "#ffcc02" : "rgba(255,240,200,0.85)" }}>
                      {cell.day}
                    </span>

                    {/* Dot indicators */}
                    {hasItems && (
                      <div style={{ display:"flex", gap:2, marginTop:2 }}>
                        {items.events.slice(0,2).map((_,i) => (
                          <div key={i} style={{ width:4, height:4, borderRadius:"50%", background:"#ffb300" }}/>
                        ))}
                        {items.tasks.slice(0,2).map((_,i) => (
                          <div key={i} style={{ width:4, height:4, borderRadius:"50%", background:"#66bb6a" }}/>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div style={{ display:"flex", gap:16, marginTop:16, justifyContent:"center" }}>
              <div style={{ display:"flex", alignItems:"center", gap:5, fontSize:11, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif" }}>
                <div style={{ width:8, height:8, borderRadius:"50%", background:"#ffb300" }}/> Events
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:5, fontSize:11, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif" }}>
                <div style={{ width:8, height:8, borderRadius:"50%", background:"#66bb6a" }}/> Tasks
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:5, fontSize:11, color:"rgba(255,200,100,0.5)", fontFamily:"'Lato',sans-serif" }}>
                <div style={{ width:16, height:10, borderRadius:3, border:"1.5px solid rgba(255,180,60,0.35)", background:"rgba(255,180,60,0.12)" }}/> Today
              </div>
            </div>
          </div>

          {/* Side panel — selected day details */}
          <div style={{ width:240, borderLeft:"1px solid rgba(255,200,100,0.08)", padding:"20px 18px", overflow:"auto", background:"rgba(0,0,0,0.2)" }}>
            {selectedDay ? (
              <>
                <div style={{ marginBottom:16 }}>
                  <div style={{ fontFamily:"'Playfair Display',serif", fontSize:28, fontWeight:700, color:"#ffe082", lineHeight:1 }}>{selectedDay}</div>
                  <div style={{ fontSize:13, color:"rgba(255,200,100,0.6)", fontFamily:"'Lato',sans-serif", fontWeight:300, marginTop:2 }}>{MONTHS[month]} {year}</div>
                  <div style={{ fontSize:11, color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>{DAYS[new Date(year, month, selectedDay).getDay()]}</div>
                </div>

                {loading ? (
                  <div style={{ fontSize:13, color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif" }}>Loading...</div>
                ) : (
                  <>
                    {/* Events */}
                    {selectedItems?.events.length > 0 && (
                      <div style={{ marginBottom:14 }}>
                        <div style={{ fontSize:10, color:"rgba(255,180,60,0.6)", fontFamily:"'Lato',sans-serif", letterSpacing:"0.1em", marginBottom:8 }}>EVENTS</div>
                        {selectedItems.events.map((e,i) => (
                          <div key={i} style={{ background:"rgba(255,180,60,0.1)", border:"1px solid rgba(255,180,60,0.2)", borderRadius:8, padding:"8px 10px", marginBottom:6, display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:8 }}>
                            <div style={{ flex:1, minWidth:0 }}>
                              <div style={{ fontSize:12, color:"rgba(255,235,180,0.92)", fontFamily:"'Lato',sans-serif", fontWeight:400 }}>{e.title}</div>
                              {e.time && <div style={{ fontSize:11, color:"rgba(255,180,60,0.6)", fontFamily:"'Lato',sans-serif", marginTop:2 }}>🕐 {e.time}</div>}
                            </div>
                            <div style={{ display:"flex", gap:4, flexShrink:0 }}>
                            <button onClick={() => startEditEvent(e)} title="Edit event" style={{ width:24, height:24, borderRadius:6, border:"none", background:"transparent", cursor:"pointer", color:"rgba(255,200,100,0.55)", display:"flex", alignItems:"center", justifyContent:"center", padding:0, transition:"color 0.15s" }} onMouseEnter={ev => ev.target.style.color="rgba(255,200,100,1)"} onMouseLeave={ev => ev.target.style.color="rgba(255,200,100,0.55)"}>
                              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                            </button>
                            <button onClick={() => deleteEvent(e)} title="Delete event" style={{ width:24, height:24, borderRadius:6, border:"none", background:"transparent", cursor:"pointer", color:"rgba(255,120,100,0.55)", display:"flex", alignItems:"center", justifyContent:"center", padding:0, transition:"color 0.15s" }} onMouseEnter={ev => ev.target.style.color="rgba(255,120,100,1)"} onMouseLeave={ev => ev.target.style.color="rgba(255,120,100,0.55)"}>
                              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                            </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Tasks */}
                    {selectedItems?.tasks.length > 0 && (
                      <div style={{ marginBottom:14 }}>
                        <div style={{ fontSize:10, color:"rgba(100,220,120,0.6)", fontFamily:"'Lato',sans-serif", letterSpacing:"0.1em", marginBottom:8 }}>TASKS DUE</div>
                        {selectedItems.tasks.map((t,i) => (
                          <div key={i} style={{ background:"rgba(100,200,120,0.1)", border:"1px solid rgba(100,200,120,0.2)", borderRadius:8, padding:"8px 10px", marginBottom:6 }}>
                            <div style={{ fontSize:12, color:"rgba(200,245,210,0.92)", fontFamily:"'Lato',sans-serif", fontWeight:400 }}>{t.title}</div>
                            <div style={{ fontSize:11, color: t.priority==="high"?"rgba(255,120,100,0.7)":t.priority==="medium"?"rgba(255,180,60,0.6)":"rgba(100,200,120,0.6)", fontFamily:"'Lato',sans-serif", marginTop:2, textTransform:"capitalize" }}>⚑ {t.priority}</div>
                          </div>
                        ))}
                      </div>
                    )}

                    {selectedItems?.events.length === 0 && selectedItems?.tasks.length === 0 && (
                      <div style={{ fontSize:13, color:"rgba(255,200,100,0.3)", fontFamily:"'Lato',sans-serif", fontWeight:300, fontStyle:"italic", marginTop:8 }}>No events or tasks for this day.</div>
                    )}
                  </>
                )}
              </>
            ) : (
              <div style={{ fontSize:13, color:"rgba(255,200,100,0.3)", fontFamily:"'Lato',sans-serif", fontWeight:300, fontStyle:"italic", marginTop:40, textAlign:"center", lineHeight:1.7 }}>
                Click a day to see its events & tasks
              </div>
            )}
          </div>
        </div>
      </div>

      {editingEvent && (
        <div style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.7)", backdropFilter:"blur(8px)", zIndex:300, display:"flex", alignItems:"center", justifyContent:"center", padding:20 }}
             onClick={ev => { if (ev.target === ev.currentTarget) cancelEditEvent(); }}>
          <div style={{ background:"linear-gradient(160deg,rgba(28,18,8,0.97),rgba(40,28,12,0.97))", border:"1px solid rgba(255,200,100,0.3)", borderRadius:14, padding:24, width:"100%", maxWidth:420, display:"flex", flexDirection:"column", gap:12, boxShadow:"0 20px 60px rgba(0,0,0,0.7)" }}>
            <div style={{ fontSize:18, fontFamily:"'Playfair Display',serif", color:"rgba(255,235,180,0.95)", marginBottom:4 }}>Edit Event</div>
            <input value={editTitle} onChange={ev => setEditTitle(ev.target.value)} placeholder="Event title..." style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:14, fontFamily:"Lato,sans-serif", outline:"none" }} />
            <div style={{ display:"flex", gap:8 }}>
              <input type="date" value={editDate} onChange={ev => setEditDate(ev.target.value)} style={{ flex:1, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:13, fontFamily:"Lato,sans-serif", outline:"none", colorScheme:"dark" }} />
              <input type="time" value={editTime} onChange={ev => setEditTime(ev.target.value)} style={{ width:120, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:13, fontFamily:"Lato,sans-serif", outline:"none", colorScheme:"dark" }} />
            </div>
            <div style={{ display:"flex", justifyContent:"flex-end", gap:8, marginTop:6 }}>
              <button onClick={cancelEditEvent} style={{ padding:"9px 18px", borderRadius:9, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", color:"rgba(255,230,170,0.6)", fontSize:13, cursor:"pointer", fontFamily:"Lato,sans-serif" }}>Cancel</button>
              <button onClick={saveEditEvent} disabled={savingEdit||!editTitle.trim()} style={{ padding:"9px 18px", borderRadius:9, border:"none", background:"linear-gradient(135deg,#ffb74d,#f57c00)", color:"white", fontSize:13, cursor:"pointer", fontFamily:"Lato,sans-serif", opacity:savingEdit||!editTitle.trim()?0.5:1 }}>
                {savingEdit?"Saving...":"Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
