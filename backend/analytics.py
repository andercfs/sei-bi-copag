from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from .models import Processo


@dataclass
class AnalyticsFilters:
    data_referencia: date | None = None
    data_inicial: date | None = None
    data_final: date | None = None
    setor: str | None = None
    tipo: str | None = None
    atribuicao: str | None = None


PROCESS_FIELDS = [
    "protocolo",
    "atribuicao",
    "tipo",
    "especificacao",
    "ponto_controle",
    "data_autuacao",
    "data_recebimento",
    "data_envio",
    "unidade_envio",
    "observacoes",
    "setor",
    "data_relatorio",
]


def _base_query(db: Session, filters: AnalyticsFilters):
    query = db.query(Processo)
    if filters.setor:
        query = query.filter(Processo.setor == filters.setor.upper())
    if filters.tipo:
        query = query.filter(Processo.tipo == filters.tipo)
    if filters.atribuicao:
        query = query.filter(Processo.atribuicao == filters.atribuicao)
    if filters.data_inicial:
        query = query.filter(Processo.data_relatorio >= filters.data_inicial)
    if filters.data_final:
        query = query.filter(Processo.data_relatorio <= filters.data_final)
    return query


def _rows_to_dataframe(rows: list[Processo]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=PROCESS_FIELDS)
    frame = pd.DataFrame(
        [
            {
                "protocolo": row.protocolo,
                "atribuicao": row.atribuicao or "Não informado",
                "tipo": row.tipo or "Não informado",
                "especificacao": row.especificacao or "",
                "ponto_controle": row.ponto_controle or "Não informado",
                "data_autuacao": row.data_autuacao,
                "data_recebimento": row.data_recebimento,
                "data_envio": row.data_envio,
                "unidade_envio": row.unidade_envio or "Não informado",
                "observacoes": row.observacoes or "",
                "setor": row.setor,
                "data_relatorio": row.data_relatorio,
            }
            for row in rows
        ]
    )
    frame["data_relatorio"] = pd.to_datetime(frame["data_relatorio"])
    return frame


def get_filter_options(db: Session) -> dict:
    rows = db.query(Processo).all()
    frame = _rows_to_dataframe(rows)
    if frame.empty:
        return {"datas": [], "setores": [], "tipos": [], "atribuicoes": []}

    datas = sorted(frame["data_relatorio"].dt.date.unique().tolist())
    setores = sorted(frame["setor"].dropna().unique().tolist())
    tipos = sorted(frame["tipo"].dropna().unique().tolist())
    atribuicoes = sorted(frame["atribuicao"].dropna().unique().tolist())
    return {"datas": datas, "setores": setores, "tipos": tipos, "atribuicoes": atribuicoes}


def _available_dates(db: Session, filters: AnalyticsFilters | None = None) -> list[date]:
    query = db.query(Processo)
    if filters:
        if filters.setor:
            query = query.filter(Processo.setor == filters.setor.upper())
        if filters.tipo:
            query = query.filter(Processo.tipo == filters.tipo)
        if filters.atribuicao:
            query = query.filter(Processo.atribuicao == filters.atribuicao)
        if filters.data_inicial:
            query = query.filter(Processo.data_relatorio >= filters.data_inicial)
        if filters.data_final:
            query = query.filter(Processo.data_relatorio <= filters.data_final)

    values = {row[0] for row in query.with_entities(Processo.data_relatorio).distinct().all()}
    return sorted(values)


def _resolve_reference_date(db: Session, filters: AnalyticsFilters) -> date | None:
    dates = _available_dates(db, filters)
    if not dates:
        return None
    if not filters.data_referencia:
        return dates[-1]
    eligible = [day for day in dates if day <= filters.data_referencia]
    return eligible[-1] if eligible else dates[-1]


def _load_dataframe(
    db: Session,
    filters: AnalyticsFilters,
    upto_reference: bool = True,
) -> tuple[pd.DataFrame, date | None, list[date]]:
    reference_date = _resolve_reference_date(db, filters)
    query = _base_query(db, filters)
    if upto_reference and reference_date:
        query = query.filter(Processo.data_relatorio <= reference_date)
    rows = query.order_by(Processo.data_relatorio.asc()).all()
    frame = _rows_to_dataframe(rows)
    dates = sorted(frame["data_relatorio"].dt.date.unique().tolist()) if not frame.empty else []
    return frame, reference_date, dates


