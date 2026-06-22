from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class UserCreate(BaseModel):
    nome: str
    email: str
    password: str
    role: str = "tecnico"
    cargo: Optional[str] = None
    matricula: Optional[str] = None
    telefone: Optional[str] = None
    setor: Optional[str] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    role: Optional[str] = None
    cargo: Optional[str] = None
    matricula: Optional[str] = None
    telefone: Optional[str] = None
    setor: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    nome: str
    email: str
    role: str
    cargo: Optional[str]
    matricula: Optional[str]
    telefone: Optional[str]
    setor: Optional[str]
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class LinhaCapacidadeCreate(BaseModel):
    linha: int
    sku: str
    gramatura_kg: float
    pacote_por_fardo: Optional[int] = None
    fardo_por_palete: Optional[int] = None
    velocidade_ppm: float
    min_por_hora: float = 60.0
    carga_horaria_turno1: Optional[float] = None
    carga_horaria_turno2: Optional[float] = None
    validado: bool = True
    observacoes: Optional[str] = None

class LinhaCapacidadeUpdate(BaseModel):
    sku: Optional[str] = None
    gramatura_kg: Optional[float] = None
    pacote_por_fardo: Optional[int] = None
    fardo_por_palete: Optional[int] = None
    velocidade_ppm: Optional[float] = None
    min_por_hora: Optional[float] = None
    carga_horaria_turno1: Optional[float] = None
    carga_horaria_turno2: Optional[float] = None
    validado: Optional[bool] = None
    observacoes: Optional[str] = None

class LinhaCapacidadeOut(BaseModel):
    id: int
    linha: int
    sku: str
    gramatura_kg: float
    pacote_por_fardo: Optional[int]
    fardo_por_palete: Optional[int]
    velocidade_ppm: float
    min_por_hora: float
    carga_horaria_turno1: Optional[float]
    carga_horaria_turno2: Optional[float]
    cap_fardo_hora: Optional[float]
    cap_fardo_turno: Optional[float]
    cap_kg_hora: Optional[float]
    cap_kg_turno: Optional[float]
    cap_fardo_dia: Optional[float]
    cap_kg_dia: Optional[float]
    validado: bool
    observacoes: Optional[str]
    updated_at: Optional[datetime]
    class Config:
        from_attributes = True

class ParadaCreate(BaseModel):
    hora_inicio: str
    hora_fim: Optional[str] = None
    tempo_minutos: Optional[float] = None
    categoria: Optional[str] = None
    ocorrencia: str
    acao: Optional[str] = None

class ParadaOut(BaseModel):
    id: int
    hora_inicio: str
    hora_fim: Optional[str]
    tempo_minutos: Optional[float]
    categoria: Optional[str]
    ocorrencia: str
    acao: Optional[str]
    class Config:
        from_attributes = True

class RelatorioEnvaseCreate(BaseModel):
    data: date
    turno: str
    linha: int
    maquina: Optional[str] = None
    produto: str
    sku: Optional[str] = None
    marca: Optional[str] = None
    gramatura_kg: Optional[float] = None
    pacote_por_fardo: Optional[int] = None
    operador_nome: Optional[str] = None
    leitura_empacotadora_pacotes: Optional[int] = None
    leitura_enfardadeira_fardos: Optional[int] = None
    peso_alto_unidades: Optional[int] = None
    peso_alto_kg: Optional[float] = None
    peso_bom_unidades: Optional[int] = None
    peso_bom_kg: Optional[float] = None
    peso_baixo_unidades: Optional[int] = None
    peso_baixo_kg: Optional[float] = None
    peso_medio: Optional[float] = None
    perda_peso_percentual: Optional[float] = None
    perda_emb_empacotadora_kg: Optional[float] = None
    perda_emb_enfardadeira_kg: Optional[float] = None
    velocidade_real_ppm: Optional[float] = None
    total_fardos_produzidos: Optional[int] = None
    total_kg_produzidos: Optional[float] = None
    tempo_disponivel_min: Optional[float] = None
    observacoes: Optional[str] = None
    paradas: List[ParadaCreate] = []

class RelatorioEnvaseOut(BaseModel):
    id: int
    data: date
    turno: str
    linha: int
    maquina: Optional[str]
    produto: str
    sku: Optional[str]
    marca: Optional[str]
    gramatura_kg: Optional[float]
    pacote_por_fardo: Optional[int]
    operador_nome: Optional[str]
    leitura_empacotadora_pacotes: Optional[int]
    leitura_enfardadeira_fardos: Optional[int]
    peso_alto_unidades: Optional[int]
    peso_alto_kg: Optional[float]
    peso_bom_unidades: Optional[int]
    peso_bom_kg: Optional[float]
    peso_baixo_unidades: Optional[int]
    peso_baixo_kg: Optional[float]
    peso_medio: Optional[float]
    perda_peso_percentual: Optional[float]
    perda_emb_empacotadora_kg: Optional[float]
    perda_emb_enfardadeira_kg: Optional[float]
    velocidade_real_ppm: Optional[float]
    total_fardos_produzidos: Optional[int]
    total_kg_produzidos: Optional[float]
    cap_teorica_fardos_turno: Optional[float]
    cap_teorica_kg_turno: Optional[float]
    produtividade_fardos_pct: Optional[float]
    produtividade_kg_pct: Optional[float]
    total_minutos_parada: Optional[float]
    tempo_disponivel_min: Optional[float]
    oee_disponibilidade: Optional[float]
    oee_performance: Optional[float]
    oee_qualidade: Optional[float]
    oee: Optional[float]
    observacoes: Optional[str]
    created_at: datetime
    paradas: List[ParadaOut] = []
    class Config:
        from_attributes = True

class BatidaCreate(BaseModel):
    equipamento: str
    numero_batida: int
    kg_por_batida: float
    produto: Optional[str] = None
    observacao: Optional[str] = None

class BatidaOut(BaseModel):
    id: int
    equipamento: str
    numero_batida: int
    kg_por_batida: float
    total_kg: Optional[float]
    produto: Optional[str]
    observacao: Optional[str]
    class Config:
        from_attributes = True

class RelatorioManipulacaoCreate(BaseModel):
    data: date
    turno: str
    produto: str
    operador_nome: Optional[str] = None
    tempo_disponivel_min: Optional[float] = None
    observacoes: Optional[str] = None
    paradas: List[ParadaCreate] = []
    batidas: List[BatidaCreate] = []

class RelatorioManipulacaoOut(BaseModel):
    id: int
    data: date
    turno: str
    produto: str
    operador_nome: Optional[str]
    total_kg_produzidos: Optional[float]
    total_minutos_parada: Optional[float]
    tempo_disponivel_min: Optional[float]
    eficiencia_percentual: Optional[float]
    observacoes: Optional[str]
    created_at: datetime
    paradas: List[ParadaOut] = []
    batidas: List[BatidaOut] = []
    class Config:
        from_attributes = True
