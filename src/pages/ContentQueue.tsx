import { useEffect, useState } from 'react';
import { Check, X, Clock, Video, FileText, Tag, ChevronRight } from 'lucide-react';

type Filter = 'all' | 'pending' | 'approved';

export default function ContentQueue() {
  const [filter, setFilter] = useState<Filter>('all');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch real queue from FastAPI Team Leader
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/content/queue');
        const data = await res.json();
        setItems(data);
      } catch (err) {
        console.error("Failed to load queue", err);
      } finally {
        setLoading(false);
      }
    };
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  const filtered = filter === 'all' ? items : items.filter(i => (i.status === 'pending_approval' ? 'pending' : 'approved') === filter);

  const handleApprove = (id: string) => {
    setItems(prev => prev.map(i => i.id === id ? { ...i, status: 'approved_uploaded' as const } : i));
  };
  
  const handleReject = (id: string) => {
    setItems(prev => prev.filter(i => i.id !== id));
  };

  const getFilename = (path: string) => {
    if (!path) return '';
    const parts = path.split(/[/\\]/);
    return parts[parts.length - 1];
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Video size={16} className="text-blue-400" />
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">
              Production Pipeline
            </span>
          </div>
          <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">
            Content Queue
          </h1>
          <div className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">
            {items.filter(i => i.status === 'pending_approval').length} items awaiting review
          </div>
        </div>

        {/* Filters */}
        <div className="flex bg-zinc-900/50 p-1 rounded-xl border border-zinc-800/50">
          {(['all', 'pending', 'approved'] as Filter[]).map(f => (
            <button 
              key={f} 
              className={`
                px-4 py-1.5 rounded-lg text-xs font-bold transition-all duration-200
                ${filter === f 
                  ? 'bg-zinc-800 text-zinc-100 shadow-lg' 
                  : 'text-zinc-500 hover:text-zinc-300'
                }
              `} 
              onClick={() => setFilter(f)}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <div className="w-12 h-12 border-4 border-zinc-800 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-zinc-500 font-medium animate-pulse">Syncing with Team Leader...</p>
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="bg-zinc-900/30 border border-zinc-800/50 border-dashed rounded-3xl py-20 text-center">
          <p className="text-zinc-500 font-medium">No items in the queue. Start the pipeline from the dashboard!</p>
        </div>
      )}

      <div className="grid gap-6">
        {filtered.map(item => (
          <div 
            key={item.id} 
            className="group relative bg-zinc-900/40 border border-zinc-800/60 rounded-3xl overflow-hidden transition-all duration-300 hover:bg-zinc-800/40 hover:border-zinc-700 hover:shadow-2xl"
          >
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-0">
              {/* Content Info (Left) */}
              <div className="xl:col-span-2 p-8 space-y-6">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold text-zinc-100 group-hover:text-emerald-400 transition-colors">
                      {item.script?.title_youtube || item.news?.title}
                    </h2>
                    <div className="flex items-center gap-3 text-xs text-zinc-500">
                      <span className="flex items-center gap-1"><Clock size={12} /> {new Date(item.created_at).toLocaleDateString()}</span>
                      <span className="w-1 h-1 rounded-full bg-zinc-700" />
                      <span className="font-mono text-zinc-400">{item.news?.source}</span>
                    </div>
                  </div>
                  <span 
                    className={`
                      px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border
                      ${item.status === 'pending_approval' 
                        ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' 
                        : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                      }
                    `}
                  >
                    {item.status === 'pending_approval' ? 'Needs Review' : 'Approved'}
                  </span>
                </div>

                {/* Script Preview */}
                <div className="relative">
                  <div className="absolute -left-4 top-0 bottom-0 w-1 bg-emerald-500/20 rounded-full" />
                  <div className="bg-zinc-950/50 rounded-2xl p-5 border border-zinc-800/30">
                    <div className="flex items-center gap-2 mb-3 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                      <FileText size={12} />
                      Generated Script
                    </div>
                    <p className="text-sm text-zinc-300 leading-relaxed max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-800">
                      {item.script?.script || "No script generated."}
                    </p>
                  </div>
                </div>

                {/* Footer / Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pt-4">
                  <div className="flex flex-wrap gap-2">
                    {item.script?.tags?.map((k: string) => (
                      <span key={k} className="flex items-center gap-1 px-2 py-1 bg-zinc-800/50 rounded-lg text-[10px] text-zinc-400 font-medium border border-zinc-700/30">
                        <Tag size={10} /> {k}
                      </span>
                    ))}
                  </div>

                  {item.status === 'pending_approval' && (
                    <div className="flex items-center gap-3">
                      <button 
                        className="flex items-center gap-2 px-5 py-2.5 bg-zinc-800 hover:bg-red-500/20 text-zinc-300 hover:text-red-400 rounded-xl text-xs font-bold transition-all border border-zinc-700/50 hover:border-red-500/30"
                        onClick={() => handleReject(item.id)}
                      >
                        <X size={14} /> Reject
                      </button>
                      <button 
                        className="flex items-center gap-2 px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-zinc-950 rounded-xl text-xs font-bold transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 active:scale-95"
                        onClick={() => handleApprove(item.id)}
                      >
                        <Check size={14} strokeWidth={3} /> Approve & Publish
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Video Preview (Right) */}
              <div className="relative bg-zinc-950 border-l border-zinc-800/60 min-h-[300px] flex items-center justify-center group/video">
                {item.video?.video_path ? (
                  <>
                    <video 
                      className="w-full h-full object-cover"
                      src={`http://localhost:8000/media/videos/${getFilename(item.video.video_path)}`}
                    />
                    <div className="absolute inset-0 bg-zinc-950/40 flex items-center justify-center opacity-100 group-hover/video:opacity-0 transition-opacity">
                       <div className="w-16 h-16 rounded-full bg-zinc-100/10 backdrop-blur-md flex items-center justify-center border border-white/20">
                          <Video size={24} className="text-white" />
                       </div>
                    </div>
                    <div className="absolute bottom-4 right-4 flex items-center gap-2 px-3 py-1 bg-zinc-950/80 backdrop-blur-md rounded-full border border-zinc-800 text-[10px] text-zinc-400 font-mono">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      4K RENDER READY
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center gap-3 text-zinc-600">
                    <Video size={48} strokeWidth={1} />
                    <span className="text-xs font-medium uppercase tracking-widest">Video Pending</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