def _snapshot(frame: pd.DataFrame, report_date: date | None) -> pd.DataFrame:
    if frame.empty or not report_date:
        return frame.iloc[0:0]
    return frame[frame["data_relatorio"].dt.date == report_date].copy()


def _count_series(frame: pd.DataFrame, column: str) -> list[dict]:
    if frame.empty:
        return []
    grouped = frame.groupby(column)["protocolo"].count().sort_values(ascending=False)
    return [{"label": key, "value": int(value)} for key, value in grouped.items()]


def _span_record(start: dict, end: dict, available_dates: list[date], idx_map: dict[date, int]) -> dict:
    start_day = pd.Timestamp(start["data_relatorio"]).date()
    end_day = pd.Timestamp(end["data_relatorio"]).date()
    end_idx = idx_map[end_day]
    next_date = available_dates[end_idx + 1] if end_idx < len(available_dates) - 1 else None
    duration_end = next_date or end_day

    return {
        "protocolo": start["protocolo"],
        "setor": start["setor"],
        "atribuicao": end["atribuicao"],
        "tipo": end["tipo"],
        "especificacao": end["especificacao"],
        "ponto_controle": end["ponto_controle"],
        "entrada_setor": start_day,
        "ultima_presenca": end_day,
        "saida_setor": next_date,
        "duracao_dias": max((duration_end - start_day).days, 0),
        "aberto": next_date is None,
    }


def _build_presence_spans(frame: pd.DataFrame, available_dates: list[date]) -> pd.DataFrame:
    if frame.empty or not available_dates:
        return pd.DataFrame(
            columns=[
                "protocolo",
                "setor",
                "atribuicao",
                "tipo",
                "especificacao",
                "ponto_controle",
                "entrada_setor",
                "ultima_presenca",
                "saida_setor",
                "duracao_dias",
                "aberto",
            ]
        )

    idx_map = {day: idx for idx, day in enumerate(available_dates)}
    frame = frame.sort_values(["protocolo", "setor", "data_relatorio"])
    spans: list[dict] = []

    for (_, _), group in frame.groupby(["protocolo", "setor"], sort=False):
        records = group.sort_values("data_relatorio").to_dict(orient="records")
        start = records[0]
        previous = records[0]
        previous_idx = idx_map[pd.Timestamp(previous["data_relatorio"]).date()]

        for current in records[1:]:
            current_day = pd.Timestamp(current["data_relatorio"]).date()
            current_idx = idx_map[current_day]
            if current_idx == previous_idx + 1:
                previous = current
                previous_idx = current_idx
                continue

            spans.append(_span_record(start, previous, available_dates, idx_map))
            start = current
            previous = current
            previous_idx = current_idx

        spans.append(_span_record(start, previous, available_dates, idx_map))

    return pd.DataFrame(spans)


def _previous_date(available_dates: list[date], reference_date: date | None) -> date | None:
    if not available_dates or not reference_date:
        return None
    previous = [day for day in available_dates if day < reference_date]
    return previous[-1] if previous else None


def get_dashboard_data(db: Session, filters: AnalyticsFilters) -> dict:
    frame, reference_date, available_dates = _load_dataframe(db, filters)
    current = _snapshot(frame, reference_date)

    total_unique = int(current["protocolo"].nunique()) if not current.empty else 0
    duplicates = 0
    if not current.empty:
        duplicates = int(
            current.groupby("protocolo")["setor"].nunique().loc[lambda series: series > 1].shape[0]
        )

    evolution = []
    if not frame.empty:
        evolution_series = frame.groupby(frame["data_relatorio"].dt.date)["protocolo"].nunique()
        evolution = [{"date": str(day), "value": int(value)} for day, value in evolution_series.items()]

    spans = _build_presence_spans(frame, available_dates)
    finalized_ranking = []
    if not spans.empty:
        finalized = spans[~spans["aberto"]]
        if not finalized.empty:
            ranking = finalized.groupby("atribuicao")["protocolo"].count().sort_values(ascending=False).head(10)
            finalized_ranking = [{"label": key, "value": int(value)} for key, value in ranking.items()]

    return {
        "data_referencia": str(reference_date) if reference_date else None,
        "kpis": {
            "total_processos_ativos": total_unique,
            "total_registros_snapshot": int(len(current)),
            "setores_ativos": int(current["setor"].nunique()) if not current.empty else 0,
            "duplicidades_multissetor": duplicates,
        },
        "por_setor": _count_series(current, "setor"),
        "por_tipo": _count_series(current, "tipo"),
        "por_atribuicao": _count_series(current, "atribuicao"),
        "ranking_atribuicoes": _count_series(current, "atribuicao")[:10],
        "ranking_atribuicoes_finalizadas": finalized_ranking,
        "evolucao_diaria": evolution,
    }


