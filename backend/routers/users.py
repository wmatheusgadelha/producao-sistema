from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user, require_admin, get_password_hash
from ..models.models import ProdUser
from ..schemas.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter()

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(ProdUser).order_by(ProdUser.nome).all()

@router.post("/", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    if db.query(ProdUser).filter(ProdUser.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = ProdUser(
        nome=data.nome, email=data.email,
        hashed_password=get_password_hash(data.password),
        role=data.role, cargo=data.cargo, matricula=data.matricula,
        telefone=data.telefone, setor=data.setor
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.query(ProdUser).filter(ProdUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.query(ProdUser).filter(ProdUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.is_active = False
    db.commit()
    return {"message": "Usuário desativado"}
