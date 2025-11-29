import { useState } from 'react';
import { Database, Activity, Calendar, Play, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { mockAdminStats, mockSchedulerJobs, mockSchedulerLogs } from '../utils/mockData';

export function Admin() {
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);

  const handleRunAnalysisAll = async () => {
    setIsRunningAnalysis(true);
    // Simulate API call
    setTimeout(() => {
      setIsRunningAnalysis(false);
      alert('所有植物分析完成！');
    }, 3000);
  };

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'paused':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'stopped':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getLogStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">系统管理</h1>
          <p className="text-gray-600">监控系统状态和调度任务</p>
        </div>

        {/* System Overview */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-gray-900 mb-6">系统概况</h2>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-8">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-700 mb-1">总植物数</p>
              <p className="text-3xl text-green-900">{mockAdminStats.totalPlants}</p>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-700 mb-1">图像总数</p>
              <p className="text-3xl text-blue-900">{mockAdminStats.totalImages}</p>
            </div>
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="text-sm text-purple-700 mb-1">传感器记录</p>
              <p className="text-3xl text-purple-900">{mockAdminStats.totalSensorRecords}</p>
            </div>
            <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-sm text-orange-700 mb-1">分析结果</p>
              <p className="text-3xl text-orange-900">{mockAdminStats.totalAnalysisResults}</p>
            </div>
            <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
              <p className="text-sm text-pink-700 mb-1">梦境图总数</p>
              <p className="text-3xl text-pink-900">{mockAdminStats.totalDreams}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
            <Activity className={`w-6 h-6 ${mockAdminStats.schedulerRunning ? 'text-green-600' : 'text-red-600'}`} />
            <div>
              <p className="text-gray-900">APScheduler 状态</p>
              <p className={`text-sm ${mockAdminStats.schedulerRunning ? 'text-green-600' : 'text-red-600'}`}>
                {mockAdminStats.schedulerRunning ? '运行中' : '已停止'}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Registered Jobs */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-5 h-5 text-gray-600" />
                <h2 className="text-gray-900">已注册的定时任务</h2>
              </div>
              <p className="text-sm text-gray-600">当前系统中运行的所有调度任务</p>
            </div>

            <div className="divide-y divide-gray-200">
              {mockSchedulerJobs.map((job) => (
                <div key={job.id} className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-gray-900">{job.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{job.description}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs border ${getJobStatusColor(job.status)}`}>
                      {job.status === 'running' && '运行中'}
                      {job.status === 'paused' && '已暂停'}
                      {job.status === 'stopped' && '已停止'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>调度: {job.schedule}</span>
                    <span>·</span>
                    <span>下次执行: {job.nextRun}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Scheduler Logs */}
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2 mb-1">
                <Database className="w-5 h-5 text-gray-600" />
                <h2 className="text-gray-900">调度执行日志</h2>
              </div>
              <p className="text-sm text-gray-600">最近的任务执行记录</p>
            </div>

            <div className="divide-y divide-gray-200 max-h-[400px] overflow-y-auto">
              {mockSchedulerLogs.map((log) => (
                <div key={log.id} className="p-4">
                  <div className="flex items-start gap-3">
                    {getLogStatusIcon(log.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-gray-900">{log.jobType}</h3>
                        <span className="text-xs text-gray-500">{log.timestamp}</span>
                      </div>
                      {log.message && (
                        <p className="text-sm text-gray-600">{log.message}</p>
                      )}
                      <p className="text-xs text-gray-400 mt-1">执行时长: {log.duration}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Manual Triggers */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-gray-900 mb-4">手动触发区</h2>
          <p className="text-sm text-gray-600 mb-6">用于开发和演示的手动操作面板</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={handleRunAnalysisAll}
              disabled={isRunningAnalysis}
              className="flex items-center justify-center gap-3 p-6 border-2 border-green-200 rounded-lg hover:bg-green-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className={`w-6 h-6 text-green-600 ${isRunningAnalysis ? 'animate-pulse' : ''}`} />
              <div className="text-left">
                <p className="text-gray-900">触发全量植物分析</p>
                <p className="text-sm text-gray-600">对所有植物执行一次完整分析</p>
              </div>
            </button>

            <button className="flex items-center justify-center gap-3 p-6 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition-colors">
              <Play className="w-6 h-6 text-purple-600" />
              <div className="text-left">
                <p className="text-gray-900">生成所有梦境图</p>
                <p className="text-sm text-gray-600">为每个植物生成一张梦境花园图</p>
              </div>
            </button>

            <button className="flex items-center justify-center gap-3 p-6 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
              <Play className="w-6 h-6 text-blue-600" />
              <div className="text-left">
                <p className="text-gray-900">触发全量报告生成</p>
                <p className="text-sm text-gray-600">为所有植物生成 LLM 分析报告</p>
              </div>
            </button>

            <button className="flex items-center justify-center gap-3 p-6 border-2 border-orange-200 rounded-lg hover:bg-orange-50 transition-colors">
              <Play className="w-6 h-6 text-orange-600" />
              <div className="text-left">
                <p className="text-gray-900">清理旧数据</p>
                <p className="text-sm text-gray-600">清理30天前的传感器数据</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
