import React, { useState } from 'react';
import {
  Users,
  Bot,
  Play,
  Activity,
  Tv,
  MapPin,
  ShieldCheck,
  Zap,
  Sparkles,
} from 'lucide-react';
import { SystemStats, Profile } from '../types';
import { StatCard } from '../components/StatCard';
import { ActiveBotCard } from '../components/ActiveBotCard';
import { MarkovVisualizer } from '../components/MarkovVisualizer';

interface DashboardViewProps {
  stats: SystemStats | null;
  profiles: Profile[];
  onStartFarm: (profileIds: string[], loops: number, preset: string) => void;
  onStopBot: (id: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  stats,
  profiles,
  onStartFarm,
  onStopBot,
}) => {
  const [selectedPreset, setSelectedPreset] = useState('US_FULL_TRUST');
  const [loopsCount, setLoopsCount] = useState(3);
  const [selectedProfileId, setSelectedProfileId] = useState('ALL');

  const runningProfiles = profiles.filter((p) => p.is_running);

  const handleLaunch = () => {
    const targetIds = selectedProfileId === 'ALL' 
      ? profiles.map((p) => p.id) 
      : [selectedProfileId];
    onStartFarm(targetIds, loopsCount, selectedPreset);
  };

  return (
    <div className="space-y-6">
      {/* Top Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total GPM Profiles"
          value={stats?.total_profiles_count || profiles.length}
          subtitle="GPM API v2 Managed"
          icon={Users}
          color="cyan"
        />
        <StatCard
          title="Active Running Bots"
          value={stats?.active_bots_count || runningProfiles.length}
          subtitle={runningProfiles.length > 0 ? 'Parallel execution active' : 'All bots idle'}
          icon={Bot}
          color="emerald"
        />
        <StatCard
          title="Total Videos Watched"
          value={stats?.total_videos_watched || 0}
          subtitle="Ads automatically bypassed"
          icon={Tv}
          color="rose"
        />
        <StatCard
          title="Google Trust Signals"
          value={`${(stats?.total_maps_viewed || 0) + (stats?.total_reddit_read || 0) + (stats?.total_wiki_read || 0)}`}
          subtitle="Maps, Reddit & Wiki signals"
          icon={ShieldCheck}
          color="violet"
        />
      </div>

      {/* Quick Launch Control Panel */}
      <div className="p-5 glass-panel space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-cyber-emerald">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">Quick Farm Launch Station</h2>
              <p className="text-xs text-slate-400">Launch automated nurture campaigns with 1 click</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            Markov Presets
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Target Profile Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Profiles</label>
            <select
              value={selectedProfileId}
              onChange={(e) => setSelectedProfileId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-all font-mono"
            >
              <option value="ALL">🌟 All Profiles ({profiles.length} profiles)</option>
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.proxy ? `[${p.proxy.split(':')[0]}]` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Strategy Preset Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Strategy Preset</label>
            <select
              value={selectedPreset}
              onChange={(e) => setSelectedPreset(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-all font-mono"
            >
              <option value="US_FULL_TRUST">🇺🇸 US Full Trust (YouTube + Maps + Reddit + Wiki)</option>
              <option value="YT_AGGRESSIVE">🎬 YouTube Aggressive (Watch + Shorts + Hover)</option>
              <option value="LOCAL_MAPS">🗺️ Local Trust (Google Maps US + Google News)</option>
              <option value="QUICK_CHECK">⚡ Quick Check (Fast 5m session, low footprint)</option>
            </select>
          </div>

          {/* Loops Count */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Session Loops</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="50"
                value={loopsCount}
                onChange={(e) => setLoopsCount(parseInt(e.target.value) || 0)}
                className="w-24 px-3 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <span className="text-xs text-slate-500 font-mono">
                {loopsCount === 0 ? '(Infinite Loop)' : `(${loopsCount} loop iterations)`}
              </span>
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={handleLaunch}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/30 active:scale-95 transition-all"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>Launch Farm Campaign</span>
          </button>
        </div>
      </div>

      {/* Markov Visualizer */}
      <MarkovVisualizer />

      {/* Active Running Bots Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyber-emerald animate-pulse" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              Active Running Bots ({runningProfiles.length})
            </h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">Real-time Task Monitor</span>
        </div>

        {runningProfiles.length === 0 ? (
          <div className="p-8 rounded-xl bg-dark-900/40 border border-slate-800/60 text-center space-y-2">
            <Bot className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 font-medium">No bots currently running</p>
            <p className="text-[11px] text-slate-500">
              Select profiles and click Launch to start automated human simulation.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {runningProfiles.map((p) => (
              <ActiveBotCard key={p.id} profile={p} onStop={onStopBot} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
