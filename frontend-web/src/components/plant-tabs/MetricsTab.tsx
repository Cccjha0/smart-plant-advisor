import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Calendar, Download } from 'lucide-react';
import { mockDetailedMetrics, mockGrowthAnalysis } from '../../utils/mockData';

export function MetricsTab({ plantId }: { plantId: string }) {
  const [timeRange, setTimeRange] = useState('7d');
  const [visibleLines, setVisibleLines] = useState({
    temperature: true,
    light: true,
    moisture: true,
    weight: true
  });

  const toggleLine = (key: keyof typeof visibleLines) => {
    setVisibleLines((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-600" />
            <h2 className="text-gray-900">时间区间选择</h2>
          </div>
          <div className="flex gap-2">
            {['24h', '3d', '7d', '30d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  timeRange === range
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {range === '24h' && '24小时'}
                {range === '3d' && '3天'}
                {range === '7d' && '7天'}
                {range === '30d' && '30天'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Multi-dimensional Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-gray-900">多维度数据图表</h2>
          <div className="flex gap-3">
            {Object.entries(visibleLines).map(([key, visible]) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={visible}
                  onChange={() => toggleLine(key as keyof typeof visibleLines)}
                  className="w-4 h-4 text-green-600 rounded focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 capitalize">{key}</span>
              </label>
            ))}
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={mockDetailedMetrics}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} stroke="#9ca3af" />
            <YAxis yAxisId="left" tick={{ fontSize: 12 }} stroke="#9ca3af" />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} stroke="#9ca3af" />
            <Tooltip />
            <Legend />
            {visibleLines.temperature && (
              <Line yAxisId="left" type="monotone" dataKey="temperature" stroke="#ef4444" strokeWidth={2} dot={false} name="温度 (°C)" />
            )}
            {visibleLines.light && (
              <Line yAxisId="right" type="monotone" dataKey="light" stroke="#f59e0b" strokeWidth={2} dot={false} name="光照 (lux)" />
            )}
            {visibleLines.moisture && (
              <Line yAxisId="left" type="monotone" dataKey="moisture" stroke="#3b82f6" strokeWidth={2} dot={false} name="湿度 (%)" />
            )}
            {visibleLines.weight && (
              <Line yAxisId="right" type="monotone" dataKey="weight" stroke="#10b981" strokeWidth={2} dot={false} name="重量 (g)" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Growth Analysis Visualization */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">生长算法可视化</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Reference Weight */}
          <div>
            <h3 className="text-gray-900 mb-4">日参考体重</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={mockGrowthAnalysis.dailyWeight}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={2} name="实际重量" />
                <Line type="monotone" dataKey="reference" stroke="#6366f1" strokeWidth={2} strokeDasharray="5 5" name="参考重量" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 3-Day Growth Rate */}
          <div>
            <h3 className="text-gray-900 mb-4">3日生长率</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={mockGrowthAnalysis.growthRate}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Legend />
                <Bar dataKey="rate" fill="#10b981" name="生长率 (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stress Factors */}
        <div className="mt-6">
          <h3 className="text-gray-900 mb-4">压力因子分析</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {mockGrowthAnalysis.stressFactors.map((factor, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">{factor.name}</p>
                <div className="flex items-end gap-2">
                  <p className="text-2xl text-gray-900">{factor.value.toFixed(1)}</p>
                  <p className="text-sm text-gray-500 mb-1">/ {factor.max}</p>
                </div>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      factor.value < factor.max * 0.3 ? 'bg-green-500' :
                      factor.value < factor.max * 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(factor.value / factor.max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Raw Data Table */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-gray-900">原始数据表格</h2>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            <span className="text-sm">导出 CSV</span>
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm text-gray-700">时间戳</th>
                <th className="px-6 py-3 text-left text-sm text-gray-700">传感器类型</th>
                <th className="px-6 py-3 text-left text-sm text-gray-700">原始值</th>
                <th className="px-6 py-3 text-left text-sm text-gray-700">单位</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {mockDetailedMetrics.slice(0, 10).map((metric, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">{metric.timestamp}</td>
                  <td className="px-6 py-4 text-sm text-gray-700">Temperature</td>
                  <td className="px-6 py-4 text-sm text-gray-900">{metric.temperature}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">°C</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
