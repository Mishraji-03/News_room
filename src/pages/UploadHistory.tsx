import { useState } from 'react';
import { UploadCloud, CheckCircle2, Clock, Tv2 } from 'lucide-react';
import { uploadHistory } from '../data/pipeline';

type Filter = 'all' | 'published' | 'pending';

export default function UploadHistory() {
  const [filter, setFilter] = useState<Filter>('all');
  const filtered = filter === 'all' ? uploadHistory : uploadHistory.filter((u) => u.status === filter);

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <UploadCloud size={16} className="text-emerald-400" />
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Publishing Log</span>
          </div>
          <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">Upload History</h1>
          <p className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">
            {uploadHistory.length} total uploads
          </p>
        </div>

        {/* Filter */}
        <div className="flex bg-zinc-900/50 p-1 rounded-xl border border-zinc-800/50">
          {(['all', 'published', 'pending'] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all duration-200
                ${filter === f ? 'bg-zinc-800 text-zinc-100 shadow-lg' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-6 py-4">Title</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-4 py-4">Platform</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-4 py-4">Date</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-4 py-4">Status</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-4 py-4">Views</th>
                <th className="text-left text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-4 py-4">Retention</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id} className="border-b border-zinc-800/40 hover:bg-zinc-800/30 transition-colors">
                  <td className="px-6 py-4 text-zinc-200 font-medium max-w-xs truncate">{u.title}</td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1.5">
                      {u.platform === 'YouTube' ? (
                        <Tv2 size={14} className="text-red-400" />
                      ) : (
                        <Tv2 size={14} className="text-pink-400" />
                      )}
                      <span className="text-zinc-300 text-xs">{u.platform}</span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-zinc-500 text-xs">{u.date}</td>
                  <td className="px-4 py-4">
                    {u.status === 'published' ? (
                      <span className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                        <CheckCircle2 size={12} />
                        Published
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-amber-400 text-xs font-medium">
                        <Clock size={12} />
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-4 text-emerald-400 font-bold text-xs">
                    {u.views !== '—' ? u.views : <span className="text-zinc-600">—</span>}
                  </td>
                  <td className="px-4 py-4">
                    {u.retention !== '—' ? (
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: u.retention }} />
                        </div>
                        <span className="text-zinc-300 text-xs">{u.retention}</span>
                      </div>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
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
