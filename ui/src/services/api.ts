import axios from 'axios';
import { Profile, ProxyCheckResult, FarmConfig, SystemStats } from '../types';

// Dynamic API URL: when served from FastAPI it uses relative origin, otherwise defaults to localhost:8000
const API_BASE = window.location.port === '5173' 
  ? 'http://127.0.0.1:8000/api' 
  : '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

export const api = {
  getHealth: async () => {
    const res = await client.get('/health');
    return res.data;
  },

  getStats: async (): Promise<SystemStats> => {
    const res = await client.get('/system/stats');
    return res.data;
  },

  getProfiles: async (): Promise<Profile[]> => {
    const res = await client.get('/profiles');
    return res.data;
  },

  startProfiles: async (profileIds: string[] = [], loopCount: number = 1, proxy?: string) => {
    const res = await client.post('/profiles/start', {
      profile_ids: profileIds,
      loop_count: loopCount,
      proxy: proxy || null,
    });
    return res.data;
  },

  stopProfiles: async (profileIds: string[] = []) => {
    const res = await client.post('/profiles/stop', {
      profile_ids: profileIds,
    });
    return res.data;
  },

  updateProxy: async (profileId: string, proxy: string) => {
    const res = await client.post('/profiles/proxy/update', {
      profile_id: profileId,
      proxy,
    });
    return res.data;
  },

  checkProxy: async (proxy: string): Promise<ProxyCheckResult> => {
    const res = await client.post('/profiles/proxy/check', { proxy });
    return res.data;
  },

  getConfig: async (): Promise<FarmConfig> => {
    const res = await client.get('/config');
    return res.data;
  },

  updateConfig: async (config: FarmConfig) => {
    const res = await client.post('/config', config);
    return res.data;
  },
};
