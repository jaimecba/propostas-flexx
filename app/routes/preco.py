from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from app.database import get_db
from app.models import TabelaPrecosPlanos
import math

router = APIRouter(prefix="/api/precos", tags=["precos"])

# 
# FUNÇÃO AUXILIAR: Buscar Preço do Plano
# 
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

# 
# ENDPOINT: Calcular Orçamento
# 
@router.post("/orcamento/calcular")
def calcular_orcamento(
    plano: str = Query(..., description="Nome do plano (Basic, Pro, Ultimate)"),
    usuarios: int = Query(..., description="Quantidade de usuários"),
    db: Session = Depends(get_db)
):
    """
    Calcula preço do orçamento conforme lógica Flexx
    """
    try:
        # Arredondar para próxima dezena
        faixa_flexx = math.ceil(usuarios / 10) * 10 if usuarios > 0 else 10
        
        # 🟢 CORREÇÃO 1: Valores FIXOS para até 10 usuários
        if faixa_flexx <= 10:
            if plano.lower() == 'basic':
                preco_final = 99.90
            elif plano.lower() == 'pro':
                preco_final = 119.90
            elif plano.lower() == 'ultimate':
                preco_final = 139.90
            else:
                preco_final = 99.90
                
            return {
                "usuarios_entrada": usuarios,
                "faixa_flexx": faixa_flexx,
                "preco_unitario": round(preco_final / 10, 2),
                "markup_percentual": 0,
                "preco_final": preco_final,
                "detalhamento": f"Valor fixo para até 10 usuários: R$ {preco_final}"
            }
            
        # Para faixas acima de 10 usuários, busca no banco
        preco_unitario = buscar_valor_plano(db, plano, usuarios)
        
        # 🟢 CORREÇÃO 2: Markup fixo é 300% (multiplica por 3) e não 290%
        markup_percentual = 300
        
        # Calcular preço final
        preco_final = round(
            float(preco_unitario) * faixa_flexx * (markup_percentual / 100),
            2
        )
        
        return {
            "usuarios_entrada": usuarios,
            "faixa_flexx": faixa_flexx,
            "preco_unitario": float(preco_unitario),
            "markup_percentual": markup_percentual,
            "preco_final": preco_final,
            "detalhamento": f"{preco_unitario} × {faixa_flexx} × {markup_percentual/100} = {preco_final}"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 
# ENDPOINT: Listar Serviços Adicionais com Cálculo (DO BANCO DE DADOS)
# 
@router.get("/servicos")
def listar_servicos_adicionais(
    faixa: int = Query(..., description="Faixa Flexx (quantidade de usuários arredondada)"),
    db: Session = Depends(get_db)
):
    """
    Lista os serviços adicionais com seus preços calculados
    Busca os dados da tabela tabela_precos_servicos_adicionais
    """
    try:
        # Buscar serviços do banco de dados - SEM descricao
        query = text("""
            SELECT id, nome_servico, valor_unitario, tipo_cobranca
            FROM tabela_precos_servicos_adicionais
            WHERE ativo = true
            ORDER BY id
        """)
        
        resultado = db.execute(query).fetchall()
        
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="Nenhum serviço adicional encontrado no banco de dados."
            )
        
        # Processar os serviços e calcular preços
        servicos = []
        for row in resultado:
            id_servico, nome_servico, valor_unitario, tipo_cobranca = row
            
            # Calcular preço baseado no tipo de cálculo
            if tipo_cobranca == "fixo":
                preco_calculado = float(valor_unitario)
            elif tipo_cobranca == "por_faixa":
                preco_calculado = round(float(valor_unitario) * faixa, 2)
            else:
                preco_calculado = float(valor_unitario)
            
            servicos.append({
                "id": id_servico,
                "nome": nome_servico,
                "preco_unitario": float(valor_unitario),
                "tipo_calculo": tipo_cobranca,
                "faixa": faixa if tipo_cobranca == "por_faixa" else None,
                "preco_calculado": preco_calculado
            })
        
        return {
            "faixa": faixa,
            "servicos": servicos,
            "total_servicos": len(servicos)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 
# ENDPOINT: Listar Tipos de Treinamento com Preços (DO BANCO DE DADOS)
# 
@router.get("/treinamento")
def listar_treinamentos(db: Session = Depends(get_db)):
    """
    Lista os tipos de treinamento disponíveis com seus preços
    Busca os dados da tabela tabela_precos_treinamentos
    """
    try:
        # Buscar treinamentos do banco de dados
        query = text("""
            SELECT id, tipo_treinamento, valor
            FROM tabela_precos_treinamentos
            WHERE ativo = true
            ORDER BY id
        """)
        
        resultado = db.execute(query).fetchall()
        
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="Nenhum tipo de treinamento encontrado no banco de dados."
            )
        
        # Processar os treinamentos
        treinamentos = []
        for row in resultado:
            id_treinamento, tipo_treinamento, valor = row
            treinamentos.append({
                "id": id_treinamento,
                "tipo": tipo_treinamento,
                "preco": float(valor)
            })
        
        return {
            "treinamentos": treinamentos,
            "total_treinamentos": len(treinamentos)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 
# ENDPOINT: Buscar Preço de Treinamento Específico (DO BANCO DE DADOS)
# 
@router.get("/treinamento/{tipo}")
def buscar_treinamento(tipo: str = Path(..., description="Tipo de treinamento (Online, Presencial, Híbrido)"), db: Session = Depends(get_db)):
    """
    Busca o preço de um tipo específico de treinamento
    """
    try:
        # Buscar treinamento do banco de dados
        query = text("""
            SELECT id, tipo_treinamento, valor
            FROM tabela_precos_treinamentos
            WHERE LOWER(tipo_treinamento) = LOWER(:tipo) AND ativo = true
        """)
        
        resultado = db.execute(query, {"tipo": tipo}).fetchone()
        
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail=f"Tipo de treinamento '{tipo}' não encontrado. Opções: Online, Presencial, Híbrido"
            )
        
        id_treinamento, tipo_treinamento, valor = resultado
        
        return {
            "id": id_treinamento,
            "tipo": tipo_treinamento,
            "preco": float(valor)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))