import React from 'react';
import { Square, Tv, MapPin, Globe, BookOpen, Search, Newspaper, Bot } from 'lucide-react';
import { Profile } from '../types';

interface ActiveBotCardProps {
  profile: Profile;
  onStop: (id: string) => void;
}

export const ActiveBotCard: React.FC<ActiveBotCardProps> = ({ profile, onStop }) => {
  const getActivityIcon = (activity: string) => {
    const act = activity.toLowerCase();
    if (act.includes('youtube') || act.includes('shorts') || act.includes('video')) {
      return <Tv className="w-4 h-4 text-cyber-rose" />;
    } else if (act.includes('map')) {
      return <MapPin className="w-4 h-4 text-cyber-emerald" />;
    } else if (act.includes('reddit')) {
      return <Globe className="w-4 h-4 text-cyber-amber" />;
    } else if (act.includes('wiki')) {
      return <BookOpen className="w-4 h-4 text-cyber-cyan" />;
    } else if (act.includes('search') || act.includes('google')) {
      return <Search className="w-4 h-4 text-cyber-violet" />;
    } else if (act.includes('news') || act.includes('báo')) {
      return <Newspaper className="w-4 h-4 text-blue-400" />;
    }
    return <Bot className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="p-4 rounded-xl bg-dark-900/80 border border-emerald-500/30 shadow-lg shadow-emerald-500/5 backdrop-blur-md transition-all hover:border-emerald-500/50">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              {getActivityIcon(profile.current_activity)}
            </div>
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyber-emerald animate-ping" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyber-emerald" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white tracking-tight">{profile.name}</h4>
            <p className="text-[10px] font-mono text-slate-400 truncate max-w-[140px]">
              {profile.proxy || 'Direct IP'}
            </p>
          </div>
        </div>

        <button
          onClick={() => onStop(profile.id)}
          className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-cyber-rose transition-all active:scale-90"
          title="Stop this Bot"
        >
          <Square className="w-3.5 h-3.5 fill-current" />
        </button>
      </div>

      <div className="mt-3 p-2.5 rounded-lg bg-dark-950/70 border border-slate-800 text-xs">
        <div className="flex items-center justify-between text-[11px] mb-1">
          <span className="text-slate-400 font-medium">Activity:</span>
          <span className="font-semibold text-cyber-emerald">{profile.current_activity || 'Running'}</span>
        </div>
        <p className="text-[11px] text-slate-300 font-mono truncate">
          {profile.current_detail || 'Simulating human session...'}
        </p>
      </div>

      <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-400 font-mono">
        <span className="flex items-center gap-1 text-cyber-emerald">
          <span className="w-1.5 h-1.5 rounded-full bg-cyber-emerald inline-block" />
          Cookie Health: {profile.cookie_score}%
        </span>
        <span>ID: {profile.id.slice(0, 8)}...</span>
      </div>
    </div>
  );
};
