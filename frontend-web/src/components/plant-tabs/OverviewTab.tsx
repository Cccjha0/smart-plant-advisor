import { AlertCircle, Droplets, Thermometer, Sun, Weight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { mockMetricsData } from '../../utils/mockData';

interface Plant {
  id: string;
  nickname: string;
  species: string;
  status: string;
  createdAt: string;
  lastWatering: string;
}

export function OverviewTab({ plant }: { plant: Plant }) {
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
        return '健康';
      case 'slightly_stressed':
        return '轻微压力';
      case 'stressed':
        return '严重压力';
      default:
        return '数据不足';
    }
  };

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'healthy':
        return '植物生长状态良好，各项指标正常。继续保持当前的养护节奏。';
      case 'slightly_stressed':
        return '植物处于轻微压力状态，建议检查土壤湿度和光照条件。可能需要适当调整浇水频率。';
      case 'stressed':
        return '植物处于较大压力状态，需要立即检查。建议检查根系健康、土壤状态和环境因素。';
      default:
        return '近期数据不足，无法做出准确评估。请确保传感器正常工作。';
    }
  };

  return (
    <div className="space-y-6">
      {/* Plant Info Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-4">植物信息</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500 mb-1">植物昵称</p>
            <p className="text-gray-900">{plant.nickname}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">植物种类</p>
            <p className="text-gray-900">{plant.species}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">创建时间</p>
            <p className="text-gray-900">{plant.createdAt}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">最近浇水</p>
            <p className="text-gray-900">{plant.lastWatering}</p>
          </div>
        </div>
      </div>

      {/* Status & Suggestions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-4">当前状态 & 建议</h2>
        
        <div className="flex items-start gap-4 mb-4">
          <AlertCircle className="w-6 h-6 text-gray-400 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-gray-700">状态评估：</span>
              <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(plant.status)}`}>
                {getStatusText(plant.status)}
              </span>
            </div>
            <p className="text-gray-600 leading-relaxed">
              {getStatusMessage(plant.status)}
            </p>
          </div>
        </div>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900 mb-2">💡 今日建议</p>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>保持当前的浇水节奏，每3-4天浇水一次</li>
            <li>确保植物接收充足的散射光，避免强光直射</li>
            <li>定期检查土壤湿度，保持适度湿润</li>
          </ul>
        </div>
      </div>

      {/* 7-Day Metrics */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-gray-900 mb-6">近 7 天关键指标</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weight Trend */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Weight className="w-5 h-5 text-gray-600" />
              <h3 className="text-gray-900">重量趋势</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mockMetricsData.weight}>
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
              <h3 className="text-gray-900">土壤湿度</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mockMetricsData.moisture}>
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
              <h3 className="text-gray-900">温度变化</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mockMetricsData.temperature}>
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
              <h3 className="text-gray-900">光照强度</h3>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={mockMetricsData.light}>
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
