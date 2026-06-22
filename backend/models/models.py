from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy import event
from datetime import datetime
from ..core.database import Base


class ProdUser(Base):
    __tablename__ = "prod_users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="tecnico")
    cargo = Column(String(100), nullable=True)
    matricula = Column(String(50), nullable=True)
    telefone = Column(String(20), nullable=True)
    setor = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LinhaCapacidade(Base):
    __tablename__ = "prod_linha_capacidade"

    id = Column(Integer, primary_key=True, index=True)
    linha = Column(Integer, nullable=False)
    sku = Column(String(150), nullable=False)
    gramatura_kg = Column(Float, nullable=False)
    pacote_por_fardo = Column(Integer, nullable=True)
    fardo_por_palete = Column(Integer, nullable=True)
    velocidade_ppm = Column(Float, nullable=False)
    min_por_hora = Column(Float, default=60.0)
    carga_horaria_turno1 = Column(Float, nullable=True)
    carga_horaria_turno2 = Column(Float, nullable=True)
    cap_fardo_hora = Column(Float, nullable=True)
    cap_fardo_turno = Column(Float, nullable=True)
    cap_kg_hora = Column(Float, nullable=True)
    cap_kg_turno = Column(Float, nullable=True)
    cap_fardo_dia = Column(Float, nullable=True)
    cap_kg_dia = Column(Float, nullable=True)
    validado = Column(Boolean, default=True)
    observacoes = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=True)


class RelatorioEnvase(Base):
    __tablename__ = "prod_relatorio_envase"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False)
    turno = Column(String(10), nullable=False)
    linha = Column(Integer, nullable=False)
    maquina = Column(String(100), nullable=True)
    produto = Column(String(150), nullable=False)
    sku = Column(String(150), nullable=True)
    marca = Column(String(100), nullable=True)
    gramatura_kg = Column(Float, nullable=True)
    pacote_por_fardo = Column(Integer, nullable=True)
    operador_nome = Column(String(150), nullable=True)
    operador_id = Column(Integer, nullable=True)
    leitura_empacotadora_pacotes = Column(Integer, nullable=True)
    leitura_enfardadeira_fardos = Column(Integer, nullable=True)
    peso_alto_unidades = Column(Integer, nullable=True)
    peso_alto_kg = Column(Float, nullable=True)
    peso_bom_unidades = Column(Integer, nullable=True)
    peso_bom_kg = Column(Float, nullable=True)
    peso_baixo_unidades = Column(Integer, nullable=True)
    peso_baixo_kg = Column(Float, nullable=True)
    peso_medio = Column(Float, nullable=True)
    perda_peso_percentual = Column(Float, nullable=True)
    perda_emb_empacotadora_kg = Column(Float, nullable=True)
    perda_emb_enfardadeira_kg = Column(Float, nullable=True)
    velocidade_real_ppm = Column(Float, nullable=True)
    total_fardos_produzidos = Column(Integer, nullable=True)
    total_kg_produzidos = Column(Float, nullable=True)
    cap_teorica_fardos_turno = Column(Float, nullable=True)
    cap_teorica_kg_turno = Column(Float, nullable=True)
    produtividade_fardos_pct = Column(Float, nullable=True)
    produtividade_kg_pct = Column(Float, nullable=True)
    total_minutos_parada = Column(Float, nullable=True)
    tempo_disponivel_min = Column(Float, nullable=True)
    oee_disponibilidade = Column(Float, nullable=True)
    oee_performance = Column(Float, nullable=True)
    oee_qualidade = Column(Float, nullable=True)
    oee = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    paradas = relationship(
        "ParadaEnvase",
        primaryjoin="RelatorioEnvase.id == foreign(ParadaEnvase.relatorio_id)",
        back_populates="relatorio",
        cascade="all, delete-orphan"
    )


class ParadaEnvase(Base):
    __tablename__ = "prod_parada_envase"

    id = Column(Integer, primary_key=True, index=True)
    relatorio_id = Column(Integer, nullable=False)
    hora_inicio = Column(String(10), nullable=False)
    hora_fim = Column(String(10), nullable=True)
    tempo_minutos = Column(Float, nullable=True)
    categoria = Column(String(50), nullable=True)
    ocorrencia = Column(Text, nullable=False)
    acao = Column(Text, nullable=True)

    relatorio = relationship(
        "RelatorioEnvase",
        primaryjoin="foreign(ParadaEnvase.relatorio_id) == RelatorioEnvase.id",
        back_populates="paradas"
    )


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
    eficiencia_percentual = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    paradas = relationship(
        "ParadaManipulacao",
        primaryjoin="RelatorioManipulacao.id == foreign(ParadaManipulacao.relatorio_id)",
        back_populates="relatorio",
        cascade="all, delete-orphan"
    )
    batidas = relationship(
        "BatidaManipulacao",
        primaryjoin="RelatorioManipulacao.id == foreign(BatidaManipulacao.relatorio_id)",
        back_populates="relatorio",
        cascade="all, delete-orphan"
    )


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

    relatorio = relationship(
        "RelatorioManipulacao",
        primaryjoin="foreign(ParadaManipulacao.relatorio_id) == RelatorioManipulacao.id",
        back_populates="paradas"
    )


class BatidaManipulacao(Base):
    __tablename__ = "prod_batida_manipulacao"

    id = Column(Integer, primary_key=True, index=True)
    relatorio_id = Column(Integer, nullable=False)
    equipamento = Column(String(50), nullable=False)
    numero_batida = Column(Integer, nullable=False)
    kg_por_batida = Column(Float, nullable=False)
    total_kg = Column(Float, nullable=True)
    produto = Column(String(150), nullable=True)
    observacao = Column(Text, nullable=True)

    relatorio = relationship(
        "RelatorioManipulacao",
        primaryjoin="foreign(BatidaManipulacao.relatorio_id) == RelatorioManipulacao.id",
        back_populates="batidas"
    )
