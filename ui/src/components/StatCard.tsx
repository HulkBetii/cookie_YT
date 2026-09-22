import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'emerald' | 'cyan' | 'violet' | 'amber' | 'rose';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'emerald',
}) => {
  const colorMap = {
    emerald: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-cyber-emerald',
      glow: 'hover:border-emerald-500/40',
    },
    cyan: {
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
      text: 'text-cyber-cyan',
      glow: 'hover:border-cyan-500/40',
    },
    violet: {
      bg: 'bg-violet-500/10',
      border: 'border-violet-500/20',
      text: 'text-cyber-violet',
      glow: 'hover:border-violet-500/40',
    },
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-cyber-amber',
      glow: 'hover:border-amber-500/40',
    },
    rose: {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      text: 'text-cyber-rose',
      glow: 'hover:border-rose-500/40',
    },
  };

  const scheme = colorMap[color];

  return (
    <div className={`p-4 rounded-xl bg-dark-900/60 border border-slate-800/80 backdrop-blur-sm transition-all duration-200 ${scheme.glow}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400">{title}</span>
        <div className={`p-2 rounded-lg ${scheme.bg} ${scheme.border} border`}>
          <Icon className={`w-4 h-4 ${scheme.text}`} />
        </div>
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">{value}</span>
      </div>
      {subtitle && (
        <p className="mt-1 text-[11px] text-slate-500 font-mono flex items-center gap-1">
          {subtitle}
        </p>
      )}
    </div>
  );
};
