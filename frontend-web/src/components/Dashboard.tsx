import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Leaf, Activity, AlertTriangle, Image, Search, TrendingUp, TrendingDown, Minus, Sparkles } from 'lucide-react';
import { api, AlertDto, DashboardOverview, Plant, DreamDto } from '../utils/api';

export function Dashboard() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [plants, setPlants] = useState<Plant[]>([]);
  const [stats, setStats] = useState<DashboardOverview | null>(null);
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [dreams, setDreams] = useState<DreamDto[]>([]);
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

        const firstIds = (plantsRes || []).slice(0, 4).map((p) => p.id);
        const dreamLists = await Promise.all(firstIds.map((id) => api.getDreamsByPlant(id).catch(() => [])));
        const merged = dreamLists.flat().sort((a, b) => (b.created_at || '').localeCompare(a.created_at || '')).slice(0, 4);
        setDreams(merged);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredPlants = useMemo(() => {
    return plants.filter((plant) => {
      const nickname = plant.nickname || '';
      const species = plant.species || '';
      const matchesSearch =
        nickname.toLowerCase().includes(searchTerm.toLowerCase()) ||
        species.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterStatus === 'all';
      return matchesSearch && matchesFilter;
    });
  }, [plants, searchTerm, filterStatus]);

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
        return '健康';
      case 'slightly_stressed':
        return '轻微压力';
      case 'stressed':
        return '严重压力';
      default:
        return '数据不足';
    }
  };

  const getGrowthIcon = (rate: number) => {
    if (rate > 0.5) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (rate < -0.5) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-gray-900 mb-8">系统总览</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Leaf className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">总植物数</p>
            <p className="text-3xl text-gray-900">{stats?.total_plants ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">24h 活跃植物</p>
            <p className="text-3xl text-gray-900">{stats?.active_last_24h ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">异常状态植物</p>
            <p className="text-3xl text-gray-900">{stats?.abnormal_plants ?? '—'}</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Image className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-1">今日生成梦境</p>
            <p className="text-3xl text-gray-900">{stats?.dreams_generated_today ?? '—'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-gray-900 mb-4">植物列表</h2>

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
                    <option value="all">全部状态</option>
                  </select>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {loading && <div className="p-6 text-gray-500">加载中...</div>}
                {!loading && filteredPlants.length === 0 && (
                  <div className="p-6 text-gray-500">暂无植物</div>
                )}
                {filteredPlants.map((plant) => (
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
                          <h3 className="text-gray-900">{plant.nickname || '未命名'}</h3>
                          <p className="text-sm text-gray-500">{plant.species || '未填写种类'}</p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor('unknown')}`}>
                        {getStatusText('unknown')}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">最近数据</p>
                        <p className="text-gray-900">—</p>
                      </div>
                      <div>
                        <p className="text-gray-500">最近梦境</p>
                        <p className="text-gray-900">—</p>
                      </div>
                      <div>
                        <p className="text-gray-500">生长率</p>
                        <div className="flex items-center gap-1">
                          {getGrowthIcon(0)}
                          <span className="text-gray-900">—</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-gray-900 mb-4">最近异常提醒</h2>
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
                {!alerts.length && !loading && <p className="text-sm text-gray-500">暂无提醒</p>}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-gray-900 mb-4">近期梦境预览</h2>
              <div className="grid grid-cols-2 gap-3">
                {dreams.map((dream) => (
                  <div
                    key={dream.id}
                    onClick={() => navigate('/dreams')}
                    className="cursor-pointer group"
                  >
                    <div className="aspect-square bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg mb-2 overflow-hidden">
                      <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Sparkles className="w-8 h-8 text-purple-400" />
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">Plant #{dream.plant_id}</p>
                    <p className="text-xs text-gray-400">{new Date(dream.created_at).toLocaleString()}</p>
                  </div>
                ))}
                {!dreams.length && !loading && (
                  <p className="text-sm text-gray-500 col-span-2">暂无梦境图片</p>
                )}
              </div>
              <button
                onClick={() => navigate('/dreams')}
                className="w-full mt-4 px-4 py-2 text-sm text-green-700 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
              >
                查看全部梦境
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
