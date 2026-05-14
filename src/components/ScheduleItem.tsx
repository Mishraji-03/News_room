import { memo, useMemo } from 'react';

import {
  CheckCircle2,
  Clock3,
  Eye,
  TimerReset,
  AlertTriangle,
  Radio,
} from 'lucide-react';

import type { ScheduleEntry } from '../data/schedule';


// ============================================================
// TYPES
// ============================================================

type ScheduleStatus = 'scheduled' | 'pending' | 'review' | 'live' | 'failed';

interface ScheduleItemProps extends ScheduleEntry {
  className?: string;
  /** Optional click callback – receives the entry's id if available */
  onClick?: (id?: string) => void;
}


// ============================================================
// STATUS CONFIG
// ============================================================

const STATUS_CONFIG: Record<
  ScheduleStatus,
  {
    label: string;
    badgeClass: string;
    dotClass: string;
    icon: React.ReactNode;
  }
> = {
  scheduled: {
    label: 'Scheduled',
    badgeClass: 'bg-zinc-800 text-zinc-300 border border-zinc-700',
    dotClass: 'bg-zinc-500',
    icon: <Clock3 size={14} />,
  },
  pending: {
    label: 'Pending',
    badgeClass: 'bg-zinc-800 text-zinc-300 border border-zinc-700',
    dotClass: 'bg-zinc-500',
    icon: <Clock3 size={14} />,
  },
  review: {
    label: 'Review',
    badgeClass: 'bg-yellow-500/10 text-yellow-300 border border-yellow-500/20',
    dotClass: 'bg-yellow-400',
    icon: <TimerReset size={14} />,
  },
  live: {
    label: 'Live',
    badgeClass: 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20',
    dotClass: 'bg-emerald-400 animate-pulse',
    icon: <Radio size={14} />,
  },
  failed: {
    label: 'Failed',
    badgeClass: 'bg-red-500/10 text-red-300 border border-red-500/20',
    dotClass: 'bg-red-400',
    icon: <AlertTriangle size={14} />,
  },
};


// ============================================================
// HELPERS
// ============================================================

function formatMetaText(status: ScheduleStatus): string {
  switch (status) {
    case 'review': return 'Awaiting approval';
    case 'scheduled':
    case 'pending': return 'Scheduled for publishing';
    case 'live': return 'Published to YouTube';
    case 'failed': return 'Publishing failed';
    default: return '';
  }
}


// ============================================================
// COMPONENT
// ============================================================

const ScheduleItem = memo(function ScheduleItem({
  id,
  time,
  title,
  status = 'scheduled',
  views,
  retention,
  className = '',
  onClick,
}: ScheduleItemProps) {
  const config =
    STATUS_CONFIG[status as ScheduleStatus] ||
    STATUS_CONFIG.scheduled;

  const metaText = useMemo(
    () => formatMetaText(status as ScheduleStatus),
    [status]
  );

  const handleClick = () => {
    onClick?.(id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <div
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : -1}
      className={`
        group
        flex
        items-center
        gap-4
        rounded-2xl
        border
        border-zinc-800
        bg-zinc-950/60
        hover:bg-zinc-900/70
        transition-all
        duration-300
        px-4
        py-3
        backdrop-blur-md

        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      aria-label={onClick ? `${title} – ${config.label}. Click to view details.` : undefined}
    >
      {/* Time */}
      <div className="min-w-[64px] text-sm font-medium text-zinc-300">
        {time}
      </div>

      {/* Status dot */}
      <div className={`w-3 h-3 rounded-full shrink-0 ${config.dotClass}`} />

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Title */}
        <div className="text-sm font-semibold text-zinc-100 truncate">
          {title}
        </div>

        {/* Meta */}
        <div className="mt-1 flex items-center gap-3 text-xs text-zinc-400">
          <span>{metaText}</span>

          {views && (
            <span className="flex items-center gap-1">
              <Eye size={12} />
              {views}
            </span>
          )}

          {retention && (
            <span className="flex items-center gap-1">
              <CheckCircle2 size={12} />
              {retention}
            </span>
          )}
        </div>
      </div>

      {/* Badge */}
      <div
        className={`
          flex
          items-center
          gap-1
          px-3
          py-1
          rounded-full
          text-xs
          font-medium
          shrink-0
          ${config.badgeClass}
        `}
      >
        {config.icon}
        <span>{config.label}</span>
      </div>
    </div>
  );
});

export default ScheduleItem;