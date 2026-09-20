import React, { useState, useEffect } from 'react';
import { 
  PlayIcon, 
  CheckCircleIcon, 
  ArrowPathIcon,
  VideoCameraIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const [pipelineStatus, setPipelineStatus] = useState('running'); // running, idle, error
  const [recentVideos, setRecentVideos] = useState([
    { id: 1, title: 'Epic AI Video 1', status: 'uploaded', time: '10m ago', url: '#' },
    { id: 2, title: 'Crazy Facts 2', status: 'rendering', time: '25m ago', url: '#' },
    { id: 3, title: 'History Shorts', status: 'completed', time: '1h ago', url: '#' },
  ]);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 font-sans selection:bg-indigo-500/30">
      {/* Sidebar / Nav */}
      <nav className="fixed inset-y-0 left-0 w-64 border-r border-neutral-800 bg-neutral-900/50 backdrop-blur-xl p-6 flex flex-col">
        <div className="flex items-center gap-3 mb-12">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <VideoCameraIcon className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">VidRush</h1>
        </div>

        <div className="space-y-2 flex-1">
          <NavItem active icon={<ChartBarIcon className="w-5 h-5" />} label="Dashboard" />
          <NavItem icon={<PlayIcon className="w-5 h-5" />} label="Pipelines" />
          <NavItem icon={<VideoCameraIcon className="w-5 h-5" />} label="Library" />
          <NavItem icon={<Cog6ToothIcon className="w-5 h-5" />} label="Settings" />
        </div>
        
        <div className="mt-auto">
          <div className="p-4 rounded-2xl bg-neutral-800/50 border border-neutral-700/50">
            <div className="text-xs text-neutral-400 mb-1">Pipeline Status</div>
            <div className="flex items-center gap-2 text-sm font-medium text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              Active (Running)
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="ml-64 p-10 max-w-7xl">
        <header className="mb-12 flex justify-between items-end">
          <div>
            <h2 className="text-3xl font-light tracking-tight mb-2">Welcome back, Creator.</h2>
            <p className="text-neutral-400">Your AI video machine is running smoothly.</p>
          </div>
          <button className="px-5 py-2.5 rounded-xl bg-white text-black font-medium hover:bg-neutral-200 transition-colors flex items-center gap-2">
            <PlayIcon className="w-4 h-4" />
            Force Run Pipeline
          </button>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <StatCard title="Videos Generated" value="142" trend="+12% this week" />
          <StatCard title="Total Views (Est)" value="8.4M" trend="+4% this week" />
          <StatCard title="Uptime" value="99.9%" trend="Stable" />
        </div>

        {/* Recent Output */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-medium">Recent Outputs</h3>
            <button className="text-sm text-indigo-400 hover:text-indigo-300 transition-colors">View all</button>
          </div>
          
          <div className="bg-neutral-900/40 border border-neutral-800 rounded-3xl overflow-hidden backdrop-blur-sm">
            <div className="divide-y divide-neutral-800/50">
              {recentVideos.map((vid) => (
                <div key={vid.id} className="p-5 flex items-center justify-between hover:bg-neutral-800/30 transition-colors group cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-neutral-800 flex items-center justify-center text-neutral-400 group-hover:text-white transition-colors">
                      <VideoCameraIcon className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="font-medium text-neutral-200 mb-1">{vid.title}</div>
                      <div className="flex items-center gap-2 text-xs text-neutral-500">
                        <ClockIcon className="w-3.5 h-3.5" />
                        {vid.time}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge status={vid.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

const NavItem = ({ icon, label, active }) => (
  <button className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${active ? 'bg-indigo-500/10 text-indigo-400 font-medium' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'}`}>
    {icon}
    {label}
  </button>
);

const StatCard = ({ title, value, trend }) => (
  <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-800 backdrop-blur-sm hover:border-neutral-700 transition-colors">
    <div className="text-neutral-400 text-sm mb-4">{title}</div>
    <div className="text-4xl font-light mb-2">{value}</div>
    <div className="text-xs text-neutral-500">{trend}</div>
  </div>
);

const StatusBadge = ({ status }) => {
  const styles = {
    uploaded: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    rendering: 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse',
    completed: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  };
  
  const icons = {
    uploaded: <CheckCircleIcon className="w-4 h-4 mr-1" />,
    rendering: <ArrowPathIcon className="w-4 h-4 mr-1 animate-spin" />,
    completed: <CheckCircleIcon className="w-4 h-4 mr-1" />,
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${styles[status]}`}>
      {icons[status]}
      <span className="capitalize">{status}</span>
    </span>
  );
};

export default Dashboard;
