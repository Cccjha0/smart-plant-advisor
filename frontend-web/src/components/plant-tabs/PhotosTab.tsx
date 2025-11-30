import { useState } from 'react';
import { Image as ImageIcon, X } from 'lucide-react';
import { mockPhotos } from '../../utils/mockData';

export function PhotosTab({ plantId }: { plantId: number }) {
  const [selectedPhoto, setSelectedPhoto] = useState<any>(null);

  const groupPhotosByDate = (photos: any[]) => {
    const groups: { [key: string]: any[] } = {
      '今天': [],
      '昨天': [],
      '本周': [],
      '更早': []
    };

    photos.forEach((photo) => {
      if (photo.date.includes('11-28')) groups['今天'].push(photo);
      else if (photo.date.includes('11-27')) groups['昨天'].push(photo);
      else if (photo.date.includes('11-2')) groups['本周'].push(photo);
      else groups['更早'].push(photo);
    });

    return groups;
  };

  const groupedPhotos = groupPhotosByDate(mockPhotos);

  return (
    <div className="space-y-6">
      {/* Photo Timeline */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">照片时间轴</h2>

        {Object.entries(groupedPhotos).map(([group, photos]) => (
          photos.length > 0 && (
            <div key={group} className="mb-8 last:mb-0">
              <h3 className="text-gray-700 mb-4">{group}</h3>
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
                    <p className="text-xs text-gray-600">{photo.time}</p>
                    {photo.analysisStatus && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        photo.analysisStatus === 'success'
                          ? 'bg-green-100 text-green-700'
                          : photo.analysisStatus === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {photo.analysisStatus === 'success' && '已分析'}
                        {photo.analysisStatus === 'pending' && '分析中'}
                        {photo.analysisStatus === 'failed' && '失败'}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>

      {/* Photo Detail Modal */}
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
                  <p className="text-gray-900">{selectedPhoto.date} {selectedPhoto.time}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">文件路径</p>
                  <p className="text-gray-900 text-sm">{selectedPhoto.path}</p>
                </div>
              </div>

              {selectedPhoto.analysis && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-gray-900 mb-2">LLM 视觉分析摘要</h3>
                  <p className="text-gray-700 leading-relaxed">{selectedPhoto.analysis}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
