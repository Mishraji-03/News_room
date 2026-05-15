import { useState } from 'react';
import { Users, GitBranch, Wrench, Calendar, ArrowRight, Bot } from 'lucide-react';
import { agents } from '../data/agents';
import { freeTools } from '../data/tools';
import { pipelineFlow } from '../data/pipeline';
import { weeklySchedule } from '../data/schedule';
import {
  Crown, Shield, Users as UsersIcon, Search, ShieldCheck, PenTool,
  Video, TrendingUp, UploadCloud, BarChart2,
} from 'lucide-react';

type Tab = 'team' | 'pipeline' | 'tools' | 'schedule';

const iconMap: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  crown: Crown, shield: Shield, users: UsersIcon, search: Search,
  'shield-check': ShieldCheck, 'pen-tool': PenTool, video: Video,
  'trending-up': TrendingUp, 'upload-cloud': UploadCloud, 'bar-chart-2': BarChart2,
};

const colorMap: Record<string, string> = {
  'var(--green)': '#4ade80',
  'var(--blue)': '#60a5fa',
  'var(--amber)': '#fbbf24',
  'var(--red)': '#f87171',
  'var(--purple)': '#c084fc',
  'var(--orange)': '#fb923c',
};

const tabs: { id: Tab; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: 'team', label: 'AI Team', icon: Users },
  { id: 'pipeline', label: 'Pipeline', icon: GitBranch },
  { id: 'tools', label: 'Free Tools', icon: Wrench },
  { id: 'schedule', label: 'Schedule', icon: Calendar },
];

const times = ['6:00 AM', '12:00 PM', '5:00 PM', '7:00 PM'];

export default function AIAgents() {
  const [tab, setTab] = useState<Tab>('team');

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500" />
            <span className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="w-3 h-3 rounded-full bg-emerald-500" />
          </div>
          <Bot size={16} className="text-emerald-400" />
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Company Blueprint</span>
        </div>
        <h1 className="text-3xl font-extrabold text-zinc-100 tracking-tight">AutoNews AI</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Fully autonomous AI-driven news media · Same brand on YouTube + Instagram · 4 videos/day
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-zinc-900/50 p-1.5 rounded-2xl border border-zinc-800/50 w-fit">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200
              ${tab === id ? 'bg-zinc-800 text-zinc-100 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
      </div>

      {/* Team Tab */}
      {tab === 'team' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map((a) => {
            const Icon = iconMap[a.icon] || Crown;
            const color = colorMap[a.color] || a.color;
            return (
              <div
                key={a.id}
                className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-5 hover:border-zinc-700 hover:bg-zinc-800/40 transition-all duration-200"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}18` }}>
                    <Icon size={18} color={color} />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-zinc-100">{a.title}</h3>
                    <p className="text-[10px] font-medium uppercase tracking-widest" style={{ color }}>{a.role}</p>
                  </div>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed mb-4">{a.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {a.tools.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pipeline Tab */}
      {tab === 'pipeline' && (
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6 space-y-3">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6">End-to-End Pipeline Flow</h3>
          {pipelineFlow.map((stage, i) => (
            <div key={i} className="flex items-center gap-3 flex-wrap">
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest w-24 shrink-0">{stage.label}</span>
              <div className="flex items-center gap-2 flex-wrap">
                {stage.nodes.map((node, j) => (
                  <div key={j} className="flex items-center gap-2">
                    <span className="px-3 py-1.5 rounded-lg text-xs font-medium bg-zinc-800 text-zinc-200 border border-zinc-700/50">
                      {node}
                    </span>
                    {j < stage.nodes.length - 1 && <span className="text-zinc-600 text-xs">+</span>}
                  </div>
                ))}
              </div>
              {i < pipelineFlow.length - 1 && (
                <ArrowRight size={14} className="text-emerald-500 ml-auto shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tools Tab */}
      {tab === 'tools' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {freeTools.map((cat) => (
            <div key={cat.category} className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-5">
              <h3 className="text-xs font-bold text-zinc-300 uppercase tracking-widest mb-4">{cat.category}</h3>
              <div className="space-y-2">
                {cat.tools.map((t) => (
                  <div key={t.name} className="flex items-center justify-between py-2 border-b border-zinc-800/50 last:border-0">
                    <span className="text-sm text-zinc-200 font-medium">{t.name}</span>
                    <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      {t.limit}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Schedule Tab */}
      {tab === 'schedule' && (
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6 overflow-x-auto">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6">Weekly Publishing Schedule</h3>
          <table className="w-full text-xs min-w-[600px]">
            <thead>
              <tr>
                <th className="text-left text-zinc-500 font-bold uppercase tracking-widest pb-3 pr-4 w-24">Time</th>
                {weeklySchedule.map((d) => (
                  <th key={d.day} className="text-center text-zinc-500 font-bold uppercase tracking-widest pb-3 px-2">
                    {d.day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {times.map((time, ti) => (
                <tr key={time} className="border-t border-zinc-800/50">
                  <td className="py-3 pr-4 text-zinc-400 font-medium">{time}</td>
                  {weeklySchedule.map((d) => (
                    <td key={d.day} className="py-3 px-2 text-center">
                      {d.slots[ti] ? (
                        <span className="px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium whitespace-nowrap">
                          {d.slots[ti]}
                        </span>
                      ) : (
                        <span className="text-zinc-700">—</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
