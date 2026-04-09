import io
import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Proposta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFConfig:
    SCALE_FACTOR = 0.5
    FONT_SCALE = 1.2
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN_LEFT = 2.5 * cm * SCALE_FACTOR
    MARGIN_RIGHT = 2.5 * cm * SCALE_FACTOR
    MARGIN_TOP = 2.0 * cm * SCALE_FACTOR
    MARGIN_BOTTOM = 2.0 * cm * SCALE_FACTOR
    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    FONT_ITALIC = 'Helvetica-Oblique'
    COLOR_PRIMARY = colors.HexColor('#343a40')
    COLOR_SECONDARY = colors.HexColor('#6c757d')
    COLOR_ACCENT = colors.HexColor('#007bff')
    COLOR_LIGHT_BG = colors.HexColor('#f8f9fa')
    COLOR_BORDER = colors.HexColor('#e9ecef')
    BASE_PROPOSAL_URL = "http://localhost:8000/proposta/"
    LOGO_PATH: Optional[Path] = None

    def __init__(self):
        if self.LOGO_PATH and not self.LOGO_PATH.exists():
            logger.warning(f"Logo não encontrada em: {self.LOGO_PATH}. O PDF será gerado sem logo.")
            self.LOGO_PATH = None


class PDFService:
    def __init__(self, config: PDFConfig):
        self.config = config
        self.styles = self._criar_estilos_customizados()
        logger.info("PDFService inicializado com sucesso.")

    def _criar_estilos_customizados(self) -> Any:
        styles = getSampleStyleSheet()
        sf = self.config.SCALE_FACTOR
        fs = self.config.FONT_SCALE

        styles.add(ParagraphStyle(
            name='TituloCustomizado',
            parent=styles['h1'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(24 * sf * fs),
            leading=int(28 * sf * fs),
            alignment=TA_CENTER,
            textColor=self.config.COLOR_ACCENT,
            spaceAfter=int(0.8*cm * sf),
        ))

        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['h2'],
            fontName=self.config.FONT_NORMAL,
            fontSize=int(14 * sf * fs),
            leading=int(16 * sf * fs),
            alignment=TA_CENTER,
            textColor=self.config.COLOR_SECONDARY,
            spaceAfter=int(1*cm * sf),
        ))

        styles.add(ParagraphStyle(
            name='HeaderStyle',
            parent=styles['h3'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(12 * sf * fs),
            leading=int(14 * sf * fs),
            alignment=TA_LEFT,
            textColor=self.config.COLOR_ACCENT,
            spaceBefore=int(0.7*cm * sf),
            spaceAfter=int(0.2*cm * sf),
        ))

        styles.add(ParagraphStyle(
            name='MainHeaderStyle',
            parent=styles['h3'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(10 * sf * fs),
            leading=int(14 * sf * fs),
            alignment=TA_CENTER,
            textColor=self.config.COLOR_ACCENT,
            spaceBefore=int(0.7*cm * sf),
            spaceAfter=int(0.2*cm * sf),
        ))

        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontName=self.config.FONT_NORMAL,
            fontSize=int(10 * sf * fs),
            leading=int(12 * sf * fs),
            alignment=TA_LEFT,
            textColor=self.config.COLOR_PRIMARY,
        ))

        # ✅ ADICIONE ESTE ESTILO (estava faltando):
        styles.add(ParagraphStyle(
            name='BoldBodyText',
            parent=styles['Normal'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(9 * sf * fs),
            leading=int(10 * sf * fs),
            alignment=TA_LEFT,
            textColor=self.config.COLOR_PRIMARY,
        ))

        styles.add(ParagraphStyle(
            name='BoldBodyTextBlue',
            parent=styles['Normal'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(9 * sf * fs),
            leading=int(10 * sf * fs),
            alignment=TA_LEFT,
            textColor=colors.HexColor('#003366'),  # Azul escuro
        ))

        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontName=self.config.FONT_NORMAL,
            fontSize=int(8 * sf * fs),
            leading=int(10 * sf * fs),
            alignment=TA_CENTER,
            textColor=self.config.COLOR_SECONDARY,
            spaceBefore=int(0.5*cm * sf),
        ))

        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['h3'],
            fontName=self.config.FONT_BOLD,
            fontSize=int(11 * sf * fs),
            leading=int(13 * sf * fs),
            alignment=TA_LEFT,
            textColor=self.config.COLOR_PRIMARY,
            spaceBefore=int(0.5*cm * sf),
            spaceAfter=int(0.2*cm * sf),
            backColor=self.config.COLOR_LIGHT_BG,
            borderPadding=int(3 * sf),
        ))

        return styles

    def formatar_moeda(self, valor: Decimal) -> str:
        if not isinstance(valor, Decimal):
            valor = Decimal(str(valor))
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def gerar_pdf_proposta(self, proposta_data: Dict[str, Any], layout: str = "card") -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(self.config.PAGE_WIDTH, self.config.PAGE_HEIGHT),
            leftMargin=self.config.MARGIN_LEFT,
            rightMargin=self.config.MARGIN_RIGHT,
            topMargin=self.config.MARGIN_TOP,
            bottomMargin=self.config.MARGIN_BOTTOM,
        )
        story = self._construir_story(proposta_data, layout)
        doc.build(story, onFirstPage=self._criar_cabecalho, onLaterPages=self._criar_cabecalho)
        buffer.seek(0)
        return buffer

    def _construir_story(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("PROPOSTA COMERCIAL", self.styles['TituloCustomizado']))
        story.append(Spacer(1, int(0.5*cm * sf)))
        story.extend(self._criar_secao_informacoes_gerais(proposta_data, layout))
        
    def _construir_story(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("PROPOSTA COMERCIAL", self.styles['TituloCustomizado']))
        story.append(Spacer(1, int(0.3*cm * sf)))
        story.extend(self._criar_secao_informacoes_gerais(proposta_data, layout))
        story.extend(self._criar_secao_cliente(proposta_data, layout))
        story.extend(self._criar_secao_plano_usuarios(proposta_data, layout))
        story.extend(self._criar_secao_servicos_adicionais_mensal(proposta_data, layout))
        story.extend(self._criar_secao_treinamento_setup(proposta_data, layout))
        story.extend(self._criar_secao_observacoes(proposta_data, layout))
        story.extend(self._criar_secao_resumo_proposta(proposta_data, layout))
        story.extend(self._criar_rodape(proposta_data))
        return story

    def _criar_cabecalho(self, canvas, doc):
        canvas.saveState()
        sf = self.config.SCALE_FACTOR
        fs = self.config.FONT_SCALE
        canvas.setFont(self.config.FONT_NORMAL, int(9 * sf * fs))
        if self.config.LOGO_PATH and self.config.LOGO_PATH.exists():
            try:
                canvas.drawImage(str(self.config.LOGO_PATH), self.config.MARGIN_LEFT, self.config.PAGE_HEIGHT - self.config.MARGIN_TOP + int(0.5*cm * sf), width=int(3*cm * sf), height=int(1*cm * sf), mask='auto')
            except Exception as e:
                logger.error(f"Erro ao carregar logo: {e}")
        canvas.drawString(self.config.PAGE_WIDTH - self.config.MARGIN_RIGHT - int(5*cm * sf), self.config.PAGE_HEIGHT - self.config.MARGIN_TOP + int(0.5*cm * sf), f"Data: {datetime.now().strftime('%d/%m/%Y')}")
        canvas.restoreState()

    def _get_zebra_table_style(self, num_rows: int) -> TableStyle:
        sf = self.config.SCALE_FACTOR
        fs = self.config.FONT_SCALE
        style = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), int(10 * sf * fs)),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.config.COLOR_PRIMARY),
            ('TOPPADDING', (0, 0), (-1, -1), int(8 * sf)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), int(8 * sf)),
            ('LEFTPADDING', (0, 0), (-1, -1), int(6 * sf)),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, self.config.COLOR_BORDER),
        ]
        for i in range(num_rows):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            else:
                style.append(('BACKGROUND', (0, i), (-1, i), self.config.COLOR_LIGHT_BG))
        return TableStyle(style)

    def _get_card_table_style(self, num_rows: int) -> TableStyle:
        sf = self.config.SCALE_FACTOR
        fs = self.config.FONT_SCALE
        style = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), int(10 * sf * fs)),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.config.COLOR_PRIMARY),
            ('TOPPADDING', (0, 0), (-1, -1), int(10 * sf)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), int(10 * sf)),
            ('LEFTPADDING', (0, 0), (-1, -1), int(12 * sf)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f7f6')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dce3e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e8eceb')),
        ]
        return TableStyle(style)

    def _get_grid_table_style(self, num_rows: int) -> TableStyle:
        sf = self.config.SCALE_FACTOR
        fs = self.config.FONT_SCALE
        style = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), int(10 * sf * fs)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), self.config.COLOR_ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), self.config.FONT_BOLD),
            ('TOPPADDING', (0, 0), (-1, 0), int(8 * sf)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), int(8 * sf)),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TOPPADDING', (0, 1), (-1, -1), int(12 * sf)),
            ('BOTTOMPADDING', (0, 1), (-1, -1), int(12 * sf)),
        ]
        return TableStyle(style)

    def _get_table_style_for_layout(self, layout: str, num_rows: int) -> TableStyle:
        if layout == "card":
            return self._get_card_table_style(num_rows)
        elif layout == "grid":
            return self._get_grid_table_style(num_rows)
        else:
            return self._get_zebra_table_style(num_rows)

    def _criar_secao_informacoes_gerais(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("INFORMAÇÕES GERAIS", self.styles['MainHeaderStyle']))
        data_val = proposta_data.get('data_validade')
        data_cri = proposta_data.get('data_criacao')
        proposal_url = f"{self.config.BASE_PROPOSAL_URL}{proposta_data.get('hash_id', 'N/A')}"
        id_link = f"<link href='{proposal_url}'><font color='blue'>{proposta_data.get('hash_id', 'N/A')}</font></link> <font size='4' color='red'>(Clique na ID para ver o relatório em tela)</font>"
        
        if layout == 'grid':
            data = [
                [Paragraph("ID da Proposta", self.styles['BoldBodyText']), Paragraph("Status", self.styles['BoldBodyText']), Paragraph("Data de Validade", self.styles['BoldBodyText']), Paragraph("Data de Criação", self.styles['BoldBodyText'])],
                [Paragraph(id_link, self.styles['NormalText']), Paragraph(proposta_data.get('status', 'N/A'), self.styles['NormalText']), Paragraph(data_val.strftime('%d/%m/%Y') if data_val else 'N/A', self.styles['NormalText']), Paragraph(data_cri.strftime('%d/%m/%Y') if data_cri else 'N/A', self.styles['NormalText'])]
            ]
            table = Table(data, colWidths=[int(4*cm * sf), int(4*cm * sf), int(4*cm * sf), int(4*cm * sf)])
        else:
            data = [
                [Paragraph("ID da Proposta:", self.styles['BoldBodyText']), Paragraph(id_link, self.styles['NormalText'])],
                [Paragraph("Status:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('status', 'N/A'), self.styles['NormalText'])],
                [Paragraph("Data de Validade:", self.styles['BoldBodyText']), Paragraph(data_val.strftime('%d/%m/%Y') if data_val else 'N/A', self.styles['NormalText'])],
                [Paragraph("Data de Criação:", self.styles['BoldBodyText']), Paragraph(data_cri.strftime('%d/%m/%Y') if data_cri else 'N/A', self.styles['NormalText'])],
            ]
            table = Table(data, colWidths=[int(5*cm * sf), int(11*cm * sf)])
        
        table.setStyle(self._get_table_style_for_layout(layout, len(data)))
        story.append(table)
        story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_cliente(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("DADOS DO CLIENTE", self.styles['MainHeaderStyle']))
        if layout == 'grid':
            data = [
                [Paragraph("Nome/Razão Social", self.styles['BoldBodyText']), Paragraph("Nome Fantasia", self.styles['BoldBodyText']), Paragraph("CNPJ", self.styles['BoldBodyText'])],
                [Paragraph(proposta_data.get('razao_social', 'N/A'), self.styles['NormalText']), Paragraph(proposta_data.get('nome_fantasia', 'N/A'), self.styles['NormalText']), Paragraph(proposta_data.get('cnpj', 'N/A'), self.styles['NormalText'])],
                [Paragraph("Email", self.styles['BoldBodyText']), Paragraph("WhatsApp", self.styles['BoldBodyText']), Paragraph("", self.styles['BoldBodyText'])],
                [Paragraph(proposta_data.get('email', 'N/A'), self.styles['NormalText']), Paragraph(proposta_data.get('whatsapp', 'Não informado'), self.styles['NormalText']), Paragraph("", self.styles['NormalText'])]
            ]
            table = Table(data, colWidths=[int(5.3*cm * sf), int(5.3*cm * sf), int(5.3*cm * sf)])
        else:
            data = [
                [Paragraph("Nome/Razão Social:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('razao_social', 'N/A'), self.styles['NormalText'])],
                [Paragraph("Nome Fantasia:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('nome_fantasia', 'N/A'), self.styles['NormalText'])],
                [Paragraph("CNPJ:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('cnpj', 'N/A'), self.styles['NormalText'])],
                [Paragraph("Email:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('email', 'N/A'), self.styles['NormalText'])],
                [Paragraph("WhatsApp:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('whatsapp', 'Não informado'), self.styles['NormalText'])],
            ]
            table = Table(data, colWidths=[int(5*cm * sf), int(11*cm * sf)])
        table.setStyle(self._get_table_style_for_layout(layout, len(data)))
        story.append(table)
        story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_plano_usuarios(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("PLANO E USUÁRIOS", self.styles['MainHeaderStyle']))
        valor_plano_base = proposta_data.get('valor_plano_base', Decimal('0.00'))
        if layout == 'grid':
            data = [
                [Paragraph("Plano Escolhido", self.styles['BoldBodyText']), Paragraph("Faixa de Usuários", self.styles['BoldBodyText']), Paragraph("Valor da Licença (Mensal)", self.styles['BoldBodyText'])],
                [Paragraph(proposta_data.get('plano', 'N/A').upper(), self.styles['NormalText']), Paragraph(str(proposta_data.get('usuarios_arredondados', 'N/A')), self.styles['NormalText']), Paragraph(self.formatar_moeda(valor_plano_base), self.styles['NormalText'])]
            ]
            table = Table(data, colWidths=[int(5.3*cm * sf), int(5.3*cm * sf), int(5.3*cm * sf)])
        else:
            data = [
                [Paragraph("Plano Escolhido:", self.styles['BoldBodyText']), Paragraph(proposta_data.get('plano', 'N/A').upper(), self.styles['NormalText'])],
                [Paragraph("Faixa de Usuários:", self.styles['BoldBodyText']), Paragraph(str(proposta_data.get('usuarios_arredondados', 'N/A')), self.styles['NormalText'])],
                [Paragraph("Valor da Licença (Mensal):", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(valor_plano_base), self.styles['NormalText'])],
            ]
            table = Table(data, colWidths=[int(5*cm * sf), int(11*cm * sf)])
        table.setStyle(self._get_table_style_for_layout(layout, len(data)))
        story.append(table)
        story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_servicos_adicionais_mensal(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        servicos_adicionais_detalhes = proposta_data.get('servicos_adicionais_detalhes', [])
        total_adicionais = proposta_data.get('total_adicionais', Decimal('0.00'))
        if servicos_adicionais_detalhes:
            story.append(Paragraph("CONTRATAÇÃO SERVIÇOS ADICIONAIS (Mensal)", self.styles['MainHeaderStyle']))
            data = []
            if layout == 'grid':
                data.append([Paragraph("Serviço", self.styles['BoldBodyText']), Paragraph("Valor", self.styles['BoldBodyText'])])
                for servico in servicos_adicionais_detalhes:
                    data.append([Paragraph(servico.get('nome', 'N/A'), self.styles['NormalText']), Paragraph(self.formatar_moeda(servico.get('valor_total', Decimal('0.00'))), self.styles['NormalText'])])
                data.append([Paragraph("Valor Total Serviços Adicionais:", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(total_adicionais), self.styles['BoldBodyText'])])
                table = Table(data, colWidths=[int(11*cm * sf), int(5*cm * sf)])
            else:
                for servico in servicos_adicionais_detalhes:
                    data.append([Paragraph(servico.get('nome', 'N/A'), self.styles['NormalText']), Paragraph(self.formatar_moeda(servico.get('valor_total', Decimal('0.00'))), self.styles['NormalText'])])
                data.append([Paragraph("Valor Total Serviços Adicionais:", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(total_adicionais), self.styles['BoldBodyText'])])
                table = Table(data, colWidths=[int(11*cm * sf), int(5*cm * sf)])
            table.setStyle(self._get_table_style_for_layout(layout, len(data)))
            story.append(table)
            story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_treinamento_setup(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        treinamento_valor = proposta_data.get('valor_treinamento', Decimal('0.00'))
        setup_valor = proposta_data.get('valor_setup', Decimal('0.00'))
        if treinamento_valor > 0 or setup_valor > 0:
            story.append(Paragraph("SETUP DE IMPLANTAÇÃO", self.styles['MainHeaderStyle']))
            data = []
            if layout == 'grid':
                headers = []
                values = []
                if treinamento_valor > 0:
                    headers.append(Paragraph("Treinamento", self.styles['BoldBodyText']))
                    values.append(Paragraph(f"{proposta_data.get('treinamento_tipo', 'N/A')} ({self.formatar_moeda(treinamento_valor)})", self.styles['NormalText']))
                if setup_valor > 0:
                    headers.append(Paragraph("Setup Inicial", self.styles['BoldBodyText']))
                    values.append(Paragraph(self.formatar_moeda(setup_valor), self.styles['NormalText']))
                if headers:
                    data.append(headers)
                    data.append(values)
                    col_width = (self.config.PAGE_WIDTH - self.config.MARGIN_LEFT - self.config.MARGIN_RIGHT) / len(headers)
                    table = Table(data, colWidths=[col_width] * len(headers))
                    table.setStyle(self._get_table_style_for_layout(layout, len(data)))
                    story.append(table)
            else:
                if treinamento_valor > 0:
                    data.append([Paragraph(f"Treinamento ({proposta_data.get('treinamento_tipo', 'N/A')}):", self.styles['NormalText']), Paragraph(self.formatar_moeda(treinamento_valor), self.styles['NormalText'])])
                if setup_valor > 0:
                    data.append([Paragraph("Setup Inicial:", self.styles['NormalText']), Paragraph(self.formatar_moeda(setup_valor), self.styles['NormalText'])])
                table = Table(data, colWidths=[int(11*cm * sf), int(5*cm * sf)])
                table.setStyle(self._get_table_style_for_layout(layout, len(data)))
                story.append(table)
            story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_observacoes(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        observacoes = proposta_data.get('observacoes')
        if observacoes:
            story.append(Paragraph("OBSERVAÇÕES", self.styles['MainHeaderStyle']))
            story.append(Paragraph(observacoes, self.styles['NormalText']))
            story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_secao_resumo_proposta(self, proposta_data: Dict[str, Any], layout: str) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Paragraph("RESUMO DA PROPOSTA", self.styles['MainHeaderStyle']))
        valor_plano_base = proposta_data.get('valor_plano_base', Decimal('0.00'))
        total_adicionais = proposta_data.get('total_adicionais', Decimal('0.00'))
        valor_total_contrato_mensal = valor_plano_base + total_adicionais
        if layout == 'grid':
            data_mensal = [
                [Paragraph("Licença (Mensal)", self.styles['BoldBodyText']), Paragraph("Serviços Adicionais", self.styles['BoldBodyText']), Paragraph("TOTAL (MENSAL)", self.styles['BoldBodyText'])],
                [Paragraph(self.formatar_moeda(valor_plano_base), self.styles['NormalText']), Paragraph(self.formatar_moeda(total_adicionais), self.styles['NormalText']), Paragraph(self.formatar_moeda(valor_total_contrato_mensal), self.styles['BoldBodyText'])]
            ]
            table_mensal = Table(data_mensal, colWidths=[int(5.3*cm * sf), int(5.3*cm * sf), int(5.3*cm * sf)])
        else:
            data_mensal = [
                [Paragraph("Valor Total da Licença (Mensal):", self.styles['NormalText']), Paragraph(self.formatar_moeda(valor_plano_base), self.styles['NormalText'])],
                [Paragraph("Valor Total dos Serviços Adicionais:", self.styles['NormalText']), Paragraph(self.formatar_moeda(total_adicionais), self.styles['NormalText'])],
                [Paragraph("VALOR TOTAL DO CONTRATO (MENSAL):", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(valor_total_contrato_mensal), self.styles['BoldBodyText'])],
            ]
            table_mensal = Table(data_mensal, colWidths=[int(11*cm * sf), int(5*cm * sf)])
        table_mensal.setStyle(self._get_table_style_for_layout(layout, len(data_mensal)))
        story.append(table_mensal)
        story.append(Spacer(1, int(0.5*cm * sf)))
        setup_valor = proposta_data.get('valor_setup', Decimal('0.00'))
        treinamento_valor = proposta_data.get('valor_treinamento', Decimal('0.00'))
        desconto_valor = proposta_data.get('desconto_valor', Decimal('0.00'))
        total_servicos_avulsos = setup_valor + treinamento_valor
        total_geral_a_pagar_avulsos = total_servicos_avulsos - desconto_valor
        if layout == 'grid':
            data_avulsos = [
                [Paragraph("Setup", self.styles['BoldBodyText']), Paragraph("Treinamento", self.styles['BoldBodyText']), Paragraph("Total Avulsos", self.styles['BoldBodyText']), Paragraph("Desconto", self.styles['BoldBodyText']), Paragraph("TOTAL GERAL", self.styles['BoldBodyText'])],
                [Paragraph(self.formatar_moeda(setup_valor), self.styles['NormalText']), Paragraph(self.formatar_moeda(treinamento_valor), self.styles['NormalText']), Paragraph(self.formatar_moeda(total_servicos_avulsos), self.styles['BoldBodyText']), Paragraph(f"-{self.formatar_moeda(desconto_valor)}", self.styles['NormalText']), Paragraph(self.formatar_moeda(total_geral_a_pagar_avulsos), self.styles['BoldBodyText'])]
            ]
            table_avulsos = Table(data_avulsos, colWidths=[int(3.2*cm * sf), int(3.2*cm * sf), int(3.2*cm * sf), int(3.2*cm * sf), int(3.2*cm * sf)])
        else:
            data_avulsos = [
                [Paragraph("Setup de Implantação:", self.styles['NormalText']), Paragraph(self.formatar_moeda(setup_valor), self.styles['NormalText'])],
                [Paragraph(f"Treinamento ({proposta_data.get('treinamento_tipo', 'N/A')}):", self.styles['NormalText']), Paragraph(self.formatar_moeda(treinamento_valor), self.styles['NormalText'])],
                [Paragraph("TOTAL SERVIÇOS AVULSOS:", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(total_servicos_avulsos), self.styles['BoldBodyText'])],
                [Paragraph("Desconto:", self.styles['NormalText']), Paragraph(f"-{self.formatar_moeda(desconto_valor)}", self.styles['NormalText'])],
                [Paragraph("TOTAL GERAL A PAGAR (AVULSOS):", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(total_geral_a_pagar_avulsos), self.styles['BoldBodyText'])],
            ]
            table_avulsos = Table(data_avulsos, colWidths=[int(11*cm * sf), int(5*cm * sf)])
        table_avulsos.setStyle(self._get_table_style_for_layout(layout, len(data_avulsos)))
        story.append(table_avulsos)
        story.append(Spacer(1, int(0.5*cm * sf)))
        return story

    def _criar_rodape(self, proposta_data: Dict[str, Any]) -> list:
        story = []
        sf = self.config.SCALE_FACTOR
        story.append(Spacer(1, int(1*cm * sf)))
        story.append(Paragraph(f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}. Valores sujeitos a confirmação.", self.styles['Footer']))
        return story


router = APIRouter()
pdf_config = PDFConfig()
pdf_service = PDFService(pdf_config)


@router.get("/proposta/{hash_id}/pdf")
async def baixar_pdf_proposta_melhorado(hash_id: str, layout: str = "card", db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")
    servicos_detalhes = []
    total_adicionais = Decimal('0.00')
    if proposta.servicos_adicionais:
        try:
            servicos_json = json.loads(proposta.servicos_adicionais)
            if isinstance(servicos_json, dict):
                for key, value in servicos_json.items():
                    if isinstance(value, dict) and 'valor_total' in value:
                        val_total = Decimal(str(value.get('valor_total', 0)))
                        servicos_detalhes.append({'nome': key.replace('_', ' ').title(), 'valor_total': val_total})
                        total_adicionais += val_total
        except Exception as e:
            logger.error(f"Erro ao processar serviços adicionais para proposta {hash_id}: {e}")
    valor_mensal_total_do_banco = Decimal(str(getattr(proposta, 'valor_mensal') or 0))
    valor_plano_base = valor_mensal_total_do_banco - total_adicionais
    if valor_plano_base < 0:
        valor_plano_base = Decimal('0.00')
    proposta_data = {
        'hash_id': getattr(proposta, 'hash_id') or 'N/A',
        'razao_social': getattr(proposta, 'razao_social') or 'N/A',
        'nome_fantasia': getattr(proposta, 'nome_fantasia') or 'N/A',
        'cnpj': getattr(proposta, 'cnpj') or 'N/A',
        'email': getattr(proposta, 'email') or 'N/A',
        'whatsapp': getattr(proposta, 'whatsapp') or 'Não informado',
        'plano': getattr(proposta, 'plano') or 'N/A',
        'usuarios': getattr(proposta, 'usuarios') or 0,
        'usuarios_arredondados': getattr(proposta, 'usuarios_arredondados') or 0,
        'valor_plano_base': valor_plano_base,
        'servicos_adicionais_detalhes': servicos_detalhes,
        'total_adicionais': total_adicionais,
        'valor_setup': Decimal(str(getattr(proposta, 'setup_ajustado') or getattr(proposta, 'setup_padrao') or 0)),
        'valor_treinamento': Decimal(str(getattr(proposta, 'treinamento_valor') or 0)),
        'treinamento_tipo': getattr(proposta, 'treinamento_tipo') or 'N/A',
        'desconto_valor': Decimal(str(getattr(proposta, 'desconto_valor') or 0)),
        'desconto_percentual': Decimal(str(getattr(proposta, 'desconto_percentual') or 0)),
        'observacoes': getattr(proposta, 'observacoes') or '',
        'data_validade': getattr(proposta, 'data_validade'),
        'data_criacao': getattr(proposta, 'data_criacao'),
        'status': getattr(proposta, 'status') or 'N/A',
    }
    pdf_buffer = pdf_service.gerar_pdf_proposta(proposta_data, layout)
    return StreamingResponse(iter([pdf_buffer.getvalue()]), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=proposta_{proposta.hash_id}_{layout}.pdf"})