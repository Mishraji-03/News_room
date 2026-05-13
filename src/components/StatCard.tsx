interface Props {
  label: string;
  value: string | number;
  sub?: string;
  colorClass?: string;
}

export default function StatCard({ label, value, sub, colorClass = '' }: Props) {
  return (
    <div className={`stat-card ${colorClass}`}>
      <div className="label">{label}</div>
      <div className="value">
        {value}
        {sub && <span> {sub}</span>}
      </div>
    </div>
  );
}
