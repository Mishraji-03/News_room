import {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
  memo,
} from 'react';

import {
  Trash2,
  Wifi,
  WifiOff,
  Loader2,
  Pause,
  Play,
  AlertCircle,
} from 'lucide-react';


// ============================================================
// TYPES
// ============================================================

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

type LogLevel = 'INFO' | 'WARNING' | 'ERROR' | 'RETRY';

interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  level: LogLevel;
}

interface LogTerminalProps {
  endpoint?: string;
  maxLogs?: number;
  autoScroll?: boolean;
  className?: string;
}


// ============================================================
// CONSTANTS
// ============================================================

const DEFAULT_MAX_LOGS = 500;

const LEVEL_COLORS: Record<LogLevel, string> = {
  INFO: 'text-emerald-400',
  WARNING: 'text-yellow-400',
  ERROR: 'text-red-400',
  RETRY: 'text-orange-400',
};


// ============================================================
// HELPERS
// ============================================================

function detectLogLevel(message: string): LogLevel {
  const text = message.toUpperCase();

  if (text.includes('ERROR') || text.includes('FAILED')) {
    return 'ERROR';
  }

  if (text.includes('RETRY')) {
    return 'RETRY';
  }

  if (text.includes('WARNING')) {
    return 'WARNING';
  }

  return 'INFO';
}

function createLogEntry(message: string): LogEntry {
  return {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    message,
    level: detectLogLevel(message),
  };
}


// ============================================================
// COMPONENT
// ============================================================

