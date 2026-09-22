import React from 'react';
import { Play, Square, RefreshCw, Radio, Clock, ShieldCheck } from 'lucide-react';
import { SystemStats } from '../types';

interface HeaderProps {
  stats: SystemStats | null;
  wsConnected: boolean;
  onStartAll: () => void;
  onStopAll: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  stats,
  wsConnected,
  onStartAll,
  onStopAll,
  onRefresh,
  isRefreshing,
}) => {
  return (
    <header className="h-16 px-6 glass-panel rounded-none border-t-0 border-x-0 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Market */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <span className="text-xl">⚡</span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              YouTube Farm Pro
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-cyber-emerald border border-emerald-500/30 rounded-full flex items-center gap-1">
              <span>🇺🇸</span> US Market
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">GPM-Login v2 API + Biometric Engine</p>
        </div>
      </div>

      {/* Telemetry Status Bar */}
      <div className="flex items-center gap-4">
        {/* US Circadian Clock */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-850/80 border border-slate-800 text-xs">
          <Clock className="w-3.5 h-3.5 text-cyber-cyan" />
          <span className="font-mono text-slate-200">{stats?.us_time_est || 'Loading EST...'}</span>
          {stats?.circadian_mode === 'SLEEP' && (
            <span className="px-1.5 py-0.5 text-[9px] font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded">
              🌙 Sleep (8.0x)
            </span>
          )}
          {stats?.circadian_mode === 'ACTIVE' && (
            <span className="px-1.5 py-0.5 text-[9px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded">
              ☀️ Peak (0.2x)
            </span>
          )}
        </div>

        {/* GPM Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-850/80 border border-slate-800 text-xs">
          <ShieldCheck className={`w-3.5 h-3.5 ${stats?.gpm_connected ? 'text-cyber-emerald' : 'text-cyber-rose'}`} />
          <span className="text-slate-300">GPM API:</span>
          <span className={`font-semibold ${stats?.gpm_connected ? 'text-cyber-emerald' : 'text-cyber-rose'}`}>
            {stats?.gpm_connected ? '19955 Connected' : 'Offline'}
          </span>
        </div>

        {/* WebSocket Stream Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400">
          <Radio className={`w-3 h-3 ${wsConnected ? 'text-cyber-emerald animate-pulse' : 'text-slate-600'}`} />
          <span className="font-mono text-[11px]">{wsConnected ? 'Live Stream' : 'Connecting...'}</span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 ml-2">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-dark-850 hover:bg-dark-800 border border-slate-800 text-slate-300 hover:text-white transition-all disabled:opacity-50"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={onStartAll}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/25 active:scale-95 transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Start All</span>
          </button>

          <button
            onClick={onStopAll}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-rose-600/25 active:scale-95 transition-all"
          >
            <Square className="w-3.5 h-3.5 fill-white" />
            <span>Stop All</span>
          </button>
        </div>
      </div>
    </header>
  );
};
