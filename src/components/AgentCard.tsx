import { memo, useMemo } from 'react';
import {
  Crown, Shield, Users, Search, ShieldCheck, PenTool,
  Video, TrendingUp, UploadCloud, BarChart2, AlertCircle,
  type LucideIcon
} from 'lucide-react';
import type { Agent } from '../data/agents';

// Strictly typed icon map
const iconMap: Record<string, LucideIcon> = {
  crown: Crown,
  shield: Shield,
  users: Users,
  search: Search,
  'shield-check': ShieldCheck,
  'pen-tool': PenTool,
  video: Video,
  'trending-up': TrendingUp,
  'upload-cloud': UploadCloud,
  'bar-chart-2': BarChart2,
};

// Default accent color (green)
const DEFAULT_COLOR = '#4ade80';

// Helper: Check if a string is a valid CSS color (simplified)
const isValidColor = (color: string): boolean => {
  return /^(#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})|rgb\(|rgba\(|var\(--)/.test(color);
};

export interface AgentCardProps extends Agent {
  /** Optional animation delay (ms) for staggered entrance */
  animationDelay?: number;
  /** Enable/disable hover scaling effect */
  hoverEffect?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Optional click handler */
  onClick?: () => void;
  /** Optional test ID for e2e testing */
  testId?: string;
}

/**
 * AgentCard Component
 * Renders a single AI agent card with icon, role, description, and tools.
 * Memoized to prevent unnecessary re-renders.
 */
const AgentCard = memo(function AgentCard({
  title,
  role,
  description,
  tools = [],
  color = DEFAULT_COLOR,
  icon = 'crown',
  animationDelay = 0,
  hoverEffect = true,
  className = '',
  onClick,
  testId,
}: AgentCardProps) {
  // Resolve icon – fallback to AlertCircle
  const IconComponent = iconMap[icon] || AlertCircle;

  // Normalize color to a valid CSS value
  const accentColor = isValidColor(color) ? color : DEFAULT_COLOR;

  // Memoize inline styles to avoid recreation on every render
  const iconStyle = useMemo(() => ({
    backgroundColor: `${accentColor}15`, // 15% opacity variant
    color: accentColor,
  }), [accentColor]);

  // Generate a unique ID for accessibility labelling
  const titleId = useMemo(() => `agent-title-${title.replace(/\s+/g, '-')}-${Math.random().toString(36).slice(2, 6)}`, [title]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={`agent-card ${hoverEffect ? 'agent-card--hoverable' : ''} ${className}`}
      style={{ animationDelay: `${animationDelay}ms` }}
      role={onClick ? 'button' : 'article'}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-labelledby={titleId}
      data-testid={testId}
    >
      <div className="card-header">
        {/* Icon */}
        <div
          className="card-icon"
          style={iconStyle}
          aria-hidden="true"
        >
          <IconComponent size={20} strokeWidth={2.25} />
        </div>

        {/* Title & Role */}
        <div className="card-info">
          <h3 id={titleId} className="card-title">
            {title}
          </h3>
          <p className="card-role">{role}</p>
        </div>
      </div>

      {/* Description */}
      <p className="card-desc">{description}</p>

      {/* Tools */}
      {tools.length > 0 && (
        <div className="card-tools" aria-label="Tools and technologies used">
          {tools.map((tool, index) => (
            <span key={`${tool}-${index}`} className="tool-tag">
              {tool}
            </span>
          ))}
        </div>
      )}
    </div>
  );
});

export default AgentCard;