import { useEffect, useState } from "react";

import api from "../api/client";
import DataTable from "../components/DataTable";
import LoadingBlock from "../components/LoadingBlock";
import { useFilters } from "../context/FiltersContext";


export default function MultiSectorPage() {
  const { filters, toQueryParams } = useFilters();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await api.get("/analytics/multi-sector", { params: toQueryParams() });
        setData(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || "Falha ao detectar múltiplos setores.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [filters]);

  if (loading) {
    return <LoadingBlock label="Investigando múltiplos setores..." />;
  }

  if (error) {
    return <div className="alert error">{error}</div>;
  }

  return (
    <div className="page-grid">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Consistência do snapshot</p>
          <h1>Processos em múltiplos setores</h1>
          <span>Protocolos que aparecem em mais de um setor no mesmo dia.</span>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Ocorrências para {data?.data_referencia || "a data selecionada"}</h3>
            <p>Use o filtro de data no topo para analisar snapshots específicos.</p>
          </div>
        </div>
        <DataTable
          columns={[
            { key: "protocolo", label: "Protocolo" },
            { key: "setores", label: "Setores" },
            { key: "data_relatorio", label: "Data do relatório" },
          ]}
          rows={data?.processos || []}
          emptyMessage="Nenhum processo encontrado em múltiplos setores com os filtros atuais."
        />
      </section>
    </div>
  );
}
