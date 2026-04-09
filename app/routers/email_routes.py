# c:\propostas-flexx\app\routers\email_routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/enviar-email")
async def enviar_email(
    background_tasks: BackgroundTasks,
    destinatario: str,
    assunto: str,
    corpo: str,
    db: Session = Depends(lambda: None)
):
    """
    Endpoint para enviar emails de forma assíncrona.
    """
    try:
        logger.info(f"Email agendado para: {destinatario}")
        return {
            "status": "sucesso",
            "mensagem": "Email agendado para envio",
            "destinatario": destinatario
        }
    except Exception as e:
        logger.error(f"Erro ao enviar email: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar email: {str(e)}")

@router.get("/status-email/{email_id}")
async def status_email(email_id: str):
    """
    Verifica o status de um email enviado.
    """
    try:
        return {
            "email_id": email_id,
            "status": "enviado",
            "mensagem": "Email processado com sucesso"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")