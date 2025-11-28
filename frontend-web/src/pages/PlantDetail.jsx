import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

const API_BASE = "http://127.0.0.1:8000";
const tabs = ["overview", "metrics", "reports", "photos", "dream"];

export default function PlantDetail() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState("overview");
  const [plant, setPlant] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        // Try /plants/:id; if missing, fall back to /plants then filter
        let plantData = null;
        const pRes = await fetch(`${API_BASE}/plants/${id}`);
        if (pRes.ok) {
          plantData = await pRes.json();
        } else {
          const listRes = await fetch(`${API_BASE}/plants`);
          if (listRes.ok) {
            const list = await listRes.json();
            plantData = list.find((p) => String(p.id) === String(id)) || null;
          }
        }
        setPlant(plantData);

        const aRes = await fetch(`${API_BASE}/analysis/${id}`);
        if (aRes.ok) setAnalysis(await aRes.json());

        const mRes = await fetch(`${API_BASE}/metrics/${id}`);
        if (mRes.ok) setMetrics(await mRes.json());
      } catch (e) {
        console.error(e);
        setError("加载失败，请检查后端或网络");
      }
    };
    load();
  }, [id]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <h2 className="section-title">植物详情 #{id}</h2>
      <div className="tabs">
        {tabs.map((t) => (
          <div key={t} className={`tab ${activeTab === t ? "active" : ""}`} onClick={() => setActiveTab(t)}>
            {t.toUpperCase()}
          </div>
        ))}
      </div>
      {activeTab === "overview" && <OverviewTab plant={plant} analysis={analysis} error={error} />}
      {activeTab === "metrics" && <MetricsTab metrics={metrics} />}
      {activeTab === "reports" && <ReportsTab />}
      {activeTab === "photos" && <PhotosTab />}
      {activeTab === "dream" && <DreamTab />}
    </div>
  );
}

function OverviewTab({ plant, analysis, error }) {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card">
        <h3>植物信息</h3>
        {error && <div className="muted">{error}</div>}
        {!plant && !error && <div className="muted">加载中...</div>}
        <div className="muted">昵称: {plant?.nickname || "未命名"}</div>
        <div className="muted">种类: {plant?.species || "未填写"}</div>
      </div>
      <div className="card">
        <h3>当前状态</h3>
        <div className="muted">状态: {analysis?.growth_status || "待分析"}</div>
        <div className="muted">生长率: {analysis?.growth_rate_3d ?? "N/A"}</div>
        <div className="muted">压力因子: {analysis?.stress_factors?.join(", ") || "无"}</div>
      </div>
    </div>
  );
}

function MetricsTab({ metrics }) {
  return (
    <div className="grid cols-4">
      <div className="card">
        <h3>温度</h3>
        <div className="muted">当前: {metrics?.temperature?.temp_now ?? "--"}</div>
        <div className="muted">6h均值: {metrics?.temperature?.temp_6h_avg ?? "--"}</div>
        <div className="muted">24h极值: {metrics?.temperature?.temp_24h_min ?? "--"} / {metrics?.temperature?.temp_24h_max ?? "--"}</div>
      </div>
      <div className="card">
        <h3>土壤湿度</h3>
        <div className="muted">当前: {metrics?.soil_moisture?.soil_now ?? "--"}</div>
        <div className="muted">24h极值: {metrics?.soil_moisture?.soil_24h_min ?? "--"} / {metrics?.soil_moisture?.soil_24h_max ?? "--"}</div>
        <div className="muted">趋势: {metrics?.soil_moisture?.soil_24h_trend ?? "--"}</div>
      </div>
      <div className="card">
        <h3>光照</h3>
        <div className="muted">当前: {metrics?.light?.light_now ?? "--"}</div>
        <div className="muted">1h均值: {metrics?.light?.light_1h_avg ?? "--"}</div>
        <div className="muted">今日累计: {metrics?.light?.light_today_sum ?? "--"} lux·h</div>
      </div>
      <div className="card">
        <h3>重量</h3>
        <div className="muted">当前: {metrics?.weight?.weight_now ?? "--"} g</div>
        <div className="muted">24h变化: {metrics?.weight?.weight_24h_diff ?? "--"} g</div>
        <div className="muted">蒸腾速率: {metrics?.weight?.water_loss_per_hour ?? "--"} g/h</div>
      </div>
    </div>
  );
}

function ReportsTab() {
  return (
    <div className="card">
      <h3>报告列表</h3>
      <div className="muted">接入 /report/{`{id}`} 列表后显示</div>
      <button className="button primary" style={{ marginTop: 12 }}>
        重新生成今日报告
      </button>
    </div>
  );
}

function PhotosTab() {
  return (
    <div className="card">
        <h3>照片时间轴</h3>
        <div className="muted">接入 /images 列表后显示缩略图与上传功能</div>
    </div>
  );
}

function DreamTab() {
  return (
    <div className="card">
      <h3>梦境花园</h3>
      <div className="muted">接入 /dreams 列表与手动生成</div>
    </div>
  );
}
