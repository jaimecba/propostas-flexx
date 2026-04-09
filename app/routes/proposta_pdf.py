from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse, StreamingResponse

from app.database import get_db
from app.models import Proposta
from app.routes.proposta import (
    fmt, formatar_data, formatar_data_curta, processar_servicos_adicionais,
    get_safe_str, get_safe_int, get_safe_decimal
)

router = APIRouter()


def gerar_pdf_proposta(proposta: Proposta) -> bytes:
    """Gera PDF da proposta usando ReportLab"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0056b3'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0056b3'),
        spaceAfter=10,
        spaceBefore=10,
        borderPadding=5,
        backColor=colors.HexColor('#e9f5ff')
    )
    
    normal_style = styles['Normal']
    
    # Elementos do PDF
    elements = []
    
    # Cabeçalho
    elements.append(Paragraph("PROPOSTA COMERCIAL", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Dados do Cliente
    elements.append(Paragraph("DADOS DO CLIENTE", heading_style))
    
    client_data = [
        ["CNPJ:", get_safe_str(proposta, 'cnpj')],
        ["Razão Social:", get_safe_str(proposta, 'razao_social')],
        ["Nome Fantasia:", get_safe_str(proposta, 'nome_fantasia')],
        ["Email:", get_safe_str(proposta, 'email')],
        ["Telefone:", get_safe_str(proposta, 'telefone')],
        ["WhatsApp:", get_safe_str(proposta, 'whatsapp')],
    ]
    
    client_table = Table(client_data, colWidths=[1.5*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(client_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Plano e Usuários
    elements.append(Paragraph("PLANO E USUÁRIOS", heading_style))
    
    plan_data = [
        ["Plano:", get_safe_str(proposta, 'plano')],
        ["Usuários:", str(get_safe_int(proposta, 'usuarios'))],
        ["Usuários Arredondados:", str(get_safe_int(proposta, 'usuarios_arredondados'))],
    ]
    
    plan_table = Table(plan_data, colWidths=[1.5*inch, 4.5*inch])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(plan_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Valores
    elements.append(Paragraph("VALORES", heading_style))
    
    setup_valor = get_safe_decimal(proposta, 'setup_ajustado', get_safe_decimal(proposta, 'setup_padrao', Decimal("0.00")))
    desconto_valor = get_safe_decimal(proposta, 'desconto_valor', Decimal("0.00"))
    valor_mensal = get_safe_decimal(proposta, 'valor_mensal', Decimal("0.00"))
    treinamento_valor = get_safe_decimal(proposta, 'treinamento_valor', Decimal("0.00"))
    total = get_safe_decimal(proposta, 'total', Decimal("0.00"))
    
    values_data = [
        ["Valor Mensal:", fmt(valor_mensal)],
        ["Setup:", fmt(setup_valor)],
        ["Treinamento:", fmt(treinamento_valor)],
        ["Desconto:", fmt(desconto_valor)],
        ["TOTAL:", fmt(total)],
    ]
    
    values_table = Table(values_data, colWidths=[1.5*inch, 4.5*inch])
    values_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -2), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#0056b3')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(values_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Serviços Adicionais
    servicos_adicionais_list = processar_servicos_adicionais(proposta.servicos_adicionais)
    if servicos_adicionais_list:
        elements.append(Paragraph("SERVIÇOS ADICIONAIS", heading_style))
        
        servicos_data = [[servico] for servico in servicos_adicionais_list]
        servicos_table = Table(servicos_data, colWidths=[6*inch])
        servicos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(servicos_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Observações
    observacoes = get_safe_str(proposta, 'observacoes', "")
    if observacoes:
        elements.append(Paragraph("OBSERVAÇÕES", heading_style))
        elements.append(Paragraph(observacoes, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Datas
    elements.append(Paragraph("DATAS", heading_style))
    
    dates_data = [
        ["Data de Criação:", formatar_data(getattr(proposta, 'data_criacao', None))],
        ["Data de Validade:", formatar_data_curta(getattr(proposta, 'data_validade', None))],
        ["Status:", get_safe_str(proposta, 'status', "Pendente")],
    ]
    
    dates_table = Table(dates_data, colWidths=[1.5*inch, 4.5*inch])
    dates_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    elements.append(dates_table)
    
    # Rodapé
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        f"<i>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
    ))
    
    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/proposta/{hash_id}/pdf")
async def baixar_pdf_proposta(hash_id: str, db: Session = Depends(get_db)):
    """Endpoint para baixar o PDF de uma proposta específica."""
    
    proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()
    
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")
    
    # Gerar PDF
    pdf_bytes = gerar_pdf_proposta(proposta)
    
    # Retornar como arquivo
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=proposta_{proposta.hash_id}.pdf"}
    )