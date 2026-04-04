import { useState, useEffect } from "react";

const API = "http://localhost:8080";

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
);
const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
);
const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
);
const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
);

export default function NotesPage({ sessionId, onClose }) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [search, setSearch] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newTags, setNewTags] = useState("");
  const [saving, setSaving] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);

  const fetchNotes = () => {
    if (!sessionId) { setLoading(false); return; }
    fetch(`${API}/session/${sessionId}/summary`)
      .then(r => r.json())
      .then(d => { setNotes(d.notes || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchNotes(); }, [sessionId]);

  const saveNote = async () => {
    if (!newTitle.trim() && !newContent.trim()) return;
    setSaving(true);
    try {
      await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Save a note titled "${newTitle || "Untitled"}" with content: ${newContent}${newTags ? ". Tags: " + newTags : ""}`,
          session_id: sessionId,
        }),
      });
      setNewTitle(""); setNewContent(""); setNewTags("");
      setShowAdd(false);
      setTimeout(fetchNotes, 800);
    } catch(e) {}
    setSaving(false);
  };

  const filtered = notes.filter(n =>
    !search || n.title?.toLowerCase().includes(search.toLowerCase()) ||
    n.content?.toLowerCase().includes(search.toLowerCase()) ||
    n.tags?.some(t => t.toLowerCase().includes(search.toLowerCase()))
  );

  const tagColors = ["rgba(255,180,60,0.2)", "rgba(100,200,120,0.2)", "rgba(150,180,255,0.2)", "rgba(255,150,180,0.2)"];
  const tagBorders = ["rgba(255,180,60,0.4)", "rgba(100,200,120,0.4)", "rgba(150,180,255,0.4)", "rgba(255,150,180,0.4)"];

  return (
    <div style={{ position:"fixed", inset:0, zIndex:100, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.6)", backdropFilter:"blur(8px)" }}
      onClick={e => { if(e.target===e.currentTarget) onClose(); }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lato:wght@300;400&display=swap');
        .note-card:hover{background:rgba(255,255,255,0.08)!important;border-color:rgba(255,200,100,0.25)!important;transform:translateY(-2px)}
        .note-card{transition:all 0.18s}
        .add-input::placeholder{color:rgba(255,230,170,0.35)}
        .add-input:focus{outline:none;border-color:rgba(255,180,60,0.5)!important}
      `}</style>

      <div style={{ width:"min(860px,96vw)", height:"88vh", background:"rgba(6,12,6,0.94)", backdropFilter:"blur(24px)", border:"1px solid rgba(255,200,100,0.12)", borderRadius:20, overflow:"hidden", boxShadow:"0 24px 80px rgba(0,0,0,0.7)", display:"flex", flexDirection:"column" }}>

        {/* Header */}
        <div style={{ padding:"16px 22px", borderBottom:"1px solid rgba(255,200,100,0.08)", display:"flex", alignItems:"center", gap:12, flexShrink:0 }}>
          <div style={{ width:36, height:36, borderRadius:10, background:"rgba(150,180,255,0.12)", border:"1px solid rgba(150,180,255,0.3)", display:"flex", alignItems:"center", justifyContent:"center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#90caf9" strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <div>
            <div style={{ fontFamily:"'Playfair Display',serif", fontSize:18, fontWeight:700, color:"#ffe082" }}>My Notes</div>
            <div style={{ fontSize:11, color:"rgba(255,200,100,0.45)", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>{notes.length} note{notes.length!==1?"s":""} saved</div>
          </div>
          <div style={{ marginLeft:"auto", display:"flex", gap:8, alignItems:"center" }}>
            <button onClick={()=>setShowAdd(true)} style={{ display:"flex", alignItems:"center", gap:6, background:"rgba(150,180,255,0.15)", border:"1px solid rgba(150,180,255,0.3)", borderRadius:9, padding:"7px 14px", color:"rgba(200,220,255,0.9)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif", fontWeight:300 }}>
              <PlusIcon/> New Note
            </button>
            <button onClick={onClose} style={{ width:34, height:34, borderRadius:9, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", cursor:"pointer", color:"rgba(255,230,170,0.6)", display:"flex", alignItems:"center", justifyContent:"center" }}><CloseIcon/></button>
          </div>
        </div>

        {/* Search */}
        <div style={{ padding:"12px 22px", borderBottom:"1px solid rgba(255,255,255,0.04)", flexShrink:0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"8px 14px" }}>
            <span style={{ color:"rgba(255,200,100,0.4)" }}><SearchIcon/></span>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search notes..." className="add-input" style={{ flex:1, border:"none", background:"transparent", fontSize:13, color:"rgba(255,240,200,0.9)", fontFamily:"'Lato',sans-serif", fontWeight:300, outline:"none" }}/>
            {search && <button onClick={()=>setSearch("")} style={{ border:"none", background:"none", color:"rgba(255,200,100,0.4)", cursor:"pointer", fontSize:16, lineHeight:1 }}>×</button>}
          </div>
        </div>

        <div style={{ flex:1, display:"flex", overflow:"hidden" }}>

          {/* Notes list */}
          <div style={{ width:selectedNote?300:"100%", borderRight: selectedNote?"1px solid rgba(255,255,255,0.06)":"none", overflow:"auto", padding:"14px 16px", display:"flex", flexDirection:"column", gap:8, transition:"width 0.2s" }}>
            {loading ? (
              <div style={{ textAlign:"center", padding:40, color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif", fontSize:13 }}>Loading...</div>
            ) : filtered.length === 0 ? (
              <div style={{ textAlign:"center", padding:40 }}>
                <div style={{ fontSize:40, marginBottom:12 }}>📝</div>
                <div style={{ color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif", fontSize:13, fontWeight:300 }}>{search ? "No notes match your search" : "No notes yet. Add your first note!"}</div>
                {!search && <button onClick={()=>setShowAdd(true)} style={{ marginTop:16, display:"inline-flex", alignItems:"center", gap:6, background:"rgba(150,180,255,0.15)", border:"1px solid rgba(150,180,255,0.3)", borderRadius:9, padding:"8px 16px", color:"rgba(200,220,255,0.9)", fontSize:12, cursor:"pointer", fontFamily:"'Lato',sans-serif" }}><PlusIcon/> Add Note</button>}
              </div>
            ) : filtered.map((note, i) => (
              <div key={note.id||i} className="note-card" onClick={()=>setSelectedNote(selectedNote?.id===note.id?null:note)}
                style={{ background: selectedNote?.id===note.id?"rgba(150,180,255,0.12)":"rgba(255,255,255,0.04)", border:`1px solid ${selectedNote?.id===note.id?"rgba(150,180,255,0.35)":"rgba(255,255,255,0.06)"}`, borderRadius:12, padding:"12px 14px", cursor:"pointer" }}>
                <div style={{ fontFamily:"'Lato',sans-serif", fontSize:13, fontWeight:400, color:"rgba(255,240,200,0.92)", marginBottom:4, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{note.title || "Untitled"}</div>
                <div style={{ fontSize:12, color:"rgba(255,220,150,0.45)", fontFamily:"'Lato',sans-serif", fontWeight:300, display:"-webkit-box", WebkitLineClamp:2, WebkitBoxOrient:"vertical", overflow:"hidden", lineHeight:1.5, marginBottom: note.tags?.length>0?6:0 }}>{note.content}</div>
                {note.tags?.length>0 && (
                  <div style={{ display:"flex", flexWrap:"wrap", gap:4 }}>
                    {note.tags.map((tag,ti)=>(
                      <span key={ti} style={{ fontSize:10, padding:"1px 7px", borderRadius:99, background:tagColors[ti%4], border:`1px solid ${tagBorders[ti%4]}`, color:"rgba(255,230,170,0.7)", fontFamily:"'Lato',sans-serif" }}>{tag}</span>
                    ))}
                  </div>
                )}
                <div style={{ fontSize:10, color:"rgba(255,200,100,0.25)", fontFamily:"'Lato',sans-serif", marginTop:6 }}>
                  {note.created_at ? new Date(note.created_at).toLocaleDateString("en-IN", {day:"numeric",month:"short",year:"numeric"}) : ""}
                </div>
              </div>
            ))}
          </div>

          {/* Note detail */}
          {selectedNote && (
            <div style={{ flex:1, padding:"20px 22px", overflow:"auto" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:16 }}>
                <div>
                  <div style={{ fontFamily:"'Playfair Display',serif", fontSize:20, fontWeight:700, color:"#ffe082", marginBottom:4 }}>{selectedNote.title||"Untitled"}</div>
                  <div style={{ fontSize:11, color:"rgba(255,200,100,0.4)", fontFamily:"'Lato',sans-serif" }}>
                    {selectedNote.created_at ? new Date(selectedNote.created_at).toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"long",year:"numeric"}) : ""}
                  </div>
                </div>
                <button onClick={()=>setSelectedNote(null)} style={{ width:30, height:30, borderRadius:8, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", cursor:"pointer", color:"rgba(255,230,170,0.5)", display:"flex", alignItems:"center", justifyContent:"center" }}><CloseIcon/></button>
              </div>
              {selectedNote.tags?.length>0 && (
                <div style={{ display:"flex", flexWrap:"wrap", gap:5, marginBottom:16 }}>
                  {selectedNote.tags.map((tag,ti)=>(
                    <span key={ti} style={{ fontSize:11, padding:"3px 10px", borderRadius:99, background:tagColors[ti%4], border:`1px solid ${tagBorders[ti%4]}`, color:"rgba(255,230,170,0.8)", fontFamily:"'Lato',sans-serif" }}>{tag}</span>
                  ))}
                </div>
              )}
              <div style={{ fontSize:14, color:"rgba(255,240,200,0.88)", fontFamily:"'Lato',sans-serif", fontWeight:300, lineHeight:1.8, whiteSpace:"pre-wrap", background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.05)", borderRadius:12, padding:"16px 18px" }}>
                {selectedNote.content || <span style={{opacity:0.4,fontStyle:"italic"}}>No content</span>}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Note modal */}
      {showAdd && (
        <div style={{ position:"fixed", inset:0, zIndex:200, display:"flex", alignItems:"center", justifyContent:"center", background:"rgba(0,0,0,0.5)" }}
          onClick={e=>{if(e.target===e.currentTarget)setShowAdd(false);}}>
          <div style={{ width:"min(520px,94vw)", background:"rgba(6,12,6,0.97)", backdropFilter:"blur(24px)", border:"1px solid rgba(150,180,255,0.2)", borderRadius:18, padding:"24px", boxShadow:"0 24px 80px rgba(0,0,0,0.8)" }}>
            <div style={{ fontFamily:"'Playfair Display',serif", fontSize:18, fontWeight:700, color:"#ffe082", marginBottom:18 }}>✏️ New Note</div>
            <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
              <input value={newTitle} onChange={e=>setNewTitle(e.target.value)} placeholder="Note title..." className="add-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:14, fontFamily:"'Lato',sans-serif", fontWeight:300 }}/>
              <textarea value={newContent} onChange={e=>setNewContent(e.target.value)} placeholder="Write your note here..." rows={5} className="add-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:14, fontFamily:"'Lato',sans-serif", fontWeight:300, resize:"vertical", outline:"none" }}/>
              <input value={newTags} onChange={e=>setNewTags(e.target.value)} placeholder="Tags (comma separated): work, ideas, important..." className="add-input" style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:10, padding:"10px 14px", color:"rgba(255,240,200,0.9)", fontSize:13, fontFamily:"'Lato',sans-serif", fontWeight:300 }}/>
              <div style={{ display:"flex", gap:8, justifyContent:"flex-end", marginTop:4 }}>
                <button onClick={()=>setShowAdd(false)} style={{ padding:"9px 18px", borderRadius:9, border:"1px solid rgba(255,255,255,0.1)", background:"rgba(255,255,255,0.05)", color:"rgba(255,230,170,0.6)", fontSize:13, cursor:"pointer", fontFamily:"'Lato',sans-serif" }}>Cancel</button>
                <button onClick={saveNote} disabled={saving||(!newTitle.trim()&&!newContent.trim())} style={{ padding:"9px 20px", borderRadius:9, border:"none", background: saving?"rgba(150,180,255,0.2)":"linear-gradient(135deg,#90caf9,#5c8fd6)", color:"white", fontSize:13, cursor:saving?"not-allowed":"pointer", fontFamily:"'Lato',sans-serif", fontWeight:400, display:"flex", alignItems:"center", gap:6 }}>
                  {saving ? "Saving..." : <><PlusIcon/> Save Note</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
