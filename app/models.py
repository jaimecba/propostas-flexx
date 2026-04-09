# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import enum

Base = declarative_base()

# ============================================================================
# ENUM: Status da Proposta
# ============================================================================
class StatusProposta(str, enum.Enum):
    PENDENTE = "PENDENTE"
    ACEITA = "ACEITA"
    REJEITADA = "REJEITADA"
    EXPIRADA = "EXPIRADA"
    CANCELADA = "CANCELADA"

# ============================================================================
# ENUM: Papel do Usuário
# ============================================================================
class PapelUsuario(str, enum.Enum):
    VENDEDOR = "vendedor"
    GERENTE = "gerente"
    ADMIN = "admin"
    CLIENTE = "cliente"

# ============================================================================
# ENUM: Tipo de Treinamento
# ============================================================================
class TipoTreinamento(str, enum.Enum):
    ONLINE = "Online"
    PRESENCIAL = "Presencial"
    HIBRIDO = "Híbrido"

# ============================================================================
# ENUM: Tipo de Compartilhamento
# ============================================================================
class TipoCompartilhamento(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINK = "link"

# ============================================================================
# MODEL: Usuario
# ============================================================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    papel = Column(String(50), default=PapelUsuario.VENDEDOR.value)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    propostas_criadas = relationship("Proposta", foreign_keys="Proposta.vendedor_id", back_populates="vendedor")
    propostas_gerenciadas = relationship("Proposta", foreign_keys="Proposta.gerente_id", back_populates="gerente")
    historicos = relationship("PropostaHistorico", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(id={self.id}, nome='{self.nome}', email='{self.email}', papel='{self.papel}')>"

# ============================================================================
# MODEL: Proposta (ATUALIZADO)
# ============================================================================
class Proposta(Base):
    __tablename__ = "propostas"

    # Identificadores
    id = Column(Integer, primary_key=True, index=True)
    hash_id = Column(String(50), unique=True, nullable=False, index=True)

    # Dados do Cliente
    cnpj = Column(String(18), nullable=False, index=True)
    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    telefone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True, index=True)

    # Plano e Usuários
    plano = Column(String(50), nullable=False)
    usuarios = Column(Integer, nullable=False)
    usuarios_arredondados = Column(Integer, nullable=True)
    valor_mensal = Column(Numeric(10, 2), nullable=False)

    # Treinamento e Setup
    treinamento_tipo = Column(String(50), nullable=True)
    setup_padrao = Column(Numeric(10, 2), nullable=True)
    setup_ajustado = Column(Numeric(10, 2), nullable=True)
    treinamento_valor = Column(Numeric(10, 2), default=0)

    # Desconto
    desconto_percentual = Column(Numeric(5, 2), nullable=True)
    desconto_valor = Column(Numeric(10, 2), default=0)

    # Totais
    subtotal = Column(Numeric(10, 2), nullable=True)
    total = Column(Numeric(10, 2), nullable=True)

    # Observações
    observacoes = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default=StatusProposta.PENDENTE.value, index=True)

    # Vendedor e Gerente
    vendedor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)
    gerente_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True)

    # Datas
    data_criacao = Column(DateTime, default=datetime.utcnow, index=True)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_validade = Column(DateTime, nullable=True)
    data_inicio_servico = Column(String(10), nullable=True)  # Formato: YYYY-MM-DD

    # Soft Delete
    ativo = Column(Boolean, default=True, index=True)  # True = ativo, False = deletado logicamente
    data_delecao = Column(DateTime, nullable=True)  # Data quando foi deletado

    # Rastreamento
    ip_criacao = Column(String(45), nullable=True)
    user_agent_criacao = Column(Text, nullable=True)

       # Relacionamentos
    vendedor = relationship("Usuario", foreign_keys=[vendedor_id], back_populates="propostas_criadas")
    gerente = relationship("Usuario", foreign_keys=[gerente_id], back_populates="propostas_gerenciadas")
    analytics = relationship("Analytics", back_populates="proposta", cascade="all, delete-orphan")
    historicos = relationship("PropostaHistorico", back_populates="proposta", cascade="all, delete-orphan")
    compartilhamentos = relationship("PropostaCompartilhamento", back_populates="proposta", cascade="all, delete-orphan")

    servicos_adicionais = Column(JSON, nullable=True)  # Para armazenar JSON dos serviços
    taxa_unica = Column(Numeric(10, 2), default=0)     # Para a taxa única
    

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    def valor_total(self) -> float:
        """Calcula o valor total da proposta"""
        setup = float(self.setup_ajustado or self.setup_padrao or 0)
        treinamento = float(self.treinamento_valor or 0)
        desconto = float(self.desconto_valor or 0)
        
        total = (float(self.valor_mensal) + setup + treinamento) - desconto
        return max(total, 0)  # Garante que não seja negativo

    def is_expirada(self) -> bool:
        """Verifica se a proposta expirou"""
        if not self.data_validade:
            return False
        return datetime.utcnow() > self.data_validade

    def total_visualizacoes(self) -> int:
        """Retorna o total de visualizações"""
        return len(self.analytics) if self.analytics else 0

    def dias_para_expirar(self) -> int:
        """Retorna quantos dias faltam para expirar"""
        if not self.data_validade:
            return 0
        delta = self.data_validade - datetime.utcnow()
        return max(delta.days, 0)
    
    # Soft Delete (NOVO)
    def deletar_logicamente(self):
        """Deleta a proposta logicamente (Soft Delete)"""
        self.ativo = False
        self.data_delecao = datetime.utcnow()
    
    def restaurar(self):
        """Restaura uma proposta deletada"""
        self.ativo = True
        self.data_delecao = None
        self.data_atualizacao = datetime.utcnow()

    def __repr__(self):
        return f"<Proposta(id={self.id}, hash_id='{self.hash_id}', cliente='{self.razao_social}', status='{self.status}')>"

