import { useEffect, useState, useRef } from 'react';
import { Play, Square, Sparkles } from 'lucide-react';
import StatCard from '../components/StatCard';
import PipelineTracker from '../components/PipelineTracker';
import AgentHealth from '../components/AgentHealth';
import LogTerminal from '../components/LogTerminal';

const API = 'http://localhost:8000';

interface PipelineState {
  is_running: boolean;
  current_task: string;
  run_id: string | null;
  agents: Record<string, { status: string; message: string }>;
}

interface Stats {
  videos_today: number;
  total_videos: number;
  pending_approval: number;
  last_run: string | null;
}

export default function Dashboard() {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  const [pipelineState, setPipelineState] = useState<PipelineState>({
    is_running: false,
    current_task: 'Idle',
    run_id: null,
    agents: {},
  });

  const [stats, setStats] = useState<Stats>({
    videos_today: 0,
    total_videos: 0,
    pending_approval: 0,
    last_run: null,
  });

  const [statsLoading, setStatsLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(true);
  // stable run_id ref — avoids PipelineTracker re-render flicker
  const stableRunId = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchAll = async () => {
      try {
        const [statusRes, statsRes] = await Promise.all([
          fetch(`${API}/api/pipeline/status`),
          fetch(`${API}/api/stats`),
        ]);

        if (!cancelled) {
          const statusData: PipelineState = await statusRes.json();
          const statsData: Stats = await statsRes.json();

          // Only update run_id ref when a new run actually starts
          if (statusData.run_id && statusData.run_id !== stableRunId.current) {
            stableRunId.current = statusData.run_id;
          }

          setPipelineState(statusData);
          setStats(statsData);
          setStatsLoading(false);
          setBackendOnline(true);
        }
      } catch {
        if (!cancelled) {
          setBackendOnline(false);
          setStatsLoading(false);
        }
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const handleRunPipeline = async () => {
    try {
      await fetch(`${API}/api/pipeline/start`, { method: 'POST' });
    } catch {
      alert('Failed to start pipeline. Is the backend running?');
    }
  };

  const handleCancelPipeline = async () => {
    try {
      await fetch(`${API}/api/pipeline/cancel`, { method: 'POST' });
    } catch {
      alert('Failed to cancel pipeline.');
    }
  };

  const lastRunDisplay = stats.last_run
    ? new Date(stats.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '—';

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
          <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">Dashboard</h1>
          <div className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">
            {dateStr}
          </div>
          {!backendOnline && (
            <div className="mt-2 text-xs text-red-400 font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
              Backend offline — connect to localhost:8000
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {pipelineState.is_running && (
            <button
              className="px-5 py-3 rounded-2xl font-bold text-sm bg-zinc-800 hover:bg-red-950/40 text-zinc-400 hover:text-red-400 border border-zinc-700 hover:border-red-900/50 transition-all duration-200 flex items-center gap-2"
              onClick={handleCancelPipeline}
            >
              <Square size={14} fill="currentColor" />
              Cancel
            </button>
          )}

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
            {!pipelineState.is_running && (
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:animate-shimmer-fast" />
            )}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Videos today"
          value={stats.videos_today}
          sub={`/ ${stats.total_videos} total`}
          trend={stats.videos_today > 0 ? 12 : 0}
          loading={statsLoading}
        />
        <StatCard
          label="Total produced"
          value={stats.total_videos}
          loading={statsLoading}
          format="none"
        />
        <StatCard
          label="Last run"
          value={lastRunDisplay}
          sub={stats.last_run ? new Date(stats.last_run).toLocaleDateString() : 'Never'}
          loading={statsLoading}
        />
        <StatCard
          label="Pending approval"
          value={stats.pending_approval}
          sub="Awaiting review"
          trend={0}
          loading={statsLoading}
        />
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Tracker & Health */}
        <div className="xl:col-span-2 space-y-8">
          <PipelineTracker
            currentTask={pipelineState.current_task}
            runId={stableRunId.current}
          />

          <div>
            <h2 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2">
              <span className="w-1.5 h-6 bg-emerald-500 rounded-full" />
              Agent Health Monitoring
            </h2>
            <AgentHealth agents={pipelineState.agents} />
          </div>
        </div>

        {/* Live Logs */}
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
