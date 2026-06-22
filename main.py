from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.core.database import engine, SessionLocal
from backend.core.config import settings
from backend.core.security import get_password_hash
from backend.models.models import (
    Base, ProdUser, LinhaCapacidade,
    RelatorioEnvase, ParadaEnvase,
    RelatorioManipulacao, ParadaManipulacao, BatidaManipulacao
)
from backend.routers import auth, users, capacidade, envase, manipulacao, dashboard


def calcular_caps(item):
    if item.velocidade_ppm and item.gramatura_kg and item.pacote_por_fardo:
        ch1 = item.carga_horaria_turno1 or 8.46
        ch2 = item.carga_horaria_turno2 or 8.71
        min_hora = item.min_por_hora or 60.0
        item.cap_fardo_hora = round((item.velocidade_ppm * min_hora) / item.pacote_por_fardo, 2)
        item.cap_fardo_turno = round(item.cap_fardo_hora * ch1, 2)
        item.cap_kg_hora = round(item.cap_fardo_hora * item.pacote_por_fardo * item.gramatura_kg, 2)
        item.cap_kg_turno = round(item.cap_fardo_turno * item.pacote_por_fardo * item.gramatura_kg, 2)
        item.cap_fardo_dia = round(item.cap_fardo_hora * (ch1 + ch2), 2)
        item.cap_kg_dia = round(item.cap_fardo_dia * item.pacote_por_fardo * item.gramatura_kg, 2)


