import hashlib
import secrets
import re
import logging
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, Any
from urllib.parse import quote

# Configuração de logging para este módulo
logger = logging.getLogger(__name__)

def gerar_link_proposta(hash_id: str, base_url: str) -> str:
    """
    Gera o link completo para a página de visualização da proposta.

    Args:
        hash_id (str): O ID único da proposta.
        base_url (str): A URL base da aplicação (ex: "http://localhost:8000").

    Returns:
        str: O link completo da proposta.

    Exemplo:
        >>> gerar_link_proposta("abc123def456", "http://meuapp.com")
        'http://meuapp.com/proposta/abc123def456'
    """
    if not hash_id or not base_url:
        logger.warning("gerar_link_proposta recebeu hash_id ou base_url vazios.")
        return ""
    return f"{base_url}/proposta/{hash_id}"

def gerar_mensagem_whatsapp(cliente_nome: str, link_proposta: str) -> str:
    """
    Gera a mensagem de texto para ser enviada via WhatsApp.

    Args:
        cliente_nome (str): O nome do cliente ou razão social.
        link_proposta (str): O link completo da proposta.

    Returns:
        str: A mensagem formatada para o WhatsApp.

    Exemplo:
        >>> gerar_mensagem_whatsapp("Empresa Teste", "http://link.com/proposta/123")
        'Olá Empresa Teste! Confira sua proposta comercial: http://link.com/proposta/123'
    """
    if not cliente_nome or not link_proposta:
        logger.warning("gerar_mensagem_whatsapp recebeu nome ou link vazios.")
        return "Confira sua proposta comercial."
    return f"Olá {cliente_nome}! Confira sua proposta comercial: {link_proposta}"

def gerar_link_whatsapp(whatsapp_numero: str, mensagem: str) -> str:
    """
    Gera o link para iniciar uma conversa no WhatsApp com uma mensagem pré-definida.

    Args:
        whatsapp_numero (str): O número de telefone do WhatsApp (com ou sem DDI/DDD).
        mensagem (str): A mensagem a ser pré-preenchida.

    Returns:
        str: O link 'wa.me' para o WhatsApp.

    Exemplo:
        >>> gerar_link_whatsapp("5511987654321", "Olá!")
        'https://wa.me/5511987654321?text=Ol%C3%A1%21'
    """
    if not whatsapp_numero or not mensagem:
        logger.warning("gerar_link_whatsapp recebeu número ou mensagem vazios.")
        return ""
    
    # Limpa o número de telefone, removendo caracteres não numéricos
    whatsapp_limpo = re.sub(r'\D', '', whatsapp_numero)
    
    # Adiciona DDI do Brasil se não houver
    if len(whatsapp_limpo) == 11 and not whatsapp_limpo.startswith("55"):
        whatsapp_limpo = "55" + whatsapp_limpo
    
    # Codifica a mensagem para URL
    mensagem_encoded = quote(mensagem)
    
    return f"https://wa.me/{whatsapp_limpo}?text={mensagem_encoded}"

def gerar_hash_id(tamanho: int = 16) -> str:
    """
    Gera um ID único usando um hash SHA256.

    Args:
        tamanho (int): O número de caracteres do hash a ser retornado.

    Returns:
        str: Uma string hexadecimal representando o hash.

    Exemplo:
        >>> len(gerar_hash_id(10))
        10
    """
    if not isinstance(tamanho, int) or tamanho <= 0:
        logger.error(f"gerar_hash_id recebeu tamanho inválido: {tamanho}. Usando 16.")
        tamanho = 16
    
    # Usa secrets para gerar bytes aleatórios e hashlib para garantir o tamanho
    random_bytes = secrets.token_bytes(32)
    return hashlib.sha256(random_bytes).hexdigest()[:tamanho]

