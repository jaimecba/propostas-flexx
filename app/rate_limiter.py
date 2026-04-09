# app/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ============================================================================
# CONFIGURAÇÃO DE RATE LIMITING
# ============================================================================

# Cria o limitador com chave baseada no IP do cliente
limiter = Limiter(key_func=get_remote_address)

# Configurações de limite
RATE_LIMITS = {
    "default": "100/minute",      # 100 requisições por minuto (padrão)
    "login": "5/minute",           # 5 tentativas de login por minuto
    "proposal": "50/minute",       # 50 requisições de proposta por minuto
    "strict": "10/minute"          # 10 requisições por minuto (muito restritivo)
}


# ============================================================================
# HANDLER PARA ERRO DE RATE LIMIT
# ============================================================================

async def rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
    """Trata quando o limite de requisições é excedido"""
    return JSONResponse(
        status_code=429,
        content={
            "status_code": 429,
            "message": "Muitas requisições",
            "detail": "Você excedeu o limite de requisições. Tente novamente mais tarde.",
            "retry_after": exc.detail
        }
    )


# ============================================================================
# FUNÇÃO PARA REGISTRAR O RATE LIMITER
# ============================================================================

def setup_rate_limiter(app: FastAPI):
    """Registra o rate limiter na aplicação"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)