from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pathlib import Path
from datetime import datetime
import json

from app.config import settings
from app.database import get_db
from app.models import Proposta
from app.config_templates import jinja_env  # ← IMPORTAR DAQUI

router = APIRouter()


def fmt(valor: Any) -> str:
    """Formata um valor para moeda brasileira (R$)"""
    try:
        if valor is None:
            valor = Decimal("0.00")
        valor_decimal = Decimal(str(valor)) if not isinstance(valor, Decimal) else valor
        return f"R$ {valor_decimal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def formatar_data(data: Any) -> str:
    """Formata uma data para o padrão brasileiro (DD/MM/YYYY HH:MM:SS)"""
    if data is None:
        return "Não informado"
    try:
        if isinstance(data, str):
            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
        return data.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Não informado"


def formatar_data_curta(data: Any) -> str:
    """Formata uma data para o padrão brasileiro curto (DD/MM/YYYY)"""
    if data is None:
        return "Não informado"
    try:
        if isinstance(data, str):
            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
        return data.strftime("%d/%m/%Y")
    except Exception:
        return "Não informado"


def processar_servicos_adicionais(servicos: Any) -> Dict[str, Any]:
    """Converte servicos_adicionais em dicionário estruturado"""
    if not servicos:
        return {}

    try:
        # Se for string JSON, faz parse
        if isinstance(servicos, str):
            try:
                parsed_json = json.loads(servicos)
                return parsed_json if isinstance(parsed_json, dict) else {}
            except json.JSONDecodeError:
                return {}
        
        # Se já for dicionário, retorna
        if isinstance(servicos, dict):
            return servicos
        
        # Caso contrário, retorna vazio
        return {}

    except Exception as e:
        print(f"❌ Erro ao processar serviços adicionais: {e}")
        return {}


def calcular_total_servicos(servicos_dict: Dict[str, Any]) -> Decimal:
    """Calcula o valor total dos serviços adicionais"""
    total = Decimal("0.00")
    
    try:
        for servico_key, servico_data in servicos_dict.items():
            if isinstance(servico_data, dict) and "valor_total" in servico_data:
                try:
                    valor = Decimal(str(servico_data["valor_total"]))
                    total += valor
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        print(f"❌ Erro ao calcular total de serviços: {e}")
    
    return total


def get_safe_str(obj: Any, attr: str, default: str = "Não informado") -> str:
    """Obtém um atributo como string de forma segura"""
    val = getattr(obj, attr, None)
    return str(val) if val is not None else default


def get_safe_int(obj: Any, attr: str, default: int = 0) -> int:
    """Obtém um atributo como inteiro de forma segura"""
    val = getattr(obj, attr, None)
    try:
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def get_safe_decimal(obj: Any, attr: str, default: Decimal = Decimal("0.00")) -> Decimal:
    """Obtém um atributo como Decimal de forma segura"""
    val = getattr(obj, attr, None)
    try:
        return Decimal(str(val)) if val is not None else default
    except (ValueError, TypeError):
        return default


