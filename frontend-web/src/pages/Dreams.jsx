import React from "react";

export default function Dreams() {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <h2 className="section-title">梦境画廊</h2>
      <div className="card">
        <h3>过滤与搜索</h3>
        <div className="muted">按植物、时间范围筛选（接入 /dreams 列表）</div>
      </div>
      <div className="card">
        <h3>画廊</h3>
        <div className="muted">展示梦境缩略图，点击查看详情</div>
      </div>
    </div>
  );
}
