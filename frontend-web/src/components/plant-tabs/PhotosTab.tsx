import { useEffect, useMemo, useState } from 'react';
import { Image as ImageIcon, X } from 'lucide-react';
import { api } from '../../utils/api';

type PhotoItem = {
  id: number;
  plant_id: number;
  file_path: string;
  captured_at: string;
  plant_type?: string | null;
  leaf_health?: string | null;
  symptoms?: any;
};

export function PhotosTab({ plantId }: { plantId: number }) {
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoItem | null>(null);
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadedIds, setLoadedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    const load = async () => {
      try {
        const list = await api.getImagesByPlant(plantId).catch(() => []);
        setPhotos(list || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [plantId]);

  const groupedList = useMemo(() => {
    const pad = (n: number) => String(n).padStart(2, '0');
    const grouped = photos.reduce<Record<string, { label: string; items: PhotoItem[] }>>((acc, item) => {
      const dateObj = new Date(item.captured_at);
      const key = `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())}`; // 本地日期
      const label = `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())} (${dateObj.toLocaleDateString('zh-CN', { weekday: 'short' })})`;

      if (!acc[key]) {
        acc[key] = { label, items: [] };
      }
      acc[key].items.push(item);
      return acc;
    }, {});

    return Object.entries(grouped)
      .sort(([a], [b]) => (a > b ? -1 : 1)) // 按日期倒序
      .map(([, value]) => ({
        ...value,
        items: value.items.sort((a, b) => (a.captured_at > b.captured_at ? -1 : 1)),
      }));
  }, [photos]);

  const handleImageLoad = (id: number) => {
    setLoadedIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">照片时间轴</h2>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">加载中...</p>
          </div>
        ) : groupedList.length === 0 ? (
          <div className="text-center py-12">
            <ImageIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">暂无照片</p>
          </div>
        ) : (
          <div className="space-y-28 relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-200" />
            {groupedList.map((group, groupIndex) => (
              <div key={group.label} className="relative pl-10 pb-4">
                <div className="mb-4">
                  <p className="text-sm text-black">{group.label}</p>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {group.items.map((photo) => (
                    <div
                      key={`${groupIndex}-${photo.id}`}
                      onClick={() => setSelectedPhoto(photo)}
                      className="cursor-pointer group"
                    >
                      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-2 relative">
                        {!loadedIds.has(photo.id) && (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <ImageIcon className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                        <img
                          src={photo.file_path}
                          alt={photo.plant_type || 'photo'}
                          className={`w-full h-full object-cover transition-opacity duration-300 ${
                            loadedIds.has(photo.id) ? 'opacity-100' : 'opacity-0'
                          }`}
                          loading="lazy"
                          onLoad={() => handleImageLoad(photo.id)}
                          onError={() => handleImageLoad(photo.id)}
                        />
                      </div>
                      <p className="text-xs text-gray-600">
                        {new Date(photo.captured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      {/* 类型信息不再展示 */}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedPhoto && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-gray-900">图片详情</h2>
              <button
                onClick={() => setSelectedPhoto(null)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="aspect-video bg-gray-100 rounded-lg mb-6 flex items-center justify-center overflow-hidden">
                <img
                  src={selectedPhoto.file_path}
                  alt={selectedPhoto.plant_type || 'photo'}
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">拍摄时间</p>
                  <p className="text-gray-900 text-sm">{new Date(selectedPhoto.captured_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">文件路径</p>
                  <p className="text-gray-900 text-sm break-all">{selectedPhoto.file_path}</p>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
