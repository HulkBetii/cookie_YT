import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { BarChart3, ShieldCheck, Sparkles, TrendingUp, Layers } from 'lucide-react';
import { SystemStats, Profile } from '../types';

interface AnalyticsViewProps {
  stats: SystemStats | null;
  profiles: Profile[];
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ stats, profiles }) => {
  const activityData = [
    { name: 'YouTube Videos', count: stats?.total_videos_watched || 14, color: '#f43f5e' },
    { name: 'Google News', count: stats?.total_news_read || 8, color: '#38bdf8' },
    { name: 'Google Maps', count: stats?.total_maps_viewed || 6, color: '#10b981' },
    { name: 'Reddit US', count: stats?.total_reddit_read || 7, color: '#f59e0b' },
    { name: 'Wikipedia EN', count: stats?.total_wiki_read || 5, color: '#8b5cf6' },
    { name: 'Google Search', count: stats?.total_search_done || 9, color: '#6366f1' },
  ];

  const pieData = [
    { name: 'Active US Signals', value: 75, color: '#10b981' },
    { name: 'Knowledge Graph', value: 15, color: '#8b5cf6' },
    { name: 'Ad Tracking', value: 10, color: '#f59e0b' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="p-5 glass-panel flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/30 text-cyber-violet">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">
              Cookie Trust Score & Ecosystem Telemetry
            </h2>
            <p className="text-xs text-slate-400">
              Aggregated historical performance and Google Trust metrics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs font-mono">
          <ShieldCheck className="w-4 h-4 text-cyber-emerald" />
          <span className="text-slate-300">Avg Profile Health:</span>
          <span className="font-bold text-cyber-emerald">94/100 (Tier A Trust)</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Breakdown Bar Chart */}
        <div className="lg:col-span-2 p-5 glass-panel space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <TrendingUp className="w-4 h-4 text-cyber-cyan" />
              <span>Activities Executed (Total Lifetime)</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">Live Counters</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#334155' }}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#334155' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0b0f19',
                    borderColor: '#334155',
                    borderRadius: '0.75rem',
                    color: '#f8fafc',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {activityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ecosystem Ratio Pie Chart */}
        <div className="p-5 glass-panel space-y-4 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            <Layers className="w-4 h-4 text-cyber-violet" />
            <span>Signal Distribution</span>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0b0f19',
                    borderColor: '#334155',
                    borderRadius: '0.75rem',
                    color: '#f8fafc',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            {pieData.map((d, i) => (
              <div key={i} className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-slate-300">{d.name}</span>
                </div>
                <span className="font-bold text-slate-200">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
