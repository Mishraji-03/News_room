import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ListChecks, BarChart3, Bot, UploadCloud, Search, Settings } from 'lucide-react';

const navItems = [
  { to:'/', icon:LayoutDashboard, label:'Dashboard' },
  { to:'/queue', icon:ListChecks, label:'Content queue', badge:4 },
  { to:'/analytics', icon:BarChart3, label:'Analytics' },
  { to:'/agents', icon:Bot, label:'AI agents' },
  { to:'/uploads', icon:UploadCloud, label:'Upload history' },
  { to:'/seo', icon:Search, label:'SEO tracker' },
  { to:'/settings', icon:Settings, label:'Settings' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h2>AutoNews AI</h2>
        <span>Admin Studio</span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <item.icon />
            {item.label}
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="avatar">A</div>
        <div className="info">
          Admin
          <span>Owner · Full access</span>
        </div>
      </div>
    </aside>
  );
}
