import { useState } from 'react';
import { contentQueue } from '../data/pipeline';

type Filter = 'all' | 'pending' | 'approved';

export default function ContentQueue() {
  const [filter, setFilter] = useState<Filter>('all');
  const [items, setItems] = useState(contentQueue);

  const filtered = filter === 'all' ? items : items.filter(i => i.status === filter);

  const handleApprove = (id: string) => {
    setItems(prev => prev.map(i => i.id === id ? { ...i, status: 'approved' as const } : i));
  };
  const handleReject = (id: string) => {
    setItems(prev => prev.filter(i => i.id !== id));
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Content Queue</h1>
          <div className="date">{items.filter(i => i.status === 'pending').length} items awaiting approval</div>
        </div>
      </div>

      <div className="filter-row">
        {(['all','pending','approved'] as Filter[]).map(f => (
          <button key={f} className={`filter-chip ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {filtered.map(item => (
        <div className="queue-card" key={item.id}>
          <div className="q-header">
            <div>
              <div className="q-title">{item.title}</div>
              <div className="q-time">Scheduled: {item.scheduledTime} · Source: {item.source}</div>
            </div>
            <span className={`schedule-badge ${item.status === 'approved' ? 'live' : 'review'}`}>
              {item.status}
            </span>
          </div>
          <div className="q-script">{item.script}</div>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
            <div className="card-tools">
              {item.keywords.map(k => <span key={k} className="tool-tag">{k}</span>)}
            </div>
            {item.status === 'pending' && (
              <div className="q-actions">
                <button className="btn btn-approve" onClick={() => handleApprove(item.id)}>✓ Approve</button>
                <button className="btn btn-reject" onClick={() => handleReject(item.id)}>✕ Reject</button>
              </div>
            )}
          </div>
        </div>
      ))}
    </>
  );
}
