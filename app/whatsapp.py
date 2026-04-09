# app/whatsapp.py
"""
Integração com WhatsApp para compartilhamento de propostas
"""

import re
from typing import Tuple
from urllib.parse import quote

# ============================================================================
# FUNÇÕES DE WHATSAPP
# ============================================================================

def extrair_numeros_telefone(telefone: str) -> str:
    """
    Extrai apenas os números do telefone.
    
    Args:
        telefone: Telefone formatado (ex: "(67) 99999-9999")
    
    Returns:
        String com apenas números (ex: "6799999999")
    
    Exemplo:
        >>> extrair_numeros_telefone("(67) 99999-9999")
        "6799999999"
    """
    return re.sub(r'\D', '', telefone)

def formatar_whatsapp_internacional(telefone: str, codigo_pais: str = "55") -> str:
    """
    Formata o telefone para o padrão internacional do WhatsApp.
    
    Args:
        telefone: Telefone (com ou sem formatação)
        codigo_pais: Código do país (padrão: 55 para Brasil)
    
    Returns:
        String formatada para WhatsApp (ex: "5567999999999")
    
    Exemplo:
        >>> formatar_whatsapp_internacional("(67) 99999-9999")
        "5567999999999"
    """
    numeros = extrair_numeros_telefone(telefone)
    
    # Se já tem código do país, retorna como está
    if numeros.startswith(codigo_pais):
        return numeros
    
    # Senão, adiciona o código do país
    return f"{codigo_pais}{numeros}"

def gerar_link_whatsapp(telefone: str, mensagem: str, codigo_pais: str = "55") -> str:
    """
    Gera o link para compartilhar via WhatsApp.
    
    Args:
        telefone: Telefone do cliente
        mensagem: Mensagem a enviar
        codigo_pais: Código do país (padrão: 55 para Brasil)
    
    Returns:
        String com o link do WhatsApp
    
    Exemplo:
        >>> gerar_link_whatsapp("(67) 99999-9999", "Olá!")
        "https://wa.me/5567999999999?text=Olá!"
    """
    
    # Formatar telefone para padrão internacional
    telefone_internacional = formatar_whatsapp_internacional(telefone, codigo_pais)
    
    # URL encode da mensagem
    mensagem_encoded = quote(mensagem)
    
    return f"https://wa.me/{telefone_internacional}?text={mensagem_encoded}"

def gerar_mensagem_proposta(
    cliente_nome: str,
    link_proposta: str,
    plano: str,
    usuarios: int,
    valor_total: float,
    vendedor_nome: str = "Flexx"
) -> str:
    """
    Gera a mensagem padrão para compartilhar proposta via WhatsApp.
    
    Args:
        cliente_nome: Nome do cliente
        link_proposta: Link da proposta
        plano: Nome do plano
        usuarios: Número de usuários
        valor_total: Valor total da proposta
        vendedor_nome: Nome do vendedor
    
    Returns:
        String com a mensagem formatada
    """
    
    mensagem = f"""Olá {cliente_nome}! 👋

Segue sua proposta personalizada:

📋 *Detalhes da Proposta:*
• Plano: {plano}
• Usuários: {usuarios}
• Valor Total: R$ {valor_total:,.2f}

🔗 *Acesse sua proposta:*
{link_proposta}

Dúvidas? Responda esta mensagem!

Atenciosamente,
{vendedor_nome}
Flexx Proposta"""
    
    return mensagem

def gerar_mensagem_email(
    cliente_nome: str,
    link_proposta: str,
    plano: str,
    usuarios: int,
    valor_total: float,
    vendedor_nome: str = "Flexx"
) -> str:
    """
    Gera a mensagem padrão para enviar por email.
    
    Args:
        cliente_nome: Nome do cliente
        link_proposta: Link da proposta
        plano: Nome do plano
        usuarios: Número de usuários
        valor_total: Valor total da proposta
        vendedor_nome: Nome do vendedor
    
    Returns:
        String com a mensagem formatada
    """
    
    mensagem = f"""Olá {cliente_nome},

Segue sua proposta personalizada:

Detalhes da Proposta:
• Plano: {plano}
• Usuários: {usuarios}
• Valor Total: R$ {valor_total:,.2f}

Acesse sua proposta:
{link_proposta}

Dúvidas? Responda este email!

Atenciosamente,
{vendedor_nome}
Flexx Proposta"""
    
    return mensagem

# ============================================================================
# VALIDADORES DE WHATSAPP
# ============================================================================

def validar_whatsapp_para_compartilhamento(whatsapp: str) -> Tuple[bool, str]:
    """
    Valida se o WhatsApp é válido para compartilhamento.
    
    Args:
        whatsapp: WhatsApp a validar
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if not whatsapp:
        return False, "WhatsApp não foi fornecido."
    
    # Remover formatação
    numeros = extrair_numeros_telefone(whatsapp)
    
    # Verificar se tem 11 dígitos (2 código + 9 dígito + 8 números)
    if len(numeros) < 10 or len(numeros) > 13:
        return False, "WhatsApp inválido. Deve ter entre 10 e 13 dígitos."
    
    # Verificar se tem o 9 (celular)
    if len(numeros) == 11 and numeros[2] != '9':
        return False, "WhatsApp deve ser um celular (com 9 dígito)."
    
    return True, ""

# ============================================================================
# FUNÇÕES DE COMPARTILHAMENTO
# ============================================================================

def preparar_compartilhamento_whatsapp(
    cliente_nome: str,
    whatsapp: str,
    link_proposta: str,
    plano: str,
    usuarios: int,
    valor_total: float,
    vendedor_nome: str = "Flexx"
) -> dict:
    """
    Prepara todos os dados para compartilhamento via WhatsApp.
    
    Args:
        cliente_nome: Nome do cliente
        whatsapp: WhatsApp do cliente
        link_proposta: Link da proposta
        plano: Nome do plano
        usuarios: Número de usuários
        valor_total: Valor total
        vendedor_nome: Nome do vendedor
    
    Returns:
        Dicionário com dados para compartilhamento
    """
    
    # Validar WhatsApp
    valido, erro = validar_whatsapp_para_compartilhamento(whatsapp)
    
    if not valido:
        return {
            'sucesso': False,
            'erro': erro,
            'link': None
        }
    
    # Gerar mensagem
    mensagem = gerar_mensagem_proposta(
        cliente_nome,
        link_proposta,
        plano,
        usuarios,
        valor_total,
        vendedor_nome
    )
    
    # Gerar link
    link_whatsapp = gerar_link_whatsapp(whatsapp, mensagem)
    
    return {
        'sucesso': True,
        'erro': None,
        'link': link_whatsapp,
        'mensagem': mensagem,
        'whatsapp': formatar_whatsapp_internacional(whatsapp)
    }