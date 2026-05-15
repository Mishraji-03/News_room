import { memo, useMemo } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  RotateCcw,
  Loader2,
  WifiOff,
} from 'lucide-react';

// === Types ===
export type AgentStatus = 'idle' | 'active' | 'done' | 'error' | 'failed' | 'retrying' | 'offline';

export interface AgentState {
  status: AgentStatus;
  message: string;
  progress?: number;      // optional progress 0-100 for active tasks
  lastActive?: string;    // ISO timestamp
}

interface AgentHealthProps {
  agents: Record<string, AgentState>;
  labels?: Record<string, string>;
  order?: string[];
  className?: string;
  showProgress?: boolean;   // show progress bar for active agents
  compact?: boolean;        // compact mode (smaller cards)
  onAgentClick?: (agentKey: string) => void; // click handler
}

// === Status configuration (visuals) ===
const statusConfig: Record<
  AgentStatus,
  {
    icon: React.ComponentType<{ size?: number; className?: string; color?: string }>;
    color: string;
    bg: string;
    label: string;
    pulse?: boolean;
    spin?: boolean;
  }
> = {
  idle: {
    icon: Clock,
    color: '#9ca3af',
    bg: 'rgba(156, 163, 175, 0.1)',
    label: 'Idle',
  },
  active: {
    icon: Activity,
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.15)',
    label: 'Active',
    pulse: true,
  },
  done: {
    icon: CheckCircle2,
    color: '#22c55e',
    bg: 'rgba(34, 197, 94, 0.15)',
    label: 'Done',
  },
  error: {
    icon: AlertCircle,
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.15)',
    label: 'Error',
  },
  failed: {
    icon: AlertCircle,
    color: '#ef4444',
    bg: 'rgba(239, 68, 68, 0.15)',
    label: 'Failed',
  },
  retrying: {
    icon: RotateCcw,
    color: '#f97316',
    bg: 'rgba(249, 115, 22, 0.15)',
    label: 'Retrying',
    spin: true,
  },
  offline: {
    icon: WifiOff,
    color: '#6b7280',
    bg: 'rgba(107, 114, 128, 0.1)',
    label: 'Offline',
  },
};

const defaultLabels: Record<string, string> = {
  scraper: 'Trend Hunter',
  fact_checker: 'Fact Checker',
  script_writer: 'Script Writer',
  video_maker: 'Video Maker',
  uploader: 'Uploader',
  supervisor: 'Team Leader',
};

/**
 * Formats a timestamp to relative time (e.g., "2 min ago")
 */
function formatRelativeTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin} min ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  } catch {
    return '';
  }
}

const AgentHealth = memo(function AgentHealth({
  agents,
  labels = defaultLabels,
  order,
  className = '',
  showProgress = true,
  compact = false,
  onAgentClick,
}: AgentHealthProps) {
  // Determine which agent keys to show — always show all 5 known agents
  const DEFAULT_AGENT_KEYS = ['scraper', 'fact_checker', 'script_writer', 'video_maker', 'uploader'];

  const agentKeys = useMemo(() => {
    if (order && order.length) return order;
    const fromAgents = Object.keys(agents).filter(key => labels[key] || defaultLabels[key]);
    // If backend hasn't responded yet, show all default agents as idle
    return fromAgents.length > 0 ? fromAgents : DEFAULT_AGENT_KEYS;
  }, [order, agents, labels]);

  if (agentKeys.length === 0) {
    return (
      <div className="text-center py-12 text-zinc-500 dark:text-zinc-400">
        <WifiOff size={32} className="mx-auto mb-2 opacity-50" />
        <p>No agents to monitor</p>
      </div>
    );
  }

  // Grid style based on compact mode
  const gridStyle = compact
    ? { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }
    : { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' };

  return (
    <div className={`agent-health-grid ${className}`} style={gridStyle}>
      {agentKeys.map((key) => {
        const agent = agents[key] || { status: 'idle', message: 'Awaiting start...' };
        const { status = 'idle', message = '', progress, lastActive } = agent;
        const config = statusConfig[status] || statusConfig.idle;
        const Icon = config.icon;
        const displayName = labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

        const cardPadding = compact ? '12px' : '16px';
        const titleSize = compact ? '13px' : '14px';
        const messageSize = compact ? '11px' : '12px';

        return (
          <div
            key={key}
            onClick={() => onAgentClick?.(key)}
            className={`
              relative overflow-hidden rounded-2xl
              bg-zinc-900/40 border border-zinc-800/60
              transition-all duration-300
              hover:bg-zinc-800/60 hover:border-zinc-700 hover:shadow-xl
              ${onAgentClick ? 'cursor-pointer' : ''}
              ${compact ? 'p-3' : 'p-5'}
            `}
            role={onAgentClick ? 'button' : 'region'}
            tabIndex={onAgentClick ? 0 : undefined}
            aria-label={`${displayName} - ${config.label}: ${message}`}
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <h4 className={`font-bold text-zinc-100 ${compact ? 'text-sm' : 'text-base'}`}>
                {displayName}
              </h4>
              <div
                className="p-2 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: config.bg }}
                aria-hidden="true"
              >
                <Icon
                  size={compact ? 14 : 18}
                  color={config.color}
                  className={`
                    ${config.pulse ? 'animate-pulse' : ''}
                    ${config.spin ? 'animate-spin' : ''}
                  `}
                />
              </div>
            </div>

            {/* Status badge */}
            <div className="mb-4">
              <span
                className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-widest border"
                style={{
                  backgroundColor: `${config.color}15`,
                  color: config.color,
                  borderColor: `${config.color}30`,
                }}
              >
                {config.label}
              </span>
            </div>

            {/* Message */}
            <p className={`text-zinc-400 line-clamp-2 leading-relaxed ${compact ? 'text-[11px]' : 'text-xs'}`}>
              {message || 'Awaiting status...'}
            </p>

            {/* Last active timestamp (if available and not idle) */}
            {lastActive && status !== 'idle' && !compact && (
              <div className="text-[10px] text-zinc-500 mt-2">
                Last update: {formatRelativeTime(lastActive)}
              </div>
            )}

            {/* Progress Bar (if explicit progress exists) */}
            {showProgress && progress !== undefined && progress > 0 && (
              <div className="mt-4">
                <div className="flex justify-between items-center mb-1 text-[10px] font-medium text-zinc-500 uppercase">
                  <span>Progress</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-500 ease-out rounded-full"
                    style={{
                      width: `${Math.min(100, Math.max(0, progress))}%`,
                      backgroundColor: config.color,
                      boxShadow: `0 0 8px ${config.color}40`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Shimmer Progress for active tasks without percentage */}
            {showProgress && status === 'active' && (progress === undefined || progress === 0) && (
              <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full w-1/3 animate-shimmer rounded-full"
                  style={{
                    backgroundColor: config.color,
                    boxShadow: `0 0 8px ${config.color}40`,
                  }}
                />
              </div>
            )}
          </div>
        );
      })}

      {/* Optional inject keyframes if not already in global CSS */}
      <style>{`
        @keyframes shimmer-move {
          0% { transform: translateX(-150%); }
          100% { transform: translateX(300%); }
        }
        .animate-shimmer {
          animation: shimmer-move 2s infinite ease-in-out;
        }
        .animate-pulse {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
});

export default AgentHealth;