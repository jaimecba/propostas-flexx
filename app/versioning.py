# app/versioning.py

from enum import Enum
from typing import Optional

# 
# VERSÕES SUPORTADAS DA API
# 

class APIVersion(str, Enum):
    """Versões suportadas da API"""
    V1 = "v1"  # Versão 1 (atual)
    V2 = "v2"  # Versão 2 (nova)


# 
# CONFIGURAÇÃO DE VERSÕES
# 

VERSOES_SUPORTADAS = {
    "v1": {
        "descricao": "Versão 1 - Inicial",
        "status": "ativa",
        "data_lancamento": "2026-01-15",
        "data_deprecacao": None,  # Ainda não foi descontinuada
        "mudancas": [
            "Endpoints básicos de propostas",
            "Autenticação JWT",
            "Rate Limiting",
            "Cache Redis"
        ]
    },
    "v2": {
        "descricao": "Versão 2 - Melhorada",
        "status": "ativa",
        "data_lancamento": "2026-03-19",
        "data_deprecacao": None,
        "mudancas": [
            "Soft Delete para Propostas",
            "Auditoria de Mudanças",
            "Melhorias de Performance",
            "Novos Endpoints"
        ]
    }
}


# 
# FUNÇÃO PARA OBTER VERSÃO PADRÃO
# 

def obter_versao_padrao() -> str:
    """Retorna a versão padrão da API"""
    return APIVersion.V1.value


def obter_versao_mais_recente() -> str:
    """Retorna a versão mais recente da API"""
    return APIVersion.V2.value


def versao_eh_valida(versao: str) -> bool:
    """Verifica se uma versão é válida"""
    return versao in VERSOES_SUPORTADAS


def obter_info_versao(versao: str) -> Optional[dict]:
    """Obtém informações sobre uma versão específica"""
    return VERSOES_SUPORTADAS.get(versao)


def listar_versoes() -> dict:
    """Lista todas as versões disponíveis"""
    return VERSOES_SUPORTADAS