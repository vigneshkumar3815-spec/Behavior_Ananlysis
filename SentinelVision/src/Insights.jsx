import React from 'react';
import { Activity, ShieldCheck, AlertTriangle, Download, TrendingUp } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from 'recharts';

export const InsightsDashboard = () => {
  // Mock data for the presentation (since we don't have a database backend yet)
  const hourlyData = [
    { time: '08:00', normal: 120, loitering: 5, falls: 0 },
    { time: '09:00', normal: 180, loitering: 12, falls: 1 },
    { time: '10:00', normal: 250, loitering: 8, falls: 0 },
    { time: '11:00', normal: 210, loitering: 15, falls: 0 },
    { time: '12:00', normal: 150, loitering: 25, falls: 0 },
    { time: '13:00', normal: 190, loitering: 18, falls: 2 },
    { time: '14:00', normal: 300, loitering: 10, falls: 0 },
    { time: '15:00', normal: 280, loitering: 5, falls: 1 },
  ];

  const zoneData = [
    { name: 'Loading Bay', incidents: 14 },
    { name: 'Aisle 4', incidents: 8 },
    { name: 'Packing Area', incidents: 32 },
    { name: 'Break Room', incidents: 5 },
  ];

  const exportAuditLog = () => {
    // Generate mock CSV data
    const headers = "Timestamp,Event_Type,Severity,Location,Person_ID,Resolution_Time\n";
    const data = [
      "2026-10-07T09:12:33Z,FALL,CRITICAL,Aisle 4,Person 1,45s",
      "2026-10-07T10:45:11Z,LOITERING,WARNING,Loading Bay,Person 2,120s",
      "2026-10-07T13:05:22Z,FALL,CRITICAL,Packing Area,Person 3,30s",
      "2026-10-07T14:22:19Z,UNRESPONSIVE,CRITICAL,Packing Area,Person 3,Dispatch Called"
    ].join("\n");
    
    const blob = new Blob([headers + data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('href', url);
    a.setAttribute('download', 'SentinelVision_Audit_Log_2026-10-07.csv');
    a.click();
  };

  return (
    <div className="flex-1 p-8 flex flex-col overflow-y-auto custom-scrollbar">
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-800">
         <div className="flex items-center gap-3">
           <Activity size={32} className="text-blue-400"/>
           <h1 className="text-3xl font-bold text-white">Analytics & Insights</h1>
         </div>
         <button onClick={exportAuditLog} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-lg font-medium shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.5)]">
           <Download size={18} /> Export Audit CSV
         </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div className="text-slate-400 font-medium">Safety Score</div>
            <div className="p-2 bg-green-500/10 rounded-lg"><ShieldCheck size={20} className="text-green-500" /></div>
          </div>
          <div className="text-4xl font-black text-white">94.2%</div>
          <div className="text-sm text-green-400 flex items-center gap-1 mt-2 font-medium">
            <TrendingUp size={14} /> +2.4% from last week
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div className="text-slate-400 font-medium">Critical Falls Today</div>
            <div className="p-2 bg-red-500/10 rounded-lg"><AlertTriangle size={20} className="text-red-500" /></div>
          </div>
          <div className="text-4xl font-black text-white">4</div>
          <div className="text-sm text-red-400 flex items-center gap-1 mt-2 font-medium">
            <TrendingUp size={14} /> +1 from yesterday
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div className="text-slate-400 font-medium">Avg Response Time</div>
            <div className="p-2 bg-blue-500/10 rounded-lg"><Activity size={20} className="text-blue-500" /></div>
          </div>
          <div className="text-4xl font-black text-white">42s</div>
          <div className="text-sm text-green-400 flex items-center gap-1 mt-2 font-medium">
            <TrendingUp size={14} className="rotate-180" /> -12s from last week
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <div className="text-slate-400 font-medium">Total Tracked Persons</div>
            <div className="p-2 bg-purple-500/10 rounded-lg"><Activity size={20} className="text-purple-500" /></div>
          </div>
          <div className="text-4xl font-black text-white">1,680</div>
          <div className="text-sm text-slate-500 flex items-center gap-1 mt-2 font-medium">
            Across 4 camera zones
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl h-[400px] flex flex-col">
          <h3 className="text-lg font-bold text-slate-100 mb-6">Activity Volume (Hourly)</h3>
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyData}>
                <defs>
                  <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorLoiter" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="time" stroke="#64748b" tick={{fill: '#64748b'}} />
                <YAxis stroke="#64748b" tick={{fill: '#64748b'}} />
                <Tooltip contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc'}} itemStyle={{color: '#e2e8f0'}} />
                <Legend />
                <Area type="monotone" dataKey="normal" name="Normal Activity" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorNormal)" />
                <Area type="monotone" dataKey="loitering" name="Loitering Alerts" stroke="#eab308" strokeWidth={3} fillOpacity={1} fill="url(#colorLoiter)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl h-[400px] flex flex-col">
          <h3 className="text-lg font-bold text-slate-100 mb-6">Anomalies By Zone</h3>
          <div className="flex-1 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneData} layout="vertical" margin={{ top: 0, right: 0, left: 20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" tick={{fill: '#64748b'}} />
                <YAxis dataKey="name" type="category" stroke="#64748b" tick={{fill: '#cbd5e1', fontSize: 12}} width={90} />
                <Tooltip cursor={{fill: '#1e293b'}} contentStyle={{backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc'}} />
                <Bar dataKey="incidents" name="Total Incidents" fill="#ef4444" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
