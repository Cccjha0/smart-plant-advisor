import { useEffect, useMemo, useState } from 'react';
import { Search, Filter, Sparkles, X } from 'lucide-react';
import { api, DreamDto, Plant } from '../utils/api';

type FilterState = {
  plantId: string;
  query: string;
};

export function DreamGallery() {
  const [dreams, setDreams] = useState<DreamDto[]>([]);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [filter, setFilter] = useState<FilterState>({ plantId: 'all', query: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const plantList = await api.getPlants().catch(() => []);
        setPlants(plantList || []);
        const dreamList: DreamDto[] = [];
        for (const p of plantList || []) {
          const d = await api.getDreamsByPlant(p.id).catch(() => []);
          dreamList.push(...d);
        }
        dreamList.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
        setDreams(dreamList);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredDreams = useMemo(() => {
    return dreams.filter((d) => {
      const matchesPlant = filter.plantId === 'all' || d.plant_id === Number(filter.plantId);
      const matchesQuery = filter.query
        ? (d.description || '').toLowerCase().includes(filter.query.toLowerCase())
        : true;
      return matchesPlant && matchesQuery;
    });
  }, [dreams, filter]);

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-gray-900">梦境画廊</h1>
            <p className="text-gray-600">跨植物浏览所有梦境花园图片</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索描述关键字…"
                value={filter.query}
                onChange={(e) => setFilter((f) => ({ ...f, query: e.target.value }))}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-600" />
              <select
                value={filter.plantId}
                onChange={(e) => setFilter((f) => ({ ...f, plantId: e.target.value }))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="all">全部植物</option>
                {plants.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nickname || `Plant #${p.id}`}
                  </option>
                ))}
              </select>
              {filter.plantId !== 'all' && (
                <button
                  onClick={() => setFilter((f) => ({ ...f, plantId: 'all' }))}
                  className="p-2 text-sm text-gray-600 hover:text-gray-900"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          {loading && <p className="text-gray-500">加载中...</p>}
          {!loading && filteredDreams.length === 0 && <p className="text-gray-500">暂无梦境图片</p>}

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredDreams.map((dream) => (
              <div key={dream.id} className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
                <div className="aspect-square bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
                  <Sparkles className="w-10 h-10 text-purple-400" />
                </div>
                <div className="p-3">
                  <p className="text-sm text-gray-900 mb-1">
                    {plants.find((p) => p.id === dream.plant_id)?.nickname || `Plant #${dream.plant_id}`}
                  </p>
                  <p className="text-xs text-gray-500">{new Date(dream.created_at).toLocaleString()}</p>
                  {dream.description && <p className="text-xs text-gray-600 mt-1 line-clamp-2">{dream.description}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
