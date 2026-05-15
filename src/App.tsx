import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import ContentQueue from './pages/ContentQueue';
import Analytics from './pages/Analytics';
import AIAgents from './pages/AIAgents';
import UploadHistory from './pages/UploadHistory';
import SEOTracker from './pages/SEOTracker';
import Settings from './pages/Settings';

export default function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex overflow-x-hidden">
        <Sidebar defaultCollapsed={collapsed} onToggle={setCollapsed} />

        {/* Main content — offset matches sidebar width via padding */}
        <div
          className={`
            flex flex-col flex-1 min-w-0 transition-all duration-300
            ${collapsed ? 'lg:pl-20' : 'lg:pl-64'}
          `}
        >
          {/* TopBar offset matches sidebar */}
          <TopBar className={collapsed ? 'lg:left-20' : 'lg:left-64'} />

          <main className="flex-1 p-4 md:p-6 lg:p-10 pt-24 max-w-[1600px] mx-auto w-full">
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/queue" element={<ContentQueue />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/agents" element={<AIAgents />} />
                <Route path="/uploads" element={<UploadHistory />} />
                <Route path="/seo" element={<SEOTracker />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
