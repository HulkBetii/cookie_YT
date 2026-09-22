import React, { useState, useEffect, useRef } from 'react';
import {
  Terminal,
  Search,
  Filter,
  Trash2,
  Pause,
  Play,
  Download,
  ArrowDownCircle,
  Radio,
  Copy,
  Check
} from 'lucide-react';
import { LogMessage } from '../types';

interface LiveTelemetryViewProps {
  logs: LogMessage[];
  onClearLogs: () => void;
  wsConnected: boolean;
}

export const LiveTelemetryView: React.FC<LiveTelemetryViewProps> = ({
  logs,
  onClearLogs,
  wsConnected,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState<'ALL' | 'SUCCESS' | 'WARN' | 'ERROR'>('ALL');
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && !isPaused && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, isPaused]);

  // Filter logs
  const filteredLogs = logs.filter((l) => {
    const matchesSearch =
      l.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      l.profile.toLowerCase().includes(searchTerm.toLowerCase());
    if (levelFilter === 'ALL') return matchesSearch;
    return matchesSearch && l.level === levelFilter;
  });

  const handleDownloadLogs = () => {
    const content = logs
      .map((l) => `[${l.timestamp}] [${l.level}] ${l.profile ? `[${l.profile}] ` : ''}${l.text}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `youtube_farm_logs_${new Date().toISOString().slice(0, 10)}.log`;
    link.click();
  };

  const handleCopyLogs = () => {
    const content = filteredLogs.map((l) => `[${l.timestamp}] ${l.text}`).join('\n');
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'SUCCESS':
        return 'text-cyber-emerald bg-emerald-500/10 border-emerald-500/30';
      case 'WARN':
        return 'text-cyber-amber bg-amber-500/10 border-amber-500/30';
      case 'ERROR':
        return 'text-cyber-rose bg-rose-500/10 border-rose-500/30';
      case 'SKIP':
        return 'text-slate-400 bg-slate-800 border-slate-700';
      default:
        return 'text-cyber-cyan bg-cyan-500/10 border-cyan-500/30';
    }
  };

  return (
    <div className="space-y-4">
      {/* Console Controls Bar */}
      <div className="p-4 glass-panel flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-dark-950 border border-slate-800 text-xs font-mono">
            {(['ALL', 'SUCCESS', 'WARN', 'ERROR'] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  levelFilter === lvl
                    ? 'bg-dark-800 text-cyan-400 border border-slate-700'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {/* Toolbar Buttons */}
        <div className="flex items-center gap-2 w-full md:w-auto justify-end">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs">
            <Radio className={`w-3 h-3 ${wsConnected ? 'text-cyber-emerald animate-pulse' : 'text-slate-600'}`} />
            <span className="font-mono text-[11px] text-slate-300">
              {wsConnected ? 'Stream Live' : 'Disconnected'}
            </span>
          </div>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`p-2 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isPaused
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
                : 'bg-dark-800 border-slate-700 text-slate-300 hover:bg-dark-700'
            }`}
            title={isPaused ? 'Resume Stream' : 'Pause Stream'}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-2 rounded-xl border text-xs font-semibold transition-all ${
              autoScroll
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
                : 'bg-dark-800 border-slate-700 text-slate-500'
            }`}
            title="Auto-scroll to bottom"
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleCopyLogs}
            className="p-2 rounded-xl bg-dark-800 hover:bg-dark-700 border border-slate-700 text-slate-300 hover:text-white transition-all"
            title="Copy Filtered Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-cyber-emerald" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={handleDownloadLogs}
            className="p-2 rounded-xl bg-dark-800 hover:bg-dark-700 border border-slate-700 text-slate-300 hover:text-white transition-all"
            title="Download Log File"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onClearLogs}
            className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-cyber-rose transition-all"
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal Output Container */}
      <div className="glass-panel p-4 bg-dark-950/95 font-mono text-xs h-[calc(100vh-14rem)] overflow-y-auto border border-slate-800/90 shadow-2xl space-y-1.5">
        <div className="text-slate-500 pb-2 border-b border-slate-900 flex items-center justify-between text-[11px]">
          <span>⚡ WebSocket Live Telemetry Terminal — Listening on /ws/telemetry</span>
          <span>{filteredLogs.length} events logged</span>
        </div>

        {filteredLogs.length === 0 ? (
          <div className="text-slate-600 text-center py-16">
            Waiting for live log stream from GPM & Selenium workers...
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-2.5 py-0.5 hover:bg-slate-900/50 px-1.5 rounded transition-colors group"
            >
              {/* Timestamp */}
              <span className="text-slate-600 text-[11px] shrink-0">{log.timestamp}</span>

              {/* Level Badge */}
              <span
                className={`text-[9px] font-bold px-1.5 py-0.2 rounded border shrink-0 ${getLevelBadge(
                  log.level
                )}`}
              >
                {log.level}
              </span>

              {/* Profile if present */}
              {log.profile && (
                <span className="text-[11px] text-slate-400 font-semibold shrink-0">
                  [{log.profile}]
                </span>
              )}

              {/* Message Text with Syntax Highlight */}
              <span className={`text-[12px] break-all leading-relaxed ${
                log.level === 'SUCCESS'
                  ? 'text-emerald-300'
                  : log.level === 'WARN'
                  ? 'text-amber-300'
                  : log.level === 'ERROR'
                  ? 'text-rose-300'
                  : 'text-slate-200'
              }`}>
                {log.text}
              </span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
};
