from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import date, timedelta
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import RelatorioEnvase, RelatorioManipulacao, ParadaEnvase, ParadaManipulacao

router = APIRouter()

@router.get("/stats")
def get_stats(
    periodo: str = Query("semana", description="hoje|semana|mes"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    hoje = date.today()
    if periodo == "hoje":
        data_inicio = hoje
    elif periodo == "semana":
        data_inicio = hoje - timedelta(days=7)
    else:
        data_inicio = hoje - timedelta(days=30)

    # ── ENVASE ──
    env_q = db.query(RelatorioEnvase).filter(RelatorioEnvase.data >= data_inicio)
    env_rows = env_q.all()

    total_fardos = sum(r.total_fardos_produzidos or 0 for r in env_rows)
    total_kg_env = sum(r.total_kg_produzidos or 0 for r in env_rows)
    oees = [r.oee for r in env_rows if r.oee is not None]
    oee_medio = round(sum(oees) / len(oees), 2) if oees else None
    prods = [r.produtividade_fardos_pct for r in env_rows if r.produtividade_fardos_pct is not None]
    prod_media = round(sum(prods) / len(prods), 2) if prods else None

    # Paradas envase por categoria
    paradas_env = db.query(
        ParadaEnvase.categoria,
        func.count(ParadaEnvase.id).label("qtd"),
        func.sum(ParadaEnvase.tempo_minutos).label("total_min")
    ).join(
        RelatorioEnvase, ParadaEnvase.relatorio_id == RelatorioEnvase.id
    ).filter(
        RelatorioEnvase.data >= data_inicio
    ).group_by(ParadaEnvase.categoria).all()

    paradas_env_list = [{"categoria": p.categoria or "Outros", "qtd": p.qtd, "total_min": round(p.total_min or 0, 1)} for p in paradas_env]

    # OEE por linha
    oee_por_linha = {}
    for r in env_rows:
        if r.oee is not None:
            l = f"Linha {r.linha}"
            if l not in oee_por_linha:
                oee_por_linha[l] = []
            oee_por_linha[l].append(r.oee)
    oee_por_linha = {k: round(sum(v)/len(v), 2) for k, v in oee_por_linha.items()}

    # Produção por linha
    prod_por_linha = {}
    for r in env_rows:
        l = f"Linha {r.linha}"
        prod_por_linha[l] = prod_por_linha.get(l, 0) + (r.total_fardos_produzidos or 0)

    # ── MANIPULAÇÃO ──
    man_rows = db.query(RelatorioManipulacao).filter(RelatorioManipulacao.data >= data_inicio).all()
    total_kg_man = sum(r.total_kg_produzidos or 0 for r in man_rows)
    efics = [r.eficiencia_percentual for r in man_rows if r.eficiencia_percentual is not None]
    efic_media = round(sum(efics) / len(efics), 2) if efics else None

    paradas_man = db.query(
        ParadaManipulacao.categoria,
        func.count(ParadaManipulacao.id).label("qtd"),
        func.sum(ParadaManipulacao.tempo_minutos).label("total_min")
    ).join(
        RelatorioManipulacao, ParadaManipulacao.relatorio_id == RelatorioManipulacao.id
    ).filter(
        RelatorioManipulacao.data >= data_inicio
    ).group_by(ParadaManipulacao.categoria).all()

    paradas_man_list = [{"categoria": p.categoria or "Outros", "qtd": p.qtd, "total_min": round(p.total_min or 0, 1)} for p in paradas_man]

    return {
        "periodo": periodo,
        "data_inicio": str(data_inicio),
        "data_fim": str(hoje),
        "envase": {
            "total_relatorios": len(env_rows),
            "total_fardos": total_fardos,
            "total_kg": round(total_kg_env, 2),
            "oee_medio": oee_medio,
            "produtividade_media_pct": prod_media,
            "paradas_por_categoria": paradas_env_list,
            "oee_por_linha": oee_por_linha,
            "producao_por_linha": prod_por_linha,
        },
        "manipulacao": {
            "total_relatorios": len(man_rows),
            "total_kg": round(total_kg_man, 2),
            "eficiencia_media": efic_media,
            "paradas_por_categoria": paradas_man_list,
        }
    }

@router.get("/evolucao")
def get_evolucao(
    dias: int = Query(30),
    linha: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Evolução diária de produção e OEE para gráficos de tendência."""
    data_inicio = date.today() - timedelta(days=dias)
    q = db.query(
        RelatorioEnvase.data,
        func.sum(RelatorioEnvase.total_fardos_produzidos).label("fardos"),
        func.sum(RelatorioEnvase.total_kg_produzidos).label("kg"),
        func.avg(RelatorioEnvase.oee).label("oee_medio"),
        func.avg(RelatorioEnvase.produtividade_fardos_pct).label("prod_media")
    ).filter(RelatorioEnvase.data >= data_inicio)
    if linha:
        q = q.filter(RelatorioEnvase.linha == linha)
    rows = q.group_by(RelatorioEnvase.data).order_by(RelatorioEnvase.data).all()

    q_man = db.query(
        RelatorioManipulacao.data,
        func.sum(RelatorioManipulacao.total_kg_produzidos).label("kg"),
        func.avg(RelatorioManipulacao.eficiencia_percentual).label("efic")
    ).filter(RelatorioManipulacao.data >= data_inicio
    ).group_by(RelatorioManipulacao.data).order_by(RelatorioManipulacao.data).all()

    return {
        "envase": [
            {"data": str(r.data), "fardos": r.fardos or 0, "kg": round(r.kg or 0, 2),
             "oee": round(r.oee_medio or 0, 2), "produtividade": round(r.prod_media or 0, 2)}
            for r in rows
        ],
        "manipulacao": [
            {"data": str(r.data), "kg": round(r.kg or 0, 2), "eficiencia": round(r.efic or 0, 2)}
            for r in q_man
        ]
    }