BASE_CAPACIDADE = [
    # LINHA 1
    {"linha": 1, "sku": "BONNY 0,4KG",                      "gramatura_kg": 0.4, "pacote_por_fardo": 50, "fardo_por_palete": 54, "velocidade_ppm": 32, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "BONNY 0,8KG",                      "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "BONNY 1KG",                        "gramatura_kg": 1.0, "pacote_por_fardo": 20, "fardo_por_palete": 54, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "QUALIMP 0,8KG",                    "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "QUALIMP COCO 0,8KG",               "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "UNI LIMP 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "FELITA 0,8KG",                     "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AROMASIL COCO 0,4KG",              "gramatura_kg": 0.4, "pacote_por_fardo": 50, "fardo_por_palete": 54, "velocidade_ppm": 35, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AROMASIL 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AMACITEL TOQUE POESIA 0,4KG",      "gramatura_kg": 0.4, "pacote_por_fardo": 24, "fardo_por_palete": 100,"velocidade_ppm": 32, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AMACITEL TOQUE POESIA 0,8KG",      "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AMACITEL ALEGRES ENCANTOS 0,4KG",  "gramatura_kg": 0.4, "pacote_por_fardo": 24, "fardo_por_palete": 100,"velocidade_ppm": 32, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 1, "sku": "AMACITEL ALEGRES ENCANTOS 0,8KG",  "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    # LINHA 2
    {"linha": 2, "sku": "BONNY 0,8KG",                      "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "BONNY 1KG",                        "gramatura_kg": 1.0, "pacote_por_fardo": 20, "fardo_por_palete": 54, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "BONNY 1,6KG",                      "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "QUALIMP 0,8KG",                    "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "QUALIMP COCO 0,8KG",               "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "QUALIMP 1,6KG",                    "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "UNI LIMP 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "UNI LIMP 1,6KG",                   "gramatura_kg": 1.6, "pacote_por_fardo": 10, "fardo_por_palete": 56, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "FELITA 0,8KG",                     "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "FELITA 1,6KG",                     "gramatura_kg": 1.6, "pacote_por_fardo": 10, "fardo_por_palete": 56, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AROMASIL 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL TOQUE POESIA 0,8KG",      "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL TOQUE POESIA 1,6KG",      "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL TOQUE POESIA 2,4KG",      "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 18, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL ALEGRES ENCANTOS 0,8KG",  "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL ALEGRES ENCANTOS 1,6KG",  "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 21, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 2, "sku": "AMACITEL ALEGRES ENCANTOS 2,4KG",  "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 18, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    # LINHA 3
    {"linha": 3, "sku": "BONNY 1KG",                        "gramatura_kg": 1.0, "pacote_por_fardo": 20, "fardo_por_palete": 54, "velocidade_ppm": 30, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "BONNY 1,6KG",                      "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "BONNY 4KG",                        "gramatura_kg": 4.0, "pacote_por_fardo": 4,  "fardo_por_palete": 72, "velocidade_ppm": 12, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "QUALIMP 1,6KG",                    "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "QUALIMP 4KG",                      "gramatura_kg": 4.0, "pacote_por_fardo": 4,  "fardo_por_palete": 72, "velocidade_ppm": 12, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "UNI LIMP 1,6KG",                   "gramatura_kg": 1.6, "pacote_por_fardo": 10, "fardo_por_palete": 56, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "FELITA 1,6KG",                     "gramatura_kg": 1.6, "pacote_por_fardo": 10, "fardo_por_palete": 56, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "SHINE 4KG",                        "gramatura_kg": 4.0, "pacote_por_fardo": 4,  "fardo_por_palete": 72, "velocidade_ppm": 12, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL TOQUE POESIA 1,6KG",      "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL TOQUE POESIA 2,4KG",      "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 18, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL TOQUE POESIA 4KG",        "gramatura_kg": 4.0, "pacote_por_fardo": 4,  "fardo_por_palete": 72, "velocidade_ppm": 12, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL ALEGRES ENCANTOS 1,6KG",  "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 20, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL ALEGRES ENCANTOS 2,4KG",  "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 18, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    {"linha": 3, "sku": "AMACITEL ALEGRES ENCANTOS 4KG",    "gramatura_kg": 4.0, "pacote_por_fardo": 4,  "fardo_por_palete": 72, "velocidade_ppm": 12, "carga_horaria_turno1": 8.46, "carga_horaria_turno2": 8.71, "validado": True},
    # LINHA 4 (nao validado)
    {"linha": 4, "sku": "BONNY 0,8KG",                      "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "BONNY 1KG",                        "gramatura_kg": 1.0, "pacote_por_fardo": 20, "fardo_por_palete": 54, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "BONNY 1,6KG",                      "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "QUALIMP 0,8KG",                    "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "QUALIMP COCO 0,8KG",               "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "QUALIMP 1,6KG",                    "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete": 56, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "UNI LIMP 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "UNI LIMP 1,6KG",                   "gramatura_kg": 1.6, "pacote_por_fardo": 12, "fardo_por_palete":  5, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "FELITA 0,8KG",                     "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "FELITA 1,6KG",                     "gramatura_kg": 1.6, "pacote_por_fardo": 10, "fardo_por_palete": 56, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AROMASIL 0,8KG",                   "gramatura_kg": 0.8, "pacote_por_fardo": 20, "fardo_por_palete": 63, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL TOQUE POESIA 0,8KG",      "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL TOQUE POESIA 1,6KG",      "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL TOQUE POESIA 2,4KG",      "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL ALEGRES ENCANTOS 0,8KG",  "gramatura_kg": 0.8, "pacote_por_fardo": 16, "fardo_por_palete": 64, "velocidade_ppm": 35, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL ALEGRES ENCANTOS 1,6KG",  "gramatura_kg": 1.6, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
    {"linha": 4, "sku": "AMACITEL ALEGRES ENCANTOS 2,4KG",  "gramatura_kg": 2.4, "pacote_por_fardo": 7,  "fardo_por_palete": 72, "velocidade_ppm": 25, "carga_horaria_turno1": 8.8, "carga_horaria_turno2": 8.8, "validado": False, "observacoes": "Linha nao validada"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset = settings.RESET_SEED
        if reset:
            db.query(BatidaManipulacao).delete()
            db.query(ParadaManipulacao).delete()
            db.query(RelatorioManipulacao).delete()
            db.query(ParadaEnvase).delete()
            db.query(RelatorioEnvase).delete()
            db.query(LinhaCapacidade).delete()
            db.query(ProdUser).delete()
            db.commit()

        if not db.query(ProdUser).first():
            admin = ProdUser(
                nome="Administrador",
                email="admin@producao.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                cargo="Administrador do Sistema",
                setor="ambos"
            )
            gestor = ProdUser(
                nome="Gestor de Producao",
                email="gestor@producao.com",
                hashed_password=get_password_hash("gestor123"),
                role="gestor",
                cargo="Gerente de Producao",
                setor="ambos"
            )
            op_env = ProdUser(
                nome="Operador Envase",
                email="envase@producao.com",
                hashed_password=get_password_hash("envase123"),
                role="tecnico",
                cargo="Operador de Envase",
                setor="envase"
            )
            op_man = ProdUser(
                nome="Operador Manipulacao",
                email="manipulacao@producao.com",
                hashed_password=get_password_hash("manipulacao123"),
                role="tecnico",
                cargo="Operador de Manipulacao",
                setor="manipulacao"
            )
            db.add_all([admin, gestor, op_env, op_man])
            db.commit()

        if not db.query(LinhaCapacidade).first():
            for row in BASE_CAPACIDADE:
                item = LinhaCapacidade(**row)
                item.min_por_hora = 60.0
                calcular_caps(item)
                db.add(item)
            db.commit()

    finally:
        db.close()
    yield


app = FastAPI(title="Sistema de Producao - Qualimpel", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api/auth",         tags=["Auth"])
app.include_router(users.router,        prefix="/api/users",        tags=["Usuarios"])
app.include_router(capacidade.router,   prefix="/api/capacidade",   tags=["Base de Capacidade"])
app.include_router(envase.router,       prefix="/api/envase",       tags=["Envase"])
app.include_router(manipulacao.router,  prefix="/api/manipulacao",  tags=["Manipulacao"])
app.include_router(dashboard.router,    prefix="/api/dashboard",    tags=["Dashboard"])

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/health")
def health():
    return {"status": "ok"}
