import { useEffect, useState } from "react";

import api from "../api/client";
import BarChartCard from "../charts/BarChartCard";
import LineChartCard from "../charts/LineChartCard";
import DataTable from "../components/DataTable";
import LoadingBlock from "../components/LoadingBlock";
import StatCard from "../components/StatCard";
import { useFilters } from "../context/FiltersContext";


export default function ProductivityPage() {
  const { filters, toQueryParams } = useFilters();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await api.get("/analytics/productivity", { params: toQueryParams() });
        setData(response.data);
      } catch (requestError) {
        setError(requestError.response?.data?.detail || "Falha ao carregar produtividade.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [filters]);

  if (loading) {
    return <LoadingBlock label="Calculando produtividade e permanência..." />;
  }

  if (error) {
    return <div className="alert error">{error}</div>;
  }

  const maiorTempoMedio = data?.tempo_medio_por_setor?.[0];
  const maisAntigo = data?.top_10_mais_antigos?.[0];

  return (
    <div className="page-grid">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Produtividade</p>
          <h1>Permanência e carga operacional</h1>
          <span>Indicadores derivados da permanência dos processos em cada setor ao longo dos snapshots.</span>
        </div>
      </section>

      <section className="stats-grid">
        <StatCard
          label="Maior tempo médio"
          value={maiorTempoMedio ? `${maiorTempoMedio.value} dias` : "0 dias"}
          hint={maiorTempoMedio?.label}
        />
        <StatCard label="Setores monitorados" value={data?.tempo_medio_por_setor?.length ?? 0} />
        <StatCard
          label="Processo mais antigo"
          value={maisAntigo ? `${maisAntigo.dias_no_setor} dias` : "0 dias"}
          hint={maisAntigo?.protocolo}
        />
      </section>

      <section className="charts-grid">
        <BarChartCard title="Tempo médio de permanência por setor" data={data?.tempo_medio_por_setor || []} />
        <BarChartCard
          title="Tempo médio por tipo de processo"
          data={(data?.tempo_medio_por_tipo || []).slice(0, 10)}
          color="#0f5f73"
        />
        <LineChartCard
          title="Evolução diária da carga por setor"
          data={data?.evolucao_carga_setorial || []}
          xKey="date"
          valueKey="carga"
          seriesKey="setor"
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Top 10 processos mais antigos em tramitação</h3>
            <p>Processos com maior tempo inferido no setor atual.</p>
          </div>
        </div>
        <DataTable
          columns={[
            { key: "protocolo", label: "Protocolo" },
            { key: "setor", label: "Setor" },
            { key: "atribuicao", label: "Atribuição" },
            { key: "tipo", label: "Tipo" },
            { key: "entrada_setor", label: "Entrada no setor" },
            { key: "dias_no_setor", label: "Dias no setor" },
          ]}
          rows={data?.top_10_mais_antigos || []}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Métricas setoriais</h3>
            <p>Resumo de entradas, saídas, saldo, carga atual e permanência média por setor.</p>
          </div>
        </div>
        <DataTable
          columns={[
            { key: "setor", label: "Setor" },
            { key: "entradas", label: "Entradas" },
            { key: "saidas", label: "Saídas" },
            { key: "saldo", label: "Saldo" },
            { key: "carga_atual", label: "Carga atual" },
            { key: "tempo_medio_permanencia", label: "Tempo médio (dias)" },
          ]}
          rows={data?.metricas_setoriais || []}
        />
      </section>
    </div>
  );
}
