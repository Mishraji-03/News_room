import { Search, TrendingUp, Hash } from 'lucide-react';
import StatCard from '../components/StatCard';

const keywords = [
  { keyword: 'AI News India', rank: 3, change: '+2', volume: '12.1k' },
  { keyword: 'DeepSeek V4', rank: 1, change: 'New', volume: '45k' },
  { keyword: 'ISRO Moon Mission 2026', rank: 5, change: '+1', volume: '8.3k' },
  { keyword: 'GPT-5 Release Date', rank: 2, change: '+4', volume: '33k' },
  { keyword: 'Tesla FSD India', rank: 7, change: '-1', volume: '6.2k' },
  { keyword: 'Tech News Hindi', rank: 4, change: '0', volume: '18k' },
  { keyword: 'Nvidia RTX 5090 Price', rank: 6, change: '+3', volume: '9.8k' },
];

const titleSuggestions = [
  { original: 'Tesla FSD India launch', optimized: 'Tesla FSD India Launch APPROVED? 🚗 Full Details Hindi', score: 87 },
  { original: 'GPT-5 release date', optimized: 'OpenAI GPT-5 Release Date CONFIRMED! 🤖 Kya Hai Naya?', score: 92 },
  { original: 'DeepSeek V4 launch', optimized: 'China ka AI DeepSeek V4 Launch Hua! 🔥 India Pe Asar?', score: 89 },
];

function changeColor(change: string) {
  if (change.startsWith('+')) return 'text-emerald-400';
  if (change === 'New') return 'text-blue-400';
  if (change === '0') return 'text-zinc-500';
  return 'text-red-400';
}

export default function SEOTracker() {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Search size={16} className="text-emerald-400" />
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Search Optimization</span>
        </div>
        <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">SEO Tracker</h1>
        <p className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">Keyword rankings & optimization</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Avg SEO score" value="86" sub="/ 100" trend={2.1} />
        <StatCard label="Ranked keywords" value="24" trend={0} />
        <StatCard label="Top 3 rankings" value="5" trend={1} />
        <StatCard label="Impressions (7d)" value="48200" format="compact" trend={6.3} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Keyword Rankings */}
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6 flex items-center gap-2">
            <Hash size={13} className="text-emerald-400" />
            Keyword Rankings
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Keyword</th>
                  <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Rank</th>
                  <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3 pr-4">Change</th>
                  <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest pb-3">Volume</th>
                </tr>
              </thead>
              <tbody>
                {keywords.map((k) => (
                  <tr key={k.keyword} className="border-b border-zinc-800/40 hover:bg-zinc-800/30 transition-colors">
                    <td className="py-3 pr-4 text-zinc-200 font-medium">{k.keyword}</td>
                    <td className="py-3 pr-4">
                      <span className="text-emerald-400 font-bold">#{k.rank}</span>
                    </td>
                    <td className={`py-3 pr-4 font-bold text-xs ${changeColor(k.change)}`}>
                      {k.change === '0' ? '—' : k.change}
                    </td>
                    <td className="py-3 text-zinc-400 text-xs">{k.volume}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Title Optimization */}
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6">
          <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-6 flex items-center gap-2">
            <TrendingUp size={13} className="text-emerald-400" />
            Title Optimization
          </h3>
          <div className="space-y-5">
            {titleSuggestions.map((t) => (
              <div key={t.original} className="pb-5 border-b border-zinc-800/50 last:border-0 last:pb-0">
                <p className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Original</p>
                <p className="text-xs text-zinc-400 mb-3">{t.original}</p>
                <p className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Optimized</p>
                <p className="text-sm text-zinc-200 font-medium mb-3">{t.optimized}</p>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                      style={{ width: `${t.score}%` }}
                    />
                  </div>
                  <span className="text-emerald-400 font-bold text-sm w-10 text-right">{t.score}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
