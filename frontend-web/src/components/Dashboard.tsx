import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, Activity, AlertTriangle, Image, Search, TrendingUp, TrendingDown, Minus, Sparkles } from 'lucide-react';
import { api, AlertDto, DashboardOverview, Plant, DreamDto, AnalysisDto, MetricsDto } from '../utils/api';

export function Dashboard() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [plants, setPlants] = useState<Plant[]>([]);
  const [analysisMap, setAnalysisMap] = useState<Record<number, AnalysisDto | null>>({});
  const [metricsMap, setMetricsMap] = useState<Record<number, MetricsDto | null>>({});
  const [dreamMap, setDreamMap] = useState<Record<number, DreamDto | null>>({});
  const [stats, setStats] = useState<DashboardOverview | null>(null);
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [dreams, setDreams] = useState<(DreamDto & { nickname?: string | null })[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, plantsRes, alertsRes] = await Promise.all([
          api.getDashboardOverview().catch(() => null),
          api.getPlants().catch(() => []),
          api.getAlerts(10).catch(() => []),
        ]);
        setStats(statsRes);
        setPlants(plantsRes || []);
        setAlerts(alertsRes || []);

        const firstPlants = (plantsRes || []).slice(0, 4);
        const dreamLists = await Promise.all(
          firstPlants.map((p) =>
            api.getDreamsByPlant(p.id)
              .then((ds) => ds.map((d) => ({ ...d, nickname: p.nickname })))
              .catch(() => []),
          ),
        );
        const merged = dreamLists
          .flat()
          .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
          .slice(0, 4);
        setDreams(merged);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    const loadPerPlantData = async () => {
      if (!plants.length) {
        setAnalysisMap({});
        setMetricsMap({});
        setDreamMap({});
        return;
      }
      const entries = await Promise.all(
        plants.map(async (p) => {
          const [analysis, metrics, dreams] = await Promise.all([
            api.getAnalysis(p.id).catch(() => null),
            api.getMetrics(p.id).catch(() => null),
            api.getDreamsByPlant(p.id).catch(() => [] as DreamDto[]),
          ]);
          return {
            id: p.id,
            analysis,
            metrics,
            dream: dreams[0] ?? null,
          };
        }),
      );

      setAnalysisMap(Object.fromEntries(entries.map((e) => [e.id, e.analysis])));
      setMetricsMap(Object.fromEntries(entries.map((e) => [e.id, e.metrics])));
      setDreamMap(Object.fromEntries(entries.map((e) => [e.id, e.dream])));
    };
    loadPerPlantData();
  }, [plants]);

  const filteredPlants = useMemo(() => {
    return plants.filter((plant) => {
      const nickname = plant.nickname || '';
      const species = plant.species || '';
      const matchesSearch =
        nickname.toLowerCase().includes(searchTerm.toLowerCase()) ||
        species.toLowerCase().includes(searchTerm.toLowerCase());
      const status = mapGrowthStatus(analysisMap[plant.id]?.growth_status);
      const matchesFilter = filterStatus === 'all' || status === filterStatus;
      return matchesSearch && matchesFilter;
    });
  }, [plants, searchTerm, filterStatus, analysisMap]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'slightly_stressed':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'stressed':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'slightly_stressed':
        return 'Mild stress';
      case 'stressed':
        return 'Severe stress';
      default:
        return 'Not enough data';
    }
  };

  const getGrowthIcon = (rate: number) => {
    if (rate > 0.5) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (rate < -0.5) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  const timeAgo = (iso?: string | null) => {
    if (!iso) return '—';
    const normalized = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`;
    const ts = new Date(normalized).getTime();
    if (Number.isNaN(ts)) return '—';
    const diffSec = Math.max(0, (Date.now() - ts) / 1000);
    if (diffSec < 60) return 'just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} minutes ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hours ago`;
    const days = Math.floor(diffSec / 86400);
    if (days < 30) return `${days} days ago`;
    return new Date(iso).toLocaleDateString();
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-gray-900 mb-8">System Overview</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Leaf className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">Total plants</p>
            <p className="text-3xl text-gray-900">{stats?.total_plants ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">Active plants (24h)</p>
            <p className="text-3xl text-gray-900">{stats?.active_last_24h ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">Abnormal plants</p>
            <p className="text-3xl text-gray-900">{stats?.abnormal_plants ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Image className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">Dreams today</p>
            <p className="text-3xl text-gray-900">{stats?.dreams_generated_today ?? '—'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-gray-900 mb-4">Plant list</h2>

                <div className="flex gap-4 mb-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="搜索植物昵称或种类..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>

                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                <option value="all">All statuses</option>
                    <option value="healthy">All statuses</option>
                    <option value="slightly_stressed">Mild stress</option>
                    <option value="stressed">Severe stress</option>
                    <option value="unknown">Not enough data</option>
                  </select>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {loading && <div className="p-6 text-gray-500">Loading...</div>}
                {!loading && filteredPlants.length === 0 && (
                  <div className="p-6 text-gray-500">No plants</div>
                )}
                {filteredPlants.map((plant) => {
                  const analysis = analysisMap[plant.id];
                  const status = mapGrowthStatus(analysis?.growth_status);
                  const growthRate =
                    typeof analysis?.growth_rate_3d === 'number' && Number.isFinite(analysis.growth_rate_3d)
                      ? analysis.growth_rate_3d
                      : null;
                  const metrics = metricsMap[plant.id];
                  const dream = dreamMap[plant.id];
                  const latestTimestamp =
                    metrics?.meta?.last_sensor_timestamp ||
                    metrics?.weight?.weight_at ||
                    metrics?.temperature?.temp_at ||
                    metrics?.soil_moisture?.soil_at ||
                    metrics?.light?.light_at;
                  const latestDataText = metrics
                    ? `${timeAgo(latestTimestamp)} · ${metrics.temperature.temp_now ?? '—'}°C / ${metrics.soil_moisture.soil_now ?? '—'}% / ${metrics.weight.weight_now ?? '—'}g`
                    : '—';
                  const latestDreamText = dream?.created_at ? timeAgo(dream.created_at) : '—';
                  return (
                    <div
                      key={plant.id}
                      onClick={() => navigate(`/plants/${plant.id}`)}
                      className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <Leaf className="w-6 h-6 text-green-600" />
                          </div>
                          <div>
                            <h3 className="text-gray-900">{plant.nickname || 'Unnamed'}</h3>
                            <p className="text-sm text-gray-500">{plant.species || 'Species not set'}</p>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(status)}`}>
                          {getStatusText(status)}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Latest data</p>
                          <p className="text-gray-900">{latestDataText}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Latest dream</p>
                          <p className="text-gray-900">{latestDreamText}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Growth rate</p>
                          <div className="flex items-center gap-1">
                            {getGrowthIcon(growthRate ?? 0)}
                            <span className="text-gray-900">
                              {growthRate != null ? `${growthRate.toFixed(1)}%` : '—'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-gray-900 mb-4">Recent alerts</h2>
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div key={alert.id} className="flex gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-900">{alert.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{new Date(alert.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
                {!alerts.length && !loading && <p className="text-sm text-gray-500">No alerts</p>}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-gray-900 mb-4">Recent dreams</h2>
              <div className="grid grid-cols-2 gap-3">
                {dreams.map((dream) => (
                  <div
                    key={dream.id}
                    onClick={() => navigate('/dreams')}
                    className="cursor-pointer group"
                  >
                    <div className="aspect-square bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg mb-2 overflow-hidden">
                      {dream.file_path ? (
                        <img
                          src={dream.file_path}
                          alt="dream"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition-transform">
                          <Sparkles className="w-8 h-8 text-purple-400" />
                        </div>
                      )}
                    </div>
                    <p className="text-xs text-gray-600">{dream.nickname || `Plant #${dream.plant_id}`}</p>
                    <p className="text-xs text-gray-400">{new Date(dream.created_at).toLocaleString()}</p>
                  </div>
                ))}
                {!dreams.length && !loading && (
                  <p className="text-sm text-gray-500 col-span-2">No dream images yet</p>
                )}
              </div>
              <button
                onClick={() => navigate('/dreams')}
                className="w-full mt-4 px-4 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
              >
                View all dreams
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
  const mapGrowthStatus = (status: string | null | undefined) => {
    switch (status) {
      case 'normal':
        return 'healthy';
      case 'slow':
      case 'stagnant':
        return 'slightly_stressed';
      case 'stressed':
        return 'stressed';
      default:
        return 'unknown';
    }
  };
