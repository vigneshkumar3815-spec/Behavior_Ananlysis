import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, AlertTriangle, LayoutDashboard, Settings, Upload, Eye, ShieldCheck, Download, Zap, Sparkles, Cpu, Target, Camera, Server } from 'lucide-react';
import { fetchEvents } from './api';
import { InsightsDashboard } from './Insights';

const Sidebar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;
  
  const NavItem = ({ to, icon, label }) => {
    const active = isActive(to);
    return (
      <Link to={to} className={`relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group overflow-hidden ${active ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
        {active && <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-white/10 rounded-xl" />}
        <div className={`relative z-10 p-1.5 rounded-lg transition-colors ${active ? 'bg-blue-500/20 text-blue-400' : 'group-hover:bg-white/5'}`}>
          {icon}
        </div>
        <span className="relative z-10 font-medium text-sm tracking-wide">{label}</span>
        {active && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-r-full shadow-[0_0_10px_rgba(59,130,246,0.8)]" />}
      </Link>
    );
  };

  return (
    <div className="w-72 h-screen p-5 flex flex-col gap-6 z-20 border-r border-white/[0.05] bg-black/40 backdrop-blur-2xl">
      <div className="flex items-center gap-3 px-2 py-4">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500 rounded-xl blur-md opacity-50 animate-pulse-slow"></div>
          <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 p-2.5 rounded-xl border border-white/20">
            <Eye size={22} className="text-white" />
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 tracking-tight">Sentinel</span>
          <span className="text-[10px] font-bold text-blue-400 uppercase tracking-[0.2em] -mt-1">Vision AI</span>
        </div>
      </div>

      <div className="flex flex-col gap-1 mt-4">
        <div className="text-[10px] font-bold text-slate-600 uppercase tracking-widest px-4 mb-2">Core Systems</div>
        <NavItem to="/" icon={<LayoutDashboard size={18} />} label="Command Center" />
        <NavItem to="/events" icon={<AlertTriangle size={18} />} label="Incident Logs" />
        <NavItem to="/insights" icon={<Activity size={18} />} label="Neural Analytics" />
      </div>
      
      <div className="flex flex-col gap-1 mt-4">
        <div className="text-[10px] font-bold text-slate-600 uppercase tracking-widest px-4 mb-2">Configuration</div>
        <NavItem to="/settings" icon={<Settings size={18} />} label="System Prefs" />
      </div>
      
      <div className="mt-auto glass-panel p-4 rounded-2xl relative overflow-hidden group">
         <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
         <div className="flex items-center gap-3 mb-3 relative z-10">
           <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
             <ShieldCheck size={16} className="text-emerald-400"/>
           </div>
           <div>
             <div className="text-xs font-bold text-slate-200">System Online</div>
             <div className="text-[10px] text-emerald-400/80 font-mono">ALL SECURE</div>
           </div>
         </div>
         <div className="space-y-1.5 relative z-10">
           <div className="flex justify-between text-[10px] font-mono">
             <span className="text-slate-500">ENGINE</span>
             <span className="text-slate-300">YOLOv8 + GEMINI</span>
           </div>
           <div className="flex justify-between text-[10px] font-mono">
             <span className="text-slate-500">LATENCY</span>
             <span className="text-blue-400">~34ms (OPT)</span>
           </div>
         </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [hasSource, setHasSource] = useState(false);
  const [customRule, setCustomRule] = useState("");
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [ruleLoading, setRuleLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const logsEndRef = useRef(null);

  const applyCustomRule = async () => {
    setRuleLoading(true);
    try {
      await fetch("http://localhost:8002/api/custom_rule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rule: customRule, api_key: geminiApiKey })
      });
    } catch(e) { console.error(e); }
    setRuleLoading(false);
  };

  useEffect(() => {
    const interval = setInterval(async () => {
      const newEvents = await fetchEvents();
      if (newEvents.length > 0) {
        setEvents(prev => [...prev, ...newEvents].slice(-50));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://localhost:8002/api/upload", { method: "POST", body: formData });
      if (res.ok) setHasSource(true);
      else alert("Upload failed. Is the backend server running?");
    } catch (err) {
      console.error(err);
      alert("Error uploading file: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const enableWebcam = async () => {
    try {
      const res = await fetch("http://localhost:8002/api/set_source", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: 0 })
      });
      if (res.ok) setHasSource(true);
    } catch (err) { console.error(err); }
  };

  const getEventStyle = (type) => {
    if (type.includes("NORMAL") || type.includes("RECOVER")) return "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]";
    if (type.includes("CUSTOM_ALERT")) return "bg-purple-500/10 border-purple-500/40 text-purple-300 shadow-[0_0_20px_rgba(168,85,247,0.15)]";
    if (type.includes("PANIC") || type.includes("ANOMALY") || type.includes("FALL") || type.includes("DISPATCH")) return "bg-rose-500/10 border-rose-500/40 text-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.2)]";
    return "bg-amber-500/10 border-amber-500/30 text-amber-400";
  };

  const getEventIcon = (type) => {
    if (type.includes("NORMAL") || type.includes("RECOVER")) return <Activity size={14} />;
    if (type.includes("CUSTOM_ALERT")) return <Sparkles size={14} className="animate-pulse" />;
    return <AlertTriangle size={14} />;
  };

  return (
    <div className="flex-1 h-screen flex flex-col relative z-10 overflow-hidden">
      <header className="h-20 flex items-center justify-between px-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight glow-text">Command Center</h1>
          <p className="text-xs text-slate-400 font-medium mt-1">Live autonomous surveillance active.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="glass-panel px-4 py-2 rounded-full flex items-center gap-3">
            {hasSource ? (
              <>
                <div className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                </div>
                <span className="text-xs font-bold text-slate-200 tracking-wider">LIVE FEED</span>
              </>
            ) : (
              <>
                <div className="h-2.5 w-2.5 rounded-full bg-slate-600"></div>
                <span className="text-xs font-bold text-slate-400 tracking-wider">STANDBY</span>
              </>
            )}
          </div>
        </div>
      </header>
      
      <main className="flex-1 flex p-6 pt-0 gap-6 overflow-hidden">
        <div className="flex-1 flex flex-col gap-6 h-full">
          {/* Main Video Area */}
          <div className="flex-1 glass-panel rounded-3xl overflow-hidden relative flex items-center justify-center scanline-effect group">
            {!hasSource ? (
              <div className="flex flex-col items-center justify-center w-full h-full relative z-20">
                <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-purple-500/5"></div>
                <div className="w-24 h-24 mb-6 relative flex items-center justify-center">
                  <div className="absolute inset-0 border border-white/10 rounded-full animate-spin" style={{ animationDuration: '4s'}}></div>
                  <div className="absolute inset-2 border border-blue-500/30 rounded-full animate-spin" style={{ animationDuration: '3s', animationDirection: 'reverse'}}></div>
                  <Camera size={32} className="text-blue-400/80" />
                </div>
                <h2 className="text-3xl font-light text-white mb-3">Initialize Feed</h2>
                <p className="text-slate-400 text-sm max-w-sm text-center mb-10">Upload footage for AI analysis or connect a live optical sensor.</p>
                
                <div className="flex gap-4">
                  <div className="relative overflow-hidden group/btn">
                    <input type="file" accept="video/*" onChange={handleFileUpload} className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10" />
                    <button className="relative px-6 py-3 rounded-xl font-semibold flex items-center gap-2 overflow-hidden transition-all bg-white/5 border border-white/10 hover:border-blue-500/50 text-white group-hover/btn:shadow-[0_0_20px_rgba(59,130,246,0.3)]">
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-transparent opacity-0 group-hover/btn:opacity-100 transition-opacity"></div>
                      <Upload size={18} className="text-blue-400 relative z-10" /> 
                      <span className="relative z-10">{uploading ? "INITIALIZING..." : "UPLOAD FOOTAGE"}</span>
                    </button>
                  </div>
                  <button onClick={enableWebcam} className="px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)]">
                    <Target size={18} /> LIVE OPTICS
                  </button>
                </div>
              </div>
            ) : (
              <>
                <img src="http://localhost:8002/api/video_feed" className="w-full h-full object-contain relative z-20" alt="Live Feed" />
                <button onClick={() => setHasSource(false)} className="absolute top-6 right-6 glass-panel hover:bg-white/10 text-white px-4 py-2 rounded-lg text-xs font-bold tracking-wider transition-colors z-30 opacity-0 group-hover:opacity-100">
                  DISCONNECT
                </button>
                
                {/* HUD Elements overlay */}
                <div className="absolute top-6 left-6 z-30 flex flex-col gap-2">
                  <div className="px-3 py-1 bg-black/50 backdrop-blur-md rounded border border-rose-500/30 text-[10px] font-mono text-rose-400 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></div> REC
                  </div>
                  <div className="px-3 py-1 bg-black/50 backdrop-blur-md rounded border border-blue-500/30 text-[10px] font-mono text-blue-400">
                    AI VISION: ACTIVE
                  </div>
                </div>
              </>
            )}
          </div>
          
          {/* Timeline */}
          <div className="h-28 glass-panel rounded-3xl p-5 flex flex-col shrink-0 relative overflow-hidden">
             <div className="flex justify-between items-end mb-3 relative z-10">
               <h3 className="text-xs font-bold text-slate-400 tracking-widest uppercase">Neural Activity Timeline</h3>
             </div>
             <div className="flex-1 w-full bg-black/40 rounded-xl relative border border-white/5 overflow-hidden flex items-center z-10">
                <div className="h-full w-1/4 bg-emerald-500/20 relative">
                  <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent,rgba(16,185,129,0.2),transparent)] animate-[shimmer_2s_infinite]"></div>
                </div>
                <div className="h-full w-[2px] bg-rose-500 shadow-[0_0_12px_#f43f5e] z-10 relative"></div>
                <div className="h-full w-1/6 bg-amber-500/20"></div>
                <div className="h-full w-1/2 bg-emerald-500/10"></div>
                {hasSource && <div className="absolute top-0 bottom-0 right-0 w-[2px] bg-blue-500 shadow-[0_0_15px_#3b82f6] animate-pulse"></div>}
             </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-[420px] flex flex-col gap-6 shrink-0 h-full">
          {/* Custom Rule Card */}
          <div className="glass-panel rounded-3xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
            <div className="flex items-center gap-3 mb-5 relative z-10">
              <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-500/30">
                <Sparkles size={18} className="text-purple-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">Gemini Vision AI</h3>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest">Zero-Shot Detection</p>
              </div>
            </div>
            
            <div className="space-y-3 relative z-10">
              <div className="relative">
                <input type="text" placeholder="Rule (e.g., holding a weapon)" className="w-full bg-black/40 border border-white/10 focus:border-purple-500/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition-all shadow-inner" value={customRule} onChange={e => setCustomRule(e.target.value)} />
              </div>
              <div className="relative">
                <input type="password" placeholder="Gemini API Key (if not in env)" className="w-full bg-black/40 border border-white/10 focus:border-purple-500/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition-all shadow-inner" value={geminiApiKey} onChange={e => setGeminiApiKey(e.target.value)} />
              </div>
              <button onClick={applyCustomRule} className="w-full relative overflow-hidden rounded-xl font-bold py-3 text-sm transition-all bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_20px_rgba(147,51,234,0.3)] hover:shadow-[0_0_30px_rgba(147,51,234,0.5)] group/btn mt-2">
                <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent)] -translate-x-full group-hover/btn:translate-x-full transition-transform duration-700"></div>
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {ruleLoading ? <Cpu size={16} className="animate-spin" /> : <Zap size={16} />} 
                  {ruleLoading ? "DEPLOYING RULE..." : "DEPLOY NEURAL RULE"}
                </span>
              </button>
            </div>
          </div>

          {/* Event Stream */}
          <div className="flex-1 glass-panel rounded-3xl flex flex-col overflow-hidden">
            <div className="p-5 border-b border-white/5 flex justify-between items-center bg-black/20">
              <h2 className="font-bold text-sm text-slate-200 tracking-widest uppercase flex items-center gap-2">
                <Activity size={16} className="text-blue-400" /> Live Telemetry
              </h2>
              <span className="px-2.5 py-1 rounded-md bg-blue-500/20 text-blue-400 text-[10px] font-bold tracking-widest border border-blue-500/30">STREAMING</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar bg-black/10">
              {events.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4">
                  <div className="relative">
                    <div className="absolute inset-0 bg-blue-500 rounded-full blur-xl opacity-20 animate-pulse-slow"></div>
                    <Server size={32} className="relative z-10 opacity-40" />
                  </div>
                  <p className="text-xs uppercase tracking-widest font-medium">Awaiting telemetry...</p>
                </div>
              ) : (
                events.map((event, i) => (
                  <div key={event.id || i} className={`rounded-2xl p-4 border backdrop-blur-sm transition-all animate-in fade-in slide-in-from-right-4 duration-500 ${getEventStyle(event.type)}`}>
                    <div className="flex justify-between items-start mb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-black/20 shadow-inner">
                           {getEventIcon(event.type)}
                        </div>
                        <span className="text-[10px] font-black tracking-widest uppercase">{event.type.replace('_', ' ')}</span>
                      </div>
                      <span className="text-[10px] font-mono opacity-60 bg-black/20 px-2 py-0.5 rounded">T+{Math.floor(event.time)}s</span>
                    </div>
                    <p className="text-sm font-medium opacity-90 leading-relaxed">{event.message}</p>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const SimplePage = ({ title, icon }) => (
  <div className="flex-1 p-10 flex flex-col relative z-10">
    <div className="flex items-center justify-between mb-10 pb-8 border-b border-white/5">
       <div className="flex items-center gap-4">
         <div className="p-3 bg-white/5 rounded-2xl border border-white/10 shadow-lg">
           {icon}
         </div>
         <h1 className="text-4xl font-light text-white tracking-tight">{title}</h1>
       </div>
       <button className="flex items-center gap-2 glass-panel hover:bg-white/5 text-white px-5 py-2.5 rounded-xl font-semibold transition-all hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]">
         <Download size={18} /> EXPORT DATA
       </button>
    </div>
    
    <div className="flex-1 flex flex-col items-center justify-center glass-panel rounded-3xl border-dashed border-2 border-white/10 text-slate-500 relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
      <LayoutDashboard size={56} className="mb-6 opacity-20 group-hover:scale-110 transition-transform duration-700" />
      <h2 className="text-2xl font-light text-slate-300 mb-3 tracking-wide">Module Offline</h2>
      <p className="max-w-md text-center text-sm leading-relaxed">The {title} neural interface is currently synchronizing with the central grid. Please verify connection status.</p>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-[#050505] text-slate-50 font-sans selection:bg-blue-500/30 overflow-hidden">
        {/* Background Effects */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen"></div>
          <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] mix-blend-screen"></div>
        </div>
        
        <Sidebar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events" element={<SimplePage title="Incident Logs" icon={<AlertTriangle size={32} className="text-rose-400"/>} />} />
          <Route path="/insights" element={<InsightsDashboard />} />
          <Route path="/settings" element={<SimplePage title="System Configuration" icon={<Settings size={32} className="text-slate-400"/>} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

