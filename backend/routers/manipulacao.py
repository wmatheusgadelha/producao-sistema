from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import RelatorioManipulacao, ParadaManipulacao, BatidaManipulacao
from ..schemas.schemas import RelatorioManipulacaoCreate, RelatorioManipulacaoOut

router = APIRouter()

@router.get("/", response_model=List[RelatorioManipulacaoOut])
def list_relatorios(
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(RelatorioManipulacao)
    if data_inicio:
        q = q.filter(RelatorioManipulacao.data >= data_inicio)
    if data_fim:
        q = q.filter(RelatorioManipulacao.data <= data_fim)
    if turno:
        q = q.filter(RelatorioManipulacao.turno == turno)
    return q.order_by(RelatorioManipulacao.data.desc()).all()

@router.get("/{rel_id}", response_model=RelatorioManipulacaoOut)
def get_relatorio(rel_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioManipulacao).filter(RelatorioManipulacao.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return rel

@router.post("/", response_model=RelatorioManipulacaoOut)
def create_relatorio(data: RelatorioManipulacaoCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    paradas_data = data.paradas
    batidas_data = data.batidas
    rel_data = data.dict(exclude={"paradas", "batidas"})
    rel = RelatorioManipulacao(**rel_data, created_by=current_user.id)
    db.add(rel)
    db.flush()

    for p in paradas_data:
        db.add(ParadaManipulacao(relatorio_id=rel.id, **p.dict()))

    total_kg = 0.0
    for b in batidas_data:
        total_kg_batida = b.kg_por_batida * b.numero_batida
        total_kg += total_kg_batida
        db.add(BatidaManipulacao(relatorio_id=rel.id, total_kg=total_kg_batida, **b.dict()))

    db.flush()

    # Recalcula totais
    rel.total_minutos_parada = db.query(func.sum(ParadaManipulacao.tempo_minutos)).filter(
        ParadaManipulacao.relatorio_id == rel.id
    ).scalar() or 0.0

    rel.total_kg_produzidos = round(total_kg, 3)
    disp = rel.tempo_disponivel_min or 480.0
    tempo_prod = disp - rel.total_minutos_parada
    if disp > 0:
        rel.eficiencia_percentual = round((tempo_prod / disp) * 100, 2)

    db.commit()
    db.refresh(rel)
    return rel

@router.put("/{rel_id}", response_model=RelatorioManipulacaoOut)
def update_relatorio(rel_id: int, data: RelatorioManipulacaoCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioManipulacao).filter(RelatorioManipulacao.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    paradas_data = data.paradas
    batidas_data = data.batidas
    rel_data = data.dict(exclude={"paradas", "batidas"})
    for field, value in rel_data.items():
        setattr(rel, field, value)

    db.query(ParadaManipulacao).filter(ParadaManipulacao.relatorio_id == rel_id).delete()
    db.query(BatidaManipulacao).filter(BatidaManipulacao.relatorio_id == rel_id).delete()

    for p in paradas_data:
        db.add(ParadaManipulacao(relatorio_id=rel.id, **p.dict()))

    total_kg = 0.0
    for b in batidas_data:
        total_kg_batida = b.kg_por_batida * b.numero_batida
        total_kg += total_kg_batida
        db.add(BatidaManipulacao(relatorio_id=rel.id, total_kg=total_kg_batida, **b.dict()))

    db.flush()
    rel.total_minutos_parada = db.query(func.sum(ParadaManipulacao.tempo_minutos)).filter(
        ParadaManipulacao.relatorio_id == rel.id
    ).scalar() or 0.0
    rel.total_kg_produzidos = round(total_kg, 3)
    disp = rel.tempo_disponivel_min or 480.0
    tempo_prod = disp - rel.total_minutos_parada
    if disp > 0:
        rel.eficiencia_percentual = round((tempo_prod / disp) * 100, 2)

    db.commit()
    db.refresh(rel)
    return rel

@router.delete("/{rel_id}")
def delete_relatorio(rel_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rel = db.query(RelatorioManipulacao).filter(RelatorioManipulacao.id == rel_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    db.delete(rel)
    db.commit()
    return {"message": "Relatório excluído"}
