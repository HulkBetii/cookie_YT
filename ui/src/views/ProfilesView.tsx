import React, { useState } from 'react';
import {
  Search,
  Filter,
  Play,
  Square,
  Globe,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  Edit2,
  RefreshCw
} from 'lucide-react';
import { Profile, ProxyCheckResult } from '../types';
import { api } from '../services/api';

interface ProfilesViewProps {
  profiles: Profile[];
  onStartProfiles: (ids: string[]) => void;
  onStopProfiles: (ids: string[]) => void;
  onRefresh: () => void;
}

export const ProfilesView: React.FC<ProfilesViewProps> = ({
  profiles,
  onStartProfiles,
  onStopProfiles,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'RUNNING' | 'IDLE'>('ALL');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [proxyTestingId, setProxyTestingId] = useState<string | null>(null);
  const [proxyResults, setProxyResults] = useState<Record<string, ProxyCheckResult>>({});

  // Edit proxy modal state
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [newProxyValue, setNewProxyValue] = useState('');
  const [isSavingProxy, setIsSavingProxy] = useState(false);

  // Filter profiles
  const filteredProfiles = profiles.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.proxy.toLowerCase().includes(searchTerm.toLowerCase());
    if (statusFilter === 'RUNNING') return matchesSearch && p.is_running;
    if (statusFilter === 'IDLE') return matchesSearch && !p.is_running;
    return matchesSearch;
  });

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(filteredProfiles.map((p) => p.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleTestProxy = async (profile: Profile) => {
    if (!profile.proxy) return;
    setProxyTestingId(profile.id);
    try {
      const res = await api.checkProxy(profile.proxy);
      setProxyResults((prev) => ({ ...prev, [profile.id]: res }));
    } catch (e) {
      // Error handled
    } finally {
      setProxyTestingId(null);
    }
  };

  const handleOpenEditProxy = (profile: Profile) => {
    setEditingProfile(profile);
    setNewProxyValue(profile.proxy || '');
  };

  const handleSaveProxy = async () => {
    if (!editingProfile) return;
    setIsSavingProxy(true);
    try {
      await api.updateProxy(editingProfile.id, newProxyValue.trim());
      setEditingProfile(null);
      onRefresh();
    } catch (e) {
      alert('Lỗi cập nhật proxy');
    } finally {
      setIsSavingProxy(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Actions Bar */}
      <div className="p-4 glass-panel flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search & Filters */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search profiles or proxies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-dark-950 border border-slate-800 text-xs">
            {(['ALL', 'RUNNING', 'IDLE'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setStatusFilter(mode)}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  statusFilter === mode
                    ? 'bg-dark-800 text-cyber-emerald shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode === 'ALL' ? 'All' : mode === 'RUNNING' ? 'Running' : 'Idle'}
              </button>
            ))}
          </div>
        </div>

        {/* Bulk Action Buttons */}
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2 animate-fade-in">
            <span className="text-xs text-slate-400 font-mono">
              {selectedIds.length} selected
            </span>
            <button
              onClick={() => onStartProfiles(selectedIds)}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-emerald-600/20"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Start Selected</span>
            </button>
            <button
              onClick={() => onStopProfiles(selectedIds)}
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-rose-600/20"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              <span>Stop Selected</span>
            </button>
          </div>
        )}
      </div>

      {/* Profiles Data Table */}
      <div className="glass-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-950/80 border-b border-slate-800 text-slate-400 font-mono text-[11px] uppercase">
              <tr>
                <th className="p-3.5 w-10 text-center">
                  <input
                    type="checkbox"
                    checked={
                      filteredProfiles.length > 0 &&
                      selectedIds.length === filteredProfiles.length
                    }
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded bg-dark-900 border-slate-700 text-emerald-500 focus:ring-0 focus:outline-none"
                  />
                </th>
                <th className="p-3.5">Profile Name</th>
                <th className="p-3.5">Proxy Config</th>
                <th className="p-3.5">Status & Activity</th>
                <th className="p-3.5">Cookie Health</th>
                <th className="p-3.5">Note</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredProfiles.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500 font-mono">
                    No matching profiles found
                  </td>
                </tr>
              ) : (
                filteredProfiles.map((p) => {
                  const isSelected = selectedIds.includes(p.id);
                  const proxyCheck = proxyResults[p.id];
                  return (
                    <tr
                      key={p.id}
                      className={`hover:bg-dark-850/50 transition-colors ${
                        isSelected ? 'bg-emerald-500/5' : ''
                      }`}
                    >
                      <td className="p-3.5 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelect(p.id)}
                          className="rounded bg-dark-900 border-slate-700 text-emerald-500 focus:ring-0 focus:outline-none"
                        />
                      </td>

                      {/* Profile Name & ID */}
                      <td className="p-3.5">
                        <div className="font-semibold text-slate-200 tracking-tight flex items-center gap-2">
                          <span>{p.name}</span>
                          {p.is_running && (
                            <span className="w-2 h-2 rounded-full bg-cyber-emerald animate-pulse" />
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono truncate max-w-[120px]">
                          {p.id}
                        </div>
                      </td>

                      {/* Proxy */}
                      <td className="p-3.5">
                        {p.proxy ? (
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[11px] text-slate-300">
                              {p.proxy.split(':')[0]}:{p.proxy.split(':')[1]}
                            </span>
                            <button
                              onClick={() => handleTestProxy(p)}
                              disabled={proxyTestingId === p.id}
                              className="p-1 rounded bg-dark-800 hover:bg-dark-700 text-[10px] font-mono text-slate-400 hover:text-slate-200 border border-slate-700 flex items-center gap-1"
                              title="Test Proxy Ping"
                            >
                              <Globe className={`w-3 h-3 ${proxyTestingId === p.id ? 'animate-spin text-cyan-400' : ''}`} />
                            </button>
                            {proxyCheck && (
                              <span
                                className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${
                                  proxyCheck.ok
                                    ? 'bg-emerald-500/10 text-cyber-emerald border border-emerald-500/20'
                                    : 'bg-rose-500/10 text-cyber-rose border border-rose-500/20'
                                }`}
                              >
                                {proxyCheck.ok ? `${proxyCheck.ping_ms}ms` : 'Dead'}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-[11px] text-slate-500 font-mono italic">
                            Direct (No Proxy)
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="p-3.5">
                        {p.is_running ? (
                          <div>
                            <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-cyber-emerald border border-emerald-500/30 rounded-full inline-flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-cyber-emerald animate-ping" />
                              {p.current_activity || 'Running'}
                            </span>
                            <p className="text-[10px] text-slate-400 font-mono truncate max-w-[150px] mt-0.5">
                              {p.current_detail || 'Active session'}
                            </p>
                          </div>
                        ) : (
                          <span className="px-2 py-0.5 text-[10px] font-medium bg-dark-800 text-slate-400 border border-slate-700 rounded-full">
                            Idle
                          </span>
                        )}
                      </td>

                      {/* Cookie Health Score */}
                      <td className="p-3.5">
                        <div className="w-24">
                          <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                            <span>Score</span>
                            <span className="text-cyber-emerald font-semibold">{p.cookie_score}%</span>
                          </div>
                          <div className="w-full h-1.5 rounded-full bg-dark-950 overflow-hidden border border-slate-800">
                            <div
                              className="h-full bg-gradient-to-r from-teal-500 to-emerald-400 rounded-full"
                              style={{ width: `${p.cookie_score}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Note */}
                      <td className="p-3.5">
                        <span className="text-[11px] text-slate-400 font-mono truncate max-w-[100px] block">
                          {p.note || '-'}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="p-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenEditProxy(p)}
                            className="p-1.5 rounded-lg bg-dark-800 hover:bg-dark-700 border border-slate-700 text-slate-300 hover:text-white transition-all"
                            title="Edit Proxy"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>

                          {p.is_running ? (
                            <button
                              onClick={() => onStopProfiles([p.id])}
                              className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-cyber-rose transition-all"
                              title="Stop Profile"
                            >
                              <Square className="w-3.5 h-3.5 fill-current" />
                            </button>
                          ) : (
                            <button
                              onClick={() => onStartProfiles([p.id])}
                              className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-cyber-emerald transition-all"
                              title="Start Profile"
                            >
                              <Play className="w-3.5 h-3.5 fill-current" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Proxy Modal */}
      {editingProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="p-6 rounded-2xl glass-panel w-full max-w-md space-y-4 border border-slate-700 shadow-2xl">
            <h3 className="text-sm font-bold text-white tracking-tight">
              Edit Proxy for [{editingProfile.name}]
            </h3>
            <p className="text-xs text-slate-400">
              Format: <code className="text-emerald-400">IP:PORT:USER:PASS</code> or <code className="text-emerald-400">IP:PORT</code>
            </p>
            <input
              type="text"
              placeholder="e.g. 118.70.171.121:41887:user:pass"
              value={newProxyValue}
              onChange={(e) => setNewProxyValue(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setEditingProfile(null)}
                className="px-4 py-2 rounded-xl bg-dark-800 text-slate-300 text-xs font-semibold hover:bg-dark-700 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProxy}
                disabled={isSavingProxy}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-xs font-semibold hover:from-emerald-500 hover:to-teal-500 transition-all disabled:opacity-50"
              >
                {isSavingProxy ? 'Saving...' : 'Save Proxy'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
