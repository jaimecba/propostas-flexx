# app/schemas.py
from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# ============================================================================
# SCHEMAS: Usuario
# ============================================================================

class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    papel: str = "vendedor"

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    papel: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SCHEMAS: Proposta
# ============================================================================

class PropostaBase(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    email: EmailStr
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    plano: str
    usuarios: int
    treinamento_tipo: Optional[str] = None
    setup_padrao: Optional[Decimal] = None
    setup_ajustado: Optional[Decimal] = None
    treinamento_valor: Optional[Decimal] = 0
    desconto_percentual: Optional[Decimal] = None
    desconto_valor: Optional[Decimal] = 0
    observacoes: Optional[str] = None

    @field_validator('usuarios')
    @classmethod
    def validar_usuarios(cls, v):
        if v < 1 or v > 999:
            raise ValueError('Número de usuários deve estar entre 1 e 999')
        return v

    @field_validator('plano')
    @classmethod
    def validar_plano(cls, v):
        planos_validos = ['Basic', 'PRO', 'Ultimate']
        if v not in planos_validos:
            raise ValueError(f'Plano deve ser um de: {", ".join(planos_validos)}')
        return v

class PropostaCreate(PropostaBase):
    pass

class PropostaUpdate(BaseModel):
    razao_social: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    setup_ajustado: Optional[Decimal] = None
    desconto_percentual: Optional[Decimal] = None
    desconto_valor: Optional[Decimal] = None
    observacoes: Optional[str] = None

class PropostaResponse(PropostaBase):
    id: int
    hash_id: str
    usuarios_arredondados: Optional[int]
    valor_mensal: Decimal
    subtotal: Optional[Decimal]
    total: Optional[Decimal]
    status: str
    vendedor_id: Optional[int]
    gerente_id: Optional[int]
    data_criacao: datetime
    data_atualizacao: datetime
    data_validade: Optional[datetime]
    data_inicio_servico: Optional[str]

    class Config:
        from_attributes = True

# ============================================================================
# SCHEMAS: Analytics
# ============================================================================

class AnalyticsResponse(BaseModel):
    id: int
    proposta_id: int
    ip: Optional[str]
    user_agent: Optional[str]
    visualizado_em: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SCHEMAS: PropostaHistorico
# ============================================================================

class PropostaHistoricoResponse(BaseModel):
    id: int
    proposta_id: int
    campo: str
    valor_anterior: Optional[str]
    valor_novo: Optional[str]
    alterado_por: Optional[int]
    alterado_em: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SCHEMAS: PropostaCompartilhamento
# ============================================================================

class PropostaCompartilhamentoResponse(BaseModel):
    id: int
    proposta_id: int
    tipo: str
    destinatario: Optional[str]
    compartilhado_em: datetime
    ip_origem: Optional[str]

    class Config:
        from_attributes = True