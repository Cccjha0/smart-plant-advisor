import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = "http://127.0.0.1:8000";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [plants, setPlants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [sRes, pRes] = await Promise.all([
          fetch(`${API_BASE}/admin/stats`),
          fetch(`${API_BASE}/plants`),
        ]);
        const sJson = await sRes.json();
        const pJson = await pRes.json();
        setStats(sJson);
        setPlants(pJson);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const systemCards = [
    { label: "植物总数", value: stats?.total_plants ?? "--" },
    { label: "传感器记录", value: stats?.total_sensor_records ?? "--" },
    { label: "梦境图数量", value: stats?.total_analysis_results ?? "--" },
    { label: "图像数量", value: stats?.total_images ?? "--" },
  ];

  return (
    <div className="grid" style={{ gap: 20 }}>
      <h2 className="section-title">Dashboard 总览</h2>
      <div className="grid cols-4">
        {systemCards.map((c) => (
          <div className="card" key={c.label}>
            <div className="muted">{c.label}</div>
            <div style={{ fontSize: 24, marginTop: 6 }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h3>植物列表</h3>
          <span className="muted">点击行查看详情</span>
        </div>
        <table className="list">
          <thead>
            <tr>
              <th>ID</th>
              <th>昵称</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="muted">
                  加载中...
                </td>
              </tr>
            )}
            {!loading &&
              plants.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.nickname || "未命名"}</td>
                  <td>
                    <span className="tag ok">待分析</span>
                  </td>
                  <td>
                    <Link className="button" to={`/plants/${p.id}`}>
                      查看
                    </Link>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>最近异常提醒</h3>
        <div className="muted">展示非正常状态的植物（可接入 /analysis 聚合）</div>
      </div>

      <div className="card">
        <h3>梦境预览</h3>
        <div className="muted">展示最近的梦境图片缩略图（接入 /dreams）</div>
      </div>
    </div>
  );
}