@router.get("/proposta/{hash_id}", response_class=HTMLResponse)
async def visualizar_proposta(hash_id: str, request: Request, db: Session = Depends(get_db)):
    """Exibe os detalhes de uma proposta específica em uma página HTML."""
    proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()

    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")

    # Processamento de valores
    setup_valor = get_safe_decimal(proposta, 'setup_ajustado', get_safe_decimal(proposta, 'setup_padrao', Decimal("0.00")))
    desconto_valor = get_safe_decimal(proposta, 'desconto_valor', Decimal("0.00"))
    valor_mensal = get_safe_decimal(proposta, 'valor_mensal', Decimal("0.00"))
    subtotal = get_safe_decimal(proposta, 'subtotal', Decimal("0.00"))
    total = get_safe_decimal(proposta, 'total', Decimal("0.00"))
    taxa_unica = get_safe_decimal(proposta, 'taxa_unica', Decimal("0.00"))
    treinamento_valor = get_safe_decimal(proposta, 'treinamento_valor', Decimal("0.00"))
    desconto_percentual_val = get_safe_decimal(proposta, 'desconto_percentual', Decimal("0.00"))

    # ✅ NOVO - Processamento de serviços adicionais como DICIONÁRIO
    servicos_adicionais_json = processar_servicos_adicionais(proposta.servicos_adicionais)
    valor_servicos_adicionais = calcular_total_servicos(servicos_adicionais_json)

    # Construção do dicionário de contexto
    contexto = {
        "request": request,
        "app_name": getattr(settings, 'app_name', 'Flexx Proposta'),
        "version": getattr(settings, 'app_version', '1.0.0'),
        
        # Dados do Cliente
        "hash_id": get_safe_str(proposta, 'hash_id', ""),
        "cnpj": get_safe_str(proposta, 'cnpj'),
        "razao_social": get_safe_str(proposta, 'razao_social'),
        "nome_fantasia": get_safe_str(proposta, 'nome_fantasia'),
        "email": get_safe_str(proposta, 'email'),
        "telefone": get_safe_str(proposta, 'telefone'),
        "whatsapp": get_safe_str(proposta, 'whatsapp'),

        # Plano e Usuários
        "plano": get_safe_str(proposta, 'plano'),
        "usuarios": get_safe_int(proposta, 'usuarios'),
        "usuarios_arredondados": get_safe_int(proposta, 'usuarios_arredondados', get_safe_int(proposta, 'usuarios')),

        # Treinamento e Setup
        "treinamento_tipo": get_safe_str(proposta, 'treinamento_tipo'),
        "setup": fmt(setup_valor),
        "setup_padrao": fmt(get_safe_decimal(proposta, 'setup_padrao')),
        "setup_ajustado": fmt(get_safe_decimal(proposta, 'setup_ajustado')),
        "treinamento_valor": fmt(treinamento_valor),

        # Desconto
        "desconto_percentual": f"{desconto_percentual_val.quantize(Decimal('0.01'))}%",
        "desconto": fmt(desconto_valor),

        # Totais
        "valor_mensal": fmt(valor_mensal),
        "subtotal": fmt(subtotal),
        "valor_total": fmt(total),
        "taxa_unica": fmt(taxa_unica),
        
        # --- NOVOS CÁLCULOS PARA O RESUMO ---
        "valor_mensal_total": fmt(valor_mensal), 
        "avulsos_total": fmt(setup_valor + treinamento_valor),
        "total_geral_avulsos": fmt((setup_valor + treinamento_valor) - desconto_valor),
        "setup_formatado": fmt(setup_valor),
        "treinamento_formatado": fmt(treinamento_valor),
        "desconto_formatado": fmt(desconto_valor),
        # ------------------------------------

        # Observações
        "observacoes": get_safe_str(proposta, 'observacoes', "Nenhuma observação."),

        # Status
        "status": get_safe_str(proposta, 'status', "Pendente"),

        # Datas
        "data_criacao": formatar_data(getattr(proposta, 'data_criacao', None)),
        "data_atualizacao": formatar_data(getattr(proposta, 'data_atualizacao', None)),
        "data_validade": formatar_data_curta(getattr(proposta, 'data_validade', None)),
        "data_inicio_servico": formatar_data_curta(getattr(proposta, 'data_inicio_servico', None)),

        # Soft Delete
        "ativo": "Ativo" if getattr(proposta, 'ativo', False) else "Inativo",
        "data_delecao": formatar_data(getattr(proposta, 'data_delecao', None)),

        # ✅ Serviços Adicionais - AGORA COMO DICIONÁRIO
        "servicos_adicionais_json": servicos_adicionais_json,
        "valor_servicos_adicionais": fmt(valor_servicos_adicionais),
        
        # Métodos do modelo
        "total_visualizacoes": proposta.total_visualizacoes() if hasattr(proposta, 'total_visualizacoes') and callable(proposta.total_visualizacoes) else 0,
        "is_expirada": proposta.is_expirada() if hasattr(proposta, 'is_expirada') and callable(proposta.is_expirada) else False,

        # Funções auxiliares
        "formatar_moeda": fmt,
        "formatar_data": formatar_data,
        "formatar_data_curta": formatar_data_curta,
    }

    # ← USAR JINJA_ENV DIRETAMENTE
    template = jinja_env.get_template("proposta.html")
    html = template.render(contexto)
    return HTMLResponse(content=html)