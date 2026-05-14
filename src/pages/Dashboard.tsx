import { useEffect, useState } from 'react';
import { Play, Sparkles } from 'lucide-react';
import StatCard from '../components/StatCard';
import PipelineTracker from '../components/PipelineTracker';
import AgentHealth from '../components/AgentHealth';
import LogTerminal from '../components/LogTerminal';

export default function Dashboard() {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { 
    weekday: 'long', 
    day: 'numeric', 
    month: 'long', 
    year: 'numeric' 
  });

  const [pipelineState, setPipelineState] = useState({
    is_running: false,
    current_task: 'Idle',
    run_id: null,
    agents: {}
  });

  // Fetch status every 2 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/pipeline/status');
        const data = await res.json();
        setPipelineState(data);
      } catch (err) {
        console.error("Could not connect to Team Leader API");
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRunPipeline = async () => {
    try {
      await fetch('http://localhost:8000/api/pipeline/start', { method: 'POST' });
    } catch (err) {
      alert("Failed to start pipeline. Is the backend running?");
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={16} className="text-emerald-400" />
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">
              Overview Control
            </span>
          </div>
          <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">
            Dashboard
          </h1>
          <div className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">
            {dateStr}
          </div>
        </div>

        <button 
          className={`
            relative group overflow-hidden
            px-8 py-3 rounded-2xl font-bold text-sm
            transition-all duration-300
            flex items-center gap-3
            ${pipelineState.is_running 
              ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed shadow-none' 
              : 'bg-emerald-500 text-zinc-950 hover:bg-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_30px_rgba(16,185,129,0.4)] active:scale-95'
            }
          `}
          onClick={handleRunPipeline}
          disabled={pipelineState.is_running}
        >
          <Play size={18} fill="currentColor" className={pipelineState.is_running ? '' : 'animate-pulse'} />
          <span>{pipelineState.is_running ? 'PIPELINE ACTIVE' : 'INITIALIZE PIPELINE'}</span>
          
          {/* Subtle reflection effect */}
          {!pipelineState.is_running && (
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:animate-shimmer-fast" />
          )}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Videos today" value="3" sub="/ 4" trend={12} />
        <StatCard label="Total views" value="24300" trend={5.4} format="compact" />
        <StatCard label="Subscribers" value="1240" trend={0.8} />
        <StatCard label="Pending approval" value="4" sub="Awaiting review" trend={0} />
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Tracker & Health (Left/Center) */}
        <div className="xl:col-span-2 space-y-8">
          <PipelineTracker currentTask={pipelineState.current_task} />
          
          <div>
            <h2 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2">
              <span className="w-1.5 h-6 bg-emerald-500 rounded-full" />
              Agent Health Monitoring
            </h2>
            <AgentHealth agents={pipelineState.agents} />
          </div>
        </div>

        {/* Live Logs (Right) */}
        <div className="xl:col-span-1">
          <h2 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2">
            <span className="w-1.5 h-6 bg-blue-500 rounded-full" />
            System Operations
          </h2>
          <LogTerminal />
        </div>
      </div>
    </div>
  );
}
