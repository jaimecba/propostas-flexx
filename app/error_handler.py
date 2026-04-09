# app/error_handler_simple.py

import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# ============================================================================
# CUSTOM EXCEPTIONS (Exceções Personalizadas)
# ============================================================================

class PropostaNotFound(Exception):
    """Quando uma proposta não é encontrada"""
    def __init__(self, detail: str = "Proposta não encontrada"):
        self.status_code = status.HTTP_404_NOT_FOUND
        self.detail = detail


class InvalidProposal(Exception):
    """Quando os dados da proposta são inválidos"""
    def __init__(self, detail: str = "Dados da proposta inválidos"):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = detail


class UnauthorizedAccess(Exception):
    """Quando o usuário não tem permissão"""
    def __init__(self, detail: str = "Acesso não autorizado"):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = detail


# ============================================================================
# ERROR HANDLERS (Tratadores de Erro)
# ============================================================================

async def proposta_not_found_handler(request: Request, exc: PropostaNotFound):
    """Trata quando proposta não é encontrada"""
    logger.warning(f"Proposta não encontrada: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": "Recurso não encontrado",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


async def invalid_proposal_handler(request: Request, exc: InvalidProposal):
    """Trata quando dados da proposta são inválidos"""
    logger.warning(f"Proposta inválida: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": "Requisição inválida",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


async def unauthorized_access_handler(request: Request, exc: UnauthorizedAccess):
    """Trata quando usuário não tem permissão"""
    logger.warning(f"Acesso não autorizado: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "message": "Não autorizado",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Trata qualquer erro não previsto"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "Erro interno do servidor",
            "detail": "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.",
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# FUNÇÃO PARA REGISTRAR OS HANDLERS
# ============================================================================

def register_exception_handlers(app: FastAPI):
    """Registra todos os tratadores de erro na aplicação"""
    app.add_exception_handler(PropostaNotFound, proposta_not_found_handler)
    app.add_exception_handler(InvalidProposal, invalid_proposal_handler)
    app.add_exception_handler(UnauthorizedAccess, unauthorized_access_handler)
    app.add_exception_handler(Exception, generic_exception_handler)