def get_entries_exits_data(db: Session, filters: AnalyticsFilters) -> dict:
    frame, reference_date, available_dates = _load_dataframe(db, filters)
    current = _snapshot(frame, reference_date)
    previous_date = _previous_date(available_dates, reference_date)
    previous = _snapshot(frame, previous_date)

    sectors = sorted(set(current["setor"].tolist()) | set(previous["setor"].tolist()))
    resumo: list[dict] = []
    for setor in sectors:
        current_protocols = set(current.loc[current["setor"] == setor, "protocolo"].tolist())
        previous_protocols = set(previous.loc[previous["setor"] == setor, "protocolo"].tolist())
        entradas = len(current_protocols - previous_protocols)
        saidas = len(previous_protocols - current_protocols)
        saldo = len(current_protocols) - len(previous_protocols)
        resumo.append(
            {
                "setor": setor,
                "entradas": entradas,
                "saidas": saidas,
                "saldo": saldo,
                "carga_atual": len(current_protocols),
            }
        )

    flow_series = []
    if available_dates:
        all_setores = sorted(frame["setor"].unique().tolist()) if not frame.empty else []
        for idx, day in enumerate(available_dates):
            day_snapshot = _snapshot(frame, day)
            previous_snapshot = _snapshot(frame, available_dates[idx - 1]) if idx > 0 else day_snapshot.iloc[0:0]
            for setor in all_setores:
                current_protocols = set(day_snapshot.loc[day_snapshot["setor"] == setor, "protocolo"].tolist())
                previous_protocols = set(previous_snapshot.loc[previous_snapshot["setor"] == setor, "protocolo"].tolist())
                flow_series.append(
                    {
                        "date": str(day),
                        "setor": setor,
                        "entradas": len(current_protocols - previous_protocols) if idx > 0 else len(current_protocols),
                        "saidas": len(previous_protocols - current_protocols) if idx > 0 else 0,
                        "saldo": len(current_protocols) - len(previous_protocols) if idx > 0 else len(current_protocols),
                        "carga": len(current_protocols),
                    }
                )

    return {
        "data_referencia": str(reference_date) if reference_date else None,
        "data_anterior": str(previous_date) if previous_date else None,
        "resumo_setorial": resumo,
        "entradas_por_setor": [{"label": item["setor"], "value": item["entradas"]} for item in resumo],
        "saidas_por_setor": [{"label": item["setor"], "value": item["saidas"]} for item in resumo],
        "saldo_por_setor": [{"label": item["setor"], "value": item["saldo"]} for item in resumo],
        "evolucao_fluxo": flow_series,
    }


