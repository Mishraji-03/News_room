import { useState } from 'react';
import { uploadHistory } from '../data/pipeline';

type Filter = 'all' | 'published' | 'pending';

export default function UploadHistory() {
  const [filter, setFilter] = useState<Filter>('all');
  const filtered = filter === 'all' ? uploadHistory : uploadHistory.filter(u => u.status === filter);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Upload History</h1>
          <div className="date">{uploadHistory.length} total uploads</div>
        </div>
      </div>

      <div className="filter-row">
        {(['all','published','pending'] as Filter[]).map(f => (
          <button key={f} className={`filter-chip ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <table className="data-table">
        <thead>
          <tr><th>Title</th><th>Platform</th><th>Date</th><th>Status</th><th>Views</th><th>Retention</th></tr>
        </thead>
        <tbody>
          {filtered.map(u => (
            <tr key={u.id}>
              <td style={{ fontWeight:500 }}>{u.title}</td>
              <td>{u.platform}</td>
              <td style={{ color:'var(--text-300)', fontSize:12 }}>{u.date}</td>
              <td><span className={`status-dot ${u.status}`}>{u.status}</span></td>
              <td style={{ color: u.views !== '—' ? 'var(--green)' : 'var(--text-300)' }}>{u.views}</td>
              <td>{u.retention}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
