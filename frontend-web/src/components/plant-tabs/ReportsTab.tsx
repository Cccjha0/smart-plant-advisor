import { useEffect, useMemo, useState } from 'react';
import { FileText, RefreshCw, Copy, Check } from 'lucide-react';
import { api } from '../../utils/api';

type ReportItem = {
  id: number;
  summary: string;
  content: string;
  suggestions?: string | string[];
  environment?: string;
  timestamp: string;
  trigger: 'scheduled' | 'watering' | 'manual' | 'default' | 'history' | 'unknown';
};

export function ReportsTab({ plantId }: { plantId: number }) {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const loadReports = async () => {
    try {
      const res = await api.getReports(plantId, 20);
      const items: ReportItem[] = (res || []).map((r: any) => ({
        id: r.id,
        summary: r.growth_overview || '报告',
        content: r.full_analysis || r.growth_overview || '暂无内容',
        suggestions: r.suggestions,
        environment: r.environment_assessment,
        timestamp: r.created_at || new Date().toISOString(),
        trigger: (r.trigger as ReportItem['trigger']) || 'history',
      }));
      setReports(items);
      setSelectedReport(items[0] || null);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadReports();
  }, [plantId]);

  const fetchReport = async () => {
    try {
      const res = await api.getReport(plantId);
      const now = new Date().toISOString();
      const item: ReportItem = {
        id: res.analysis_result_id || Date.now(),
        summary: res.report?.growth_overview || '报告',
        content: res.report?.full_analysis || res.report?.growth_overview || '暂无内容',
        suggestions: res.report?.suggestions,
        environment: res.report?.environment_assessment,
        timestamp: now,
        trigger: (res.report?.trigger as ReportItem['trigger']) || 'manual',
      };
      setReports([item, ...reports]);
      setSelectedReport(item);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    await fetchReport();
    setIsGenerating(false);
  };

  const handleCopy = () => {
    if (!selectedReport) return;
    navigator.clipboard.writeText(selectedReport.content || '');
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
      case 'history':
        return 'bg-gray-100 text-gray-700 border-gray-200';
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
      case 'history':
        return '历史记录';
      default:
        return '未知';
    }
  };

  const reportList = useMemo(() => reports, [reports]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
              <span>{isGenerating ? '生成中...' : '生成最新报告'}</span>
            </button>
          </div>

          <div className="divide-y divide-gray-200">
            {reportList.map((report) => (
              <div
                key={report.id}
                onClick={() => setSelectedReport(report)}
                className={`p-4 cursor-pointer transition-colors ${
                  selectedReport?.id === report.id ? 'bg-green-50' : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 mb-1 line-clamp-2">{report.summary || '报告'}</p>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${getTriggerBadgeColor(report.trigger)}`}>
                        {getTriggerText(report.trigger)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{new Date(report.timestamp).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            ))}
            {!reportList.length && <div className="p-4 text-sm text-gray-500">暂无报告，生成一个试试</div>}
          </div>
        </div>
      </div>

      <div className="lg:col-span-2">
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-gray-900 mb-1">报告详情</h2>
              <p className="text-sm text-gray-500">
                {selectedReport ? new Date(selectedReport.timestamp).toLocaleString() : '暂无报告'}
              </p>
            </div>
            <button
              onClick={handleCopy}
              disabled={!selectedReport}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
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
            {selectedReport ? (
              <div className="prose max-w-none">
                <div className="mb-6">
                  <h3 className="text-gray-900 mb-2">今日生长情况概览</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {selectedReport.summary || selectedReport.content || '暂无内容'}
                  </p>
                </div>

                <div className="mb-6">
                  <h3 className="text-gray-900 mb-2">环境状态评价</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {selectedReport.environment || '暂无环境描述'}
                  </p>
                </div>

                <div className="mb-6">
                  <h3 className="text-gray-900 mb-2">建议</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <ul className="text-gray-700 space-y-2 list-disc list-inside">
                      {(Array.isArray(selectedReport.suggestions)
                        ? selectedReport.suggestions
                        : (selectedReport.suggestions || '').split('\n')
                      ).filter(Boolean).map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                      {!selectedReport.suggestions && <li>暂无建议</li>}
                    </ul>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 mb-2">完整分析内容：</p>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {selectedReport.content || '暂无内容'}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">暂无报告</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
