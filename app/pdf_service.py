import io
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import black, HexColor, grey

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class PDFConfig:
    """
    Configurações globais para a geração de PDFs.
    Define tamanhos de página, margens, fontes e cores padrão.
    """
    PAGE_SIZE = A4
    MARGIN_TOP = 20 * mm
    MARGIN_BOTTOM = 15 * mm
    MARGIN_LEFT = 20 * mm
    MARGIN_RIGHT = 20 * mm

    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    FONT_ITALIC = 'Helvetica-Oblique'

    FONT_SIZE_HEADER = 20
    FONT_SIZE_SUBHEADER = 14
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_SMALL = 8
    FONT_SIZE_TINY = 7

    COLOR_PRIMARY = HexColor('#1A3A52')      # Azul escuro profissional
    COLOR_SECONDARY = HexColor('#2E5C8A')    # Azul médio
    COLOR_ACCENT = HexColor('#007BFF')       # Azul claro
    COLOR_TEXT = HexColor('#333333')         # Cinza escuro
    COLOR_LIGHT = HexColor('#F5F5F5')        # Cinza claro
    COLOR_BORDER = HexColor('#CCCCCC')       # Cinza médio

    COMPANY_NAME = "Flexx Solutions Ltda."
    COMPANY_CNPJ = "XX.XXX.XXX/0001-XX"
    COMPANY_ADDRESS = "Rua da Inovação, 123 - Centro, São Paulo - SP"
    COMPANY_PHONE = "(11) 98765-4321"
    COMPANY_EMAIL = "contato@flexx.com.br"
    COMPANY_WEBSITE = "www.flexx.com.br"

    LOGO_DEFAULT_PATH: Optional[str] = None