# ============================================================================
# MODEL: Analytics (Rastreamento de Visualizações)
# ============================================================================
class Analytics(Base):
    __tablename__ = "propostas_analytics"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    visualizado_em = Column(DateTime, default=datetime.utcnow, index=True)

    # Relacionamento
    proposta = relationship("Proposta", back_populates="analytics")

    def __repr__(self):
        return f"<Analytics(id={self.id}, proposta_id={self.proposta_id}, ip='{self.ip}')>"

# ============================================================================
# MODEL: PropostaHistorico (Rastreamento de Alterações)
# ============================================================================
class PropostaHistorico(Base):
    __tablename__ = "propostas_historico"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    campo = Column(String(100), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_novo = Column(Text, nullable=True)
    alterado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    alterado_em = Column(DateTime, default=datetime.utcnow, index=True)

    # Relacionamentos
    proposta = relationship("Proposta", back_populates="historicos")
    usuario = relationship("Usuario", back_populates="historicos")

    def __repr__(self):
        return f"<PropostaHistorico(id={self.id}, proposta_id={self.proposta_id}, campo='{self.campo}')>"

# ============================================================================
# MODEL: PropostaCompartilhamento (Rastreamento de Compartilhamentos)
# ============================================================================
class PropostaCompartilhamento(Base):
    __tablename__ = "propostas_compartilhamentos"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # 'email', 'whatsapp', 'link'
    destinatario = Column(String(255), nullable=True)
    compartilhado_em = Column(DateTime, default=datetime.utcnow, index=True)
    ip_origem = Column(String(45), nullable=True)

    # Relacionamento
    proposta = relationship("Proposta", back_populates="compartilhamentos")

    def __repr__(self):
        return f"<PropostaCompartilhamento(id={self.id}, proposta_id={self.proposta_id}, tipo='{self.tipo}')>"
    
class TabelaPrecosPlanos(Base):
    __tablename__ = "tabela_precos_planos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plano = Column(String(50), nullable=False, index=True)
    faixa_inicio = Column(Integer, nullable=False)
    faixa_fim = Column(Integer, nullable=False)
    valor_mensal = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, index=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TabelaPrecosPlanos(plano='{self.plano}', faixa={self.faixa_inicio}-{self.faixa_fim}, valor={self.valor_mensal})>"


class TabelaPrecosServicosAdicionais(Base):
    __tablename__ = "tabela_precos_servicos_adicionais"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_servico = Column(String(100), nullable=False, index=True)
    plano = Column(String(50), nullable=False, index=True)
    faixa_inicio = Column(Integer, nullable=False)
    faixa_fim = Column(Integer, nullable=False)
    valor_unitario = Column(Numeric(10, 2), nullable=False)
    tipo_cobranca = Column(String(20), nullable=False)  # 'faixa' ou 'quantidade'
    ativo = Column(Boolean, default=True, index=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TabelaPrecosServicosAdicionais(servico='{self.nome_servico}', plano='{self.plano}', faixa={self.faixa_inicio}-{self.faixa_fim}, valor={self.valor_unitario})>"


class TabelaPrecosTreinamentos(Base):
    __tablename__ = "tabela_precos_treinamentos"

    id = Column(Integer, primary_key=True, index=True)
    tipo_treinamento = Column(String(50), nullable=False, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, index=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TabelaPrecosTreinamentos(tipo='{self.tipo_treinamento}', valor={self.valor})>"

# ============================================================================
# MODEL: PrecoFornecedor (NOVO - Preços Unitários do Fornecedor)
# ============================================================================
class PrecoFornecedor(Base):
    __tablename__ = "tabela_precos_fornecedor"
    
    id = Column(Integer, primary_key=True, index=True)
    plano = Column(String(50), nullable=False)
    faixa_inicio = Column(Integer, nullable=False)
    faixa_fim = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PrecoFornecedor(plano='{self.plano}', faixa={self.faixa_inicio}-{self.faixa_fim}, unitario={self.preco_unitario})>"

# ============================================================================
# MODEL: Markup (NOVO - Margem de Lucro por Plano)
# ============================================================================
class Markup(Base):
    __tablename__ = "tabela_markup"
    
    id = Column(Integer, primary_key=True, index=True)
    plano = Column(String(50), nullable=False, unique=True)
    markup_percentual = Column(Numeric(5, 2), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Markup(plano='{self.plano}', markup={self.markup_percentual}%)>"

# ============================================================================
# MODEL: PrecoHistorico (NOVO - Histórico de Alterações de Preços)
# ============================================================================
class PrecoHistorico(Base):
    __tablename__ = "tabela_precos_historico"
    
    id = Column(Integer, primary_key=True, index=True)
    tabela_origem = Column(String(50), nullable=False)
    plano = Column(String(50), nullable=False)
    faixa_inicio = Column(Integer, nullable=True)
    faixa_fim = Column(Integer, nullable=True)
    valor_anterior = Column(Numeric(10, 2), nullable=True)
    valor_novo = Column(Numeric(10, 2), nullable=True)
    alterado_por = Column(String(100), nullable=True)
    data_alteracao = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PrecoHistorico(tabela='{self.tabela_origem}', plano='{self.plano}', data={self.data_alteracao})>"