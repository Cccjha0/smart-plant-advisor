import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Droplets, Thermometer, Sun, Weight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api, AnalysisDto, DailyMetric, Plant } from '../../utils/api';

export function OverviewTab({ plant }: { plant: Plant }) {
  const [analysis, setAnalysis] = useState<AnalysisDto | null>(null);
  const [dailyMetrics, setDailyMetrics] = useState<DailyMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [latestSuggestions, setLatestSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [a, m, reports] = await Promise.all([
          api.getAnalysis(plant.id).catch(() => null),
          api.getMetricsDaily7d(plant.id).catch(() => ({ metrics: [] })),
          api.getReports(plant.id, 1).catch(() => []),
        ]);
        setAnalysis(a);
        setDailyMetrics(m.metrics || []);
        const firstReport = Array.isArray(reports) ? reports[0] : null;
        const sugg = firstReport?.suggestions;
        const suggList = Array.isArray(sugg)
          ? sugg
          : typeof sugg === 'string'
            ? sugg.split('\n').map((s) => s.trim()).filter(Boolean)
            : [];
        setLatestSuggestions(suggList);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [plant.id]);

  const mapGrowthStatus = (status: string | null | undefined) => {
    switch (status) {
      case 'normal':
        return 'healthy';
      case 'slow':
      case 'stagnant':
        return 'slightly_stressed';
      case 'stressed':
        return 'stressed';
      default:
        return 'unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'slightly_stressed':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'stressed':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'slightly_stressed':
        return 'Mild stress';
      case 'stressed':
        return 'Severe stress';
      default:
        return 'Not enough data';
    }
  };

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Plant growth looks good. All indicators are normal. Keep the current routine.';
      case 'slightly_stressed':
        return 'Plant is under mild stress. Check soil moisture and light, and adjust watering frequency as needed.';
      case 'stressed':
        return 'Plant is under high stress. Inspect roots, soil condition, and environment immediately.';
      default:
        return 'Recent data is insufficient to assess. Ensure sensors are working.';
    }
  };

  const lineDataWeight = useMemo(
    () => dailyMetrics.map((m) => ({ time: m.date, value: m.weight })),
    [dailyMetrics]
  );
  const lineDataMoisture = useMemo(
    () => dailyMetrics.map((m) => ({ time: m.date, value: m.soil_moisture })),
    [dailyMetrics]
  );
  const lineDataTemp = useMemo(
    () => dailyMetrics.map((m) => ({ time: m.date, value: m.temperature })),
    [dailyMetrics]
  );
  const lineDataLight = useMemo(
    () => dailyMetrics.map((m) => ({ time: m.date, value: m.light })),
    [dailyMetrics]
  );

  const status = mapGrowthStatus(analysis?.growth_status);

  if (loading) {
    return <div className="text-gray-500">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Plant Info Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-4">Plant Info</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500 mb-1">Nickname</p>
            <p className="text-gray-900">{plant.nickname || 'Unnamed'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Species</p>
            <p className="text-gray-900">{plant.species || 'Species not set'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Created at</p>
            <p className="text-gray-900">
              {plant.created_at ? new Date(plant.created_at).toLocaleString() : '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Last watering</p>
            <p className="text-gray-900">
              {plant.last_watered_at ? new Date(plant.last_watered_at).toLocaleString() : '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Status & Suggestions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-4">Current status & tips</h2>

        <div className="flex items-start gap-4 mb-4">
          <AlertCircle className="w-6 h-6 text-gray-400 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-gray-700">Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(status)}`}>
                {getStatusText(status)}
              </span>
            </div>
            <p className="text-gray-600 leading-relaxed">{getStatusMessage(status)}</p>
          </div>
        </div>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900 mb-2">💡 Today’s suggestion</p>
          {latestSuggestions.length ? (
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              {latestSuggestions.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-blue-800">No latest suggestion yet; waiting for new analysis.</p>
          )}
        </div>
      </div>

      {/* 7-Day Metrics */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">Key metrics (7 days)</h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weight Trend */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Weight className="w-5 h-5 text-gray-600" />
              <h3 className="text-gray-900">Weight trend</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={lineDataWeight}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Moisture Trend */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Droplets className="w-5 h-5 text-blue-600" />
              <h3 className="text-gray-900">Soil moisture</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={lineDataMoisture}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Temperature Trend */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Thermometer className="w-5 h-5 text-red-600" />
              <h3 className="text-gray-900">Temperature</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={lineDataTemp}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Light Trend */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sun className="w-5 h-5 text-yellow-600" />
              <h3 className="text-gray-900">Light intensity</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={lineDataLight}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
