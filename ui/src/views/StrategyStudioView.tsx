import React, { useState, useEffect } from 'react';
import {
  SlidersHorizontal,
  Save,
  Sparkles,
  Layers,
  Clock,
  Keyboard,
  MousePointer,
  Tags,
  Plus,
  X,
  CheckCircle2,
  TrendingUp,
  Radio
} from 'lucide-react';
import { FarmConfig, Profile } from '../types';
import { api } from '../services/api';
import { SchedulerSection } from '../components/SchedulerSection';

interface StrategyStudioViewProps {
  initialConfig: FarmConfig | null;
  profiles: Profile[];
  onConfigSaved: () => void;
}

export const StrategyStudioView: React.FC<StrategyStudioViewProps> = ({
  initialConfig,
  profiles,
  onConfigSaved,
}) => {
  const [config, setConfig] = useState<FarmConfig | null>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [notification, setNotification] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  // New tag inputs
  const [newKeyword, setNewKeyword] = useState('');
  const [newSubreddit, setNewSubreddit] = useState('');
  const [newMapsCity, setNewMapsCity] = useState('');
  const [newWikiTopic, setNewWikiTopic] = useState('');
  const [newTicker, setNewTicker] = useState('');

  useEffect(() => {
    if (initialConfig) setConfig(initialConfig);
  }, [initialConfig]);

  const showNotification = (msg: string, type: 'success' | 'error') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  if (!config) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono">
        Loading configuration from server...
      </div>
    );
  }

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateConfig(config);
      setSaveSuccess(true);
      showNotification('Đã lưu toàn bộ cấu hình Strategy & Datasets thành công!', 'success');
      onConfigSaved();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      showNotification(`Lỗi khi lưu cấu hình: ${e.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const addTag = (field: keyof FarmConfig, val: string, clearFn: () => void) => {
    if (!val.trim() || !config) return;
    const currentList = (config[field] as string[]) || [];
    if (!currentList.includes(val.trim())) {
      setConfig({
        ...config,
        [field]: [...currentList, val.trim()],
      });
    }
    clearFn();
  };

  const removeTag = (field: keyof FarmConfig, index: number) => {
    if (!config) return;
    const currentList = [...((config[field] as string[]) || [])];
    currentList.splice(index, 1);
    setConfig({
      ...config,
      [field]: currentList,
    });
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 text-sm font-medium border animate-in slide-in-from-top-3 ${
          notification.type === 'success' 
            ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-200' 
            : 'bg-rose-950/90 border-rose-500/50 text-rose-200'
        }`}>
          <CheckCircle2 className="w-4 h-4" />
          <span>{notification.msg}</span>
        </div>
      )}

      {/* ── 1. Cron Scheduler Studio Section ── */}
      <SchedulerSection profiles={profiles} onNotify={showNotification} />

      {/* ── 2. Strategy & Biometrics Header ── */}
      <div className="p-4 glass-panel flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyber-cyan">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">Strategy & Biometric Preset Studio</h2>
            <p className="text-xs text-slate-400">Configure Markov state weights, human simulations, and datasets</p>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 transition-all active:scale-95 disabled:opacity-50"
        >
          {saveSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-slate-950" />
              <span>Saved!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Platform Toggles & Timing */}
        <div className="space-y-6">
          {/* Enabled Modules Toggle Matrix */}
          <div className="p-5 glass-panel space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <Layers className="w-4 h-4 text-cyber-cyan" />
              <span>Multi-Platform Ecosystem Toggles</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {[
                { key: 'TIM_KIEM_GOOGLE', label: 'Google Search US', icon: '🔍', color: 'border-blue-500/30' },
                { key: 'SU_DUNG_GOOGLE_NEWS', label: 'Google News US', icon: '📰', color: 'border-cyan-500/30' },
                { key: 'SU_DUNG_GOOGLE_MAPS', label: 'Google Maps Local', icon: '🗺️', color: 'border-emerald-500/30' },
                { key: 'SU_DUNG_GOOGLE_FINANCE', label: 'Google Finance US', icon: '💹', color: 'border-teal-500/30' },
                { key: 'SU_DUNG_REDDIT', label: 'Reddit US Feed', icon: '👽', color: 'border-amber-500/30' },
                { key: 'SU_DUNG_WIKIPEDIA', label: 'Wikipedia EN', icon: '📚', color: 'border-indigo-500/30' },
                { key: 'LUOT_TWITTER', label: 'Twitter / X News', icon: '🐦', color: 'border-sky-500/30' },
                { key: 'TRON_PROFILES', label: 'Shuffle Profiles', icon: '🔀', color: 'border-purple-500/30' },
              ].map(({ key, label, icon, color }) => {
                const isEnabled = (config as any)[key];
                return (
                  <div
                    key={key}
                    onClick={() => setConfig({ ...config, [key]: !isEnabled })}
                    className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                      isEnabled
                        ? `bg-slate-900/90 ${color} text-slate-100 shadow-sm`
                        : 'bg-dark-950/40 border-slate-800 text-slate-500 opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-xs font-medium">
                      <span>{icon}</span>
                      <span>{label}</span>
                    </div>
                    <div className={`w-8 h-4 rounded-full transition-colors relative ${isEnabled ? 'bg-cyan-500' : 'bg-slate-800'}`}>
                      <div className={`w-3.5 h-3.5 rounded-full bg-slate-950 absolute top-0.5 transition-transform ${isEnabled ? 'left-4' : 'left-0.5'}`} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* YouTube Timing & Duration Sliders */}
          <div className="p-5 glass-panel space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <Clock className="w-4 h-4 text-cyber-cyan" />
              <span>Session Duration & Video Quotas</span>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Videos Per Session (Min - Max)</span>
                  <span className="font-mono text-cyan-400 font-bold">{config.SO_VIDEO_MIN} - {config.SO_VIDEO_MAX} videos</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={config.SO_VIDEO_MIN}
                    onChange={(e) => setConfig({ ...config, SO_VIDEO_MIN: parseInt(e.target.value) })}
                    className="accent-cyan-500"
                  />
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={config.SO_VIDEO_MAX}
                    onChange={(e) => setConfig({ ...config, SO_VIDEO_MAX: parseInt(e.target.value) })}
                    className="accent-cyan-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Watch Duration Per Video (Seconds)</span>
                  <span className="font-mono text-cyan-400 font-bold">
                    {config.MIN_GIAY_XEM}s - {config.MAX_GIAY_XEM}s ({Math.round(config.MIN_GIAY_XEM / 60)}m - {Math.round(config.MAX_GIAY_XEM / 60)}m)
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="range"
                    min="30"
                    max="300"
                    step="10"
                    value={config.MIN_GIAY_XEM}
                    onChange={(e) => setConfig({ ...config, MIN_GIAY_XEM: parseInt(e.target.value) })}
                    className="accent-cyan-500"
                  />
                  <input
                    type="range"
                    min="60"
                    max="600"
                    step="10"
                    value={config.MAX_GIAY_XEM}
                    onChange={(e) => setConfig({ ...config, MAX_GIAY_XEM: parseInt(e.target.value) })}
                    className="accent-cyan-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Datasets Manager */}
        <div className="space-y-6">
          {/* Google Finance Tickers Dataset */}
          <div className="p-5 glass-panel space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal-300 font-mono">
                <TrendingUp className="w-4 h-4 text-teal-400" />
                <span>Google Finance US Tickers ({(config.FINANCE_TICKERS || []).length})</span>
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. AAPL:NASDAQ, NVDA:NASDAQ, SPY:NYSEARCA"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag('FINANCE_TICKERS', newTicker, () => setNewTicker(''))}
                className="flex-1 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-teal-500"
              />
              <button
                onClick={() => addTag('FINANCE_TICKERS', newTicker, () => setNewTicker(''))}
                className="px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pt-1">
              {(config.FINANCE_TICKERS || []).map((ticker, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-dark-950 border border-teal-500/20 text-[11px] font-mono text-teal-300 flex items-center gap-1.5 group"
                >
                  <span>📈 {ticker}</span>
                  <button
                    onClick={() => removeTag('FINANCE_TICKERS', i)}
                    className="text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Search Keywords Dataset */}
          <div className="p-5 glass-panel space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
                <Tags className="w-4 h-4 text-cyber-violet" />
                <span>Search Keywords ({config.DANH_SACH_TU_KHOA.length})</span>
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Add new keyword..."
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag('DANH_SACH_TU_KHOA', newKeyword, () => setNewKeyword(''))}
                className="flex-1 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-violet-500"
              />
              <button
                onClick={() => addTag('DANH_SACH_TU_KHOA', newKeyword, () => setNewKeyword(''))}
                className="px-3 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pt-1">
              {config.DANH_SACH_TU_KHOA.map((kw, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-dark-950 border border-slate-800 text-[11px] font-mono text-slate-300 flex items-center gap-1.5 group"
                >
                  <span>{kw}</span>
                  <button
                    onClick={() => removeTag('DANH_SACH_TU_KHOA', i)}
                    className="text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Subreddits Dataset */}
          <div className="p-5 glass-panel space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <span>👽</span>
              <span>US Subreddits ({config.REDDIT_SUBREDDITS.length})</span>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. technology"
                value={newSubreddit}
                onChange={(e) => setNewSubreddit(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag('REDDIT_SUBREDDITS', newSubreddit, () => setNewSubreddit(''))}
                className="flex-1 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-amber-500"
              />
              <button
                onClick={() => addTag('REDDIT_SUBREDDITS', newSubreddit, () => setNewSubreddit(''))}
                className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pt-1">
              {config.REDDIT_SUBREDDITS.map((sub, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-dark-950 border border-amber-500/20 text-[11px] font-mono text-amber-300 flex items-center gap-1.5"
                >
                  <span>r/{sub}</span>
                  <button
                    onClick={() => removeTag('REDDIT_SUBREDDITS', i)}
                    className="text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Google Maps Queries Dataset */}
          <div className="p-5 glass-panel space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <span>🗺️</span>
              <span>Google Maps Local Queries ({config.MAPS_CITIES_QUERIES.length})</span>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="e.g. coffee shops in Brooklyn NYC"
                value={newMapsCity}
                onChange={(e) => setNewMapsCity(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addTag('MAPS_CITIES_QUERIES', newMapsCity, () => setNewMapsCity(''))}
                className="flex-1 px-3 py-1.5 rounded-xl bg-dark-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
              />
              <button
                onClick={() => addTag('MAPS_CITIES_QUERIES', newMapsCity, () => setNewMapsCity(''))}
                className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto pt-1">
              {config.MAPS_CITIES_QUERIES.map((query, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-lg bg-dark-950 border border-emerald-500/20 text-[11px] font-mono text-emerald-300 flex items-center gap-1.5"
                >
                  <span>📍 {query}</span>
                  <button
                    onClick={() => removeTag('MAPS_CITIES_QUERIES', i)}
                    className="text-slate-500 hover:text-rose-400 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
