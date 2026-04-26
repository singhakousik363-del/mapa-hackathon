import { useState, useRef, useEffect } from "react";
import CalendarPage from "./Calendar";
import NotesPage from "./Notes";
import TasksPage from "./Tasks";
const API = "https://mapa-api-875352080719.asia-south1.run.app";
const INDIAN_LANGUAGES = [
  { code: "en-IN", label: "English", native: "English" },
  { code: "hi-IN", label: "Hindi", native: "\u0939\u093f\u0928\u094d\u0926\u0940" },
  { code: "ta-IN", label: "Tamil", native: "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" },
  { code: "te-IN", label: "Telugu", native: "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41" },
  { code: "bn-IN", label: "Bengali", native: "\u09ac\u09be\u0982\u09b2\u09be" },
  { code: "mr-IN", label: "Marathi", native: "\u092e\u0930\u093e\u0920\u0940" },
  { code: "kn-IN", label: "Kannada", native: "\u0c95\u0ca8\u0ccd\u0ca8\u0ca1" },
  { code: "ml-IN", label: "Malayalam", native: "\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02" },
];
const BG_IMAGES = [
  "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1920&q=90",
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=90",
  "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1920&q=90",
];
const AGENT_STYLES = {
  calendar: { bg: "rgba(255,200,80,0.12)", color: "#fff8e1", label: "Calendar", border: "rgba(255,200,80,0.3)" },
  task_manager: { bg: "rgba(100,220,140,0.12)", color: "#f1f8e9", label: "Tasks", border: "rgba(100,220,100,0.3)" },
  notes: { bg: "rgba(150,200,255,0.12)", color: "#e3f2fd", label: "Notes", border: "rgba(100,180,255,0.3)" },
};
const SUGGESTIONS = [];
const MapaLogo = ({ size = 44 }) => (
  <svg width={size} height={size} viewBox="0 0 44 44" fill="none">
    <defs><radialGradient id="lg" cx="40%" cy="35%" r="65%"><stop offset="0%" stopColor="#fff9c4"/><stop offset="55%" stopColor="#ffb300"/><stop offset="100%" stopColor="#e65100"/></radialGradient></defs>
    <circle cx="22" cy="22" r="21" fill="none" stroke="url(#lg)" strokeWidth="1.2" opacity="0.6"/>
    <path d="M4 32 L13 17 L19 24 L25 12 L40 32 Z" fill="url(#lg)" opacity="0.92"/>
    <circle cx="30" cy="13" r="5" fill="#fff9c4"/>
    <line x1="30" y1="5" x2="30" y2="3.5" stroke="#fff9c4" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="36.2" y1="7" x2="37.4" y2="5.8" stroke="#fff9c4" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="38" y1="13" x2="39.5" y2="13" stroke="#fff9c4" strokeWidth="1.5" strokeLinecap="round"/>
    <line x1="4" y1="32" x2="40" y2="32" stroke="url(#lg)" strokeWidth="0.8" opacity="0.4"/>
  </svg>
);
const CalendarIcon = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>;
const TaskIcon = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>;
const NoteIcon = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg>;
const SendIcon = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>;
const MicIcon = ({ active }) => <svg width="17" height="17" viewBox="0 0 24 24" fill={active?"rgba(255,80,80,0.9)":"none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>;
const GlobeIcon = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>;
const AGENT_ICONS = { calendar: <CalendarIcon/>, task_manager: <TaskIcon/>, notes: <NoteIcon/> };
const activeStyle = { background:"linear-gradient(135deg,rgba(255,140,0,0.7),rgba(255,80,0,0.5))", border:"1px solid rgba(255,180,0,0.9)", color:"#ffe082", boxShadow:"0 0 18px rgba(255,140,0,0.6)", fontSize:12, padding:"6px 13px", borderRadius:8, fontFamily:"Lato,sans-serif", fontWeight:400, backdropFilter:"blur(4px)", display:"flex", alignItems:"center", gap:6, cursor:"pointer", transition:"all 0.2s" };
const inactiveStyle = { background:"rgba(0,0,0,0.4)", border:"1px solid rgba(255,200,100,0.25)", color:"rgba(255,225,150,0.75)", boxShadow:"none", fontSize:12, padding:"6px 13px", borderRadius:8, fontFamily:"Lato,sans-serif", fontWeight:300, backdropFilter:"blur(4px)", display:"flex", alignItems:"center", gap:6, cursor:"pointer", transition:"all 0.2s" };
export default function App() {
  const [messages, setMessages] = useState([{ role:"assistant", content:"Good morning! I am MAPA. Speak or type in any Indian language. Click Calendar, Tasks or Notes to manage your day!" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [bgIndex, setBgIndex] = useState(0);
  const [selectedLang, setSelectedLang] = useState(INDIAN_LANGUAGES[0]);
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showTasks, setShowTasks] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:"smooth" }); }, [messages]);
  const startVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Use Chrome for voice input."); return; }
    if (isListening) { recognitionRef.current?.stop(); setIsListening(false); return; }
    const r = new SR();
    r.lang = selectedLang.code; r.continuous = false; r.interimResults = false;
    r.onstart = () => setIsListening(true);
    r.onresult = (e) => { setInput(e.results[0][0].transcript); setIsListening(false); };
    r.onerror = () => setIsListening(false);
    r.onend = () => setIsListening(false);
    recognitionRef.current = r; r.start();
  };
  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput(""); setShowSuggestions(false);
    setMessages(prev => [...prev, { role:"user", content:msg }]);
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({ message:msg, session_id:sessionId }) });
      const data = await res.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, { role:"assistant", content:data.response, agents:data.agents_called }]);
    } catch { setMessages(prev => [...prev, { role:"assistant", content:"Could not reach the server." }]); }
    setLoading(false); inputRef.current?.focus();
  };
  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100vh", position:"relative", overflow:"hidden" }} onClick={() => setShowLangMenu(false)}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400&display=swap');*{box-sizing:border-box;margin:0;padding:0}::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:rgba(255,180,60,0.4);border-radius:99px}@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes pulse{0%,100%{opacity:0.3;transform:scale(0.7)}50%{opacity:1;transform:scale(1)}}@keyframes voiceRing{0%{box-shadow:0 0 0 0 rgba(255,80,80,0.7)}100%{box-shadow:0 0 0 12px rgba(255,80,80,0)}}@keyframes typewriter{0%{width:0;opacity:1}70%{width:100%;opacity:1}85%{width:100%}95%{width:100%;opacity:0}100%{width:0;opacity:0}}@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}.msg-anim{animation:fadeUp 0.3s ease forwards}.sug-btn:hover{background:linear-gradient(135deg,rgba(255,140,0,0.5),rgba(255,80,0,0.35))!important;color:#ffe082!important;transform:translateY(-2px)}.sug-btn:active{transform:scale(0.97)}.lang-opt:hover{background:rgba(255,255,255,0.1)!important}.type-placeholder{position:absolute;left:0;top:50%;transform:translateY(-50%);pointer-events:none;overflow:hidden;white-space:nowrap;font-size:14px;font-family:Lato,sans-serif;font-weight:300;color:rgba(255,228,165,0.45);display:flex;align-items:center;gap:2px}.type-text{overflow:hidden;white-space:nowrap;animation:typewriter 3.5s ease-in-out infinite}.type-cursor{animation:blink 0.8s ease-in-out infinite;color:rgba(255,180,60,0.8)}input{caret-color:#ffb300}`}</style>
      {BG_IMAGES.map((url,i) => <div key={i} style={{ position:"absolute", inset:0, zIndex:0, backgroundImage:`url('${url}')`, backgroundSize:"cover", backgroundPosition:"center 40%", opacity:i===bgIndex?1:0, transition:"opacity 1.5s ease", filter:"brightness(0.95) contrast(1.05)" }}/>)}
      <div style={{ position:"absolute", inset:0, zIndex:1, background:"linear-gradient(to bottom,rgba(0,0,0,0.35) 0%,rgba(0,0,0,0.03) 28%,rgba(0,0,0,0.5) 100%)" }}/>
      <div style={{ position:"absolute", top:"50%", right:14, transform:"translateY(-50%)", zIndex:20, display:"flex", flexDirection:"column", gap:8 }}>
        {BG_IMAGES.map((_,i) => <button key={i} onClick={e=>{e.stopPropagation();setBgIndex(i);}} style={{ width:i===bgIndex?10:7, height:i===bgIndex?10:7, borderRadius:"50%", border:"1.5px solid rgba(255,255,255,0.7)", background:i===bgIndex?"white":"transparent", cursor:"pointer", padding:0, transition:"all 0.3s" }}/>)}
      </div>
      <div style={{ padding:"11px 22px", background:"rgba(0,0,0,0.35)", backdropFilter:"blur(6px)", borderBottom:"1px solid rgba(255,200,100,0.1)", display:"flex", alignItems:"center", gap:12, position:"relative", zIndex:10 }}>
        <div style={{ filter:"drop-shadow(0 0 10px rgba(255,160,0,0.65))", flexShrink:0 }}><MapaLogo size={42}/></div>
        <div>
          <div style={{ fontFamily:"Playfair Display,serif", fontSize:24, fontWeight:700, color:"#ffe082", letterSpacing:"0.07em", textShadow:"0 0 18px rgba(255,140,0,0.7),0 2px 6px rgba(0,0,0,0.9)", lineHeight:1 }}>MAPA</div>
          <div style={{ color:"rgba(255,215,120,0.6)", fontSize:9, fontFamily:"Lato,sans-serif", fontWeight:300, letterSpacing:"0.16em", marginTop:2 }}>MULTI-AGENT PRODUCTIVITY ASSISTANT</div>
        </div>
        <div style={{ marginLeft:"auto", display:"flex", gap:6, alignItems:"center" }}>
          <button style={showCalendar?activeStyle:inactiveStyle} onClick={e=>{e.stopPropagation();setShowCalendar(true);setShowTasks(false);setShowNotes(false);}}><CalendarIcon/> Calendar</button>
          <button style={showTasks?activeStyle:inactiveStyle} onClick={e=>{e.stopPropagation();setShowTasks(true);setShowCalendar(false);setShowNotes(false);}}><TaskIcon/> Tasks</button>
          <button style={showNotes?activeStyle:inactiveStyle} onClick={e=>{e.stopPropagation();setShowNotes(true);setShowCalendar(false);setShowTasks(false);}}><NoteIcon/> Notes</button>
          <div style={{ position:"relative" }} onClick={e=>e.stopPropagation()}>
            <button onClick={()=>setShowLangMenu(!showLangMenu)} style={{ background:"rgba(0,0,0,0.4)", border:"1px solid rgba(255,200,100,0.25)", borderRadius:8, padding:"6px 10px", color:"rgba(255,230,170,0.9)", fontSize:11, cursor:"pointer", fontFamily:"Lato,sans-serif", display:"flex", alignItems:"center", gap:5, backdropFilter:"blur(4px)" }}>
              <GlobeIcon/> {selectedLang.native} <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </button>
            {showLangMenu && (
              <div style={{ position:"absolute", top:"110%", right:0, background:"rgba(8,8,8,0.95)", backdropFilter:"blur(20px)", border:"1px solid rgba(255,200,100,0.15)", borderRadius:12, overflow:"hidden", zIndex:200, width:195, boxShadow:"0 12px 40px rgba(0,0,0,0.7)", maxHeight:340, overflowY:"auto" }}>
                <div style={{ padding:"8px 14px 6px", fontSize:10, color:"rgba(255,200,100,0.5)", fontFamily:"Lato,sans-serif", letterSpacing:"0.1em", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>SELECT LANGUAGE</div>
                {INDIAN_LANGUAGES.map(lang => (
                  <button key={lang.code} className="lang-opt" onClick={()=>{setSelectedLang(lang);setShowLangMenu(false);}} style={{ width:"100%", padding:"9px 14px", background:lang.code===selectedLang.code?"rgba(255,180,60,0.18)":"transparent", border:"none", borderBottom:"1px solid rgba(255,255,255,0.04)", color:"rgba(255,235,185,0.92)", fontSize:13, cursor:"pointer", fontFamily:"Lato,sans-serif", textAlign:"left", display:"flex", justifyContent:"space-between" }}>
                    <span>{lang.native}</span><span style={{ fontSize:10, opacity:0.45 }}>{lang.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      <div style={{ flex:1, overflowY:"auto", padding:"18px 24px", display:"flex", flexDirection:"column", gap:14, position:"relative", zIndex:5 }}>
        {messages.map((msg,i) => (
          <div key={i} className="msg-anim" style={{ display:"flex", justifyContent:msg.role==="user"?"flex-end":"flex-start", gap:10, alignItems:"flex-start" }}>
            {msg.role==="assistant" && <div style={{ width:34, height:34, borderRadius:9, background:"rgba(0,0,0,0.38)", border:"1px solid rgba(255,180,60,0.25)", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}><MapaLogo size={28}/></div>}
            <div style={{ maxWidth:"66%", display:"flex", flexDirection:"column", gap:5, alignItems:msg.role==="user"?"flex-end":"flex-start" }}>
              {msg.agents?.length>0 && <div style={{ display:"flex", gap:4, flexWrap:"wrap" }}>{msg.agents.map(a=>{const s=AGENT_STYLES[a]||{bg:"rgba(0,0,0,0.3)",color:"#fff",label:a,border:"rgba(255,255,255,0.2)"};return <span key={a} style={{ background:s.bg, color:s.color, border:`1px solid ${s.border}`, fontSize:11, padding:"2px 9px", borderRadius:6, fontFamily:"Lato,sans-serif", display:"flex", alignItems:"center", gap:4 }}>{AGENT_ICONS[a]||"•"} {s.label}</span>;})}</div>}
              <div style={{ background:msg.role==="user"?"rgba(140,60,0,0.72)":"rgba(0,0,0,0.48)", backdropFilter:"blur(8px)", color:"rgba(255,245,210,0.97)", padding:"11px 16px", borderRadius:msg.role==="user"?"17px 17px 3px 17px":"17px 17px 17px 3px", fontSize:14, lineHeight:1.75, border:msg.role==="user"?"1px solid rgba(255,150,50,0.25)":"1px solid rgba(255,255,255,0.08)", fontFamily:"Lato,sans-serif", fontWeight:300 }}>{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && <div className="msg-anim" style={{ display:"flex", gap:10 }}><div style={{ width:34, height:34, borderRadius:9, background:"rgba(0,0,0,0.38)", border:"1px solid rgba(255,180,60,0.25)", display:"flex", alignItems:"center", justifyContent:"center" }}><MapaLogo size={28}/></div><div style={{ background:"rgba(0,0,0,0.48)", backdropFilter:"blur(8px)", padding:"13px 18px", borderRadius:"17px 17px 17px 3px", border:"1px solid rgba(255,255,255,0.08)", display:"flex", gap:5, alignItems:"center" }}>{[0,1,2].map(i=><div key={i} style={{ width:7, height:7, borderRadius:"50%", background:"rgba(255,180,60,0.9)", animation:`pulse 1.4s ease-in-out ${i*0.22}s infinite` }}/>)}</div></div>}
        {showSuggestions && <div style={{ display:"flex", flexWrap:"wrap", gap:7, marginTop:4 }}>{SUGGESTIONS.map(s=><button key={s} className="sug-btn" onClick={()=>send(s)} onMouseDown={e=>e.currentTarget.style.background="linear-gradient(135deg,rgba(255,140,0,0.7),rgba(255,80,0,0.5))"} onMouseUp={e=>e.currentTarget.style.background="rgba(0,0,0,0.36)"} onTouchStart={e=>e.currentTarget.style.background="linear-gradient(135deg,rgba(255,140,0,0.7),rgba(255,80,0,0.5))"} onTouchEnd={e=>e.currentTarget.style.background="rgba(0,0,0,0.36)"} style={{ background:"rgba(0,0,0,0.36)", backdropFilter:"blur(6px)", border:"1px solid rgba(255,200,100,0.2)", borderRadius:99, padding:"7px 15px", fontSize:12.5, color:"rgba(255,228,165,0.9)", cursor:"pointer", fontFamily:"Lato,sans-serif", fontWeight:300, transition:"all 0.2s" }}>{s}</button>)}</div>}
        <div ref={bottomRef}/>
      </div>
      <div style={{ padding:"11px 22px 18px", background:"rgba(0,0,0,0.38)", backdropFilter:"blur(6px)", borderTop:"1px solid rgba(255,200,100,0.08)", position:"relative", zIndex:10 }}>
        <div style={{ fontSize:10.5, color:"rgba(255,200,100,0.4)", fontFamily:"Lato,sans-serif", marginBottom:7, display:"flex", alignItems:"center", gap:5 }}>
          <MicIcon active={false}/><span>Speaking: <span style={{ color:"rgba(255,210,120,0.75)" }}>{selectedLang.native}</span> · Tap mic to speak</span>
        </div>
        <div style={{ display:"flex", gap:7, alignItems:"center", background:"rgba(0,0,0,0.35)", border:"1px solid rgba(255,200,100,0.18)", borderRadius:16, padding:"7px 7px 7px 16px" }}>
          <div style={{ position:"relative", flex:1, display:"flex", alignItems:"center" }}>
            <input ref={inputRef} value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&send()} placeholder="" style={{ width:"100%", border:"none", background:"transparent", fontSize:14, color:"rgba(255,245,210,0.95)", outline:"none", fontFamily:"Lato,sans-serif", fontWeight:300 }}/>
            {!input && <div className="type-placeholder"><span className="type-text">Ask anything in your language...</span><span className="type-cursor">|</span></div>}
          </div>
          <button onClick={startVoice} style={{ width:38, height:38, borderRadius:11, border:`1.5px solid ${isListening?"rgba(255,80,80,0.7)":"rgba(255,255,255,0.15)"}`, background:isListening?"rgba(255,50,50,0.25)":"rgba(255,255,255,0.08)", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", animation:isListening?"voiceRing 1s ease-in-out infinite":"none", color:isListening?"rgba(255,120,120,0.9)":"rgba(255,230,170,0.8)", flexShrink:0 }}><MicIcon active={isListening}/></button>
          <button onClick={()=>send()} disabled={loading||!input.trim()} style={{ width:38, height:38, borderRadius:11, border:"none", background:loading||!input.trim()?"rgba(255,180,60,0.1)":"radial-gradient(circle at 35% 35%,#fff9c4,#ffb300)", cursor:loading||!input.trim()?"not-allowed":"pointer", display:"flex", alignItems:"center", justifyContent:"center", boxShadow:loading||!input.trim()?"none":"0 3px 12px rgba(255,140,0,0.55)", color:loading||!input.trim()?"rgba(255,180,60,0.3)":"#5c2a00", flexShrink:0 }}><SendIcon/></button>
        </div>
        <div style={{ textAlign:"center", fontSize:9, color:"rgba(255,200,100,0.28)", marginTop:7, fontFamily:"Lato,sans-serif", letterSpacing:"0.1em" }}>ENTER TO SEND · VOICE IN ANY INDIAN LANGUAGE · GOOGLE CLOUD GEN AI ACADEMY APAC 2026</div>
      </div>
      {showCalendar && <CalendarPage sessionId={sessionId} onClose={()=>setShowCalendar(false)}/>}
      {showNotes && <NotesPage sessionId={sessionId} onClose={()=>setShowNotes(false)}/>}
      {showTasks && <TasksPage sessionId={sessionId} onClose={()=>setShowTasks(false)}/>}
    </div>
  );
}