import React from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import PlantDetail from "./pages/PlantDetail";
import Dreams from "./pages/Dreams";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/" element={<Layout />}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="plants/:id" element={<PlantDetail />} />
        <Route path="dreams" element={<Dreams />} />
        <Route path="admin" element={<Admin />} />
      </Route>
      <Route path="*" element={<div style={{ padding: 40 }}>Not Found</div>} />
    </Routes>
  );
}
