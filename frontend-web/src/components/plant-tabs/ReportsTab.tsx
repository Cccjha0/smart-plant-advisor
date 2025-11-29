import { useState } from 'react';
import { FileText, RefreshCw, Copy, Check } from 'lucide-react';
import { mockReports } from '../../utils/mockData';

export function ReportsTab({ plantId }: { plantId: string }) {
  const [selectedReport, setSelectedReport] = useState(mockReports[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    // Simulate API call
    setTimeout(() => {
      setIsGenerating(false);
      alert('报告生成成功！');
    }, 2000);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(selectedReport.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getTriggerBadgeColor = (trigger: string) => {
    switch (trigger) {
      case 'scheduled':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'watering':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'manual':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getTriggerText = (trigger: string) => {
    switch (trigger) {
      case 'scheduled':
        return '定时任务';
      case 'watering':
        return '浇水后';
      case 'manual':
        return '手动触发';
      default:
        return '未知';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Report List */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-gray-900 mb-4">报告列表</h2>
            <button
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
              <span>{isGenerating ? '生成中...' : '重新生成今日报告'}</span>
            </button>
          </div>

          <div className="divide-y divide-gray-200">
            {mockReports.map((report) => (
              <div
                key={report.id}
                onClick={() => setSelectedReport(report)}
                className={`p-4 cursor-pointer transition-colors ${
                  selectedReport.id === report.id ? 'bg-green-50' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 mb-1">{report.summary}</p>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${getTriggerBadgeColor(report.trigger)}`}>
                        {getTriggerText(report.trigger)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{report.timestamp}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Report Detail */}
      <div className="lg:col-span-2">
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-gray-900 mb-1">报告详情</h2>
              <p className="text-sm text-gray-500">{selectedReport.timestamp}</p>
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-green-600">已复制</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span className="text-sm">复制内容</span>
                </>
              )}
            </button>
          </div>

          <div className="p-6">
            <div className="prose max-w-none">
              <div className="mb-6">
                <h3 className="text-gray-900 mb-2">今日生长情况概述</h3>
                <p className="text-gray-700 leading-relaxed">
                  {selectedReport.content.split('\n\n')[0]}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="text-gray-900 mb-2">环境状态评价</h3>
                <p className="text-gray-700 leading-relaxed">
                  {selectedReport.content.split('\n\n')[1]}
                </p>
              </div>

              <div className="mb-6">
                <h3 className="text-gray-900 mb-2">建议</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <ul className="text-gray-700 space-y-2 list-disc list-inside">
                    <li>建议在今天傍晚时分进行浇水，用量约200ml</li>
                    <li>观察叶片状态，如有黄化迹象需要及时处理</li>
                    <li>保持环境通风，避免病虫害</li>
                    <li>下次施肥建议在7天后进行</li>
                  </ul>
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-2">完整分析内容：</p>
                <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {selectedReport.content}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
