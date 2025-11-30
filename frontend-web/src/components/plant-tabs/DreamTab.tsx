import { useState } from 'react';
import { Sparkles, X } from 'lucide-react';
import { mockDreams } from '../../utils/mockData';

export function DreamTab({ plantId, plantName }: { plantId: number; plantName: string }) {
  const [selectedDream, setSelectedDream] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const plantDreams = mockDreams.filter((dream) => dream.plantId === plantId);

  const handleGenerateDream = async () => {
    setIsGenerating(true);
    // Simulate API call
    setTimeout(() => {
      setIsGenerating(false);
      alert('梦境图生成成功！');
    }, 3000);
  };

  return (
    <div className="space-y-6">
      {/* Generate Button */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900 mb-1">生成梦境花园</h2>
            <p className="text-sm text-gray-600">
              根据当前环境数据和传感器读数，为 {plantName} 生成一张独特的梦境图
            </p>
          </div>
          <button
            onClick={handleGenerateDream}
            disabled={isGenerating}
            className="flex items-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-300 text-white rounded-lg transition-colors"
          >
            <Sparkles className={`w-5 h-5 ${isGenerating ? 'animate-pulse' : ''}`} />
            <span>{isGenerating ? '生成中...' : '立即生成梦境'}</span>
          </button>
        </div>
      </div>

      {/* Dream Gallery */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">梦境画廊</h2>

        {plantDreams.length === 0 ? (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">还没有生成梦境图</p>
            <p className="text-sm text-gray-400 mt-1">点击上方按钮生成第一张梦境图</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {plantDreams.map((dream) => (
              <div
                key={dream.id}
                onClick={() => setSelectedDream(dream)}
                className="cursor-pointer group"
              >
                <div className="aspect-square bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 rounded-lg mb-3 overflow-hidden">
                  <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Sparkles className="w-12 h-12 text-purple-400" />
                  </div>
                </div>
                <p className="text-sm text-gray-900 mb-1">{dream.timestamp}</p>
                <p className="text-xs text-gray-500 line-clamp-2">{dream.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Dream Detail Modal */}
      {selectedDream && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Sparkles className="w-6 h-6 text-purple-500" />
                <h2 className="text-gray-900">梦境详情</h2>
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
                <p className="text-sm text-gray-500 mb-1">生成时间</p>
                <p className="text-gray-900">{selectedDream.timestamp}</p>
              </div>

              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-2">生成时环境参数</p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">温度</p>
                    <p className="text-lg text-gray-900">{selectedDream.environment.temperature}°C</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">湿度</p>
                    <p className="text-lg text-gray-900">{selectedDream.environment.moisture}%</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">光照</p>
                    <p className="text-lg text-gray-900">{selectedDream.environment.light} lux</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">体重</p>
                    <p className="text-lg text-gray-900">{selectedDream.environment.weight}g</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                <h3 className="text-gray-900 mb-2">梦境描述</h3>
                <p className="text-gray-700 leading-relaxed">{selectedDream.description}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