def calcular_data_validade(dias: int = 30) -> datetime:
    """
    Calcula a data de validade a partir da data atual mais um número de dias.

    Args:
        dias (int): O número de dias para adicionar à data atual.

    Returns:
        datetime: A data e hora de validade.

    Exemplo:
        >>> from datetime import date
        >>> calcular_data_validade(7).date() == (datetime.utcnow() + timedelta(days=7)).date()
        True
    """
    if not isinstance(dias, int) or dias < 0:
        logger.warning(f"calcular_data_validade recebeu dias inválidos: {dias}. Usando 30.")
        dias = 30
    return datetime.utcnow() + timedelta(days=dias)

def dias_para_expirar(data_validade: datetime) -> int:
    """
    Calcula o número de dias restantes para a proposta expirar.

    Args:
        data_validade (datetime): A data e hora de validade da proposta.

    Returns:
        int: O número de dias restantes. Retorna 0 ou negativo se já expirou.

    Exemplo:
        >>> from datetime import timedelta
        >>> dias_para_expirar(datetime.utcnow() + timedelta(days=5))
        5
    """
    if not isinstance(data_validade, datetime):
        logger.error(f"dias_para_expirar recebeu data_validade inválida: {data_validade}.")
        return -999
    
    diferenca = data_validade - datetime.utcnow()
    return diferenca.days

def esta_expirada(data_validade: datetime) -> bool:
    """
    Verifica se a proposta já expirou.

    Args:
        data_validade (datetime): A data e hora de validade da proposta.

    Returns:
        bool: True se a proposta expirou, False caso contrário.

    Exemplo:
        >>> from datetime import timedelta
        >>> esta_expirada(datetime.utcnow() + timedelta(days=1))
        False
    """
    if not isinstance(data_validade, datetime):
        logger.error(f"esta_expirada recebeu data_validade inválida: {data_validade}.")
        return True
    return datetime.utcnow() > data_validade

def calcular_subtotal(valor_mensal: Decimal, setup: Decimal, treinamento: Decimal) -> Decimal:
    """
    Calcula o subtotal da proposta somando valor mensal, setup e treinamento.

    Args:
        valor_mensal (Decimal): O valor mensal do plano.
        setup (Decimal): O valor do setup inicial.
        treinamento (Decimal): O valor do treinamento.

    Returns:
        Decimal: O subtotal calculado.

    Exemplo:
        >>> calcular_subtotal(Decimal('100.00'), Decimal('50.00'), Decimal('20.00'))
        Decimal('170.00')
    """
    try:
        return valor_mensal + setup + treinamento
    except InvalidOperation as e:
        logger.error(f"Erro ao calcular subtotal: {e}")
        return Decimal('0.00')

def calcular_total(subtotal: Decimal, desconto: Decimal) -> Decimal:
    """
    Calcula o valor total da proposta subtraindo o desconto do subtotal.

    Args:
        subtotal (Decimal): O subtotal da proposta.
        desconto (Decimal): O valor do desconto a ser aplicado.

    Returns:
        Decimal: O valor total final.

    Exemplo:
        >>> calcular_total(Decimal('170.00'), Decimal('20.00'))
        Decimal('150.00')
    """
    try:
        return subtotal - desconto
    except InvalidOperation as e:
        logger.error(f"Erro ao calcular total: {e}")
        return Decimal('0.00')

def limpar_string(texto: Optional[str]) -> str:
    """
    Remove espaços extras do início e fim de uma string.

    Args:
        texto (Optional[str]): A string a ser limpa.

    Returns:
        str: A string limpa ou uma string vazia se o input for None.

    Exemplo:
        >>> limpar_string("  Olá Mundo  ")
        'Olá Mundo'
    """
    return str(texto).strip() if texto is not None else ""

