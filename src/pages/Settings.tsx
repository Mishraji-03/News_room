import { useState } from 'react';

export default function Settings() {
  const [autoUpload, setAutoUpload] = useState(false);
  const [humanApproval, setHumanApproval] = useState(true);
  const [dualPlatform, setDualPlatform] = useState(true);
  const [notifications, setNotifications] = useState(true);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <div className="date">Configure your AutoNews AI portal</div>
        </div>
      </div>

      <div className="settings-grid">
        <div className="setting-card">
          <h3>🔑 API Keys</h3>
          <div className="setting-row">
            <span className="s-label">YouTube Data API v3</span>
            <span className="s-value" style={{ color:'var(--green)' }}>Connected</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Meta Graph API</span>
            <span className="s-value" style={{ color:'var(--green)' }}>Connected</span>
          </div>
          <div className="setting-row">
            <span className="s-label">NewsAPI.org</span>
            <span className="s-value" style={{ color:'var(--green)' }}>Connected</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Gemini Flash</span>
            <span className="s-value" style={{ color:'var(--amber)' }}>Free tier</span>
          </div>
          <div className="setting-row">
            <span className="s-label">D-ID</span>
            <span className="s-value" style={{ color:'var(--text-300)' }}>Not connected</span>
          </div>
        </div>

        <div className="setting-card">
          <h3>⚙️ Pipeline</h3>
          <div className="setting-row">
            <span className="s-label">Auto-upload (skip approval)</span>
            <button className={`toggle ${autoUpload ? 'on' : ''}`} onClick={() => setAutoUpload(!autoUpload)} />
          </div>
          <div className="setting-row">
            <span className="s-label">Human approval required</span>
            <button className={`toggle ${humanApproval ? 'on' : ''}`} onClick={() => setHumanApproval(!humanApproval)} />
          </div>
          <div className="setting-row">
            <span className="s-label">Dual platform (YT + IG)</span>
            <button className={`toggle ${dualPlatform ? 'on' : ''}`} onClick={() => setDualPlatform(!dualPlatform)} />
          </div>
          <div className="setting-row">
            <span className="s-label">Notifications</span>
            <button className={`toggle ${notifications ? 'on' : ''}`} onClick={() => setNotifications(!notifications)} />
          </div>
        </div>

        <div className="setting-card">
          <h3>📅 Schedule</h3>
          <div className="setting-row">
            <span className="s-label">Slot 1</span>
            <span className="s-value">6:00 AM</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Slot 2</span>
            <span className="s-value">12:00 PM</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Slot 3</span>
            <span className="s-value">5:00 PM</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Slot 4</span>
            <span className="s-value">7:00 PM</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Videos per day</span>
            <span className="s-value" style={{ color:'var(--green)' }}>4</span>
          </div>
        </div>

        <div className="setting-card">
          <h3>🏷️ Brand</h3>
          <div className="setting-row">
            <span className="s-label">Channel name</span>
            <span className="s-value">AutoNews AI</span>
          </div>
          <div className="setting-row">
            <span className="s-label">YouTube handle</span>
            <span className="s-value">@AutoNewsAI</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Instagram handle</span>
            <span className="s-value">@AutoNewsAI</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Language</span>
            <span className="s-value">Hinglish</span>
          </div>
          <div className="setting-row">
            <span className="s-label">Niche</span>
            <span className="s-value">Tech & AI News</span>
          </div>
        </div>
      </div>
    </>
  );
}
