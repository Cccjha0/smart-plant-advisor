import { useMemo, useState } from 'react';
import { Database, Activity, Calendar, Play, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { api, SchedulerJobDto, SchedulerLogDto, SystemOverview } from '../utils/api';
import { useAsync } from '../utils/hooks';

export function Admin() {
  const [jobsVersion, setJobsVersion] = useState(0);

  const { data: stats } = useAsync(async () => api.getAdminStats().catch(() => null), []);
  const { data: sysOverview } = useAsync<SystemOverview | null>(async () => {
    try {
      return await api.getSystemOverview();
    } catch {
      return null;
    }
  }, []);

  const { data: jobs, loading: jobsLoading } = useAsync(async () => {
    return api.getSchedulerJobs().catch(() => []);
  }, [jobsVersion]);

  const { data: logs, loading: logsLoading } = useAsync(async () => {
    return api.getSchedulerLogs().catch(() => []);
  }, []);

  const handleRunAll = async (path: string) => {
    try {
      await fetch(path, { method: 'POST' });
    } catch (e) {
      console.error(e);
    } finally {
      setJobsVersion((v) => v + 1);
    }
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

  const overviewCards = useMemo(() => {
    const src = sysOverview || stats;
    if (!src) return [];
    const colors = [
      { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', value: 'text-green-900' },
      { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', value: 'text-blue-900' },
      { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', value: 'text-purple-900' },
      { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', value: 'text-orange-900' },
      { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700', value: 'text-pink-900' },
    ];
    const entries = [
      { label: '总植物数', value: src.total_plants },
      { label: '图像总数', value: src.total_images },
      { label: '传感器记录', value: src.total_sensor_records },
      { label: '分析结果', value: src.total_analysis_results },
      { label: '梦境图总数', value: (src as any).total_dream_images ?? '—' },
    ];
    return entries.map((e, idx) => ({ ...e, color: colors[idx % colors.length] }));
  }, [stats, sysOverview]);

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-gray-900 mb-2">系统管理</h1>
          <p className="text-gray-600">监控系统状态和调度任务</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-gray-900 mb-6">系统概况</h2>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-8">
            {overviewCards.map((card, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${card.color?.bg || 'bg-gray-50'} ${card.color?.border || 'border-gray-200'}`}
              >
                <p className={`text-sm mb-1 ${card.color?.text || 'text-gray-700'}`}>{card.label}</p>
                <p className={`text-3xl ${card.color?.value || 'text-gray-900'}`}>{card.value ?? '—'}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
            <Activity className={`w-6 h-6 ${jobsLoading ? 'text-gray-400' : 'text-green-600'}`} />
            <div>
              <p className="text-gray-900">APScheduler 状态</p>
              <p className={`text-sm ${jobsLoading ? 'text-gray-600' : 'text-green-600'}`}>
                {jobsLoading ? '加载中...' : '运行中（见下方任务列表）'}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-5 h-5 text-gray-600" />
                <h2 className="text-gray-900">已注册的定时任务</h2>
              </div>
              <p className="text-sm text-gray-600">当前系统中运行的所有调度任务</p>
            </div>

            <div className="divide-y divide-gray-200">
              {jobsLoading && <div className="p-4 text-sm text-gray-500">加载中...</div>}
              {!jobsLoading && jobs && jobs.length === 0 && <div className="p-4 text-sm text-gray-500">暂无任务</div>}
              {(jobs || []).map((job: SchedulerJobDto) => (
                <div key={job.id} className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-gray-900">{job.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{job.description}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs border ${getJobStatusColor(job.status)}`}>
                      {job.status === 'running' ? '运行中' : '已暂停'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>调度: {job.schedule}</span>
                    <span>·</span>
                    <span>下次执行: {job.nextRun || '—'}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-2 mb-1">
                <Database className="w-5 h-5 text-gray-600" />
                <h2 className="text-gray-900">调度执行日志</h2>
              </div>
              <p className="text-sm text-gray-600">最近的任务执行记录</p>
            </div>

            <div className="divide-y divide-gray-200 max-h-[400px] overflow-y-auto">
              {logsLoading && <div className="p-4 text-sm text-gray-500">加载中...</div>}
              {!logsLoading && logs && logs.length === 0 && <div className="p-4 text-sm text-gray-500">暂无日志</div>}
              {(logs || []).map((log: SchedulerLogDto) => (
                <div key={log.id} className="p-4">
                  <div className="flex items-start gap-3">
                    {getLogStatusIcon(log.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h3 className="text-gray-900">{log.jobName || log.jobKey}</h3>
                        <span className="text-xs text-gray-500">{log.startedAt ? new Date(log.startedAt).toLocaleString() : '—'}</span>
                      </div>
                      {log.message && <p className="text-sm text-gray-600">{log.message}</p>}
                      <p className="text-xs text-gray-400 mt-1">
                        执行时长: {log.durationSeconds != null ? `${log.durationSeconds}s` : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-gray-900 mb-4">手动触发区</h2>
          <p className="text-sm text-gray-600 mb-6">用于开发和演示的手动操作入口</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => handleRunAll('/admin/run_analysis_all')}
              className="flex items-center justify-center gap-3 p-6 border-2 border-green-200 rounded-lg hover:bg-green-50 transition-colors"
            >
              <Play className="w-6 h-6 text-green-600" />
              <div className="text-left">
                <p className="text-gray-900">触发全量植物分析</p>
                <p className="text-sm text-gray-600">对所有植物执行一次完整分析</p>
              </div>
            </button>

            <button
              onClick={() => handleRunAll('/admin/run_dream_all')}
              className="flex items-center justify-center gap-3 p-6 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition-colors"
            >
              <Play className="w-6 h-6 text-purple-600" />
              <div className="text-left">
                <p className="text-gray-900">生成所有梦境图</p>
                <p className="text-sm text-gray-600">为每个植物生成一张梦境花园图</p>
              </div>
            </button>

            <button
              onClick={() => handleRunAll('/admin/run_report_all')}
              className="flex items-center justify-center gap-3 p-6 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
            >
              <Play className="w-6 h-6 text-blue-600" />
              <div className="text-left">
                <p className="text-gray-900">触发全量报告生成</p>
                <p className="text-sm text-gray-600">为所有植物生成 LLM 分析报告</p>
              </div>
            </button>

            <button
              onClick={() => handleRunAll('/admin/run_cleanup')}
              className="flex items-center justify-center gap-3 p-6 border-2 border-orange-200 rounded-lg hover:bg-orange-50 transition-colors"
            >
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
