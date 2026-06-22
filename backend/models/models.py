from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


# ─── USUÁRIOS ────────────────────────────────────────────────────────────────

class ProdUser(Base):
    __tablename__ = "prod_users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="tecnico")   # admin / gestor / tecnico
    cargo = Column(String(100), nullable=True)
    matricula = Column(String(50), nullable=True)
    telefone = Column(String(20), nullable=True)
    setor = Column(String(50), nullable=True)      # envase / manipulacao / ambos
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── BASE DE CAPACIDADE ───────────────────────────────────────────────────────

class LinhaCapacidade(Base):
    """Base de capacidade produtiva por linha/SKU — editável pelo admin."""
    __tablename__ = "prod_linha_capacidade"

    id = Column(Integer, primary_key=True, index=True)
    linha = Column(Integer, nullable=False)                    # 1, 2, 3, 4
    sku = Column(String(150), nullable=False)
    gramatura_kg = Column(Float, nullable=False)               # ex: 0.4, 0.8, 1.0, 1.6
    pacote_por_fardo = Column(Integer, nullable=True)
    fardo_por_palete = Column(Integer, nullable=True)
    velocidade_ppm = Column(Float, nullable=False)             # pacotes por minuto
    min_por_hora = Column(Float, default=60.0)
    carga_horaria_turno1 = Column(Float, nullable=True)        # horas disponíveis T1
    carga_horaria_turno2 = Column(Float, nullable=True)        # horas disponíveis T2
    # Capacidades calculadas (salvas para referência rápida)
    cap_fardo_hora = Column(Float, nullable=True)
    cap_fardo_turno = Column(Float, nullable=True)
    cap_kg_hora = Column(Float, nullable=True)
    cap_kg_turno = Column(Float, nullable=True)
    cap_fardo_dia = Column(Float, nullable=True)
    cap_kg_dia = Column(Float, nullable=True)
    validado = Column(Boolean, default=True)                   # Linha 4 = False
    observacoes = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=True)


# ─── ENVASE ──────────────────────────────────────────────────────────────────

class RelatorioEnvase(Base):
    __tablename__ = "prod_relatorio_envase"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False)
    turno = Column(String(10), nullable=False)          # A / B / C
    linha = Column(Integer, nullable=False)             # 1, 2, 3, 4
    maquina = Column(String(100), nullable=True)
    produto = Column(String(150), nullable=False)
    sku = Column(String(150), nullable=True)
    marca = Column(String(100), nullable=True)
    gramatura_kg = Column(Float, nullable=True)
    pacote_por_fardo = Column(Integer, nullable=True)
    operador_nome = Column(String(150), nullable=True)
    operador_id = Column(Integer, nullable=True)

    # Leituras de contadores
    leitura_empacotadora_pacotes = Column(Integer, nullable=True)
    leitura_enfardadeira_fardos = Column(Integer, nullable=True)

    # Check de peso
    peso_alto_unidades = Column(Integer, nullable=True)
    peso_alto_kg = Column(Float, nullable=True)
    peso_bom_unidades = Column(Integer, nullable=True)
    peso_bom_kg = Column(Float, nullable=True)
    peso_baixo_unidades = Column(Integer, nullable=True)
    peso_baixo_kg = Column(Float, nullable=True)
    peso_medio = Column(Float, nullable=True)
    perda_peso_percentual = Column(Float, nullable=True)

    # Perda de embalagem
    perda_emb_empacotadora_kg = Column(Float, nullable=True)
    perda_emb_enfardadeira_kg = Column(Float, nullable=True)

    # Produção real
    velocidade_real_ppm = Column(Float, nullable=True)
    total_fardos_produzidos = Column(Integer, nullable=True)
    total_kg_produzidos = Column(Float, nullable=True)

    # Capacidade teórica (copiada da base no momento do registro)
    cap_teorica_fardos_turno = Column(Float, nullable=True)
    cap_teorica_kg_turno = Column(Float, nullable=True)

    # Produtividade calculada
    produtividade_fardos_pct = Column(Float, nullable=True)   # real/teórico %
    produtividade_kg_pct = Column(Float, nullable=True)

    # Tempo total de parada no turno
    total_minutos_parada = Column(Float, nullable=True)
    # Tempo disponível do turno em minutos (usado para OEE)
    tempo_disponivel_min = Column(Float, nullable=True)

    # OEE
    oee_disponibilidade = Column(Float, nullable=True)
    oee_performance = Column(Float, nullable=True)
    oee_qualidade = Column(Float, nullable=True)
    oee = Column(Float, nullable=True)

    observacoes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    paradas = relationship("ParadaEnvase", back_populates="relatorio", cascade="all, delete-orphan")


class ParadaEnvase(Base):
    __tablename__ = "prod_parada_envase"

    id = Column(Integer, primary_key=True, index=True)
    relatorio_id = Column(Integer, nullable=False)
    hora_inicio = Column(String(10), nullable=False)
    hora_fim = Column(String(10), nullable=True)
    tempo_minutos = Column(Float, nullable=True)
    categoria = Column(String(50), nullable=True)
    # mecanica / eletrica / setup / qualidade / falta_material / operacional / higienizacao / outros
    ocorrencia = Column(Text, nullable=False)
    acao = Column(Text, nullable=True)

    relatorio = relationship("RelatorioEnvase", back_populates="paradas")


# ─── MANIPULAÇÃO ─────────────────────────────────────────────────────────────

class RelatorioManipulacao(Base):
    __tablename__ = "prod_relatorio_manipulacao"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False)
    turno = Column(String(10), nullable=False)
    produto = Column(String(150), nullable=False)
    operador_nome = Column(String(150), nullable=True)
    operador_id = Column(Integer, nullable=True)

    total_kg_produzidos = Column(Float, nullable=True)
    total_minutos_parada = Column(Float, nullable=True)
    tempo_disponivel_min = Column(Float, nullable=True)

    # Eficiência (tempo produtivo / disponível)
    eficiencia_percentual = Column(Float, nullable=True)

    observacoes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    paradas = relationship("ParadaManipulacao", back_populates="relatorio", cascade="all, delete-orphan")
    batidas = relationship("BatidaManipulacao", back_populates="relatorio", cascade="all, delete-orphan")


class ParadaManipulacao(Base):
    __tablename__ = "prod_parada_manipulacao"

    id = Column(Integer, primary_key=True, index=True)
    relatorio_id = Column(Integer, nullable=False)
    hora_inicio = Column(String(10), nullable=False)
    hora_fim = Column(String(10), nullable=True)
    tempo_minutos = Column(Float, nullable=True)
    categoria = Column(String(50), nullable=True)
    ocorrencia = Column(Text, nullable=False)
    acao = Column(Text, nullable=True)

    relatorio = relationship("RelatorioManipulacao", back_populates="paradas")


class BatidaManipulacao(Base):
    __tablename__ = "prod_batida_manipulacao"

    id = Column(Integer, primary_key=True, index=True)
    relatorio_id = Column(Integer, nullable=False)
    equipamento = Column(String(50), nullable=False)   # misturador / duplo_cone
    numero_batida = Column(Integer, nullable=False)
    kg_por_batida = Column(Float, nullable=False)
    total_kg = Column(Float, nullable=True)
    produto = Column(String(150), nullable=True)
    observacao = Column(Text, nullable=True)

    relatorio = relationship("RelatorioManipulacao", back_populates="batidas")
