# app/cache.py

import json
import redis
from typing import Optional, Any
from datetime import timedelta

# ============================================================================
# CONFIGURAÇÃO DO REDIS
# ============================================================================

# Conecta ao Redis (padrão: localhost:6379)
redis_client = redis.Redis(
    host='localhost',
    port=6380,
    db=0,
    decode_responses=True  # Retorna strings em vez de bytes
)

# Tempo padrão de expiração do cache (em segundos)
DEFAULT_CACHE_EXPIRATION = 3600  # 1 hora

# ============================================================================
# FUNÇÕES DE CACHE
# ============================================================================

def set_cache(key: str, value: Any, expiration: int = DEFAULT_CACHE_EXPIRATION) -> bool:
    """
    Armazena um valor no cache
    
    Args:
        key: Chave do cache
        value: Valor a ser armazenado (será convertido para JSON)
        expiration: Tempo de expiração em segundos
    
    Returns:
        True se sucesso, False se erro
    """
    try:
        # Converte o valor para JSON
        json_value = json.dumps(value)
        # Armazena no Redis com expiração
        redis_client.setex(key, expiration, json_value)
        return True
    except Exception as e:
        print(f"Erro ao armazenar cache: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Recupera um valor do cache
    
    Args:
        key: Chave do cache
    
    Returns:
        Valor armazenado ou None se não encontrado
    """
    try:
        value = redis_client.get(key)
        if value:
            # Converte de volta do JSON
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Erro ao recuperar cache: {e}")
        return None


def delete_cache(key: str) -> bool:
    """
    Deleta um valor do cache
    
    Args:
        key: Chave do cache
    
    Returns:
        True se sucesso, False se erro
    """
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Erro ao deletar cache: {e}")
        return False


def clear_cache() -> bool:
    """
    Limpa todo o cache
    
    Returns:
        True se sucesso, False se erro
    """
    try:
        redis_client.flushdb()
        return True
    except Exception as e:
        print(f"Erro ao limpar cache: {e}")
        return False


def cache_exists(key: str) -> bool:
    """
    Verifica se uma chave existe no cache
    
    Args:
        key: Chave do cache
    
    Returns:
        True se existe, False caso contrário
    """
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        print(f"Erro ao verificar cache: {e}")
        return False


# ============================================================================
# EXEMPLO: CACHE PARA TABELA DE PREÇOS
# ============================================================================

def get_preco_tabela(plano: str) -> Optional[dict]:
    """
    Recupera preço da tabela (com cache)
    
    Args:
        plano: Nome do plano (Basic, PRO, Ultimate)
    
    Returns:
        Dicionário com preço ou None
    """
    # Chave do cache
    cache_key = f"preco_tabela:{plano}"
    
    # Tenta recuperar do cache
    preco_cached = get_cache(cache_key)
    if preco_cached:
        print(f"✅ Preço recuperado do CACHE: {plano}")
        return preco_cached
    
    # Se não está em cache, calcula (simulado)
    print(f"📊 Preço NÃO estava em cache, calculando: {plano}")
    
    # Tabela de preços (simulada)
    tabela_precos = {
        "Basic": {"valor": 99.90, "usuarios": 5, "moeda": "BRL"},
        "PRO": {"valor": 299.90, "usuarios": 20, "moeda": "BRL"},
        "Ultimate": {"valor": 999.90, "usuarios": 100, "moeda": "BRL"}
    }
    
    preco = tabela_precos.get(plano)
    
    if preco:
        # Armazena no cache por 1 hora
        set_cache(cache_key, preco, expiration=3600)
        print(f"💾 Preço armazenado em CACHE: {plano}")
    
    return preco


def invalidar_cache_precos():
    """
    Invalida (limpa) o cache de preços
    Útil quando a tabela de preços é atualizada
    """
    try:
        # Deleta todas as chaves que começam com "preco_tabela:"
        keys = redis_client.keys("preco_tabela:*")
        if keys:
            redis_client.delete(*keys)
            print(f"🗑️ Cache de preços invalidado ({len(keys)} chaves deletadas)")
        return True
    except Exception as e:
        print(f"Erro ao invalidar cache: {e}")
        return False