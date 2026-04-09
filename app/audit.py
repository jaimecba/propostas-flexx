# app/audit.py

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models import Base

# 
# MODEL: Auditoria (Rastreamento de Mudanças)
# 

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tabela = Column(String(100), nullable=False, index=True)  # Nome da tabela (ex: propostas)
    registro_id = Column(Integer, nullable=False, index=True)  # ID do registro que foi alterado
    acao = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    usuario_nome = Column(String(255), nullable=True)  # Nome do usuário (backup)
    campo = Column(String(100), nullable=True)  # Campo que foi alterado
    valor_anterior = Column(Text, nullable=True)  # Valor antes da mudança
    valor_novo = Column(Text, nullable=True)  # Valor depois da mudança
    descricao = Column(Text, nullable=True)  # Descrição da mudança
    ip_origem = Column(String(45), nullable=True)  # IP de onde veio a requisição
    user_agent = Column(Text, nullable=True)  # Navegador/Cliente
    data_hora = Column(DateTime, default=datetime.utcnow, index=True)  # Quando aconteceu

    def __repr__(self):
        return f"<Auditoria(id={self.id}, tabela='{self.tabela}', acao='{self.acao}', data_hora='{self.data_hora}')>"


# 
# FUNÇÕES AUXILIARES PARA AUDITORIA
# 

def registrar_auditoria(
    db,
    tabela: str,
    registro_id: int,
    acao: str,
    usuario_id: Optional[int] = None,
    usuario_nome: Optional[str] = None,
    campo: Optional[str] = None,
    valor_anterior: Optional[str] = None,
    valor_novo: Optional[str] = None,
    descricao: Optional[str] = None,
    ip_origem: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Registra uma mudança na auditoria
    
    Parâmetros:
    - db: Sessão do banco de dados
    - tabela: Nome da tabela (ex: 'propostas')
    - registro_id: ID do registro que foi alterado
    - acao: Tipo de ação (CREATE, UPDATE, DELETE)
    - usuario_id: ID do usuário que fez a mudança
    - usuario_nome: Nome do usuário (backup)
    - campo: Campo específico que foi alterado
    - valor_anterior: Valor antes da mudança
    - valor_novo: Valor depois da mudança
    - descricao: Descrição da mudança
    - ip_origem: IP de origem da requisição
    - user_agent: User agent do cliente
    """
    
    auditoria = Auditoria(
        tabela=tabela,
        registro_id=registro_id,
        acao=acao,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        campo=campo,
        valor_anterior=valor_anterior,
        valor_novo=valor_novo,
        descricao=descricao,
        ip_origem=ip_origem,
        user_agent=user_agent
    )
    
    db.add(auditoria)
    db.commit()
    
    return auditoria


def obter_historico_auditoria(db, tabela: str, registro_id: int):
    """
    Obtém o histórico completo de mudanças de um registro
    """
    return db.query(Auditoria).filter(
        Auditoria.tabela == tabela,
        Auditoria.registro_id == registro_id
    ).order_by(Auditoria.data_hora.desc()).all()


def obter_auditoria_por_usuario(db, usuario_id: int):
    """
    Obtém todas as mudanças feitas por um usuário específico
    """
    return db.query(Auditoria).filter(
        Auditoria.usuario_id == usuario_id
    ).order_by(Auditoria.data_hora.desc()).all()


def obter_auditoria_por_acao(db, acao: str):
    """
    Obtém todas as mudanças de um tipo específico (CREATE, UPDATE, DELETE)
    """
    return db.query(Auditoria).filter(
        Auditoria.acao == acao
    ).order_by(Auditoria.data_hora.desc()).all()