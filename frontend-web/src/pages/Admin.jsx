import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function Admin() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${API_BASE}/admin/stats`);
        if (res.ok) setStats(await res.json());
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, []);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <h2 className="section-title">系统管理 & 调度监控</h2>
      <div className="card">
        <h3>系统概况</h3>
        <div className="muted">植物: {stats?.total_plants ?? "--"}</div>
        <div className="muted">传感器记录: {stats?.total_sensor_records ?? "--"}</div>
        <div className="muted">图像: {stats?.total_images ?? "--"}</div>
        <div className="muted">分析结果: {stats?.total_analysis_results ?? "--"}</div>
      </div>
      <div className="card">
        <h3>调度执行</h3>
        <div className="muted">这里可以接入 /admin/jobs 与执行日志</div>
      </div>
      <div className="card">
        <h3>手动触发</h3>
        <div className="row">
          <button className="button primary">全量分析</button>
          <button className="button">单株全流程</button>
        </div>
      </div>
    </div>
  );
}