def truncar_string(texto: Optional[str], tamanho: int) -> str:
    """
    Trunca uma string para um tamanho máximo, adicionando "..." se for truncada.

    Args:
        texto (Optional[str]): A string a ser truncada.
        tamanho (int): O tamanho máximo desejado para a string.

    Returns:
        str: A string truncada.

    Exemplo:
        >>> truncar_string("Isso é um texto longo", 10)
        'Isso é...'
    """
    if not isinstance(tamanho, int) or tamanho <= 0:
        logger.error(f"truncar_string recebeu tamanho inválido: {tamanho}. Usando 10.")
        tamanho = 10
    
    texto_limpo = limpar_string(texto)
    if len(texto_limpo) > tamanho:
        return texto_limpo[:tamanho-3] + "..."
    return texto_limpo

def extrair_numeros_telefone(telefone: Optional[str]) -> str:
    """
    Extrai apenas os dígitos numéricos de uma string de telefone.

    Args:
        telefone (Optional[str]): A string de telefone.

    Returns:
        str: Uma string contendo apenas os dígitos numéricos.

    Exemplo:
        >>> extrair_numeros_telefone("(11) 98765-4321")
        '11987654321'
    """
    if telefone is None:
        return ""
    return re.sub(r'\D', '', telefone)

def formatar_moeda(valor: Any) -> str:
    """
    Formata um valor numérico para o formato de moeda brasileira (R$).

    Args:
        valor (Any): O valor a ser formatado. Pode ser Decimal, float, int ou str.

    Returns:
        str: O valor formatado como "R$ X.XXX,XX".

    Exemplo:
        >>> formatar_moeda(Decimal('1234.56'))
        'R$ 1.234,56'
        >>> formatar_moeda(123.4)
        'R$ 123,40'
    """
    try:
        if valor is None:
            valor_decimal = Decimal('0.00')
        elif isinstance(valor, str):
            valor_decimal = Decimal(valor.replace('.', '').replace(',', '.'))
        else:
            valor_decimal = Decimal(str(valor))
        
        # Formata para duas casas decimais
        return f"R$ {valor_decimal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except InvalidOperation:
        logger.error(f"Erro de conversão ao formatar moeda para o valor: {valor}")
        return "R$ 0,00"

def desformatar_moeda(valor_str: str) -> Decimal:
    """
    Converte uma string formatada como moeda brasileira para Decimal.

    Args:
        valor_str (str): A string formatada como moeda.

    Returns:
        Decimal: O valor numérico em formato Decimal.

    Exemplo:
        >>> desformatar_moeda('R$ 1.234,56')
        Decimal('1234.56')
    """
    if not isinstance(valor_str, str):
        logger.error(f"desformatar_moeda recebeu tipo inválido: {type(valor_str)}.")
        return Decimal('0.00')
        
    # Remove "R$", espaços e pontos de milhar, depois troca vírgula por ponto decimal
    limpo = valor_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return Decimal(limpo)
    except InvalidOperation as e:
        logger.error(f"Erro ao desformatar moeda para o valor: '{valor_str}'. Erro: {e}")
        raise ValueError(f"Não foi possível converter '{valor_str}' para Decimal.") from e

def gerar_mensagem_email(cliente_nome: str, link_proposta: str) -> str:
    """
    Gera o corpo da mensagem de e-mail para o cliente.

    Args:
        cliente_nome (str): O nome do cliente ou razão social.
        link_proposta (str): O link completo da proposta.

    Returns:
        str: O corpo da mensagem de e-mail.

    Exemplo:
        >>> gerar_mensagem_email("Cliente Exemplo", "http://link.com/proposta/xyz")
        'Prezado(a) Cliente Exemplo,...'
    """
    if not cliente_nome or not link_proposta:
        logger.warning("gerar_mensagem_email recebeu nome ou link vazios.")
        return "Prezado(a) Cliente,\n\nSegue sua proposta comercial.\n\nAtenciosamente,\nEquipe Flexx"
        
    return (
        f"Prezado(a) {cliente_nome},\n\n"
        f"Segue a sua proposta comercial: {link_proposta}\n\n"
        f"Agradecemos o seu interesse em nossos serviços.\n\n"
        f"Atenciosamente,\n"
        f"Equipe Flexx"
    )