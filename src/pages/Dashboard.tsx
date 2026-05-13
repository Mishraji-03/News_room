import { ExternalLink } from 'lucide-react';
import StatCard from '../components/StatCard';
import PipelineTracker from '../components/PipelineTracker';
import ScheduleItem from '../components/ScheduleItem';
import { todaySchedule } from '../data/schedule';

export default function Dashboard() {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { weekday:'long', day:'numeric', month:'long', year:'numeric' });

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <div className="date">{dateStr}</div>
        </div>
        <button className="btn-build">
          Build this <ExternalLink size={14} />
        </button>
      </div>

      <div className="stats-row">
        <StatCard label="Videos today" value="3" sub="/ 4" />
        <StatCard label="Total views" value="24.3k" colorClass="green" />
        <StatCard label="Subscribers" value="1,240" />
        <StatCard label="Pending approval" value="4" colorClass="amber" />
      </div>

      <PipelineTracker />

      <div className="schedule-section">
        <h3>Today's schedule</h3>
        <div className="schedule-list">
          {todaySchedule.map(s => (
            <ScheduleItem key={s.time} {...s} />
          ))}
        </div>
      </div>
    </>
  );
}
