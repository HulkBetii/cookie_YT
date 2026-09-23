import axios from 'axios';
import { Profile, ProxyCheckResult, FarmConfig, SystemStats, ScheduleJob, CreateScheduleInput } from '../types';

// Dynamic API URL: when served from FastAPI it uses relative origin, otherwise defaults to localhost:8088
const API_BASE = window.location.port === '5173' 
  ? 'http://127.0.0.1:8088/api' 
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

  // ── Scheduler APIs ────────────────────────────────────────────────
  getSchedules: async (): Promise<ScheduleJob[]> => {
    const res = await client.get('/schedules');
    return res.data;
  },

  createSchedule: async (data: CreateScheduleInput): Promise<ScheduleJob> => {
    const res = await client.post('/schedules', data);
    return res.data;
  },

  toggleSchedule: async (jobId: string): Promise<ScheduleJob> => {
    const res = await client.put(`/schedules/${jobId}/toggle`);
    return res.data;
  },

  deleteSchedule: async (jobId: string) => {
    const res = await client.delete(`/schedules/${jobId}`);
    return res.data;
  },

  runScheduleNow: async (jobId: string) => {
    const res = await client.post(`/schedules/${jobId}/run-now`);
    return res.data;
  },
};
