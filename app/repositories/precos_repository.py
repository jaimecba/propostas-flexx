from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    TabelaPrecosPlanos,
    TabelaPrecosServicosAdicionais,
    TabelaPrecosTreinamentos,
)


def buscar_valor_plano(db: Session, plano: str, faixa: int) -> Decimal:
    registro = (
        db.query(TabelaPrecosPlanos)
        .filter(
            TabelaPrecosPlanos.plano.ilike(plano),
            TabelaPrecosPlanos.faixa_inicio <= faixa,
            TabelaPrecosPlanos.faixa_fim >= faixa,
            TabelaPrecosPlanos.ativo == True
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail=f"Preço não encontrado para o plano '{plano}' na faixa de {faixa} usuários."

        )

    return registro.valor_mensal


def buscar_valor_servico(db: Session, nome_servico: str, plano: str, faixa: int) -> Decimal:
    registro = (
        db.query(TabelaPrecosServicosAdicionais)
        .filter(
            TabelaPrecosServicosAdicionais.nome_servico.ilike(nome_servico),
            TabelaPrecosServicosAdicionais.plano.ilike(plano),
            TabelaPrecosServicosAdicionais.faixa_inicio <= faixa,
            TabelaPrecosServicosAdicionais.faixa_fim >= faixa,
            TabelaPrecosServicosAdicionais.ativo == True
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail=f"Preço não encontrado para o serviço '{nome_servico}' no plano '{plano}' na faixa de {faixa} usuários."
        )

    return registro.valor_unitario


def buscar_valor_treinamento(db: Session, tipo_treinamento: str) -> Decimal:
    registro = (
        db.query(TabelaPrecosTreinamentos)
        .filter(
            TabelaPrecosTreinamentos.tipo_treinamento.ilike(tipo_treinamento),
            TabelaPrecosTreinamentos.ativo == True
        )
        .first()
    )

    if not registro:
        raise HTTPException(
            status_code=404,
            detail=f"Preço não encontrado para o treinamento do tipo '{tipo_treinamento}'."
        )

    return registro.valor


# ============================================================================
# NOVAS FUNÇÕES - Cálculo de Preços com Fornecedor e Markup
# ============================================================================

import math
from app.models import PrecoFornecedor, Markup, PrecoHistorico
from datetime import datetime

class PrecoRepository:
    
    @staticmethod
    def calcular_orcamento(db: Session, plano: str, usuarios: int) -> dict:
        """
        Calcula preço do orçamento conforme lógica Flexx
        
        Exemplo:
        - 25 usuários, plano PRO
        - Faixa Flexx: 30
        - Unitário fornecedor: 2,47
        - Markup: 290%
        - Resultado: 2,47 × 30 × 2,90 = 214,89
        """
        # Arredondar para próxima dezena
        faixa_flexx = math.ceil(usuarios / 10) * 10
        
        # Buscar preço unitário do fornecedor
        preco_fornecedor = db.query(PrecoFornecedor).filter(
            PrecoFornecedor.plano == plano,
            PrecoFornecedor.faixa_inicio <= usuarios,
            PrecoFornecedor.faixa_fim >= usuarios,
            PrecoFornecedor.ativo == True
        ).first()
        
        if not preco_fornecedor:
            raise ValueError(f"Preço não encontrado para {plano} com {usuarios} usuários")
        
        # Buscar markup
        markup = db.query(Markup).filter(
            Markup.plano == plano,
            Markup.ativo == True
        ).first()
        
        if not markup:
            raise ValueError(f"Markup não configurado para {plano}")
        
        # Calcular preço final
        preco_final = round(
            float(preco_fornecedor.preco_unitario) * faixa_flexx * (float(markup.markup_percentual) / 100),
            2
        )
        
        return {
            "usuarios_entrada": usuarios,
            "faixa_flexx": faixa_flexx,
            "preco_unitario": Decimal(str(preco_fornecedor.preco_unitario)),
            "markup_percentual": Decimal(str(markup.markup_percentual)),
            "preco_final": Decimal(str(preco_final)),
            "detalhamento": f"{preco_fornecedor.preco_unitario} × {faixa_flexx} × {markup.markup_percentual/100} = {preco_final}"
        }
    
    @staticmethod
    def listar_precos_fornecedor(db: Session) -> list:
        """Lista todos os preços do fornecedor"""
        return db.query(PrecoFornecedor).filter(PrecoFornecedor.ativo == True).all()
    
    @staticmethod
    def listar_markups(db: Session) -> list:
        """Lista todos os markups"""
        return db.query(Markup).filter(Markup.ativo == True).all()
    
    @staticmethod
    def atualizar_preco_fornecedor(db: Session, id: int, novo_valor: Decimal, usuario: str):
        """Atualiza preço do fornecedor e registra no histórico"""
        preco = db.query(PrecoFornecedor).filter(PrecoFornecedor.id == id).first()
        
        if not preco:
            raise ValueError("Preço não encontrado")
        
        valor_anterior = preco.preco_unitario
        preco.preco_unitario = novo_valor
        preco.atualizado_em = datetime.utcnow()
        
        # Registrar no histórico
        historico = PrecoHistorico(
            tabela_origem="fornecedor",
            plano=preco.plano,
            faixa_inicio=preco.faixa_inicio,
            faixa_fim=preco.faixa_fim,
            valor_anterior=valor_anterior,
            valor_novo=novo_valor,
            alterado_por=usuario,
            data_alteracao=datetime.utcnow()
        )
        
        db.add(historico)
        db.commit()
        db.refresh(preco)
        
        return preco
    
    @staticmethod
    def atualizar_markup(db: Session, id: int, novo_markup: Decimal, usuario: str):
        """Atualiza markup e registra no histórico"""
        markup = db.query(Markup).filter(Markup.id == id).first()
        
        if not markup:
            raise ValueError("Markup não encontrado")
        
        valor_anterior = markup.markup_percentual
        markup.markup_percentual = novo_markup
        markup.atualizado_em = datetime.utcnow()
        
        # Registrar no histórico
        historico = PrecoHistorico(
            tabela_origem="markup",
            plano=markup.plano,
            valor_anterior=valor_anterior,
            valor_novo=novo_markup,
            alterado_por=usuario,
            data_alteracao=datetime.utcnow()
        )
        
        db.add(historico)
        db.commit()
        db.refresh(markup)
        
        return markup
    
    @staticmethod
    def listar_historico(db: Session, plano: str = None) -> list:
        """Lista histórico de alterações"""
        query = db.query(PrecoHistorico)
        if plano:
            query = query.filter(PrecoHistorico.plano == plano)
        return query.order_by(PrecoHistorico.data_alteracao.desc()).all()