def get_productivity_data(db: Session, filters: AnalyticsFilters) -> dict:
    frame, reference_date, available_dates = _load_dataframe(db, filters)
    current = _snapshot(frame, reference_date)
    previous_date = _previous_date(available_dates, reference_date)
    previous = _snapshot(frame, previous_date)
    spans = _build_presence_spans(frame, available_dates)
    open_spans = spans[spans["aberto"]] if not spans.empty else spans

    average_by_sector = []
    average_by_type = []
    oldest = []

    if not spans.empty:
        sector_avg = spans.groupby("setor")["duracao_dias"].mean().round(1).sort_values(ascending=False)
        average_by_sector = [{"label": key, "value": float(value)} for key, value in sector_avg.items()]

        type_avg = spans.groupby("tipo")["duracao_dias"].mean().round(1).sort_values(ascending=False).head(10)
        average_by_type = [{"label": key, "value": float(value)} for key, value in type_avg.items()]

        if not open_spans.empty:
            open_spans = open_spans.sort_values("duracao_dias", ascending=False).head(10)
            oldest = [
                {
                    "protocolo": row["protocolo"],
                    "setor": row["setor"],
                    "atribuicao": row["atribuicao"],
                    "tipo": row["tipo"],
                    "entrada_setor": str(row["entrada_setor"]),
                    "dias_no_setor": int(row["duracao_dias"]),
                }
                for _, row in open_spans.iterrows()
            ]

    sectors = sorted(set(current["setor"].tolist()) | set(previous["setor"].tolist()))
    sector_metrics = []
    for setor in sectors:
        current_protocols = set(current.loc[current["setor"] == setor, "protocolo"].tolist())
        previous_protocols = set(previous.loc[previous["setor"] == setor, "protocolo"].tolist())
        entradas = len(current_protocols - previous_protocols)
        saidas = len(previous_protocols - current_protocols)
        saldo = len(current_protocols) - len(previous_protocols)
        avg_days = 0.0
        if average_by_sector:
            match = next((item for item in average_by_sector if item["label"] == setor), None)
            avg_days = match["value"] if match else 0.0
        sector_metrics.append(
            {
                "setor": setor,
                "entradas": entradas,
                "saidas": saidas,
                "saldo": saldo,
                "carga_atual": len(current_protocols),
                "tempo_medio_permanencia": avg_days,
            }
        )

    load_evolution = []
    if not frame.empty:
        grouped = frame.groupby([frame["data_relatorio"].dt.date, "setor"])["protocolo"].count().reset_index()
        for _, row in grouped.iterrows():
            load_evolution.append(
                {
                    "date": str(row["data_relatorio"]),
                    "setor": row["setor"],
                    "carga": int(row["protocolo"]),
                }
            )

    return {
        "data_referencia": str(reference_date) if reference_date else None,
        "metricas_setoriais": sector_metrics,
        "tempo_medio_por_setor": average_by_sector,
        "tempo_medio_por_tipo": average_by_type,
        "top_10_mais_antigos": oldest,
        "evolucao_carga_setorial": load_evolution,
    }


def get_stale_processes_data(db: Session, filters: AnalyticsFilters) -> dict:
    frame, reference_date, available_dates = _load_dataframe(db, filters)
    spans = _build_presence_spans(frame, available_dates)
    open_spans = spans[spans["aberto"]] if not spans.empty else spans
    if open_spans.empty:
        return {
            "data_referencia": str(reference_date) if reference_date else None,
            "contagens": {"mais_de_10": 0, "mais_de_20": 0, "mais_de_30": 0},
            "processos": [],
        }

    process_list = [
        {
            "protocolo": row["protocolo"],
            "setor": row["setor"],
            "atribuicao": row["atribuicao"],
            "tipo": row["tipo"],
            "dias_sem_movimentacao": int(row["duracao_dias"]),
            "entrada_setor": str(row["entrada_setor"]),
        }
        for _, row in open_spans.sort_values("duracao_dias", ascending=False).iterrows()
    ]
    return {
        "data_referencia": str(reference_date) if reference_date else None,
        "contagens": {
            "mais_de_10": len([item for item in process_list if item["dias_sem_movimentacao"] > 10]),
            "mais_de_20": len([item for item in process_list if item["dias_sem_movimentacao"] > 20]),
            "mais_de_30": len([item for item in process_list if item["dias_sem_movimentacao"] > 30]),
        },
        "processos": process_list,
    }


def get_multi_sector_data(db: Session, filters: AnalyticsFilters) -> dict:
    search_filters = AnalyticsFilters(
        data_referencia=filters.data_referencia,
        data_inicial=filters.data_inicial,
        data_final=filters.data_final,
        setor=None,
        tipo=filters.tipo,
        atribuicao=filters.atribuicao,
    )
    frame, reference_date, _ = _load_dataframe(db, search_filters)
    current = _snapshot(frame, reference_date)
    if current.empty:
        return {"data_referencia": str(reference_date) if reference_date else None, "processos": []}

    grouped = (
        current.groupby("protocolo")
        .agg(setores=("setor", lambda values: sorted(set(values))))
        .reset_index()
    )
    grouped["quantidade_setores"] = grouped["setores"].apply(len)
    duplicated = grouped[grouped["quantidade_setores"] > 1].sort_values("quantidade_setores", ascending=False)

    if filters.setor:
        duplicated = duplicated[duplicated["setores"].apply(lambda setores: filters.setor.upper() in setores)]

    processes = [
        {
            "protocolo": row["protocolo"],
            "setores": row["setores"],
            "data_relatorio": str(reference_date) if reference_date else None,
        }
        for _, row in duplicated.iterrows()
    ]
    return {"data_referencia": str(reference_date) if reference_date else None, "processos": processes}
