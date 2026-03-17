import { Outlet, useLocation } from "react-router-dom";
import { useState } from "react";

import { useAuth } from "../context/AuthContext";
import FilterBar from "./FilterBar";
import Sidebar from "./Sidebar";


const analyticRoutes = new Set([
  "/",
  "/entradas-saidas",
  "/produtividade",
  "/processos-parados",
  "/multiplos-setores",
]);


export default function AppLayout() {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="content-shell">
        <header className="topbar">
          <button type="button" className="menu-toggle" onClick={() => setSidebarOpen((value) => !value)}>
            Menu
          </button>

          <div className="topbar-copy">
            <p className="eyebrow">Gestão administrativa</p>
            <h2>Painel operacional do SEI</h2>
          </div>

          <div className="user-chip">
            <span>{user?.name || "Usuário"}</span>
            <small>{user?.email}</small>
          </div>
        </header>

        {analyticRoutes.has(pathname) ? <FilterBar /> : null}

        <section className="page-shell">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
