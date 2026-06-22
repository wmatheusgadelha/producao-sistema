from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import RelatorioEnvase, ParadaEnvase, LinhaCapacidade
from ..schemas.schemas import RelatorioEnvaseCreate, RelatorioEnvaseOut

router = APIRouter()

def calcular_oee_produtividade(rel: RelatorioEnvase, db: Session):
    """Calcula OEE e produtividade após salvar paradas."""
    total_parada = db.query(func.sum(ParadaEnvase.tempo_minutos)).filter(
        ParadaEnvase.relatorio_id == rel.id
    ).scalar() or 0.0
    rel.total_minutos_parada = round(total_parada, 2)

    # Busca capacidade teórica pelo SKU/linha
    if rel.sku and rel.linha:
        cap = db.query(LinhaCapacidade).filter(
            LinhaCapacidade.linha == rel.linha,
            LinhaCapacidade.sku == rel.sku
        ).first()
        if cap:
            rel.cap_teorica_fardos_turno = cap.cap_fardo_turno
            rel.cap_teorica_kg_turno = cap.cap_kg_turno

    # Produtividade real vs teórico
    if rel.total_fardos_produzidos and rel.cap_teorica_fardos_turno and rel.cap_teorica_fardos_turno > 0:
        rel.produtividade_fardos_pct = round((rel.total_fardos_produzidos / rel.cap_teorica_fardos_turno) * 100, 2)
    if rel.total_kg_produzidos and rel.cap_teorica_kg_turno and rel.cap_teorica_kg_turno > 0:
        rel.produtividade_kg_pct = round((rel.total_kg_produzidos / rel.cap_teorica_kg_turno) * 100, 2)

    # OEE
    disp = rel.tempo_disponivel_min or 480.0
    tempo_operando = disp - total_parada
    if disp > 0:
        rel.oee_disponibilidade = round((tempo_operando / disp) * 100, 2)

    if rel.velocidade_real_ppm and rel.cap_teorica_fardos_turno:
        cap_row = db.query(LinhaCapacidade).filter(
            LinhaCapacidade.linha == rel.linha, LinhaCapacidade.sku == rel.sku
        ).first()
        if cap_row and cap_row.velocidade_ppm:
            rel.oee_performance = round((rel.velocidade_real_ppm / cap_row.velocidade_ppm) * 100, 2)
    if rel.oee_performance is None:
        rel.oee_performance = rel.produtividade_fardos_pct

    # Qualidade = % peso bom
    total_un = (rel.peso_alto_unidades or 0) + (rel.peso_bom_unidades or 0) + (rel.peso_baixo_unidades or 0)
    if total_un > 0:
        rel.oee_qualidade = round(((rel.peso_bom_unidades or 0) / total_un) * 100, 2)
    else:
        rel.oee_qualidade = 100.0

    disp_pct = (rel.oee_disponibilidade or 0) / 100
    perf_pct = (rel.oee_performance or 0) / 100
    qual_pct = (rel.oee_qualidade or 0) / 100
    rel.oee = round(disp_pct * perf_pct * qual_pct * 100, 2)

@router.get("/", response_model=List[RelatorioEnvaseOut])
def list_relatorios(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    linha: Optional[int] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(RelatorioEnvase)
    if data_inicio:
        q = q.filter(RelatorioEnvase.data >= data_inicio)
    if data_fim:
        q = q.filter(RelatorioEnvase.data <= data_fim)
    if linha:
        q = q.filter(RelatorioEnvase.linha == linha)
    if turno:
        q = q.filter(RelatorioEnvase.turno == turno)
    return q.order_by(RelatorioEnvase.data.desc(), RelatorioEnvase.linha).all()

@router.get("/{rel_id}", response_model=RelatorioEnvaseOut)
def get_relatorio(rel_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioEnvase).filter(RelatorioEnvase.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return rel

@router.post("/", response_model=RelatorioEnvaseOut)
def create_relatorio(data: RelatorioEnvaseCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    paradas_data = data.paradas
    rel_data = data.dict(exclude={"paradas"})
    rel = RelatorioEnvase(**rel_data, created_by=current_user.id)
    db.add(rel)
    db.flush()

    for p in paradas_data:
        parada = ParadaEnvase(relatorio_id=rel.id, **p.dict())
        db.add(parada)
    db.flush()

    calcular_oee_produtividade(rel, db)
    db.commit()
    db.refresh(rel)
    return rel

@router.put("/{rel_id}", response_model=RelatorioEnvaseOut)
def update_relatorio(rel_id: int, data: RelatorioEnvaseCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioEnvase).filter(RelatorioEnvase.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    paradas_data = data.paradas
    rel_data = data.dict(exclude={"paradas"})
    for field, value in rel_data.items():
        setattr(rel, field, value)

    # Apaga paradas antigas e recria
    db.query(ParadaEnvase).filter(ParadaEnvase.relatorio_id == rel_id).delete()
    for p in paradas_data:
        parada = ParadaEnvase(relatorio_id=rel.id, **p.dict())
        db.add(parada)
    db.flush()

    calcular_oee_produtividade(rel, db)
    db.commit()
    db.refresh(rel)
    return rel

@router.delete("/{rel_id}")
def delete_relatorio(rel_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioEnvase).filter(RelatorioEnvase.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    db.delete(rel)
    db.commit()
    return {"message": "Relatório excluído"}
