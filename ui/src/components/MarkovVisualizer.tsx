import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

export const MarkovVisualizer: React.FC = () => {
  const states = [
    { id: 'start', label: 'Start & Search', icon: '🔍', color: 'from-violet-500/20 to-indigo-500/20 text-violet-300 border-violet-500/30' },
    { id: 'youtube', label: 'YouTube Watch', icon: '🎬', color: 'from-rose-500/20 to-red-500/20 text-rose-300 border-rose-500/30' },
    { id: 'shorts', label: 'Shorts Browsing', icon: '📱', color: 'from-amber-500/20 to-orange-500/20 text-amber-300 border-amber-500/30' },
    { id: 'maps', label: 'Google Maps US', icon: '🗺️', color: 'from-emerald-500/20 to-teal-500/20 text-emerald-300 border-emerald-500/30' },
    { id: 'reddit', label: 'Reddit US', icon: '👽', color: 'from-cyan-500/20 to-blue-500/20 text-cyan-300 border-cyan-500/30' },
    { id: 'wiki', label: 'Wikipedia EN', icon: '📚', color: 'from-purple-500/20 to-pink-500/20 text-purple-300 border-purple-500/30' },
  ];

  return (
    <div className="p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 backdrop-blur-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyber-cyan" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            Markov Decision Process (Dynamic State Transitions)
          </h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">Self-evolving Session Trajectory</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
        {states.map((s, idx) => (
          <div
            key={s.id}
            className={`p-3 rounded-xl bg-gradient-to-b ${s.color} border flex flex-col items-center justify-center text-center transition-all hover:scale-105`}
          >
            <span className="text-xl mb-1">{s.icon}</span>
            <span className="text-[11px] font-semibold">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 text-[10px] text-slate-500 font-mono pt-1">
        <span>Search</span>
        <ArrowRight className="w-3 h-3 text-slate-600" />
        <span>YouTube</span>
        <ArrowRight className="w-3 h-3 text-slate-600" />
        <span>Reddit / Maps (Trust)</span>
        <ArrowRight className="w-3 h-3 text-slate-600" />
        <span>Wiki (Knowledge)</span>
        <ArrowRight className="w-3 h-3 text-slate-600" />
        <span>Rest</span>
      </div>
    </div>
  );
};
