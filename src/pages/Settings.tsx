import { useState } from 'react';
import { Settings as SettingsIcon, Key, Cpu, Calendar, Tag, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface ToggleProps {
  value: boolean;
  onChange: () => void;
}

function Toggle({ value, onChange }: ToggleProps) {
  return (
    <button
      onClick={onChange}
      className={`relative w-11 h-6 rounded-full transition-all duration-300 focus:outline-none
        ${value ? 'bg-emerald-500' : 'bg-zinc-700'}`}
      role="switch"
      aria-checked={value}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-300
          ${value ? 'translate-x-5' : 'translate-x-0'}`}
      />
    </button>
  );
}

interface SettingRowProps {
  label: string;
  children: React.ReactNode;
}

function SettingRow({ label, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-zinc-800/50 last:border-0">
      <span className="text-sm text-zinc-300">{label}</span>
      {children}
    </div>
  );
}

interface CardProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function Card({ title, icon, children }: CardProps) {
  return (
    <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-6">
      <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest mb-4 flex items-center gap-2">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  );
}

type ApiStatus = 'connected' | 'free' | 'disconnected';

function ApiStatusBadge({ status }: { status: ApiStatus }) {
  if (status === 'connected') return (
    <span className="flex items-center gap-1 text-xs font-medium text-emerald-400">
      <CheckCircle2 size={12} /> Connected
    </span>
  );
  if (status === 'free') return (
    <span className="flex items-center gap-1 text-xs font-medium text-amber-400">
      <Clock size={12} /> Free tier
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs font-medium text-zinc-500">
      <AlertCircle size={12} /> Not connected
    </span>
  );
}

export default function Settings() {
  const [autoUpload, setAutoUpload] = useState(false);
  const [humanApproval, setHumanApproval] = useState(true);
  const [dualPlatform, setDualPlatform] = useState(true);
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <SettingsIcon size={16} className="text-emerald-400" />
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">Configuration</span>
        </div>
        <h1 className="text-4xl font-extrabold text-zinc-100 tracking-tight">Settings</h1>
        <p className="text-sm text-zinc-500 font-medium mt-1 uppercase tracking-wider">Configure your AutoNews AI portal</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Keys */}
        <Card title="API Keys" icon={<Key size={14} className="text-emerald-400" />}>
          <SettingRow label="YouTube Data API v3"><ApiStatusBadge status="connected" /></SettingRow>
          <SettingRow label="Meta Graph API"><ApiStatusBadge status="connected" /></SettingRow>
          <SettingRow label="NewsAPI.org"><ApiStatusBadge status="connected" /></SettingRow>
          <SettingRow label="Gemini Flash"><ApiStatusBadge status="free" /></SettingRow>
          <SettingRow label="D-ID"><ApiStatusBadge status="disconnected" /></SettingRow>
        </Card>

        {/* Pipeline */}
        <Card title="Pipeline" icon={<Cpu size={14} className="text-emerald-400" />}>
          <SettingRow label="Auto-upload (skip approval)">
            <Toggle value={autoUpload} onChange={() => setAutoUpload(!autoUpload)} />
          </SettingRow>
          <SettingRow label="Human approval required">
            <Toggle value={humanApproval} onChange={() => setHumanApproval(!humanApproval)} />
          </SettingRow>
          <SettingRow label="Dual platform (YT + IG)">
            <Toggle value={dualPlatform} onChange={() => setDualPlatform(!dualPlatform)} />
          </SettingRow>
          <SettingRow label="Notifications">
            <Toggle value={notifications} onChange={() => setNotifications(!notifications)} />
          </SettingRow>
        </Card>

        {/* Schedule */}
        <Card title="Schedule" icon={<Calendar size={14} className="text-emerald-400" />}>
          {['6:00 AM', '12:00 PM', '5:00 PM', '7:00 PM'].map((slot, i) => (
            <SettingRow key={slot} label={`Slot ${i + 1}`}>
              <span className="text-sm font-medium text-zinc-200">{slot}</span>
            </SettingRow>
          ))}
          <SettingRow label="Videos per day">
            <span className="text-sm font-bold text-emerald-400">4</span>
          </SettingRow>
        </Card>

        {/* Brand */}
        <Card title="Brand" icon={<Tag size={14} className="text-emerald-400" />}>
          <SettingRow label="Channel name">
            <span className="text-sm font-medium text-zinc-200">AutoNews AI</span>
          </SettingRow>
          <SettingRow label="YouTube handle">
            <span className="text-sm font-medium text-zinc-200">@AutoNewsAI</span>
          </SettingRow>
          <SettingRow label="Instagram handle">
            <span className="text-sm font-medium text-zinc-200">@AutoNewsAI</span>
          </SettingRow>
          <SettingRow label="Language">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Hinglish
            </span>
          </SettingRow>
          <SettingRow label="Niche">
            <span className="text-sm font-medium text-zinc-200">Tech &amp; AI News</span>
          </SettingRow>
        </Card>
      </div>
    </div>
  );
}
