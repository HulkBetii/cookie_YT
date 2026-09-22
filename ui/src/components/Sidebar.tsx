import React from 'react';
import {
  LayoutDashboard,
  Users,
  Terminal,
  SlidersHorizontal,
  BarChart3,
  Bot,
  Activity,
  Layers
} from 'lucide-react';

export type TabType = 'dashboard' | 'profiles' | 'telemetry' | 'strategy' | 'analytics';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  activeBotsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  activeBotsCount,
}) => {
  const navItems = [
    {
      id: 'dashboard' as TabType,
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: activeBotsCount > 0 ? `${activeBotsCount} Live` : undefined,
      badgeColor: 'bg-emerald-500/20 text-cyber-emerald border-emerald-500/30',
    },
    {
      id: 'profiles' as TabType,
      label: 'Profiles & Proxies',
      icon: Users,
    },
    {
      id: 'telemetry' as TabType,
      label: 'Live Console',
      icon: Terminal,
      badge: 'WS',
      badgeColor: 'bg-cyan-500/20 text-cyber-cyan border-cyan-500/30',
    },
    {
      id: 'strategy' as TabType,
      label: 'Strategy & Biometrics',
      icon: SlidersHorizontal,
    },
    {
      id: 'analytics' as TabType,
      label: 'Cookie Trust Analytics',
      icon: BarChart3,
    },
  ];

  return (
    <aside className="w-64 glass-panel rounded-none border-t-0 border-b-0 border-l-0 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      {/* Navigation List */}
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
          System Control
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-500/15 to-cyan-500/10 text-white border border-emerald-500/30 shadow-md shadow-emerald-500/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-dark-850 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyber-emerald' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className={`px-2 py-0.5 text-[9px] font-mono font-semibold border rounded-full ${item.badgeColor}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Ecosystem Mini Banner */}
      <div className="p-3.5 rounded-xl bg-dark-850/60 border border-slate-800/80 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Layers className="w-3.5 h-3.5 text-cyber-violet" />
          <span>Active Modules (US)</span>
        </div>
        <div className="grid grid-cols-3 gap-1.5 text-[10px] font-mono text-slate-400">
          <span className="p-1 rounded bg-dark-900 text-center text-emerald-400 border border-slate-800">YouTube</span>
          <span className="p-1 rounded bg-dark-900 text-center text-emerald-400 border border-slate-800">Maps US</span>
          <span className="p-1 rounded bg-dark-900 text-center text-emerald-400 border border-slate-800">Reddit US</span>
          <span className="p-1 rounded bg-dark-900 text-center text-cyan-400 border border-slate-800">Wiki EN</span>
          <span className="p-1 rounded bg-dark-900 text-center text-cyan-400 border border-slate-800">News US</span>
          <span className="p-1 rounded bg-dark-900 text-center text-violet-400 border border-slate-800">Fitts Mouse</span>
        </div>
      </div>
    </aside>
  );
};
