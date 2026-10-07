import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Activity, AlertTriangle, LayoutDashboard, Settings, Upload, Eye, Search, Filter, ShieldCheck, Download, Calendar } from 'lucide-react';
import { fetchEvents } from './api';

const Sidebar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? "bg-blue-600/20 text-blue-400 border-r-4 border-blue-500" : "hover:bg-slate-800 text-slate-300 hover:text-white";
  
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 h-screen p-4 flex flex-col gap-6 shadow-2xl z-20">
      <div className="flex items-center gap-3 text-2xl font-black text-slate-100 mt-2 tracking-tight">
        <div className="bg-blue-600 p-2 rounded-lg"><Eye size={24} className="text-white" /></div>
        SentinelVision
      </div>
      <div className="text-xs uppercase tracking-wider font-bold text-slate-500 mb-2">Main Menu</div>
      <nav className="flex flex-col gap-2">
        <Link to="/" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/')}`}><LayoutDashboard size={20} /> Dashboard</Link>
        <Link to="/events" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/events')}`}><AlertTriangle size={20} /> Events & Alerts</Link>
        <Link to="/insights" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/insights')}`}><Activity size={20} /> Insights</Link>
      </nav>
      
      <div className="text-xs uppercase tracking-wider font-bold text-slate-500 mt-6 mb-2">Configuration</div>
      <nav className="flex flex-col gap-2">
        <Link to="/upload" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/upload')}`}><Upload size={20} /> Data Source</Link>
        <Link to="/settings" className={`flex items-center gap-3 p-3 rounded-lg transition-all ${isActive('/settings')}`}><Settings size={20} /> Settings</Link>
      </nav>
      
      <div className="mt-auto p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 flex flex-col gap-2">
         <div className="text-sm font-semibold text-slate-200 flex items-center gap-2"><ShieldCheck size={16} className="text-green-400"/> System Active</div>
         <div className="text-xs text-slate-400">Model: YOLOv8 Pose (Quantized)</div>
         <div className="text-xs text-slate-400">Latency: ~34ms</div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [hasSource, setHasSource] = useState(false);
  const [uploading, setUploading] = useState(false);
  const logsEndRef = useRef(null);

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
      if (res.ok) {
        setHasSource(true);
      } else {
        alert("Upload failed. Is the backend server running?");
      }
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
    } catch (err) {
      console.error(err);
    }
  };

  const getEventStyle = (type) => {
    if (type.includes("NORMAL") || type.includes("RECOVER")) return "bg-green-500/10 border-green-500/30 text-green-400";
    if (type.includes("PANIC") || type.includes("ANOMALY") || type.includes("FALL") || type.includes("DISPATCH")) return "bg-red-500/10 border-red-500/30 text-red-400";
    return "bg-amber-500/10 border-amber-500/30 text-amber-400";
  };

  const getEventIcon = (type) => {
    if (type.includes("NORMAL") || type.includes("RECOVER")) return <Activity size={16} />;
    return <AlertTriangle size={16} />;
  };

  return (
    <div className="flex-1 h-screen flex flex-col bg-slate-950 overflow-hidden">
      <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur flex items-center justify-between px-6 z-10">
        <h1 className="text-xl font-bold text-slate-100">Live Surveillance</h1>
        <div className="flex items-center gap-4">
          <div className="px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-sm flex items-center gap-2 text-slate-300">
            {hasSource ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                Live Feed Active
              </>
            ) : "System Standby"}
          </div>
        </div>
      </header>
      
      <main className="flex-1 flex p-6 gap-6 overflow-hidden">
        <div className="flex-1 flex flex-col gap-6">
          <div className="flex-1 bg-black rounded-2xl border border-slate-800 overflow-hidden shadow-2xl relative flex items-center justify-center">
            
            {!hasSource ? (
              <div className="flex flex-col items-center justify-center w-full h-full bg-slate-900/50 p-8">
                <Upload size={48} className="mb-4 text-blue-500" />
                <h2 className="text-2xl font-semibold text-slate-200 mb-2">Select Video Source</h2>
                <p className="text-slate-400 mb-8 max-w-md text-center">Upload a video file to begin AI behavioral analysis, or connect your local camera feed.</p>
                
                <div className="flex gap-4">
                  <div className="relative overflow-hidden cursor-pointer">
                    <input type="file" accept="video/*" onChange={handleFileUpload} className="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10" />
                    <button className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors pointer-events-none">
                      <Upload size={20} /> {uploading ? "Uploading..." : "Upload Video File"}
                    </button>
                  </div>
                  <button onClick={enableWebcam} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors">
                    <Eye size={20} /> Use Live Camera
                  </button>
                </div>
              </div>
            ) : (
              <>
                <img src="http://localhost:8002/api/video_feed" className="w-full h-full object-contain" alt="Live Surveillance Stream" />
                <button onClick={() => setHasSource(false)} className="absolute top-4 right-4 bg-slate-900/80 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-sm border border-slate-700 transition-colors backdrop-blur z-20">
                  Switch Source
                </button>
              </>
            )}
            
          </div>
          
          <div className="h-32 bg-slate-900 rounded-xl border border-slate-800 p-5 flex flex-col shrink-0">
             <div className="flex justify-between items-end mb-3">
               <h3 className="text-sm font-semibold text-slate-300">Activity Timeline (Last 5 Mins)</h3>
             </div>
             <div className="flex-1 w-full bg-slate-950 rounded-lg relative border border-slate-800/50 overflow-hidden flex items-center">
                <div className="h-full w-1/4 bg-green-500/10"></div>
                <div className="h-full w-[2px] bg-red-500 shadow-[0_0_8px_#ef4444] z-10"></div>
                <div className="h-full w-1/6 bg-amber-500/10"></div>
                <div className="h-full w-1/2 bg-green-500/10"></div>
                {hasSource && <div className="absolute top-0 bottom-0 right-0 w-[2px] bg-blue-500 shadow-[0_0_10px_#3b82f6] animate-pulse"></div>}
             </div>
          </div>
        </div>

        <div className="w-[400px] flex flex-col bg-slate-900 rounded-2xl border border-slate-800 shrink-0 overflow-hidden shadow-xl">
          <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 backdrop-blur">
            <h2 className="font-bold text-lg text-slate-100 flex items-center gap-2">Event Stream</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            {events.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-3">
                <Activity size={32} className="opacity-50" />
                <p>{hasSource ? "Monitoring for anomalies..." : "Waiting for video source..."}</p>
              </div>
            ) : (
              events.map((event, i) => (
                <div key={event.id || i} className="bg-slate-950/50 rounded-xl p-4 border border-slate-800">
                  <div className="flex justify-between items-start mb-2">
                    <div className={`flex items-center gap-1.5 text-xs font-bold px-2 py-1 rounded border uppercase ${getEventStyle(event.type)}`}>
                      {getEventIcon(event.type)} {event.type}
                    </div>
                  </div>
                  <p className="text-slate-300 text-sm">{event.message}</p>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      </main>
    </div>
  );
};

const DataSourcePage = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setUploading(true);
    setUploadStatus(`Uploading ${file.name}...`);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      // Import API_BASE dynamically or hardcode for simplicity here
      const res = await fetch("http://localhost:8002/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setUploadStatus("✅ " + data.message);
    } catch (err) {
      console.error(err);
      setUploadStatus("❌ Upload failed. Make sure backend is running.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 p-8 flex flex-col">
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-800">
         <div className="flex items-center gap-3">
           <Upload size={32} className="text-purple-400"/>
           <h1 className="text-3xl font-bold text-white">Data Sources</h1>
         </div>
      </div>
      
      <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-blue-500 transition-colors rounded-2xl bg-slate-900/40 relative cursor-pointer group">
        <input type="file" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" accept="video/mp4,video/avi" onChange={handleFileUpload} disabled={uploading}/>
        <Upload size={64} className="mb-6 text-slate-500 group-hover:text-blue-400 transition-colors" />
        <h2 className="text-2xl font-semibold text-slate-300 mb-3 group-hover:text-white transition-colors">
          {uploading ? "Uploading Video..." : "Drag & Drop Video File"}
        </h2>
        <p className="text-slate-500 mb-6 text-center max-w-md">
          {uploadStatus || "Support for .MP4, .MOV, and .AVI formats. The SentinelVision AI engine will instantly switch to processing this new feed."}
        </p>
        <button className={`px-6 py-3 rounded-full font-medium ${uploading ? 'bg-slate-700 text-slate-400' : 'bg-blue-600 hover:bg-blue-500 text-white'}`} disabled={uploading}>
          {uploading ? "Processing..." : "Browse Files"}
        </button>
      </div>
    </div>
  );
};

const SimplePage = ({ title, icon }) => (
  <div className="flex-1 p-8 flex flex-col">
    <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-800">
       <div className="flex items-center gap-3">
         {icon}
         <h1 className="text-3xl font-bold text-white">{title}</h1>
       </div>
       <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors">
         <Download size={18} /> Export Report
       </button>
    </div>
    
    <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/20 text-slate-500">
      <LayoutDashboard size={48} className="mb-4 opacity-20" />
      <h2 className="text-xl font-semibold text-slate-400 mb-2">Module Offline</h2>
      <p className="max-w-md text-center">The {title} module is currently being provisioned. Please check back after the next system update.</p>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-slate-950 text-slate-50 font-sans selection:bg-blue-500/30">
        <Sidebar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events" element={<SimplePage title="Events & Alerts" icon={<AlertTriangle size={32} className="text-red-400"/>} />} />
          <Route path="/insights" element={<SimplePage title="Analytics & Insights" icon={<Activity size={32} className="text-blue-400"/>} />} />
          <Route path="/upload" element={<DataSourcePage />} />
          <Route path="/settings" element={<SimplePage title="System Configuration" icon={<Settings size={32} className="text-slate-400"/>} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

