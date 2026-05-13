import type { ScheduleEntry } from '../data/schedule';

export default function ScheduleItem({ time, title, status, views, retention }: ScheduleEntry) {
  return (
    <div className="schedule-item">
      <span className="schedule-time">{time}</span>
      <span className={`schedule-dot ${status === 'review' ? 'pending' : status}`} />
      <div className="schedule-info">
        <div className="title">{title}</div>
        {(views || retention) && (
          <div className="meta">
            {status === 'live' ? 'Published' : 'Awaiting your approval'}
            {views && ` · ${views}`}
            {retention && ` · ${retention}`}
          </div>
        )}
        {status === 'review' && (
          <div className="meta">Awaiting your approval</div>
        )}
      </div>
      {status === 'live' && <span className="schedule-badge live">Live</span>}
      {status === 'review' && <span className="schedule-badge review">Review</span>}
    </div>
  );
}
