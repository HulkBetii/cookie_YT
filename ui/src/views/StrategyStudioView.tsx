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
  CheckCircle2
} from 'lucide-react';
import { FarmConfig } from '../types';
import { api } from '../services/api';

interface StrategyStudioViewProps {
  initialConfig: FarmConfig | null;
  onConfigSaved: () => void;
}

export const StrategyStudioView: React.FC<StrategyStudioViewProps> = ({
  initialConfig,
  onConfigSaved,
}) => {
  const [config, setConfig] = useState<FarmConfig | null>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New tag inputs
  const [newKeyword, setNewKeyword] = useState('');
  const [newSubreddit, setNewSubreddit] = useState('');
  const [newMapsCity, setNewMapsCity] = useState('');
  const [newWikiTopic, setNewWikiTopic] = useState('');

  useEffect(() => {
    if (initialConfig) setConfig(initialConfig);
  }, [initialConfig]);

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
      onConfigSaved();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      alert('Lỗi lưu cấu hình');
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
      {/* Top Header & Save Button */}
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
          className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/30 active:scale-95 transition-all disabled:opacity-50"
        >
          {saveSuccess ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-white" />
              <span>Saved!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
            </>
          )}
        </button>
      </div>

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Activity Modules & Video Durations */}
        <div className="space-y-6">
          {/* Active Modules Toggles */}
          <div className="p-5 glass-panel space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <Layers className="w-4 h-4 text-cyber-emerald" />
              <span>Ecosystem Modules (Active Toggles)</span>
            </div>

            <div className="space-y-3 pt-1">
              {[
                { key: 'SU_DUNG_GOOGLE_MAPS', label: 'Google Maps US (Local Trust & Geolocation Signals)', icon: '🗺️' },
                { key: 'SU_DUNG_REDDIT', label: 'Reddit US (Browse Communities & Trigger Google Ads)', icon: '👽' },
                { key: 'SU_DUNG_WIKIPEDIA', label: 'Wikipedia EN (Rabbit-hole Surfing & Knowledge Graph)', icon: '📚' },
                { key: 'SU_DUNG_GOOGLE_NEWS', label: 'Google News US (Read Partner Publications)', icon: '📰' },
                { key: 'TIM_KIEM_GOOGLE', label: 'Google Search US (Organic SERP & /goto Redirects)', icon: '🔍' },
                { key: 'LUOT_TWITTER', label: 'Twitter / X US (Social Trust Signals)', icon: '🐦' },
                { key: 'SU_DUNG_GOOGLE_FINANCE', label: 'Google Finance (Stock Watch & Market Tickers)', icon: '📈' },
              ].map((item) => {
                const isEnabled = config[item.key as keyof FarmConfig] as boolean;
                return (
                  <label
                    key={item.key}
                    className="flex items-center justify-between p-3 rounded-xl bg-dark-950/60 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{item.icon}</span>
                      <span className="text-xs font-medium text-slate-200">{item.label}</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          [item.key]: e.target.checked,
                        })
                      }
                      className="w-4 h-4 rounded bg-dark-900 border-slate-700 text-emerald-500 focus:ring-0 focus:outline-none"
                    />
                  </label>
                );
              })}
            </div>
          </div>

          {/* YouTube Video Timing Sliders */}
          <div className="p-5 glass-panel space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
              <Clock className="w-4 h-4 text-cyber-rose" />
              <span>YouTube Video Watch Time & Counts</span>
            </div>

            <div className="space-y-4 pt-1">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Videos Per Session (Min - Max)</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {config.SO_VIDEO_MIN} - {config.SO_VIDEO_MAX} videos
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={config.SO_VIDEO_MIN}
                    onChange={(e) => setConfig({ ...config, SO_VIDEO_MIN: parseInt(e.target.value) })}
                    className="accent-emerald-500"
                  />
                  <input
                    type="range"
                    min="2"
                    max="10"
                    value={config.SO_VIDEO_MAX}
                    onChange={(e) => setConfig({ ...config, SO_VIDEO_MAX: parseInt(e.target.value) })}
                    className="accent-emerald-500"
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

            <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto pt-1">
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

            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pt-1">
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

            <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pt-1">
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
