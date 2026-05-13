import StatCard from '../components/StatCard';

const viewsData = [
  { label:'Mon', value:65, color:'var(--green)' },
  { label:'Tue', value:45, color:'var(--green)' },
  { label:'Wed', value:80, color:'var(--green)' },
  { label:'Thu', value:55, color:'var(--green)' },
  { label:'Fri', value:90, color:'var(--green)' },
  { label:'Sat', value:70, color:'var(--green)' },
  { label:'Sun', value:40, color:'var(--green)' },
];

const platformData = [
  { label:'YouTube', value:72, color:'var(--red)' },
  { label:'Instagram', value:48, color:'var(--purple)' },
];

const topVideos = [
  { title:'AI replace karega jobs? Reality check', views:'12.4k', retention:'78%', platform:'YouTube' },
  { title:'BSNL 5G launch date final', views:'8.3k', retention:'74%', platform:'YouTube' },
  { title:'Nvidia RTX 5090 India price revealed', views:'6.1k', retention:'72%', platform:'YouTube' },
  { title:'China ka AI DeepSeek V4 launch hua', views:'4.2k', retention:'68%', platform:'YouTube' },
  { title:'ISRO moon mission 2026 latest update', views:'2.1k', retention:'61%', platform:'YouTube' },
];

export default function Analytics() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <div className="date">Last 7 days performance</div>
        </div>
      </div>

      <div className="stats-row">
        <StatCard label="Total views (7d)" value="33.6k" colorClass="green" />
        <StatCard label="New subscribers" value="+187" colorClass="green" />
        <StatCard label="Avg retention" value="67%" />
        <StatCard label="Videos published" value="24" />
      </div>

      <div className="analytics-grid">
        <div className="chart-card">
          <h3>Daily Views (in thousands)</h3>
          <div className="chart-placeholder">
            <div className="bar-chart">
              {viewsData.map(d => (
                <div key={d.label} className="bar" style={{ height:`${d.value}%`, background:d.color }}>
                  <span className="bar-label">{d.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="chart-card">
          <h3>Platform Split</h3>
          <div className="chart-placeholder">
            <div className="bar-chart">
              {platformData.map(d => (
                <div key={d.label} className="bar" style={{ height:`${d.value}%`, background:d.color, minWidth:80 }}>
                  <span className="bar-label">{d.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="chart-card" style={{ marginTop:16 }}>
        <h3>Top Performing Videos</h3>
        <table className="data-table">
          <thead>
            <tr><th>#</th><th>Title</th><th>Views</th><th>Retention</th><th>Platform</th></tr>
          </thead>
          <tbody>
            {topVideos.map((v, i) => (
              <tr key={i}>
                <td style={{ color:'var(--text-300)' }}>{i + 1}</td>
                <td style={{ fontWeight:500 }}>{v.title}</td>
                <td style={{ color:'var(--green)' }}>{v.views}</td>
                <td>{v.retention}</td>
                <td>{v.platform}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