const LogTerminal = memo(function LogTerminal({
  endpoint = 'http://localhost:8000/api/logs/stream',
  maxLogs = DEFAULT_MAX_LOGS,
  autoScroll = true,
  className = '',
}: LogTerminalProps) {

  // ============================================================
  // STATE
  // ============================================================

  const [logs, setLogs] = useState<LogEntry[]>([]);

  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>('connecting');

  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);

  const [filter, setFilter] = useState('');

  const terminalRef = useRef<HTMLDivElement | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  const reconnectTimeoutRef = useRef<number | null>(null);

  const userScrolledRef = useRef(false);


  // ============================================================
  // ADD LOG
  // ============================================================

  const addLog = useCallback(
    (message: string, timestamp?: string) => {

      const entry: LogEntry = {
        id: crypto.randomUUID(),
        timestamp: timestamp || new Date().toISOString(),
        message,
        level: detectLogLevel(message),
      };

      setLogs(prev => {
        const updated = [...prev, entry];

        if (updated.length > maxLogs) {
          return updated.slice(-maxLogs);
        }

        return updated;
      });
    },
    [maxLogs]
  );


  // ============================================================
  // SSE CONNECTION
  // ============================================================

  const connectSSE = useCallback(() => {

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setConnectionStatus('connecting');

    const eventSource = new EventSource(endpoint);

    eventSourceRef.current = eventSource;


    // CONNECTED
    eventSource.onopen = () => {
      setConnectionStatus('connected');

      addLog('[SYSTEM] SSE connected');
    };


    // MESSAGE
    eventSource.onmessage = (event) => {

      if (pausedRef.current) return;

      try {

        const parsed = JSON.parse(event.data);

        const message =
          typeof parsed === 'string'
            ? parsed
            : parsed.message || 'Unknown log';

        const timestamp =
          parsed.timestamp || new Date().toISOString();

        addLog(message, timestamp);

      } catch {

        addLog(event.data);
      }
    };


    // ERROR
    eventSource.onerror = () => {

      setConnectionStatus('disconnected');

      addLog('[SYSTEM] Connection lost. Reconnecting...');

      eventSource.close();

      reconnectTimeoutRef.current = window.setTimeout(() => {
        connectSSE();
      }, 5000);
    };

  }, [endpoint, addLog]);


  // Sync pausedRef so the SSE handler always reads current value
  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);


  // ============================================================
  // EFFECT
  // ============================================================

  useEffect(() => {

    connectSSE();

    return () => {

      eventSourceRef.current?.close();

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };

  }, [connectSSE]);


  // ============================================================
  // FILTERED LOGS
  // ============================================================

  const filteredLogs = useMemo(() => {

    if (!filter.trim()) return logs;

    return logs.filter(log =>
      log.message.toLowerCase().includes(filter.toLowerCase())
    );

  }, [logs, filter]);


  // ============================================================
  // AUTOSCROLL
  // ============================================================

  useEffect(() => {

    if (
      autoScroll &&
      terminalRef.current &&
      !userScrolledRef.current
    ) {
      terminalRef.current.scrollTop =
        terminalRef.current.scrollHeight;
    }

  }, [filteredLogs, autoScroll]);


  // ============================================================
  // HANDLE SCROLL
  // ============================================================

  const handleScroll = () => {

    if (!terminalRef.current) return;

    const {
      scrollTop,
      scrollHeight,
      clientHeight,
    } = terminalRef.current;

    const isNearBottom =
      scrollHeight - scrollTop - clientHeight < 100;

    userScrolledRef.current = !isNearBottom;
  };


  // ============================================================
  // CLEAR LOGS
  // ============================================================

  const clearLogs = () => {
    setLogs([]);
  };


  // ============================================================
  // CONNECTION INDICATOR
  // ============================================================

  const connectionUI = useMemo(() => {

    switch (connectionStatus) {

      case 'connected':
        return (
          <div className="flex items-center gap-1 text-green-400">
            <Wifi size={14} />
            <span>LIVE</span>
          </div>
        );

      case 'connecting':
        return (
          <div className="flex items-center gap-1 text-yellow-400">
            <Loader2 size={14} className="animate-spin" />
            <span>CONNECTING</span>
          </div>
        );

      default:
        return (
          <div className="flex items-center gap-1 text-red-400">
            <WifiOff size={14} />
            <span>OFFLINE</span>
          </div>
        );
    }

  }, [connectionStatus]);


  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div className={`mt-6 ${className}`}>

      {/* ===================================================== */}
      {/* HEADER */}
      {/* ===================================================== */}

      <div className="flex items-center justify-between mb-3">

        <div className="flex items-center gap-3">

          <h3 className="text-base font-semibold text-zinc-200">
            Team Leader Logs
          </h3>

          {connectionUI}

        </div>


        <div className="flex items-center gap-2">

          {/* FILTER */}
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="
              bg-zinc-900
              border
              border-zinc-700
              rounded-lg
              px-3
              py-1.5
              text-sm
              text-zinc-200
              outline-none focus:border-zinc-500
            "
          />
          {/* PAUSE / PLAY */}
          <button
            onClick={() => setPaused(!paused)}
            className="p-1.5 rounded-lg bg-zinc-950 border border-zinc-800 hover:border-zinc-600 transition-all text-zinc-400 hover:text-zinc-100"
            title={paused ? 'Resume stream' : 'Pause stream'}
          >
            {paused ? <Play size={14} fill="currentColor" /> : <Pause size={14} fill="currentColor" />}
          </button>

          {/* CLEAR */}
          <button
            onClick={clearLogs}
            className="p-1.5 rounded-lg bg-zinc-950 border border-zinc-800 hover:border-red-900/50 hover:bg-red-950/20 transition-all text-zinc-400 hover:text-red-400"
            title="Clear logs"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* TERMINAL BODY */}
      <div
        ref={terminalRef}
        onScroll={handleScroll}
        className="
          flex-1 bg-zinc-950/80 border border-zinc-800/80 rounded-b-2xl
          overflow-y-auto p-4 font-mono text-xs leading-relaxed
          scrollbar-thin scrollbar-track-transparent scrollbar-thumb-zinc-800
          shadow-2xl min-h-[350px]
        "
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-zinc-600 italic animate-pulse">
            <Loader2 size={16} className="mr-2 animate-spin" />
            Waiting for system telemetry...
          </div>
        ) : (
          <div className="space-y-1.5">
            {filteredLogs.map((log) => (
              <div key={log.id} className="flex gap-4 group transition-colors hover:bg-zinc-900/30 -mx-2 px-2 py-0.5 rounded">
                <span className="text-zinc-600 shrink-0 select-none font-medium">
                  {new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}
                </span>
                <span className={`break-words flex-1 ${LEVEL_COLORS[log.level] || 'text-zinc-300'}`}>
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* FOOTER METRICS */}
      <div className="mt-2 flex items-center justify-between px-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
        <div className="flex items-center gap-4">
          <span>Entries: {logs.length}</span>
          <span>Buffer: {Math.round((logs.length / maxLogs) * 100)}%</span>
        </div>
        <div className="flex items-center gap-1">
          <Wifi size={10} className={paused ? 'text-zinc-600' : 'text-emerald-500'} />
          <span>{paused ? 'Offline' : 'Real-time'}</span>
        </div>
      </div>
    </div>
  );
});

export default LogTerminal;