export interface Profile {
  id: string;
  name: string;
  proxy: string;
  note: string;
  is_running: boolean;
  current_activity: string;
  current_detail: string;
  cookie_score: number;
  last_run: string;
  raw?: any;
}

export interface ProxyCheckResult {
  ok: boolean;
  proxy: string;
  ping_ms: number;
  ip: string;
  country: string;
  city: string;
  error: string;
}

export interface FarmConfig {
  GPM_API_URL: string;
  SO_LUONG_CHAY_SONG_SONG: number;
  MUI_GIO_US: string;
  TRON_PROFILES: boolean;
  SO_VIDEO_MIN: number;
  SO_VIDEO_MAX: number;
  MIN_GIAY_XEM: number;
  MAX_GIAY_XEM: number;
  SU_DUNG_GOOGLE_NEWS: boolean;
  SU_DUNG_GOOGLE_MAPS: boolean;
  SU_DUNG_REDDIT: boolean;
  SU_DUNG_WIKIPEDIA: boolean;
  TIM_KIEM_GOOGLE: boolean;
  LUOT_TWITTER: boolean;
  SU_DUNG_GOOGLE_FINANCE: boolean;
  DANH_SACH_TU_KHOA: string[];
  GOOGLE_KEYWORDS: string[];
  MAPS_CITIES_QUERIES: string[];
  REDDIT_SUBREDDITS: string[];
  WIKIPEDIA_TOPICS: string[];
  FINANCE_TICKERS: string[];
}

export interface LogMessage {
  id: string;
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'ERROR' | 'SKIP';
  text: string;
  profile: string;
}

export interface SystemStats {
  gpm_connected: boolean;
  gpm_port: number;
  us_time_est: string;
  circadian_mode: 'SLEEP' | 'ACTIVE' | 'NORMAL';
  circadian_multiplier: number;
  active_bots_count: number;
  total_profiles_count: number;
  total_videos_watched: number;
  total_news_read: number;
  total_maps_viewed: number;
  total_reddit_read: number;
  total_wiki_read: number;
  total_search_done: number;
}
