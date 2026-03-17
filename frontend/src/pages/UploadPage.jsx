import { useEffect, useState } from "react";

import api from "../api/client";
import DataTable from "../components/DataTable";
import LoadingBlock from "../components/LoadingBlock";


const setores = ["DIAPE", "DICAT", "DIJOR", "DICAF", "DICAF-CHEFIA", "DICAF-REPOSICOES"];


export default function UploadPage() {
  const [form, setForm] = useState({
    setor: "DIAPE",
    data_relatorio: new Date().toISOString().slice(0, 10),
    file: null,
  });
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadUploads() {
    setLoading(true);
    try {
      const { data } = await api.get("/uploads");
      setUploads(data);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Falha ao carregar uploads.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUploads();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setSending(true);
    setMessage("");
    setError("");

    try {
      const payload = new FormData();
      payload.append("setor", form.setor);
      payload.append("data_relatorio", form.data_relatorio);
      payload.append("file", form.file);

      const { data } = await api.post("/uploads", payload, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage(`${data.message} ${data.total_registros} registros processados.`);
      setForm((current) => ({ ...current, file: null }));
      document.getElementById("upload-file-input").value = "";
      loadUploads();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Falha no envio do relatório.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Envio diário</p>
          <h1>Enviar Relatório SEI</h1>
          <span>Associe o arquivo CSV ao setor e à data do snapshot para atualizar os dashboards automaticamente.</span>
        </div>
      </section>

      <section className="panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Setor</span>
            <select value={form.setor} onChange={(event) => setForm((current) => ({ ...current, setor: event.target.value }))}>
              {setores.map((setor) => (
                <option key={setor} value={setor}>
                  {setor}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Data do relatório</span>
            <input
              type="date"
              value={form.data_relatorio}
              onChange={(event) => setForm((current) => ({ ...current, data_relatorio: event.target.value }))}
              required
            />
          </label>

          <label className="field full-width">
            <span>Arquivo CSV exportado do SEI</span>
            <input
              id="upload-file-input"
              type="file"
              accept=".csv"
              onChange={(event) => setForm((current) => ({ ...current, file: event.target.files?.[0] || null }))}
              required
            />
          </label>

          {message ? <div className="alert success full-width">{message}</div> : null}
          {error ? <div className="alert error full-width">{error}</div> : null}

          <button type="submit" className="primary-button" disabled={sending || !form.file}>
            {sending ? "Enviando..." : "Enviar"}
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h3>Histórico recente de uploads</h3>
            <p>Os snapshots carregados aqui alimentam automaticamente todas as análises.</p>
          </div>
        </div>
        {loading ? (
          <LoadingBlock label="Carregando uploads..." />
        ) : (
          <DataTable
            columns={[
              { key: "setor", label: "Setor" },
              { key: "data_relatorio", label: "Data do relatório" },
              { key: "data_upload", label: "Importado em" },
              { key: "original_filename", label: "Arquivo" },
              { key: "total_records", label: "Registros" },
            ]}
            rows={uploads}
          />
        )}
      </section>
    </div>
  );
}
