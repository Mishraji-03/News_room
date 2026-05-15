import { BarChart3, TrendingUp, Users, Video, Eye } from 'lucide-react';
import StatCard from '../components/StatCard';

const viewsData = [
  { label: 'Mon', value: 65 },
  { label: 'Tue', value: 45 },
  { label: 'Wed', value: 80 },
  { label: 'Thu', value: 55 },
  { label: 'Fri', value: 90 },
  { label: 'Sat', value: 70 },
  { label: 'Sun', value: 40 },
];

const platformData = [
  { label: 'YouTube', value: 72, color: '#ef4444' },
  { label: 'Instagram', value: 48, color: '#a855f7' },
];

const topVideos = [
  { title: 'AI replace karega jobs? Reality check', views: '12.4k', retention: '78%', platform: 'YouTube' },
  { title: 'BSNL 5G launch date final', views: '8.3k', retention: '74%', platform: 'YouTube' },
  { title: 'Nvidia RTX 5090 India price revealed', views: '6.1k', retention: '72%', platform: 'YouTube' },
  { title: 'China ka AI DeepSeek V4 launch hua', views: '4.2k', retention: '68%', platform: 'YouTube' },
  { title: 'ISRO moon mission 2026 latest update', views: '2.1k', retention: '61%', platform: 'YouTube' },
];

export default function Analytics() {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 size={16} className="text-emerald-400" />
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Performance</span>
        </div>
        <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">Analytics</h1>
        <p className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">Last 7 days performance</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total views (7d)" value="33600" format="compact" trend={8.2} icon={<Eye size={20} />} />
        <StatCard label="New subscribers" value="+187" trend={3.1} icon={<Users size={20} />} />
        <StatCard label="Avg retention" value="67%" trend={1.4} />
        <StatCard label="Videos published" value="24" trend={0} icon={<Video size={20} />} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Views Bar Chart */}
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6">Daily Views (thousands)</h3>
          <div className="flex items-end gap-3 h-48">
            {viewsData.map((d) => (
              <div key={d.label} className="flex-1 flex flex-col items-center gap-2">
                <span className="text-[10px] text-zinc-400 font-medium">{d.value}k</span>
                <div
                  className="w-full rounded-t-lg bg-emerald-500/80 hover:bg-emerald-400 transition-all duration-300"
                  style={{ height: `${d.value}%` }}
                />
                <span className="text-[10px] text-zinc-500 font-medium">{d.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Split */}
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6">Platform Split</h3>
          <div className="flex items-end gap-8 h-48 justify-center">
            {platformData.map((d) => (
              <div key={d.label} className="flex flex-col items-center gap-2 flex-1">
                <span className="text-[10px] font-medium" style={{ color: d.color }}>{d.value}%</span>
                <div
                  className="w-full rounded-t-lg transition-all duration-300"
                  style={{ height: `${d.value}%`, backgroundColor: d.color, opacity: 0.8 }}
                />
                <span className="text-xs text-zinc-400 font-medium">{d.label}</span>
              </div>
            ))}
          </div>
          {/* Legend */}
          <div className="mt-6 space-y-3">
            {platformData.map((d) => (
              <div key={d.label} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-sm text-zinc-300">{d.label}</span>
                </div>
                <div className="flex-1 mx-4 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${d.value}%`, backgroundColor: d.color }} />
                </div>
                <span className="text-sm font-bold text-zinc-200">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Videos Table */}
      <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
        <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6 flex items-center gap-2">
          <TrendingUp size={14} className="text-emerald-400" />
          Top Performing Videos
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">#</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Title</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Views</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Retention</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3">Platform</th>
              </tr>
            </thead>
            <tbody>
              {topVideos.map((v, i) => (
                <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                  <td className="py-3 pr-4 text-zinc-500 font-mono">{String(i + 1).padStart(2, '0')}</td>
                  <td className="py-3 pr-4 text-zinc-200 font-medium max-w-xs truncate">{v.title}</td>
                  <td className="py-3 pr-4 text-emerald-400 font-bold">{v.views}</td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: v.retention }} />
                      </div>
                      <span className="text-zinc-300 text-xs">{v.retention}</span>
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
                      {v.platform}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
