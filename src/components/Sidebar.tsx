import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  ListChecks,
  BarChart3,
  Bot,
  UploadCloud,
  Search,
  Settings,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

// ============================================================
// TYPES
// ============================================================

interface NavItem {
  to: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  badge?: number;
  end?: boolean;
}

// ============================================================
// NAVIGATION ITEMS
// ============================================================

const navItems: NavItem[] = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/queue', icon: ListChecks, label: 'Content Queue', badge: 4 },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/agents', icon: Bot, label: 'AI Agents' },
  { to: '/uploads', icon: UploadCloud, label: 'Upload History' },
  { to: '/seo', icon: Search, label: 'SEO Tracker' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

// ============================================================
// SIDEBAR COMPONENT
// ============================================================

interface SidebarProps {
  /** Initial collapsed state (default false) */
  defaultCollapsed?: boolean;
  /** Callback when sidebar toggles (for parent layout adjustments) */
  onToggle?: (collapsed: boolean) => void;
}

export default function Sidebar({ defaultCollapsed = false, onToggle }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const toggleCollapse = () => {
    const newState = !collapsed;
    setCollapsed(newState);
    onToggle?.(newState);
  };

  const toggleMobile = () => {
    setMobileOpen(!mobileOpen);
  };

  // Sidebar width classes
  const sidebarWidth = collapsed ? 'w-20' : 'w-64';
  const mobileSidebarClass = mobileOpen ? 'translate-x-0' : '-translate-x-full';

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={toggleMobile}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 lg:hidden"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      {/* Backdrop for mobile */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full z-40
          bg-gradient-to-b from-zinc-950 to-zinc-900
          border-r border-zinc-800
          transition-all duration-300 ease-in-out
          flex flex-col
          ${sidebarWidth}
          ${mobileSidebarClass}
          lg:translate-x-0
        `}
        aria-label="Main navigation"
      >
        {/* Brand */}
        <div className="flex items-center justify-between px-4 py-6 border-b border-zinc-800">
          <div className={`flex items-center gap-2 ${collapsed ? 'justify-center w-full' : ''}`}>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
              <span className="text-emerald-400 font-bold text-lg">A</span>
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <h2 className="font-bold text-zinc-100 text-lg leading-tight">AutoNews AI</h2>
                <span className="text-xs text-zinc-500">Admin Studio</span>
              </div>
            )}
          </div>

          {/* Collapse toggle (desktop only) */}
          <button
            onClick={toggleCollapse}
            className="hidden lg:block p-1 rounded-md hover:bg-zinc-800 text-zinc-400 transition-colors"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto" aria-label="Sidebar navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to || 
              (!item.end && location.pathname.startsWith(item.to));

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive: navLinkActive }) => {
                  const active = navLinkActive || isActive;
                  return `
                    flex items-center gap-3 px-3 py-2.5 rounded-xl
                    transition-all duration-200 group
                    ${active 
                      ? 'bg-emerald-500/10 text-emerald-400' 
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                    }
                    ${collapsed ? 'justify-center' : ''}
                  `;
                }}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={20} className="shrink-0" />
                {!collapsed && (
                  <span className="text-sm font-medium flex-1">{item.label}</span>
                )}
                {!collapsed && item.badge && (
                  <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400">
                    {item.badge}
                  </span>
                )}
                {collapsed && item.badge && (
                  <span className="absolute top-0 right-2 w-2 h-2 rounded-full bg-emerald-500" />
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer / User profile */}
        <div className="border-t border-zinc-800 p-4">
          <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-medium text-sm shadow-lg">
              A
            </div>
            {!collapsed && (
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium text-zinc-200 truncate">Admin</span>
                <span className="text-xs text-zinc-500 truncate">Owner · Full access</span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}