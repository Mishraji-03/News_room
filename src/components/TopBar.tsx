import { Lock, Monitor } from 'lucide-react';

export default function TopBar() {
  return (
    <div className="topbar">
      <div className="lock">
        <Lock /> Private admin portal · only owner access
      </div>
      <button className="sys-btn">
        <Monitor /> System overview
      </button>
    </div>
  );
}
