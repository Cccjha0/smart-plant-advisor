import React from "react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/plants/1", label: "Plant Detail" },
  { to: "/dreams", label: "Dream Gallery" },
  { to: "/admin", label: "Admin" },
];

export default function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Smart Plant</h1>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
