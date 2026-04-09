from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime

# ============================================================================
# SCHEMA: PrecoFornecedor
# ============================================================================
class PrecoFornecedorSchema(BaseModel):
    id: int
    plano: str
    faixa_inicio: int
    faixa_fim: int
    preco_unitario: Decimal
    ativo: bool
    
    class Config:
        from_attributes = True

# ============================================================================
# SCHEMA: Markup
# ============================================================================
class MarkupSchema(BaseModel):
    id: int
    plano: str
    markup_percentual: Decimal
    ativo: bool
    
    class Config:
        from_attributes = True

# ============================================================================
# SCHEMA: Resultado do Orçamento
# ============================================================================
class OrcamentoResultadoSchema(BaseModel):
    usuarios_entrada: int
    faixa_flexx: int
    preco_unitario: Decimal
    markup_percentual: Decimal
    preco_final: Decimal
    detalhamento: str

# ============================================================================
# SCHEMA: Histórico de Preços
# ============================================================================
class PrecoHistoricoSchema(BaseModel):
    id: int
    tabela_origem: str
    plano: str
    faixa_inicio: Optional[int]
    faixa_fim: Optional[int]
    valor_anterior: Optional[Decimal]
    valor_novo: Optional[Decimal]
    alterado_por: Optional[str]
    data_alteracao: datetime
    
    class Config:
        from_attributes = True
