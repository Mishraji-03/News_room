import { useState } from 'react';
import { Users, GitBranch, Wrench, Calendar, ArrowRight } from 'lucide-react';
import AgentCard from '../components/AgentCard';
import { agents } from '../data/agents';
import { freeTools } from '../data/tools';
import { pipelineFlow } from '../data/pipeline';
import { weeklySchedule } from '../data/schedule';

type Tab = 'team' | 'pipeline' | 'tools' | 'schedule';

export default function AIAgents() {
  const [tab, setTab] = useState<Tab>('team');

  return (
    <>
      <div className="blueprint-header">
        <div className="bh-top">
          <div className="bh-icons">
            <span style={{ color:'#f00', fontSize:20, fontWeight:700 }}>▶</span>
            <span style={{ color:'#e1306c', fontSize:20, fontWeight:700 }}>◉</span>
          </div>
          <h1>AutoNews AI — Company Blueprint</h1>
        </div>
        <div className="bh-sub">Fully autonomous AI-driven news media · Same brand on YouTube + Instagram · 4 videos/day</div>
      </div>

      <div className="tabs">
        <button className={`tab-btn ${tab === 'team' ? 'active' : ''}`} onClick={() => setTab('team')}>
          <Users size={14} /> AI Team
        </button>
        <button className={`tab-btn ${tab === 'pipeline' ? 'active' : ''}`} onClick={() => setTab('pipeline')}>
          <GitBranch size={14} /> Pipeline
        </button>
        <button className={`tab-btn ${tab === 'tools' ? 'active' : ''}`} onClick={() => setTab('tools')}>
          <Wrench size={14} /> Free Tools
        </button>
        <button className={`tab-btn ${tab === 'schedule' ? 'active' : ''}`} onClick={() => setTab('schedule')}>
          <Calendar size={14} /> Schedule
        </button>
      </div>

      {tab === 'team' && (
        <div className="agents-grid">
          {agents.map(a => <AgentCard key={a.id} {...a} />)}
        </div>
      )}

      {tab === 'pipeline' && (
        <div className="flow-container">
          {pipelineFlow.map((stage, i) => (
            <div className="flow-row" key={i}>
              <span style={{ minWidth:90, fontSize:12, color:'var(--text-300)', fontWeight:600 }}>{stage.label}</span>
              {stage.nodes.map((node, j) => (
                <span key={j}>
                  <span className="flow-node">{node}</span>
                  {j < stage.nodes.length - 1 && <span className="flow-arrow" style={{ margin:'0 4px' }}>+</span>}
                </span>
              ))}
              {i < pipelineFlow.length - 1 && <span className="flow-arrow"><ArrowRight size={16} /></span>}
            </div>
          ))}
        </div>
      )}

      {tab === 'tools' && (
        <div className="tools-grid">
          {freeTools.map(cat => (
            <div className="tool-category-card" key={cat.category}>
              <h3>{cat.category}</h3>
              <div className="tool-list">
                {cat.tools.map(t => (
                  <div className="tool-item" key={t.name}>
                    <span className="t-name">{t.name}</span>
                    <span className="t-limit">{t.limit}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'schedule' && (
        <div className="schedule-grid">
          <div className="sg-header">Time</div>
          {weeklySchedule.map(d => <div className="sg-header" key={d.day}>{d.day}</div>)}
          {['6:00 AM', '12:00 PM', '5:00 PM', '7:00 PM'].map((time, ti) => (
            <>
              <div className="sg-cell sg-time" key={`t-${ti}`}>{time}</div>
              {weeklySchedule.map(d => (
                <div className={`sg-cell sg-slot ${d.slots[ti] ? 'filled' : ''}`} key={`${d.day}-${ti}`}>
                  {d.slots[ti] || '—'}
                </div>
              ))}
            </>
          ))}
        </div>
      )}
    </>
  );
}
