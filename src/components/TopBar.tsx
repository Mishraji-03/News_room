import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lock,
  Monitor,
  Bell,
  LogOut,
  Settings,
  ChevronDown,
  Wifi,
  WifiOff,
  Battery,
  Clock,
} from 'lucide-react';

// ============================================================
// TYPES
// ============================================================

interface TopBarProps {
  userName?: string;
  userAvatar?: string;
  systemStatus?: 'online' | 'degraded' | 'offline';
  lastSync?: string;
  onLogout?: () => void;
  onSettings?: () => void;
  className?: string;
}

// ============================================================
// STATUS CONFIG
// ============================================================

const statusConfig = {
  online: { icon: Wifi, color: 'text-emerald-400', label: 'Online' },
  degraded: { icon: Battery, color: 'text-yellow-400', label: 'Degraded' },
  offline: { icon: WifiOff, color: 'text-red-400', label: 'Offline' },
};

// ============================================================
// COMPONENT
// ============================================================

export default function TopBar({
  userName = 'Admin',
  userAvatar,
  systemStatus = 'online',
  lastSync,
  onLogout,
  onSettings,
  className = '',
}: TopBarProps) {
  const navigate = useNavigate();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const currentStatus = statusConfig[systemStatus] || statusConfig.online;
  const StatusIcon = currentStatus.icon;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Format last sync display
  const syncDisplay = lastSync
    ? `Last sync: ${new Date(lastSync).toLocaleTimeString()}`
    : 'Not synced';

  return (
    <header
      className={`
        fixed top-0 right-0 left-0 z-30
        bg-zinc-950/80 backdrop-blur-md
        border-b border-zinc-800
        px-4 py-2
        flex items-center justify-between
        transition-all duration-300
        ${className}
      `}
      style={{ height: '60px' }}
    >
      {/* Left section: System status */}
      <div className="flex items-center gap-3 text-sm">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/50 border border-zinc-800">
          <Lock size={14} className="text-emerald-400" />
          <span className="text-zinc-300 hidden sm:inline">Private admin portal</span>
          <span className="text-zinc-400 text-xs hidden md:inline">· Owner access</span>
        </div>

        {/* System status indicator */}
        <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-zinc-900/30">
          <StatusIcon size={14} className={currentStatus.color} />
          <span className="text-xs text-zinc-400 hidden sm:inline">
            {currentStatus.label}
          </span>
        </div>

        {/* Last sync (desktop only) */}
        {lastSync && (
          <div className="hidden lg:flex items-center gap-1 text-xs text-zinc-500">
            <Clock size={12} />
            <span>{syncDisplay}</span>
          </div>
        )}
      </div>

      {/* Right section: Actions + User menu */}
      <div className="flex items-center gap-2">
        {/* System overview button */}
        <button
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 transition-colors text-zinc-300 text-sm"
          onClick={() => navigate('/system')}
          aria-label="System overview"
        >
          <Monitor size={16} />
          <span>System overview</span>
        </button>

        {/* Notifications (placeholder) */}
        <button
          className="relative p-2 rounded-lg hover:bg-zinc-800 transition-colors"
          aria-label="Notifications"
        >
          <Bell size={18} className="text-zinc-400" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500" />
        </button>

        {/* Profile dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
            aria-label="User menu"
          >
            {userAvatar && userAvatar.trim() !== '' ? (
              <img
                src={userAvatar}
                alt={userName}
                className="w-8 h-8 rounded-full object-cover"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-medium text-sm">
                {userName.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="hidden md:flex flex-col items-start">
              <span className="text-sm font-medium text-zinc-200">{userName}</span>
              <span className="text-xs text-zinc-500">Administrator</span>
            </div>
            <ChevronDown size={14} className="text-zinc-400 hidden md:block" />
          </button>

          {/* Dropdown menu */}
          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-xl bg-zinc-900 border border-zinc-800 shadow-xl overflow-hidden z-50">
              <div className="px-4 py-3 border-b border-zinc-800">
                <p className="text-sm font-medium text-zinc-200">{userName}</p>
                <p className="text-xs text-zinc-500">Admin · Full access</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    onSettings?.();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
                >
                  <Settings size={14} />
                  Settings
                </button>
                <button
                  onClick={() => {
                    setIsProfileOpen(false);
                    onLogout?.();
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  <LogOut size={14} />
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}