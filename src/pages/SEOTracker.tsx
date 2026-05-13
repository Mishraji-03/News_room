import StatCard from '../components/StatCard';

const keywords = [
  { keyword:'AI News India', rank:3, change:'+2', volume:'12.1k' },
  { keyword:'DeepSeek V4', rank:1, change:'New', volume:'45k' },
  { keyword:'ISRO Moon Mission 2026', rank:5, change:'+1', volume:'8.3k' },
  { keyword:'GPT-5 Release Date', rank:2, change:'+4', volume:'33k' },
  { keyword:'Tesla FSD India', rank:7, change:'-1', volume:'6.2k' },
  { keyword:'Tech News Hindi', rank:4, change:'0', volume:'18k' },
  { keyword:'Nvidia RTX 5090 Price', rank:6, change:'+3', volume:'9.8k' },
];

const titleSuggestions = [
  { original:'Tesla FSD India launch', optimized:'Tesla FSD India Launch APPROVED? 🚗 Full Details Hindi', score:87 },
  { original:'GPT-5 release date', optimized:'OpenAI GPT-5 Release Date CONFIRMED! 🤖 Kya Hai Naya?', score:92 },
  { original:'DeepSeek V4 launch', optimized:'China ka AI DeepSeek V4 Launch Hua! 🔥 India Pe Asar?', score:89 },
];

export default function SEOTracker() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1>SEO Tracker</h1>
          <div className="date">Keyword rankings & optimization</div>
        </div>
      </div>

      <div className="stats-row">
        <StatCard label="Avg SEO score" value="86" sub="/100" colorClass="green" />
        <StatCard label="Ranked keywords" value="24" />
        <StatCard label="Top 3 rankings" value="5" colorClass="green" />
        <StatCard label="Impressions (7d)" value="48.2k" />
      </div>

      <div className="analytics-grid">
        <div className="chart-card">
          <h3>Keyword Rankings</h3>
          <table className="data-table">
            <thead>
              <tr><th>Keyword</th><th>Rank</th><th>Change</th><th>Volume</th></tr>
            </thead>
            <tbody>
              {keywords.map(k => (
                <tr key={k.keyword}>
                  <td style={{ fontWeight:500 }}>{k.keyword}</td>
                  <td style={{ color:'var(--green)', fontWeight:700 }}>#{k.rank}</td>
                  <td style={{ color: k.change.includes('+') ? 'var(--green)' : k.change === 'New' ? 'var(--blue)' : k.change === '0' ? 'var(--text-300)' : 'var(--red)' }}>
                    {k.change === '0' ? '—' : k.change}
                  </td>
                  <td style={{ color:'var(--text-300)' }}>{k.volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="chart-card">
          <h3>Title Optimization Suggestions</h3>
          {titleSuggestions.map(t => (
            <div key={t.original} style={{ padding:'14px 0', borderBottom:'1px solid var(--surface-border)' }}>
              <div style={{ fontSize:12, color:'var(--text-300)', marginBottom:4 }}>Original: {t.original}</div>
              <div style={{ fontSize:13, fontWeight:500, marginBottom:6 }}>{t.optimized}</div>
              <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                <div style={{ flex:1, height:4, borderRadius:2, background:'var(--bg-300)', overflow:'hidden' }}>
                  <div style={{ width:`${t.score}%`, height:'100%', background:'var(--green)', borderRadius:2 }} />
                </div>
                <span style={{ fontSize:12, color:'var(--green)', fontWeight:600 }}>{t.score}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
