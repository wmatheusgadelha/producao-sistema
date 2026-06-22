from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..core.security import get_current_user, require_admin
from ..models.models import LinhaCapacidade
from ..schemas.schemas import LinhaCapacidadeCreate, LinhaCapacidadeUpdate, LinhaCapacidadeOut

router = APIRouter()

def calcular_capacidades(item: LinhaCapacidade):
    """Recalcula campos derivados sempre que PPM, gramatura ou cargas horárias mudam."""
    if item.velocidade_ppm and item.gramatura_kg and item.pacote_por_fardo:
        min_hora = item.min_por_hora or 60.0
        ch1 = item.carga_horaria_turno1 or 8.46
        ch2 = item.carga_horaria_turno2 or 8.71
        # fardos por hora = (PPM * min/hora) / pacotes por fardo
        item.cap_fardo_hora = round((item.velocidade_ppm * min_hora) / item.pacote_por_fardo, 2)
        item.cap_fardo_turno = round(item.cap_fardo_hora * ch1, 2)
        item.cap_kg_hora = round(item.cap_fardo_hora * item.pacote_por_fardo * item.gramatura_kg, 2)
        item.cap_kg_turno = round(item.cap_fardo_turno * item.pacote_por_fardo * item.gramatura_kg, 2)
        item.cap_fardo_dia = round(item.cap_fardo_hora * (ch1 + ch2), 2)
        item.cap_kg_dia = round(item.cap_fardo_dia * item.pacote_por_fardo * item.gramatura_kg, 2)

@router.get("/", response_model=List[LinhaCapacidadeOut])
def list_capacidade(linha: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(LinhaCapacidade)
    if linha:
        q = q.filter(LinhaCapacidade.linha == linha)
    return q.order_by(LinhaCapacidade.linha, LinhaCapacidade.gramatura_kg, LinhaCapacidade.sku).all()

@router.get("/linhas")
def get_linhas(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Retorna lista de linhas únicas disponíveis."""
    rows = db.query(LinhaCapacidade.linha).distinct().order_by(LinhaCapacidade.linha).all()
    return [r[0] for r in rows]

@router.get("/sku/{linha}/{sku}", response_model=LinhaCapacidadeOut)
def get_by_sku(linha: int, sku: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.query(LinhaCapacidade).filter(
        LinhaCapacidade.linha == linha,
        LinhaCapacidade.sku == sku
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="SKU não encontrado nessa linha")
    return item

@router.post("/", response_model=LinhaCapacidadeOut)
def create_capacidade(data: LinhaCapacidadeCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    item = LinhaCapacidade(**data.dict())
    calcular_capacidades(item)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/{item_id}", response_model=LinhaCapacidadeOut)
def update_capacidade(item_id: int, data: LinhaCapacidadeUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    item = db.query(LinhaCapacidade).filter(LinhaCapacidade.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(item, field, value)
    calcular_capacidades(item)
    item.updated_by = current_user.id
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_capacidade(item_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    item = db.query(LinhaCapacidade).filter(LinhaCapacidade.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    db.delete(item)
    db.commit()
    return {"message": "Registro removido"}