class PDFService:
    """
    Serviço para geração de documentos PDF, especificamente propostas comerciais.
    Utiliza a biblioteca ReportLab para criar PDFs formatados profissionalmente.
    """
    def __init__(self, config: Optional[PDFConfig] = None, email_service = None):
        """
        Inicializa o PDFService com configurações opcionais.
        """
        self.config = config or PDFConfig()
        self.email_service = email_service
        self.styles = getSampleStyleSheet()

        # Estilos de parágrafo customizados
        self._criar_estilos_customizados()

        logger.info("PDFService inicializado com sucesso")

    def _criar_estilos_customizados(self):
        """Cria estilos customizados para o PDF."""
        
        if 'TitleStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='TitleStyle',
                fontName=self.config.FONT_BOLD,
                fontSize=self.config.FONT_SIZE_HEADER,
                leading=24,
                alignment=TA_CENTER,
                textColor=self.config.COLOR_PRIMARY,
                spaceAfter=12
            ))

        if 'HeaderStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='HeaderStyle',
                fontName=self.config.FONT_BOLD,
                fontSize=self.config.FONT_SIZE_SUBHEADER,
                leading=18,
                alignment=TA_LEFT,
                textColor=self.config.COLOR_PRIMARY,
                spaceAfter=8,
                spaceBefore=8
            ))

        if 'SubHeaderStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubHeaderStyle',
                fontName=self.config.FONT_BOLD,
                fontSize=self.config.FONT_SIZE_NORMAL,
                leading=14,
                alignment=TA_LEFT,
                textColor=self.config.COLOR_SECONDARY,
                spaceAfter=6
            ))

        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                fontName=self.config.FONT_NORMAL,
                fontSize=self.config.FONT_SIZE_NORMAL,
                leading=14,
                alignment=TA_LEFT,
                textColor=self.config.COLOR_TEXT
            ))

        if 'BoldBodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BoldBodyText',
                fontName=self.config.FONT_BOLD,
                fontSize=self.config.FONT_SIZE_NORMAL,
                leading=14,
                alignment=TA_LEFT,
                textColor=self.config.COLOR_TEXT
            ))

        if 'SmallText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SmallText',
                fontName=self.config.FONT_NORMAL,
                fontSize=self.config.FONT_SIZE_SMALL,
                leading=10,
                alignment=TA_LEFT,
                textColor=self.config.COLOR_TEXT
            ))

        if 'CenterText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CenterText',
                fontName=self.config.FONT_NORMAL,
                fontSize=self.config.FONT_SIZE_NORMAL,
                leading=14,
                alignment=TA_CENTER,
                textColor=self.config.COLOR_TEXT
            ))

        if 'TotalStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='TotalStyle',
                fontName=self.config.FONT_BOLD,
                fontSize=14,
                leading=16,
                alignment=TA_RIGHT,
                textColor=self.config.COLOR_PRIMARY
            ))

    def formatar_moeda(self, valor: Any) -> str:
        """
        Formata valor para padrão brasileiro.
        """
        try:
            if isinstance(valor, Decimal):
                valor = float(valor)
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return "R$ 0,00"

    def gerar_pdf_proposta(self, proposta_data: Dict[str, Any], logo_path: Optional[str] = None) -> bytes:
        """
        Gera PDF da proposta e retorna bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=self.config.PAGE_SIZE, 
            leftMargin=self.config.MARGIN_LEFT,
            rightMargin=self.config.MARGIN_RIGHT,
            topMargin=self.config.MARGIN_TOP,
            bottomMargin=self.config.MARGIN_BOTTOM
        )
        
        story = self._construir_story(proposta_data, logo_path)
        doc.build(story)
        buffer.seek(0)
        logger.info(f"PDF gerado para proposta {proposta_data.get('hash_id', 'N/A')}")
        return buffer.getvalue()

    def _construir_story(self, proposta_data: Dict[str, Any], logo_path: Optional[str] = None) -> list:
        """
        Constrói o conteúdo do PDF com layout profissional.
        """
        story = []

        # ========== CABEÇALHO ==========
        story.extend(self._criar_cabecalho(logo_path))

        # ========== TÍTULO ==========
        story.append(Spacer(1, 12))
        story.append(Paragraph("PROPOSTA COMERCIAL", self.styles['TitleStyle']))
        story.append(Spacer(1, 6))
        
        # Número e data da proposta
        hash_id = proposta_data.get('hash_id', 'N/A')
        data_criacao = proposta_data.get('data_criacao', 'N/A')
        story.append(Paragraph(
            f"<font size=8>Proposta nº: <b>{hash_id}</b> | Data: <b>{data_criacao}</b></font>",
            self.styles['CenterText']
        ))
        story.append(Spacer(1, 12))

        # ========== DADOS DO CLIENTE ==========
        story.extend(self._criar_secao_cliente(proposta_data))

        # ========== DETALHES DA PROPOSTA ==========
        story.extend(self._criar_secao_detalhes(proposta_data))

        # ========== RESUMO FINANCEIRO ==========
        story.extend(self._criar_secao_financeira(proposta_data))

        # ========== OBSERVAÇÕES ==========
        if proposta_data.get('observacoes'):
            story.extend(self._criar_secao_observacoes(proposta_data))

        # ========== VALIDADE E ASSINATURA ==========
        story.extend(self._criar_secao_validade(proposta_data))

        # ========== RODAPÉ ==========
        story.extend(self._criar_rodape())

        return story

    def _criar_cabecalho(self, logo_path: Optional[str] = None) -> list:
        """Cria o cabeçalho do PDF com logo e dados da empresa."""
        story = []

        # Tabela com logo e dados da empresa
        logo_cell = ""
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=1.2*inch, height=0.6*inch)
                logo_cell = img
            except Exception as e:
                logger.warning(f"Logo não carregado: {e}")

        # Dados da empresa
        empresa_text = f"""
        <b>{self.config.COMPANY_NAME}</b><br/>
        CNPJ: {self.config.COMPANY_CNPJ}<br/>
        {self.config.COMPANY_ADDRESS}<br/>
        Tel: {self.config.COMPANY_PHONE}<br/>
        Email: {self.config.COMPANY_EMAIL}<br/>
        Site: {self.config.COMPANY_WEBSITE}
        """

        header_data = [
            [logo_cell, Paragraph(empresa_text, self.styles['SmallText'])]
        ]

        header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 8))
        
        # Linha separadora
        story.append(Paragraph("_" * 100, self.styles['SmallText']))
        
        return story

    def _criar_secao_cliente(self, proposta_data: Dict[str, Any]) -> list:
        """Cria a seção de dados do cliente."""
        story = []

        story.append(Paragraph("DADOS DO CLIENTE", self.styles['HeaderStyle']))

        # Tabela com dados do cliente
        cliente_data = [
            [
                Paragraph(f"<b>Razão Social:</b><br/>{proposta_data.get('razao_social', 'N/A')}", self.styles['SmallText']),
                Paragraph(f"<b>CNPJ:</b><br/>{proposta_data.get('cnpj', 'N/A')}", self.styles['SmallText'])
            ],
            [
                Paragraph(f"<b>Email:</b><br/>{proposta_data.get('email', 'N/A')}", self.styles['SmallText']),
                Paragraph(f"<b>Telefone:</b><br/>{proposta_data.get('telefone', 'N/A')}", self.styles['SmallText'])
            ],
            [
                Paragraph(f"<b>WhatsApp:</b><br/>{proposta_data.get('whatsapp', 'N/A')}", self.styles['SmallText']),
                Paragraph(f"<b>Nome Fantasia:</b><br/>{proposta_data.get('nome_fantasia', 'N/A')}", self.styles['SmallText'])
            ]
        ]

        cliente_table = Table(cliente_data, colWidths=[3.5*inch, 3.5*inch])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.config.COLOR_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, self.config.COLOR_BORDER),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(cliente_table)
        story.append(Spacer(1, 12))

        return story

    def _criar_secao_detalhes(self, proposta_data: Dict[str, Any]) -> list:
        """Cria a seção de detalhes da proposta."""
        story = []

        story.append(Paragraph("DETALHES DA PROPOSTA", self.styles['HeaderStyle']))

        # Tabela de itens
        data = [
            [
                Paragraph("<b>Item</b>", self.styles['SmallText']),
                Paragraph("<b>Descrição</b>", self.styles['SmallText']),
                Paragraph("<b>Valor Unit.</b>", self.styles['SmallText']),
                Paragraph("<b>Qtd.</b>", self.styles['SmallText']),
                Paragraph("<b>Total</b>", self.styles['SmallText'])
            ]
        ]

        # Plano
        valor_mensal = self.formatar_moeda(proposta_data.get('valor_mensal', 0))
        usuarios = proposta_data.get('usuarios_arredondados', proposta_data.get('usuarios', 0))
        subtotal_plano = float(proposta_data.get('valor_mensal', 0)) * usuarios
        
        data.append([
            Paragraph("1", self.styles['SmallText']),
            Paragraph(f"Plano {proposta_data.get('plano', 'N/A')}", self.styles['SmallText']),
            Paragraph(valor_mensal, self.styles['SmallText']),
            Paragraph(str(usuarios), self.styles['SmallText']),
            Paragraph(self.formatar_moeda(subtotal_plano), self.styles['SmallText'])
        ])

        # Setup
        # Setup
        item_num = 2
        setup_ajustado = proposta_data.get('setup_ajustado') or 0
        setup_padrao = proposta_data.get('setup_padrao') or 0
        
        if float(setup_ajustado or 0) > 0 or float(setup_padrao or 0) > 0:
            setup_valor = proposta_data.get('setup_ajustado') or proposta_data.get('setup_padrao', 0)
            data.append([
                Paragraph(str(item_num), self.styles['SmallText']),
                Paragraph("Setup / Implantação", self.styles['SmallText']),
                Paragraph(self.formatar_moeda(setup_valor), self.styles['SmallText']),
                Paragraph("1", self.styles['SmallText']),
                Paragraph(self.formatar_moeda(setup_valor), self.styles['SmallText'])
            ])
            item_num += 1

        # Treinamento
        if proposta_data.get('treinamento_valor', 0) > 0:
            data.append([
                Paragraph(str(item_num), self.styles['SmallText']),
                Paragraph(f"Treinamento ({proposta_data.get('treinamento_tipo', 'N/A')})", self.styles['SmallText']),
                Paragraph(self.formatar_moeda(proposta_data.get('treinamento_valor', 0)), self.styles['SmallText']),
                Paragraph("1", self.styles['SmallText']),
                Paragraph(self.formatar_moeda(proposta_data.get('treinamento_valor', 0)), self.styles['SmallText'])
            ])
            item_num += 1

        # Serviços adicionais
        servicos = proposta_data.get('servicos_adicionais', [])
        if servicos:
            if isinstance(servicos, str):
                servicos = [s.strip() for s in servicos.split(',') if s.strip()]
            
            for servico in servicos:
                data.append([
                    Paragraph(str(item_num), self.styles['SmallText']),
                    Paragraph(f"Serviço: {servico}", self.styles['SmallText']),
                    Paragraph("Variável", self.styles['SmallText']),
                    Paragraph("-", self.styles['SmallText']),
                    Paragraph("-", self.styles['SmallText'])
                ])
                item_num += 1

        # Criar tabela
        table = Table(data, colWidths=[0.6*inch, 2.5*inch, 1.2*inch, 0.8*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.config.COLOR_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.config.FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.config.COLOR_BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), self.config.COLOR_LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(table)
        story.append(Spacer(1, 12))

        return story

    def _criar_secao_financeira(self, proposta_data: Dict[str, Any]) -> list:
        """Cria a seção de resumo financeiro."""
        story = []

        story.append(Paragraph("RESUMO FINANCEIRO", self.styles['HeaderStyle']))

        # Tabela de resumo
        subtotal = proposta_data.get('subtotal', 0)
        desconto = proposta_data.get('desconto_valor', 0)
        total = proposta_data.get('total', 0)

        resumo_data = [
            [Paragraph("<b>Subtotal:</b>", self.styles['BoldBodyText']), Paragraph(self.formatar_moeda(subtotal), self.styles['BoldBodyText'])],
        ]

        if desconto > 0:
            desconto_pct = proposta_data.get('desconto_percentual', 0)
            if desconto_pct > 0:
                resumo_data.append([
                    Paragraph(f"<b>Desconto ({desconto_pct}%):</b>", self.styles['BoldBodyText']),
                    Paragraph(f"-{self.formatar_moeda(desconto)}", self.styles['BoldBodyText'])
                ])
            else:
                resumo_data.append([
                    Paragraph("<b>Desconto:</b>", self.styles['BoldBodyText']),
                    Paragraph(f"-{self.formatar_moeda(desconto)}", self.styles['BoldBodyText'])
                ])

        resumo_data.append([
            Paragraph("<b>TOTAL DA PROPOSTA:</b>", self.styles['TotalStyle']),
            Paragraph(self.formatar_moeda(total), self.styles['TotalStyle'])
        ])

        resumo_table = Table(resumo_data, colWidths=[4.5*inch, 2*inch])
        resumo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), self.config.FONT_NORMAL),
            ('FONTNAME', (0, -1), (-1, -1), self.config.FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), self.config.COLOR_LIGHT),
            ('GRID', (0, -1), (-1, -1), 1, self.config.COLOR_PRIMARY),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(resumo_table)
        story.append(Spacer(1, 12))

        return story

    def _criar_secao_observacoes(self, proposta_data: Dict[str, Any]) -> list:
        """Cria a seção de observações."""
        story = []

        story.append(Paragraph("OBSERVAÇÕES", self.styles['HeaderStyle']))
        story.append(Paragraph(proposta_data.get('observacoes', ''), self.styles['BodyText']))
        story.append(Spacer(1, 12))

        return story

    def _criar_secao_validade(self, proposta_data: Dict[str, Any]) -> list:
        """Cria a seção de validade e assinatura."""
        story = []

        data_validade = proposta_data.get('data_validade', 'N/A')
        story.append(Paragraph(f"<b>Válida até:</b> {data_validade}", self.styles['BoldBodyText']))
        story.append(Spacer(1, 20))

        # Assinatura
        assinatura_data = [
            [
                Paragraph("_" * 30, self.styles['SmallText']),
                Paragraph("_" * 30, self.styles['SmallText'])
            ],
            [
                Paragraph("Assinado por", self.styles['SmallText']),
                Paragraph("Data", self.styles['SmallText'])
            ]
        ]

        assinatura_table = Table(assinatura_data, colWidths=[3.5*inch, 3.5*inch])
        assinatura_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(assinatura_table)
        story.append(Spacer(1, 12))

        return story

    def _criar_rodape(self) -> list:
        """Cria o rodapé do PDF."""
        story = []

        story.append(Spacer(1, 12))
        story.append(Paragraph("_" * 100, self.styles['SmallText']))
        story.append(Spacer(1, 6))

        rodape_text = f"""
        <font size=7>
        <b>{self.config.COMPANY_NAME}</b> | CNPJ: {self.config.COMPANY_CNPJ}<br/>
        {self.config.COMPANY_ADDRESS}<br/>
        Tel: {self.config.COMPANY_PHONE} | Email: {self.config.COMPANY_EMAIL} | Site: {self.config.COMPANY_WEBSITE}<br/>
        <i>Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</i>
        </font>
        """

        story.append(Paragraph(rodape_text, self.styles['CenterText']))

        return story

# Instância global para importação
pdf_config = PDFConfig()
pdf_service = PDFService(pdf_config)

if __name__ == '__main__':
    # Teste rápido
    proposta_teste = {
        'razao_social': 'Empresa Teste Ltda',
        'nome_fantasia': 'Empresa Teste',
        'cnpj': '12.345.678/0001-90',
        'email': 'contato@empresateste.com.br',
        'telefone': '(11) 3333-3333',
        'whatsapp': '(11) 99999-9999',
        'plano': 'PRO',
        'usuarios': 15,
        'usuarios_arredondados': 20,
        'valor_mensal': Decimal('115.80'),
        'setup_padrao': Decimal('500.00'),
        'setup_ajustado': Decimal('500.00'),
        'treinamento_tipo': 'Presencial',
        'treinamento_valor': Decimal('300.00'),
        'servicos_adicionais': 'Licença Facial, Gestão de Arquivos',
        'subtotal': Decimal('2500.00'),
        'desconto_valor': Decimal('250.00'),
        'desconto_percentual': Decimal('10.00'),
        'total': Decimal('2250.00'),
        'observacoes': 'Proposta válida por 30 dias. Sujeita a alterações conforme necessidade do cliente.',
        'data_validade': (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y'),
        'data_criacao': datetime.now().strftime('%d/%m/%Y'),
        'hash_id': 'PROP-2026-001'
    }
    
    pdf_bytes = pdf_service.gerar_pdf_proposta(proposta_teste)
    with open('teste_proposta.pdf', 'wb') as f:
        f.write(pdf_bytes)
    print("✅ PDF gerado com sucesso: teste_proposta.pdf")