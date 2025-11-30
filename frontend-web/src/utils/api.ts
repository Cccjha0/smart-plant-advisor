const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export type DashboardOverview = {
  total_plants: number;
  active_last_24h: number;
  abnormal_plants: number;
  dreams_generated_today: number;
};

export type SystemOverview = {
  total_plants: number;
  total_images: number;
  total_sensor_records: number;
  total_analysis_results: number;
  total_dream_images: number;
};

export type Plant = {
  id: number;
  nickname: string | null;
  species: string | null;
};

export type AlertDto = {
  id: number;
  plant_id?: number | null;
  analysis_result_id?: number | null;
  message: string;
  created_at: string;
};

export type DreamDto = {
  id: number;
  plant_id: number;
  file_path: string;
  description: string | null;
  created_at: string;
};

export type MetricsDto = {
  temperature: {
    temp_now: number | null;
    temp_6h_avg: number | null;
    temp_24h_min: number | null;
    temp_24h_max: number | null;
  };
  soil_moisture: {
    soil_now: number | null;
    soil_24h_min: number | null;
    soil_24h_max: number | null;
    soil_24h_trend: number | null;
  };
  light: {
    light_now: number | null;
    light_1h_avg: number | null;
    light_today_sum: number | null;
  };
  weight: {
    weight_now: number | null;
    weight_24h_diff: number | null;
    water_loss_per_hour: number | null;
    hours_since_last_watering: number | null;
    weight_drop_since_last_watering: number | null;
  };
};

export type AnalysisDto = {
  plant_id: number;
  growth_status: string | null;
  growth_rate_3d: number | null;
  sensor_summary_7d?: {
    avg_temperature?: number | null;
    avg_light?: number | null;
    avg_soil_moisture?: number | null;
  };
};

export type SchedulerJobDto = {
  id: string;
  name: string;
  description: string;
  schedule: string;
  status: 'running' | 'paused';
  nextRun: string | null;
};

export type SchedulerLogDto = {
  id: number;
  jobKey: string;
  jobName: string | null;
  status: string;
  message: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  durationSeconds: number | null;
};

export const api = {
  getDashboardOverview: async () => {
    // Try dashboard view first; fallback to system overview if unavailable
    try {
      return await fetchJson<DashboardOverview>('/dashboard/system-overview');
    } catch (_err) {
      const sys = await fetchJson<any>('/system/overview');
      return {
        total_plants: sys.total_plants ?? 0,
        active_last_24h: sys.total_plants ?? 0,
        abnormal_plants: 0,
        dreams_generated_today: 0, // fallback cannot compute "today", keep zero to avoid overcount
      };
    }
  },
  getSystemOverview: () => fetchJson<SystemOverview>('/system/overview'),
  getPlants: () => fetchJson<Plant[]>('/plants'),
  getAlerts: (limit = 20) => fetchJson<AlertDto[]>(`/alerts?limit=${limit}`),
  getDreamsByPlant: (plantId: number) => fetchJson<DreamDto[]>(`/dreams/${plantId}`),
  getMetrics: (plantId: number) => fetchJson<MetricsDto>(`/metrics/${plantId}`),
  getAnalysis: (plantId: number) => fetchJson<AnalysisDto>(`/analysis/${plantId}`),
  getAdminStats: () => fetchJson<any>('/admin/stats'),
  getSchedulerJobs: () => fetchJson<SchedulerJobDto[]>('/scheduler/jobs'),
  getSchedulerLogs: (limit = 50) => fetchJson<SchedulerLogDto[]>(`/scheduler/logs?limit=${limit}`),
};
