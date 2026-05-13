import { Crown, Shield, Users, Search, ShieldCheck, PenTool, Video, TrendingUp, UploadCloud, BarChart2 } from 'lucide-react';
import type { Agent } from '../data/agents';

const iconMap: Record<string, React.ComponentType<{size?:number}>> = {
  'crown': Crown, 'shield': Shield, 'users': Users, 'search': Search,
  'shield-check': ShieldCheck, 'pen-tool': PenTool, 'video': Video,
  'trending-up': TrendingUp, 'upload-cloud': UploadCloud, 'bar-chart-2': BarChart2,
};

export default function AgentCard({ title, role, description, tools, color, icon }: Agent) {
  const Icon = iconMap[icon] || Crown;
  return (
    <div className="agent-card">
      <div className="card-header">
        <div className="card-icon" style={{ background: color.replace(')', ',0.15)').replace('var(','rgba(').includes('rgba') ? `${color}22` : 'rgba(74,222,128,0.12)', color }}>
          <Icon size={18} />
        </div>
        <div>
          <div className="card-title">{title}</div>
          <div className="card-role">{role}</div>
        </div>
      </div>
      <div className="card-desc">{description}</div>
      <div className="card-tools">
        {tools.map(t => <span key={t} className="tool-tag">{t}</span>)}
      </div>
    </div>
  );
}
