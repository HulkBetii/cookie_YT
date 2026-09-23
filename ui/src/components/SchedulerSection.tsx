import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Calendar, 
  Play, 
  Trash2, 
  Plus, 
  Sun, 
  Moon, 
  Coffee, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  Power
} from 'lucide-react';
import { api } from '../services/api';
import { ScheduleJob, CreateScheduleInput, Profile } from '../types';

interface SchedulerSectionProps {
  profiles: Profile[];
  onNotify?: (msg: string, type: 'success' | 'error') => void;
}

export const SchedulerSection: React.FC<SchedulerSectionProps> = ({ profiles, onNotify }) => {
  const [schedules, setSchedules] = useState<ScheduleJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [scheduleType, setScheduleType] = useState<'us_preset' | 'daily_time' | 'interval'>('us_preset');
  const [presetName, setPresetName] = useState<'us_morning' | 'us_afternoon' | 'us_evening'>('us_evening');
  const [timeStr, setTimeStr] = useState('20:00');
  const [intervalMinutes, setIntervalMinutes] = useState(120);
  const [timezoneMode, setTimezoneMode] = useState<'US_EST' | 'LOCAL'>('US_EST');
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [loopCount, setLoopCount] = useState(1);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const data = await api.getSchedules();
      setSchedules(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules();
    const timer = setInterval(loadSchedules, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      let finalName = name.trim();
      if (!finalName) {
        if (scheduleType === 'us_preset') {
          if (presetName === 'us_morning') finalName = 'US Morning Routine (09:00 AM EST)';
          else if (presetName === 'us_afternoon') finalName = 'US Afternoon Break (02:00 PM EST)';
          else finalName = 'US Prime Time (08:00 PM EST)';
        } else if (scheduleType === 'daily_time') {
          finalName = `Daily at ${timeStr} (${timezoneMode})`;
        } else {
          finalName = `Repeat Every ${intervalMinutes} Mins`;
        }
      }

      const payload: CreateScheduleInput = {
        name: finalName,
        schedule_type: scheduleType,
        preset_name: presetName,
        time_str: timeStr,
        interval_minutes: Number(intervalMinutes),
        timezone_mode: timezoneMode,
        profile_ids: selectedProfiles,
        loop_count: Number(loopCount),
        enabled: true,
      };

      await api.createSchedule(payload);
      if (onNotify) onNotify(`Đã tạo lịch hẹn "${finalName}" thành công!`, 'success');
      setIsCreating(false);
      setName('');
      loadSchedules();
    } catch (e: any) {
      if (onNotify) onNotify(`Lỗi khi tạo lịch: ${e.message}`, 'error');
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await api.toggleSchedule(id);
      loadSchedules();
    } catch (e: any) {
      if (onNotify) onNotify(`Không thể đổi trạng thái: ${e.message}`, 'error');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Bạn có chắc muốn xóa lịch hẹn này?')) return;
    try {
      await api.deleteSchedule(id);
      if (onNotify) onNotify('Đã xóa lịch hẹn', 'success');
      loadSchedules();
    } catch (e: any) {
      if (onNotify) onNotify(`Lỗi khi xóa: ${e.message}`, 'error');
    }
  };

  const handleRunNow = async (id: string) => {
    try {
      await api.runScheduleNow(id);
      if (onNotify) onNotify('Đã kích hoạt chạy lịch hẹn ngay lập tức!', 'success');
      loadSchedules();
    } catch (e: any) {
      if (onNotify) onNotify(`Lỗi khi kích hoạt: ${e.message}`, 'error');
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 text-indigo-400">
              <Calendar className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              Cron Scheduler Studio
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-medium">
                US Time Sync
              </span>
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Lập lịch chạy tự động theo múi giờ US EST/EDT hoặc định kỳ để tối ưu Cookie Trust Score
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadSchedules}
            disabled={loading}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition border border-slate-800"
            title="Refresh Schedules"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsCreating(!isCreating)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            {isCreating ? 'Đóng Form' : 'Tạo Lịch Mới'}
          </button>
        </div>
      </div>

      {/* Creation Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreate} className="bg-slate-950/80 border border-indigo-500/30 rounded-xl p-5 space-y-5 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Thiết lập Lịch Chạy Mới
            </h3>
            <span className="text-xs text-slate-400">Auto-calculated EST Time</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Schedule Type */}
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Phương thức kích hoạt (Trigger Type)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setScheduleType('us_preset')}
                  className={`p-3 rounded-xl border flex flex-col items-start gap-1 transition ${
                    scheduleType === 'us_preset' 
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200' 
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="font-medium text-sm flex items-center gap-1.5">
                    🇺🇸 Khung Giờ Vàng US
                  </span>
                  <span className="text-xs opacity-75">9h Sáng, 2h Chiều, 8h Tối EST</span>
                </button>

                <button
                  type="button"
                  onClick={() => setScheduleType('daily_time')}
                  className={`p-3 rounded-xl border flex flex-col items-start gap-1 transition ${
                    scheduleType === 'daily_time' 
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200' 
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="font-medium text-sm flex items-center gap-1.5">
                    ⏰ Giờ Cố Định (Daily)
                  </span>
                  <span className="text-xs opacity-75">Chạy 1 lần mỗi ngày</span>
                </button>

                <button
                  type="button"
                  onClick={() => setScheduleType('interval')}
                  className={`p-3 rounded-xl border flex flex-col items-start gap-1 transition ${
                    scheduleType === 'interval' 
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-200' 
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="font-medium text-sm flex items-center gap-1.5">
                    🔄 Lặp Định Kỳ (Interval)
                  </span>
                  <span className="text-xs opacity-75">Sau mỗi N phút / giờ</span>
                </button>
              </div>
            </div>

            {/* US Presets Selector */}
            {scheduleType === 'us_preset' && (
              <div className="space-y-2 md:col-span-2">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Chọn Khung Giờ Sinh Học US (EST)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div
                    onClick={() => setPresetName('us_morning')}
                    className={`cursor-pointer p-3 rounded-xl border flex items-center gap-3 transition ${
                      presetName === 'us_morning' 
                        ? 'bg-amber-500/20 border-amber-500/60 text-amber-200' 
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <Sun className="w-5 h-5 text-amber-400 shrink-0" />
                    <div>
                      <div className="text-sm font-semibold">09:00 AM EST</div>
                      <div className="text-xs opacity-75">Bắt đầu ngày làm việc Mỹ</div>
                    </div>
                  </div>

                  <div
                    onClick={() => setPresetName('us_afternoon')}
                    className={`cursor-pointer p-3 rounded-xl border flex items-center gap-3 transition ${
                      presetName === 'us_afternoon' 
                        ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-200' 
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <Coffee className="w-5 h-5 text-cyan-400 shrink-0" />
                    <div>
                      <div className="text-sm font-semibold">02:00 PM EST</div>
                      <div className="text-xs opacity-75">Nghỉ trưa / Đầu giờ chiều</div>
                    </div>
                  </div>

                  <div
                    onClick={() => setPresetName('us_evening')}
                    className={`cursor-pointer p-3 rounded-xl border flex items-center gap-3 transition ${
                      presetName === 'us_evening' 
                        ? 'bg-purple-500/20 border-purple-500/60 text-purple-200' 
                        : 'bg-slate-900 border-slate-800 text-slate-400'
                    }`}
                  >
                    <Moon className="w-5 h-5 text-purple-400 shrink-0" />
                    <div>
                      <div className="text-sm font-semibold">08:00 PM EST</div>
                      <div className="text-xs opacity-75">Cao điểm xem YouTube tối</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Daily Time Input */}
            {scheduleType === 'daily_time' && (
              <>
                <div className="space-y-1.5">
                  <label className="text-xs text-slate-300 font-medium">Giờ chạy (HH:MM)</label>
                  <input
                    type="time"
                    value={timeStr}
                    onChange={(e) => setTimeStr(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-indigo-500 outline-none"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs text-slate-300 font-medium">Múi Giờ</label>
                  <select
                    value={timezoneMode}
                    onChange={(e: any) => setTimezoneMode(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-indigo-500 outline-none"
                  >
                    <option value="US_EST">Giờ Mỹ (America/New_York - EST/EDT)</option>
                    <option value="LOCAL">Giờ Hệ Thống Máy Tính (Local Time)</option>
                  </select>
                </div>
              </>
            )}

            {/* Interval Minutes Input */}
            {scheduleType === 'interval' && (
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-xs text-slate-300 font-medium">Khoảng cách lặp lại (Phút)</label>
                <div className="flex gap-3">
                  <input
                    type="number"
                    min="15"
                    max="1440"
                    value={intervalMinutes}
                    onChange={(e) => setIntervalMinutes(Number(e.target.value))}
                    className="flex-1 px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-indigo-500 outline-none"
                  />
                  <div className="flex gap-2">
                    {[60, 120, 240, 360].map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => setIntervalMinutes(m)}
                        className={`px-3 py-2 text-xs rounded-xl border transition ${
                          intervalMinutes === m ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-900 border-slate-800 text-slate-400'
                        }`}
                      >
                        {m / 60} tiếng
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Profile Selection & Loop */}
            <div className="space-y-1.5">
              <label className="text-xs text-slate-300 font-medium">Target Profiles</label>
              <select
                value={selectedProfiles.length === 0 ? 'ALL' : selectedProfiles[0]}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedProfiles(val === 'ALL' ? [] : [val]);
                }}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-indigo-500 outline-none"
              >
                <option value="ALL">🌐 Chạy Tất Cả Profiles ({profiles.length})</option>
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    👤 {p.name} ({p.proxy ? p.proxy.split(':')[0] : 'No proxy'})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-slate-300 font-medium">Số vòng lặp / Session</label>
              <input
                type="number"
                min="1"
                max="50"
                value={loopCount}
                onChange={(e) => setLoopCount(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-indigo-500 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-medium transition"
            >
              Hủy
            </button>
            <button
              type="submit"
              className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-sm font-semibold shadow-md transition"
            >
              Lưu Lịch Trình
            </button>
          </div>
        </form>
      )}

      {/* Schedules List */}
      <div className="space-y-3">
        {schedules.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-800 rounded-xl text-slate-500 text-sm">
            Chưa có lịch hẹn nào được thiết lập. Bấm <strong>"Tạo Lịch Mới"</strong> để kích hoạt tự động theo giờ Mỹ.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {schedules.map((job) => (
              <div
                key={job.id}
                className={`p-4 rounded-xl border transition relative group ${
                  job.enabled
                    ? 'bg-slate-950/60 border-slate-800 hover:border-indigo-500/40'
                    : 'bg-slate-950/30 border-slate-900 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${job.enabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                      <h4 className="text-sm font-semibold text-slate-200">{job.name}</h4>
                    </div>

                    <div className="text-xs text-slate-400 space-y-0.5 pt-1">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Chạy tiếp theo: <strong className="text-indigo-300">{job.next_run || 'Pending'}</strong></span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-slate-500" />
                        <span>Lần chạy gần nhất: {job.last_run || 'Never'}</span>
                      </div>
                      <div className="text-slate-500 text-[11px] pt-1">
                        Target: {job.profile_ids.length === 0 ? 'Tất cả profiles' : `${job.profile_ids.length} profiles`} • {job.loop_count} vòng lặp
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => handleToggle(job.id)}
                      className={`p-2 rounded-lg border transition ${
                        job.enabled
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                          : 'bg-slate-800 border-slate-700 text-slate-500 hover:bg-slate-700'
                      }`}
                      title={job.enabled ? 'Đang BẬT (Click để tắt)' : 'Đang TẮT (Click để bật)'}
                    >
                      <Power className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleRunNow(job.id)}
                      className="p-2 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20 rounded-lg transition"
                      title="Chạy ngay lập tức (Run Now)"
                    >
                      <Play className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleDelete(job.id)}
                      className="p-2 bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 rounded-lg transition"
                      title="Xóa lịch"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
