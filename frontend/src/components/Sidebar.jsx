import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const menuItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/enviar-relatorio", label: "Enviar Relatório" },
  { to: "/entradas-saidas", label: "Entradas e Saídas" },
  { to: "/produtividade", label: "Produtividade" },
  { to: "/processos-parados", label: "Processos Parados" },
  { to: "/multiplos-setores", label: "Processos em Múltiplos Setores" },
  { to: "/administracao", label: "Administração", adminOnly: true },
  { to: "/logout", label: "Logout" },
];


export default function Sidebar({ open, onClose }) {
  const { user } = useAuth();
  const visibleItems = menuItems.filter((item) => !item.adminOnly || user?.is_admin);

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="brand-panel">
        <p className="eyebrow">SEI BI</p>
        <h1>Monitoramento COPAG</h1>
        <span>Dashboards inteligentes para snapshots diários do SEI</span>
      </div>

      <nav className="menu">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onClose}
            className={({ isActive }) => `menu-link ${isActive ? "active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
