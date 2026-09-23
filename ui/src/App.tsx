import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar, TabType } from './components/Sidebar';
import { DashboardView } from './views/DashboardView';
import { ProfilesView } from './views/ProfilesView';
import { LiveTelemetryView } from './views/LiveTelemetryView';
import { StrategyStudioView } from './views/StrategyStudioView';
import { AnalyticsView } from './views/AnalyticsView';

import { api } from './services/api';
import { useTelemetryWebSocket } from './services/websocket';
import { SystemStats, Profile, FarmConfig } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [config, setConfig] = useState<FarmConfig | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { isConnected: wsConnected, logs, clearLogs } = useTelemetryWebSocket();

  const fetchData = useCallback(async () => {
    try {
      const [statsData, profilesData, configData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getProfiles().catch(() => []),
        api.getConfig().catch(() => null),
      ]);

      if (statsData) setStats(statsData);
      if (profilesData) setProfiles(profilesData);
      if (configData) setConfig(configData);
    } catch (e) {
      // Background fetch error handled
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchData();
    setTimeout(() => setIsRefreshing(false), 400);
  };

  useEffect(() => {
    fetchData();
    // Poll stats & profiles every 3 seconds for live progress
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartAll = async () => {
    const allIds = profiles.map((p) => p.id);
    await api.startProfiles(allIds, 3);
    fetchData();
  };

  const handleStopAll = async () => {
    await api.stopProfiles([]);
    fetchData();
  };

  const handleStartProfiles = async (ids: string[]) => {
    await api.startProfiles(ids, 3);
    fetchData();
  };

  const handleStopProfiles = async (ids: string[]) => {
    await api.stopProfiles(ids);
    fetchData();
  };

  const activeBotsCount = profiles.filter((p) => p.is_running).length;

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Top Header */}
      <Header
        stats={stats}
        wsConnected={wsConnected}
        onStartAll={handleStartAll}
        onStopAll={handleStopAll}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      <div className="flex-1 flex">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          activeBotsCount={activeBotsCount}
        />

        {/* Main Content Workspace */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <DashboardView
              stats={stats}
              profiles={profiles}
              onStartFarm={(ids, loops) => {
                api.startProfiles(ids, loops);
                fetchData();
              }}
              onStopBot={(id) => handleStopProfiles([id])}
            />
          )}

          {activeTab === 'profiles' && (
            <ProfilesView
              profiles={profiles}
              onStartProfiles={handleStartProfiles}
              onStopProfiles={handleStopProfiles}
              onRefresh={fetchData}
            />
          )}

          {activeTab === 'telemetry' && (
            <LiveTelemetryView
              logs={logs}
              onClearLogs={clearLogs}
              wsConnected={wsConnected}
            />
          )}

          {activeTab === 'strategy' && (
            <StrategyStudioView
              initialConfig={config}
              profiles={profiles}
              onConfigSaved={fetchData}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsView stats={stats} profiles={profiles} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
