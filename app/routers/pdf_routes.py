# c:\propostas-flexx\app\routers\pdf_routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import io

from app.database import get_db
from app.models import Proposta
from app.pdf_service import pdf_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/proposta/{hash_id}/pdf")
async def baixar_pdf_proposta(
    hash_id: str,
    db: Session = Depends(get_db)
):
    """Endpoint para baixar o PDF de uma proposta específica."""
    logger.info(f"Requisição para baixar PDF da proposta: {hash_id}")
    
    proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()

    if not proposta:
        logger.warning(f"Proposta com hash_id '{hash_id}' não encontrada.")
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")

    try:
        proposta_data = {
            "razao_social": proposta.razao_social,
            "nome_fantasia": proposta.nome_fantasia if hasattr(proposta, 'nome_fantasia') else None,
            "cnpj": proposta.cnpj,
            "email": proposta.email,
            "telefone": proposta.telefone,
            "whatsapp": proposta.whatsapp,
            "plano": proposta.plano,
            "usuarios": proposta.usuarios,
            "usuarios_arredondados": proposta.usuarios_arredondados,
            "valor_mensal": proposta.valor_mensal,
            "setup_ajustado": proposta.setup_ajustado,
            "setup_padrao": proposta.setup_padrao,
            "treinamento_tipo": proposta.treinamento_tipo,
            "treinamento_valor": proposta.treinamento_valor,
            "subtotal": proposta.subtotal,
            "desconto_valor": proposta.desconto_valor,
            "total": proposta.total,
            "observacoes": proposta.observacoes,
            "data_validade": proposta.data_validade.strftime("%d/%m/%Y") if proposta.data_validade else "N/A",
            "data_criacao": proposta.data_criacao.strftime("%d/%m/%Y") if proposta.data_criacao else "N/A",
            "hash_id": proposta.hash_id,
        }

        pdf_bytes = pdf_service.gerar_pdf_proposta(proposta_data)
        filename = f"proposta_{hash_id}.pdf"

        logger.info(f"PDF da proposta '{hash_id}' gerado com sucesso.")
        
        # ✅ CORRIGIDO: Usar StreamingResponse em vez de FileResponse
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Erro ao gerar PDF para proposta '{hash_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar PDF: {str(e)}")