import { useEffect, useState } from 'react';
import { Image as ImageIcon, X } from 'lucide-react';
import { api, DreamDto } from '../../utils/api';

export function PhotosTab({ plantId }: { plantId: number }) {
  const [selectedPhoto, setSelectedPhoto] = useState<DreamDto | null>(null);
  const [photos, setPhotos] = useState<DreamDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        // 暂无独立 images 列表接口，先复用 dream images 作为占位
        const list = await api.getDreamsByPlant(plantId).catch(() => []);
        setPhotos(list || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [plantId]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">照片时间轴</h2>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">加载中...</p>
          </div>
        ) : photos.length === 0 ? (
          <div className="text-center py-12">
            <ImageIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">暂无照片</p>
            <p className="text-sm text-gray-400 mt-1">后端无 images 列表接口，暂用梦境图占位</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {photos.map((photo) => (
              <div
                key={photo.id}
                onClick={() => setSelectedPhoto(photo)}
                className="cursor-pointer group"
              >
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-2">
                  <div className="w-full h-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <ImageIcon className="w-12 h-12 text-gray-400" />
                  </div>
                </div>
                <p className="text-xs text-gray-600">{new Date(photo.created_at).toLocaleString()}</p>
                <p className="text-xs text-gray-500 line-clamp-2">{photo.description || '暂无描述'}</p>
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
              <div className="aspect-video bg-gray-100 rounded-lg mb-6 flex items-center justify-center">
                <ImageIcon className="w-24 h-24 text-gray-400" />
              </div>

              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">拍摄时间</p>
                  <p className="text-gray-900 text-sm">{new Date(selectedPhoto.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">文件路径</p>
                  <p className="text-gray-900 text-sm break-all">{selectedPhoto.file_path}</p>
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="text-gray-900 mb-2">描述</h3>
                <p className="text-gray-700 leading-relaxed">{selectedPhoto.description || '暂无描述'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
