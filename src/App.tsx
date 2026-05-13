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
  return (
    <BrowserRouter>
      <TopBar />
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/queue" element={<ContentQueue />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/agents" element={<AIAgents />} />
            <Route path="/uploads" element={<UploadHistory />} />
            <Route path="/seo" element={<SEOTracker />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
