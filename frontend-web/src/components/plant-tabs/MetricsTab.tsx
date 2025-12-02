import { useEffect, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { Calendar, Download } from 'lucide-react';
import { api, HourlyMetric, DailyMetric, RawDataResponse } from '../../utils/api';

export function MetricsTab({ plantId }: { plantId: number }) {
  const [timeRange, setTimeRange] = useState<'24h' | '3d' | '7d'>('7d');
  const [visibleLines, setVisibleLines] = useState({
    temperature: true,
    light: true,
    moisture: true,
    weight: true,
  });
  const [daily, setDaily] = useState<DailyMetric[]>([]);
  const [hourly, setHourly] = useState<HourlyMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [rawSensor, setRawSensor] = useState<'temperature' | 'soil_moisture' | 'light' | 'weight'>('temperature');
  const [rawData, setRawData] = useState<RawDataResponse | null>(null);
  const [rawLoading, setRawLoading] = useState(false);
  const [stressScores, setStressScores] = useState<Record<string, number> | null>(null);
  const [growthRateSeries, setGrowthRateSeries] = useState<{ date: string; growth_rate_pct: number | null }[]>([]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [d7, h24, analytics] = await Promise.all([
          api.getMetricsDaily7d(plantId).catch(() => ({ metrics: [] })),
          api.getMetricsHourly24h(plantId).catch(() => ({ metrics: [] })),
          api.getGrowthAnalytics(plantId).catch(() => null),
        ]);
        setDaily(d7.metrics || []);
        setHourly(h24.metrics || []);
        setStressScores(analytics?.stress_scores ?? null);
        setGrowthRateSeries(analytics?.growth_rate_3d || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [plantId]);

  useEffect(() => {
    const loadRaw = async () => {
      setRawLoading(true);
      try {
        const resp = await api.getRawData(plantId, rawSensor, 1, 25).catch(() => null);
        setRawData(resp);
      } finally {
        setRawLoading(false);
      }
    };
    loadRaw();
  }, [plantId, rawSensor]);

  const defaultUnit: Record<typeof rawSensor, string> = {
    temperature: '°C',
    soil_moisture: '%',
    light: 'lux',
    weight: 'g',
  };

  const formatValue = (v: number | null) => {
    if (v === null || v === undefined) return '-';
    if (typeof v === 'number' && Number.isFinite(v)) return v.toFixed(2);
    return `${v}`;
  };

  const formatUnit = (u?: string | null) => {
    if (!u) return '';
    return u.replace('Â', '');
  };

  const toggleLine = (key: keyof typeof visibleLines) => {
    setVisibleLines((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const chartData = useMemo(() => {
    if (timeRange === '24h') {
      return hourly.map((m) => ({
        time: m.hour,
        temperature: m.temperature,
        light: m.light,
        moisture: m.soil_moisture,
        weight: m.weight,
      }));
    }
    // 3d/7d 都用 daily-7d（前端裁剪）
    const limit = timeRange === '3d' ? 3 : 7;
    return daily.slice(-limit).map((m) => ({
      time: m.date,
      temperature: m.temperature,
      light: m.light,
      moisture: m.soil_moisture,
      weight: m.weight,
    }));
  }, [timeRange, hourly, daily]);

  const growthRateData = useMemo(() => {
    return (growthRateSeries || [])
      .map((item) => ({ date: item.date, rate: item.growth_rate_pct }))
      .filter((d) => d.rate != null);
  }, [growthRateSeries]);

  const stressFactors = useMemo(() => {
    const scoreFor = (key: string) => {
      const value = stressScores?.[key];
      return typeof value === 'number' && Number.isFinite(value) ? value : 0;
    };

    return [
      { name: '温度压力', value: scoreFor('temperature'), max: 10 },
      { name: '湿度压力', value: scoreFor('humidity'), max: 10 },
      { name: '光照压力', value: scoreFor('light'), max: 10 },
      { name: '生长压力', value: scoreFor('growth'), max: 10 },
    ];
  }, [stressScores]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-600" />
            <h2 className="text-gray-900">时间区间选择</h2>
          </div>
          <div className="flex gap-2">
            {['24h', '3d', '7d'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range as '24h' | '3d' | '7d')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  timeRange === range
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {range === '24h' && '24小时'}
                {range === '3d' && '3天'}
                {range === '7d' && '7天'}
              </button>
            ))}
          </div>
        </div>
      </div>

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

        {loading ? (
          <p className="text-gray-500">加载中...</p>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#9ca3af" />
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
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">生长算法可视化</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h3 className="text-gray-900 mb-4">日参考体重</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="weight" stroke="#10b981" strokeWidth={2} name="平均重量" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="text-gray-900 mb-4">3日生长率</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={growthRateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Legend />
                <Bar dataKey="rate" fill="#10b981" name="增长率(%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-gray-900 mb-4">压力因子分析</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stressFactors.map((factor, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">{factor.name}</p>
                <div className="flex items-end gap-2">
                  <p className="text-2xl text-gray-900">{factor.value.toFixed(1)}</p>
                  <p className="text-sm text-gray-500 mb-1">/ 10</p>
                </div>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      factor.value < factor.max * 0.3
                        ? 'bg-green-500'
                        : factor.value < factor.max * 0.7
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                    }`}
                    style={{ width: `${(factor.value / factor.max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-gray-900">原始数据表格</h2>
            <select
              value={rawSensor}
              onChange={(e) => setRawSensor(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="temperature">温度</option>
              <option value="soil_moisture">土壤湿度</option>
              <option value="light">光照</option>
              <option value="weight">重量</option>
            </select>
          </div>
          <button
            onClick={async () => {
              try {
                const csv = await api.exportRawDataCsv(plantId, rawSensor);
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `plant-${plantId}-${rawSensor}-raw.csv`;
                a.click();
                URL.revokeObjectURL(url);
              } catch (e) {
                console.error(e);
              }
            }}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">导出 CSV</span>
          </button>
        </div>
        <div className="p-6">
          {rawLoading ? (
            <p className="text-sm text-gray-500">加载中...</p>
          ) : !rawData || rawData.records.length === 0 ? (
            <p className="text-sm text-gray-500">暂无数据</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full table-fixed text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="py-3 px-2 text-gray-600 w-1/3">时间</th>
                    <th className="py-3 px-2 text-gray-600 w-1/3">值</th>
                    <th className="py-3 px-2 text-gray-600 w-1/3">单位</th>
                  </tr>
                </thead>
                <tbody>
                  {rawData.records.map((rec, idx) => (
                    <tr key={idx} className="border-b border-gray-50">
                      <td className="py-2 px-2 text-gray-900 w-1/3">
                        {rec.time_label || new Date(rec.timestamp).toLocaleString()}
                      </td>
                      <td className="py-2 px-2 text-gray-900 w-1/3">{formatValue(rec.value)}</td>
                      <td className="py-2 px-2 text-gray-500 w-1/3">
                        {formatUnit(rawData.unit || defaultUnit[rawSensor] || '')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
