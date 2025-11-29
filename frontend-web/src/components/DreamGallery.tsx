import { useState } from 'react';
import { Search, Filter, Sparkles, X } from 'lucide-react';
import { mockDreams, mockPlants } from '../utils/mockData';

export function DreamGallery() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPlant, setFilterPlant] = useState('all');
  const [selectedDream, setSelectedDream] = useState<any>(null);

  const filteredDreams = mockDreams.filter((dream) => {
    const plant = mockPlants.find((p) => p.id === dream.plantId);
    const matchesSearch = plant?.nickname.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterPlant === 'all' || dream.plantId === filterPlant;
    return matchesSearch && matchesFilter;
  });

  const getPlantName = (plantId: string) => {
    return mockPlants.find((p) => p.id === plantId)?.nickname || 'Unknown';
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">梦境画廊</h1>
          <p className="text-gray-600">探索所有植物的梦境花园图片</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="搜索植物昵称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-600" />
              <select
                value={filterPlant}
                onChange={(e) => setFilterPlant(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">全部植物</option>
                {mockPlants.map((plant) => (
                  <option key={plant.id} value={plant.id}>
                    {plant.nickname}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Gallery */}
        {filteredDreams.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">没有找到匹配的梦境图</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {filteredDreams.map((dream) => (
              <div
                key={dream.id}
                onClick={() => setSelectedDream(dream)}
                className="cursor-pointer group"
              >
                <div className="aspect-square bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 rounded-xl mb-3 overflow-hidden shadow-md hover:shadow-xl transition-shadow">
                  <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Sparkles className="w-12 h-12 text-purple-400" />
                  </div>
                </div>
                <h3 className="text-gray-900 mb-1">{getPlantName(dream.plantId)}</h3>
                <p className="text-sm text-gray-500 mb-2">{dream.timestamp}</p>
                <p className="text-xs text-gray-600 line-clamp-2">{dream.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Dream Detail Modal */}
        {selectedDream && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-6 h-6 text-purple-500" />
                  <div>
                    <h2 className="text-gray-900">{getPlantName(selectedDream.plantId)} 的梦境</h2>
                    <p className="text-sm text-gray-500">{selectedDream.timestamp}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedDream(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6">
                <div className="aspect-video bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 rounded-lg mb-6 flex items-center justify-center">
                  <Sparkles className="w-32 h-32 text-purple-400" />
                </div>

                <div className="mb-6">
                  <p className="text-sm text-gray-500 mb-2">生成时环境快照</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">温度</p>
                      <p className="text-xl text-gray-900">{selectedDream.environment.temperature}°C</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">湿度</p>
                      <p className="text-xl text-gray-900">{selectedDream.environment.moisture}%</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">光照</p>
                      <p className="text-xl text-gray-900">{selectedDream.environment.light} lux</p>
                    </div>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">体重</p>
                      <p className="text-xl text-gray-900">{selectedDream.environment.weight}g</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <h3 className="text-gray-900 mb-2">完整梦境描述</h3>
                  <p className="text-gray-700 leading-relaxed">{selectedDream.description}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
