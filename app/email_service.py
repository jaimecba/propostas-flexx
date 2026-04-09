import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, Tuple, Any
from datetime import datetime
import logging
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import qrcode
from qrcode.image.pure import PyPNGImage
from reportlab.lib.units import inch

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# CONFIGURAÇÃO DE EMAIL
class EmailConfig:
    """Configuração de email lida do ambiente."""
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_USER = os.getenv("SMTP_USER", "")
    EMAIL_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM = os.getenv("SMTP_FROM", "")
    EMAIL_FROM_NAME = os.getenv("APP_NAME", "Flexx Proposta")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    EMAIL_GERENTE = os.getenv("EMAIL_GERENTE", "")
    NOTIFICAR_GERENTE = os.getenv("NOTIFICAR_GERENTE", "True").lower() == 'true'
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# SERVIÇO DE EMAIL
class EmailService:
    """Serviço para enviar emails, incluindo anexos PDF e notificações."""

    def __init__(self):
        self.smtp_server = EmailConfig.SMTP_SERVER
        self.smtp_port = EmailConfig.SMTP_PORT
        self.email_user = EmailConfig.EMAIL_USER
        self.email_password = EmailConfig.EMAIL_PASSWORD
        self.email_from = EmailConfig.EMAIL_FROM
        self.email_from_name = EmailConfig.EMAIL_FROM_NAME
        self.base_url = EmailConfig.BASE_URL
        self.email_gerente = EmailConfig.EMAIL_GERENTE
        self.notificar_gerente = EmailConfig.NOTIFICAR_GERENTE
        self.app_version = EmailConfig.APP_VERSION
        self.timeout = 10  # Timeout para SMTP

        # Validação de configuração
        if not all([self.email_user, self.email_password, self.email_from]):
            logger.warning("⚠️ EmailService: Credenciais SMTP incompletas. Verifique SMTP_USER, SMTP_PASSWORD e SMTP_FROM no .env")
        else:
            logger.info("✅ EmailService inicializado com sucesso.")

    def enviar_email_simples(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        eh_html: bool = False
    ) -> bool:
        """
        Envia um email simples para um destinatário.
        """
        if not self.email_user or not self.email_password:
            logger.error("❌ Credenciais SMTP não configuradas no .env para enviar email simples.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = f"{self.email_from_name} <{self.email_from}>"
        msg["To"] = destinatario

        if eh_html:
            msg.attach(MIMEText(corpo, "html", 'utf-8'))
        else:
            msg.attach(MIMEText(corpo, "plain", 'utf-8'))

        server = None
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            logger.info(f"✅ Email simples enviado para {destinatario}.")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ Erro de autenticação SMTP. Verifique SMTP_USER/SMTP_PASSWORD (use App Password do Google).")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ Erro de conexão SMTP: {e}. Verifique rede/firewall.")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"❌ SMTP desconectado: {e}.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Erro SMTP geral ao enviar email simples para {destinatario}: {e}.")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no envio de email simples para {destinatario}: {e}.")
            return False
        finally:
            if server:
                server.quit()

    def gerar_pdf_proposta(self, nome_cliente: str, link_proposta: str, valor_total: str) -> Optional[bytes]:
        """
        Gera um PDF simples da proposta com informações básicas.
        """
        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Cabeçalho
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, height - 100, "Proposta Comercial Flexx")
            p.setFont("Helvetica", 10)
            p.drawString(100, height - 120, f"Cliente: {nome_cliente}")
            p.drawString(100, height - 140, f"Link para Visualizar: {link_proposta}")
            p.drawString(100, height - 160, f"Valor Total: {valor_total}")
            p.drawString(100, height - 180, f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            # Resumo básico
            y = height - 220
            p.drawString(100, y, "Resumo: Proposta inclui plano mensal, setup e serviços adicionais.")
            y -= 20
            p.drawString(100, y, "Para detalhes completos, acesse o link acima ou responda este e-mail.")

            # Rodapé com branding
            p.setFont("Helvetica", 9)
            p.drawString(100, 50, "Assinatura: Equipe Flexx Propostas")
            p.drawString(100, 30, f"Contato: {self.email_gerente or 'comercial.flexx@gmail.com'} | (11) 99999-9999")
            p.drawString(100, 10, f"© {datetime.now().year} Flexx Propostas - {self.app_version}")

            p.save()
            buffer.seek(0)
            pdf_bytes = buffer.getvalue()
            logger.info("✅ PDF gerado com sucesso.")
            return pdf_bytes
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF: {e}.")
            return None
        
    def gerar_pdf_completo(self, proposta: Any) -> Optional[bytes]:
        """
        Gera um PDF completo e profissional da proposta com todos os dados.
        """
        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Configurações
            margin = 0.5 * inch
            y_position = height - margin
            line_height = 0.2 * inch
            
            # ===== CABEÇALHO =====
            p.setFont("Helvetica-Bold", 18)
            p.drawString(margin, y_position, "PROPOSTA COMERCIAL")
            y_position -= line_height * 1.5
            
            p.setFont("Helvetica", 10)
            p.drawString(margin, y_position, f"Flexx Propostas - Sistema de Gestão")
            y_position -= line_height
            p.drawString(margin, y_position, f"ID: {proposta.hash_id}")
            y_position -= line_height * 1.5
            
            # ===== DADOS DO CLIENTE =====
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_position, "DADOS DO CLIENTE")
            y_position -= line_height
            
            p.setFont("Helvetica", 10)
            p.drawString(margin, y_position, f"Razão Social: {proposta.razao_social}")
            y_position -= line_height
            p.drawString(margin, y_position, f"CNPJ: {proposta.cnpj}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Email: {proposta.email}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Telefone: {proposta.telefone or 'N/A'}")
            y_position -= line_height
            p.drawString(margin, y_position, f"WhatsApp: {proposta.whatsapp}")
            y_position -= line_height * 1.5
            
            # ===== DETALHES DO PLANO =====
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_position, "DETALHES DO PLANO")
            y_position -= line_height
            
            p.setFont("Helvetica", 10)
            p.drawString(margin, y_position, f"Plano: {proposta.plano.upper()}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Número de Usuários: {proposta.usuarios}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Usuários Arredondados: {proposta.usuarios_arredondados}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Valor Mensal: R$ {proposta.valor_mensal:,.2f}")
            y_position -= line_height * 1.5
            
            # ===== TREINAMENTO =====
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_position, "TREINAMENTO")
            y_position -= line_height
            
            p.setFont("Helvetica", 10)
            p.drawString(margin, y_position, f"Tipo: {proposta.treinamento_tipo or 'Não informado'}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Valor: R$ {proposta.treinamento_valor or 0:,.2f}")
            y_position -= line_height * 1.5
            
            # ===== SETUP INICIAL =====
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_position, "SETUP INICIAL")
            y_position -= line_height
            
            p.setFont("Helvetica", 10)
            setup_valor = proposta.setup_ajustado or proposta.setup_padrao or 0
            p.drawString(margin, y_position, f"Valor: R$ {setup_valor:,.2f}")
            y_position -= line_height * 1.5
            
            # ===== SERVIÇOS ADICIONAIS =====
            if proposta.servicos_adicionais:
                p.setFont("Helvetica-Bold", 12)
                p.drawString(margin, y_position, "SERVIÇOS ADICIONAIS")
                y_position -= line_height

                p.setFont("Helvetica", 9)
                for servico in proposta.servicos_adicionais:
                    # Aceita objeto, dict ou string
                    if isinstance(servico, dict):
                        nome = servico.get("nome") or servico.get("nome_servico") or "Serviço"
                        tipo_raw = servico.get("tipo") or servico.get("tipo_cobranca") or ""
                        valor_raw = servico.get("valor") or servico.get("valor_unitario") or 0
                    else:
                        nome = getattr(servico, "nome", None) or getattr(servico, "nome_servico", None) or str(servico)
                        tipo_raw = getattr(servico, "tipo", None) or getattr(servico, "tipo_cobranca", None) or ""
                        valor_raw = getattr(servico, "valor", None) or getattr(servico, "valor_unitario", None) or 0

                    tipo = "Mensal" if str(tipo_raw).lower() == "mensal" else "Fixo"

                    try:
                        valor_num = float(valor_raw)
                    except Exception:
                        valor_num = 0

                    p.drawString(
                        margin + 0.2 * inch,
                        y_position,
                        f"• {nome} ({tipo}): R$ {valor_num:,.2f}"
                    )
                    y_position -= line_height

                y_position -= line_height * 0.5
            
            # ===== RESUMO DE VALORES =====
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_position, "RESUMO DE VALORES")
            y_position -= line_height
            
            p.setFont("Helvetica", 10)
            p.drawString(margin, y_position, f"Valor Mensal: R$ {proposta.valor_mensal:,.2f}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Setup Inicial: R$ {setup_valor:,.2f}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Treinamento: R$ {proposta.treinamento_valor or 0:,.2f}")
            y_position -= line_height
            
            # Subtotal
            subtotal = proposta.valor_mensal + setup_valor + (proposta.treinamento_valor or 0)
            p.drawString(margin, y_position, f"Subtotal: R$ {subtotal:,.2f}")
            y_position -= line_height
            
            # Desconto
            desconto_valor = proposta.desconto_valor or 0
            p.drawString(margin, y_position, f"Desconto: -R$ {desconto_valor:,.2f}")
            y_position -= line_height
            
            # Total
            p.setFont("Helvetica-Bold", 12)
            total = proposta.total or (subtotal - desconto_valor)
            p.drawString(margin, y_position, f"TOTAL: R$ {total:,.2f}")
            y_position -= line_height * 1.5
            
            # ===== OBSERVAÇÕES =====
            if proposta.observacoes:
                p.setFont("Helvetica-Bold", 12)
                p.drawString(margin, y_position, "OBSERVAÇÕES")
                y_position -= line_height
                
                p.setFont("Helvetica", 9)
                # Quebra texto longo em múltiplas linhas
                max_chars = 80
                observacoes = proposta.observacoes
                while len(observacoes) > max_chars:
                    p.drawString(margin, y_position, observacoes[:max_chars])
                    observacoes = observacoes[max_chars:]
                    y_position -= line_height
                
                if observacoes:
                    p.drawString(margin, y_position, observacoes)
                
                y_position -= line_height * 1.5
            
            # ===== INFORMAÇÕES ADICIONAIS =====
            p.setFont("Helvetica", 9)
            p.drawString(margin, y_position, f"Data de Criação: {proposta.data_criacao.strftime('%d/%m/%Y %H:%M') if proposta.data_criacao else 'N/A'}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Data de Validade: {proposta.data_validade.strftime('%d/%m/%Y %H:%M') if proposta.data_validade else 'N/A'}")
            y_position -= line_height
            p.drawString(margin, y_position, f"Visualizações: {proposta.total_visualizacoes()}")
            y_position -= line_height * 1.5
            
            # ===== RODAPÉ =====
            p.setFont("Helvetica", 8)
            p.drawString(margin, 40, "Flexx Propostas - Sistema de Gestão de Propostas Comerciais")
            p.drawString(margin, 25, f"Contato: {self.email_gerente or 'comercial@flexx.com.br'} | (11) 99999-9999")
            p.drawString(margin, 10, f"© {datetime.now().year} Flexx Propostas - v{self.app_version}")
            
            p.save()
            buffer.seek(0)
            pdf_bytes = buffer.getvalue()
            logger.info("✅ PDF completo gerado com sucesso.")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar PDF completo: {e}.")
            return None

    def enviar_proposta_por_email(
        self,
        destinatario: str,
        nome_cliente: str,
        link_proposta: str,
        valor_total: str,
        pdf_content: Optional[bytes] = None
    ) -> bool:
        """
        Envia a proposta por email para o cliente, com PDF anexo e cópia para o gerente.
        """
        assunto = f"Sua Proposta Flexx - {nome_cliente}"

        # Corpo HTML do email
        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                                <tr>
                                    <td style="padding: 30px; text-align: center;">
                                        <h2 style="color: #007bff; margin: 0 0 20px;">Proposta Comercial Flexx</h2>
                                        <p>Olá, {nome_cliente}!</p>
                                        <p>Sua proposta foi gerada com sucesso. Veja o resumo abaixo e o PDF em anexo para detalhes.</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 0 30px 20px;">
                                        <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Resumo + Valores</h3>
                                        <ul style="list-style-type: disc; padding-left: 20px;">
                                            <li><strong>Valor Total:</strong> {valor_total}</li>
                                            <li><strong>Data de Criação:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
                                            <li><strong>Prazo de Validade:</strong> 30 dias</li>
                                        </ul>
                                        <p>Para visualizar completa, clique no link ou abra o anexo PDF.</p>
                                        <a href="{link_proposta}" style="display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0;">
                                            Visualizar Proposta Online
                                        </a>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 0 30px 20px;">
                                        <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Instruções de Próximos Passos</h3>
                                        <ol style="padding-left: 20px;">
                                            <li>Revise o PDF anexo e confirme os serviços e valores.</li>
                                            <li>Aprove ou rejeite acessando o link ou respondendo este e-mail.</li>
                                            <li>Em caso de dúvidas, responda diretamente para nossa equipe.</li>
                                            <li>Contato: {self.email_gerente or 'comercial.flexx@gmail.com'} | (11) 99999-9999</li>
                                        </ol>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 30px 30px; text-align: center; background-color: #f8f9fa; border-top: 1px solid #ddd; border-radius: 0 0 8px 8px;">
                                        <img src="https://via.placeholder.com/200x60/007bff/ffffff?text=Logo+Flexx" alt="Logo Flexx" style="max-width: 200px; margin-bottom: 10px;">
                                        <p style="color: #666; font-size: 14px; margin: 0;">Equipe Flexx Propostas | {self.email_from_name} v{self.app_version}</p>
                                        <p style="color: #999; font-size: 12px; margin: 5px 0 0;">{self.base_url} | © {datetime.now().year}</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """

        # Se o PDF não foi fornecido, tenta gerar um simples
        if pdf_content is None:
            generated_pdf = self.gerar_pdf_proposta(nome_cliente, link_proposta, valor_total)
            if generated_pdf:
                pdf_content = generated_pdf
            else:
                logger.warning("⚠️ PDF não gerado; enviando email sem anexo.")

        # Monta mensagem com HTML e anexo PDF
        msg = MIMEMultipart('mixed')
        msg['Subject'] = assunto
        msg['From'] = f"{self.email_from_name} <{self.email_from}>"
        msg['To'] = destinatario
        msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

        # Anexa PDF, se disponível
        if pdf_content:
            pdf_attach = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attach.add_header(
                'Content-Disposition',
                'attachment',
                filename=f'proposta_flexx_{nome_cliente.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            msg.attach(pdf_attach)

        server = None
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout)
            server.starttls()
            server.login(self.email_user, self.email_password)

            # Envia para cliente
            server.send_message(msg)
            logger.info(f"✅ E-mail com PDF enviado para cliente: {destinatario}.")

            # Cópia para gerente (do .env)
            if self.notificar_gerente and self.email_gerente:
                # Cria uma nova mensagem para o gerente para evitar modificar o 'To' da mensagem original
                msg_gerente = MIMEMultipart('mixed')
                msg_gerente['Subject'] = f"[CÓPIA] {assunto}"
                msg_gerente['From'] = f"{self.email_from_name} <{self.email_from}>"
                msg_gerente['To'] = self.email_gerente
                msg_gerente.attach(MIMEText(corpo_html, 'html', 'utf-8'))

                if pdf_content:
                    pdf_attach_gerente = MIMEApplication(pdf_content, _subtype='pdf')
                    pdf_attach_gerente.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=f'proposta_flexx_{nome_cliente.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf'
                    )
                    msg_gerente.attach(pdf_attach_gerente)

                server.send_message(msg_gerente)
                logger.info(f"✅ Cópia enviada para gerente: {self.email_gerente}.")
            else:
                logger.info("Notificação gerente desativada ou email do gerente não configurado.")

            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Erro de autenticação SMTP. Verifique SMTP_USER/SMTP_PASSWORD (use App Password do Google).")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ Erro de conexão SMTP: {e}. Verifique rede/firewall.")
            return False
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"❌ SMTP desconectado: {e}.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Erro SMTP geral ao enviar proposta para {destinatario}: {e}.")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no envio de proposta para {destinatario}: {e}.")
            return False
        finally:
            if server:
                server.quit()

    def enviar_email_confirmacao(
        self,
        destinatario: str,
        nome_cliente: str
    ) -> bool:
        """
        Envia email de confirmação de aceitação da proposta.
        """
        assunto = f"Proposta Aceita - {nome_cliente}"

        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #27ae60;">Parabéns! 🎉</h2>
                    <p>Sua proposta foi <strong>ACEITA</strong> com sucesso!</p>
                    <div style="background-color: #d5f4e6; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
                        <p style="color: #27ae60; font-weight: bold;">✅ Status: ACEITA</p>
                        <p>Entraremos em contato em breve para os próximos passos.</p>
                    </div>
                    <p style="margin-top: 30px; font-size: 12px; color: #7f8c8d;">
                        Este é um email automático. Não responda diretamente.<br>
                        Para dúvidas, entre em contato conosco.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
                    <p style="font-size: 12px; color: #95a5a6;">
                        <strong>Flexx Proposta</strong><br>
                        Sistema de Gerenciamento de Propostas Comerciais<br>
                        © {datetime.now().year} - Todos os direitos reservados
                    </p>
                </div>
            </body>
        </html>
        """

        return self.enviar_email_simples(
            destinatario=destinatario,
            assunto=assunto,
            corpo=corpo_html,
            eh_html=True
        )

    def enviar_proposta_por_email_simples(self, proposta: Any) -> bool:
        """
        Versão simplificada para ser usada com background_tasks.
        Recebe um objeto 'proposta' (do banco de dados) e extrai os dados necessários.
        Usa o novo PDF completo.
        """
        try:
            link_proposta = f"{self.base_url}/proposta/{proposta.hash_id}"
            
            # Gera PDF completo
            pdf_content = self.gerar_pdf_completo(proposta)
            if not pdf_content:
                logger.warning("⚠️ PDF completo não gerado; usando PDF simples.")
                pdf_content = self.gerar_pdf_proposta(
                    proposta.razao_social,
                    link_proposta,
                    f"R$ {proposta.total:,.2f}" if proposta.total else "R$ 0,00"
                )
            
            return self.enviar_proposta_por_email(
                destinatario=proposta.email,
                nome_cliente=proposta.razao_social,
                link_proposta=link_proposta,
                valor_total=f"R$ {proposta.total:,.2f}" if proposta.total else "R$ 0,00",
                pdf_content=pdf_content
            )
        except Exception as e:
            logger.error(f"❌ Erro ao enviar proposta para {proposta.email} via enviar_proposta_por_email_simples: {e}.")
            return False

# Instância global do serviço de email
email_service = EmailService()