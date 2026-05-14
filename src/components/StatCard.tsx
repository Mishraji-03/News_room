import { memo, type ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

// ============================================================
// TYPES
// ============================================================

export interface StatCardProps {
  /** Label text (e.g., "Total Videos") */
  label: string;
  /** Main value (number or string) */
  value: string | number;
  /** Optional subtext (e.g., "last 7 days") */
  sub?: string;
  /** Optional icon component */
  icon?: ReactNode;
  /** Optional trend percentage (e.g., +12.5, -3.2) */
  trend?: number;
  /** Loading state – shows skeleton */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Value formatting – e.g., "compact" for K/M/B, "currency" */
  format?: 'compact' | 'currency' | 'percent' | 'none';
}

// ============================================================
// HELPERS
// ============================================================

function formatValue(value: string | number, format: StatCardProps['format']): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  
  switch (format) {
    case 'compact':
      if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
      if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
      if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
      return num.toString();
    case 'currency':
      return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num);
    case 'percent':
      return `${num.toFixed(1)}%`;
    default:
      return num.toLocaleString();
  }
}

// ============================================================
// COMPONENT
// ============================================================

export const StatCard = memo(function StatCard({
  label,
  value,
  sub,
  icon,
  trend,
  loading = false,
  className = '',
  format = 'none',
}: StatCardProps) {
  // Trend indicator
  const TrendIcon = trend === undefined ? null : trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus;
  const trendColor = trend === undefined ? 'text-zinc-500' : trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-red-400' : 'text-zinc-400';
  const trendValue = trend !== undefined ? `${trend > 0 ? '+' : ''}${trend}%` : null;

  const displayValue = !loading ? formatValue(value, format) : '—';

  return (
    <div
      className={`
        relative overflow-hidden rounded-2xl
        bg-gradient-to-br from-zinc-900 to-zinc-950
        border border-zinc-800
        p-5
        transition-all duration-200
        hover:border-zinc-700 hover:shadow-lg
        ${className}
      `}
    >
      {/* Optional icon */}
      {icon && (
        <div className="absolute top-4 right-4 text-zinc-700 opacity-50">
          {icon}
        </div>
      )}

      {/* Label */}
      <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">
        {label}
      </div>

      {/* Value */}
      <div className="text-3xl font-bold text-zinc-100 tracking-tight">
        {displayValue}
        {loading && (
          <span className="inline-block ml-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        )}
      </div>

      {/* Trend + Subtext */}
      <div className="flex items-center gap-2 mt-2">
        {trendValue && TrendIcon && (
          <div className={`flex items-center gap-0.5 text-xs font-medium ${trendColor}`}>
            <TrendIcon size={12} />
            <span>{trendValue}</span>
          </div>
        )}
        {sub && !loading && (
          <div className="text-xs text-zinc-500">{sub}</div>
        )}
      </div>

      {/* Subtle bottom accent */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500/0 via-emerald-500/20 to-emerald-500/0" />
    </div>
  );
});

export default StatCard;