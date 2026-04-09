# app/validators.py
import re
from decimal import Decimal
from typing import Tuple, Dict, Any
from datetime import datetime, timedelta
import logging  # NOVO: Para logs de debug

logger = logging.getLogger(__name__)

# ============================================================================
# VALIDADORES DE CNPJ
# ============================================================================
def validar_cnpj(cnpj: str) -> Tuple[bool, str]:
    """
    Valida o CNPJ usando o algoritmo correto de dígito verificador.
    Args:
        cnpj: String com o CNPJ (com ou sem formatação)
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    Exemplo:
        >>> validar_cnpj("11.222.333/0001-81")
        (True, "")
    """
    # Limpeza robusta: remove não-dígitos e espaços
    cnpj_limpo = re.sub(r'\D', '', cnpj.strip())
    
    # Log para debug (veja no console)
    logger.info(f"Validando CNPJ limpo: {cnpj_limpo}")
    
    # Verificar tamanho
    if len(cnpj_limpo) != 14:
        logger.warning(f"Tamanho inválido: {len(cnpj_limpo)} dígitos")
        return False, "CNPJ deve ter 14 dígitos."
    
    # Verificar se todos os dígitos são iguais (CNPJ inválido)
    if cnpj_limpo == cnpj_limpo[0] * 14:
        logger.warning("Todos dígitos iguais")
        return False, "CNPJ inválido (todos os dígitos iguais)."
    
    # ✅ ALGORITMO CORRETO - Primeiro dígito verificador (DV1)
    soma = 0
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(12):
        soma += int(cnpj_limpo[i]) * peso[i]
    
    resto = soma % 11
    primeiro_digito = 0 if resto < 2 else 11 - resto
    
    logger.info(f"DV1 calculado: {primeiro_digito}, real: {cnpj_limpo[12]}")
    
    if int(cnpj_limpo[12]) != primeiro_digito:
        return False, "CNPJ inválido. Dígito verificador 1 incorreto."
    
    # ✅ ALGORITMO CORRETO - Segundo dígito verificador (DV2)
    soma = 0
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i in range(13):
        soma += int(cnpj_limpo[i]) * peso[i]
    
    resto = soma % 11
    segundo_digito = 0 if resto < 2 else 11 - resto
    
    logger.info(f"DV2 calculado: {segundo_digito}, real: {cnpj_limpo[13]}")
    
    if int(cnpj_limpo[13]) != segundo_digito:
        return False, "CNPJ inválido. Dígito verificador 2 incorreto."
    
    logger.info("CNPJ validado com sucesso")
    return True, ""

# ============================================================================
# VALIDADORES DE EMAIL
# ============================================================================

def validar_email(email: str) -> Tuple[bool, str]:
    """
    Valida o formato do email.
    
    Args:
        email: String com o email
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(padrao, email):
        return False, "Email inválido. Verifique o formato."
    
    return True, ""

# ============================================================================
# VALIDADORES DE TELEFONE
# ============================================================================

def validar_telefone(telefone: str) -> Tuple[bool, str]:
    """
    Valida o formato do telefone.
    Aceita formatos: (XX) XXXX-XXXX ou XXXXXXXXXX
    
    Args:
        telefone: String com o telefone
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    
    Exemplo:
        >>> validar_telefone("(67) 3333-3333")
        (True, "")
        >>> validar_telefone("6733333333")
        (True, "")
    """
    # Remover formatação
    numeros = re.sub(r'\D', '', telefone)
    
    # Verificar se tem 10 dígitos (2 de DDD + 8 dígitos do telefone)
    if len(numeros) != 10:
        return False, "Telefone inválido. Use (XX) XXXX-XXXX ou XXXXXXXXXX."
    
    return True, ""


def validar_whatsapp(whatsapp: str) -> Tuple[bool, str]:
    """
    Valida o formato do WhatsApp.
    Aceita formatos com 10 ou 11 dígitos (celulares ou fixos).
    
    Args:
        whatsapp: String com o WhatsApp
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    # Remover formatação (deixa só os números)
    numeros = re.sub(r'\D', '', whatsapp)
    
    # Verificar se tem 10 ou 11 dígitos
    if len(numeros) not in [10, 11]:
        return False, "WhatsApp inválido. O número deve ter 10 ou 11 dígitos com o DDD."
    
    # Removida a obrigatoriedade do dígito 9 para aceitar WhatsApp Business (fixo)
    
    return True, ""
    
    # Verificar se o 3º dígito é 9 (celular)
    if numeros[2] != '9':
        return False, "WhatsApp inválido. Deve ser um celular (9º dígito = 9)."
    
    return True, ""


def formatar_telefone(telefone: str) -> str:
    """
    Formata o telefone para (XX) XXXX-XXXX
    
    Args:
        telefone: String com o telefone
    
    Returns:
        String formatada
    
    Exemplo:
        >>> formatar_telefone("6733333333")
        "(67) 3333-3333"
        >>> formatar_telefone("67999999999")
        "(67) 99999-9999"
    """
    numeros = re.sub(r'\D', '', telefone)
    
    if len(numeros) == 10:
        return f"({numeros[0:2]}) {numeros[2:6]}-{numeros[6:10]}"
    elif len(numeros) == 11:
        return f"({numeros[0:2]}) {numeros[2:7]}-{numeros[7:11]}"
    
    return telefone

# ============================================================================
# VALIDADORES DE PLANO
# ============================================================================

PLANOS_VALIDOS = {
    'Basic': {
        'usuarios_min': 1,
        'usuarios_max': 10,
        'valor_mensal': Decimal('50.00'),
        'descricao': 'Acesso básico, 1 admin'
    },
    'PRO': {
        'usuarios_min': 11,
        'usuarios_max': 50,
        'valor_mensal': Decimal('100.00'),
        'descricao': 'Acesso avançado, 3 admins, relatórios'
    },
    'Ultimate': {
        'usuarios_min': 51,
        'usuarios_max': 999,
        'valor_mensal': Decimal('200.00'),
        'descricao': 'Acesso total, suporte 24/7, API'
    }
}

def validar_plano(plano: str) -> Tuple[bool, str]:
    """
    Valida se o plano é válido.
    
    Args:
        plano: String com o nome do plano
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if plano not in PLANOS_VALIDOS:
        planos = ', '.join(PLANOS_VALIDOS.keys())
        return False, f"Plano inválido. Deve ser um de: {planos}"
    
    return True, ""

def obter_plano_por_usuarios(usuarios: int) -> str:
    """
    Retorna o plano recomendado baseado no número de usuários.
    
    Args:
        usuarios: Número de usuários
    
    Returns:
        String com o nome do plano
    """
    
    for plano, config in PLANOS_VALIDOS.items():
        if config['usuarios_min'] <= usuarios <= config['usuarios_max']:
            return plano
    
    return 'Ultimate'

# ============================================================================
# VALIDADORES DE USUÁRIOS
# ============================================================================

def validar_usuarios(usuarios: int) -> Tuple[bool, str]:
    """
    Valida o número de usuários.
    
    Args:
        usuarios: Número de usuários
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if not isinstance(usuarios, int):
        return False, "Número de usuários deve ser um inteiro."
    
    if usuarios < 1 or usuarios > 999:
        return False, "Número de usuários deve estar entre 1 e 999."
    
    return True, ""

def arredondar_usuarios(usuarios: int) -> int:
    """
    Arredonda o número de usuários para a dezena superior.
    
    Regra:
    - Se é múltiplo de 10: mantém
    - Se não é: arredonda para próxima dezena
    
    Args:
        usuarios: Número de usuários
    
    Returns:
        Número arredondado
    
    Exemplo:
        >>> arredondar_usuarios(51)
        60
    """
    
    if usuarios % 10 == 0:
        return usuarios
    
    return ((usuarios // 10) + 1) * 10

# ============================================================================
# VALIDADORES DE TREINAMENTO
# ============================================================================

TIPOS_TREINAMENTO = {
    'Online': {
        'setup_padrao': Decimal('0.00'),
        'descricao': 'Sem custo de deslocamento'
    },
    'Presencial': {
        'setup_padrao': Decimal('350.00'),
        'descricao': 'Deslocamento + facilitador'
    },
    'Híbrido': {
        'setup_padrao': Decimal('250.00'),
        'descricao': 'Misto (online + presencial)'
    }
}

def validar_treinamento(treinamento: str) -> Tuple[bool, str]:
    """
    Valida o tipo de treinamento.
    
    Args:
        treinamento: String com o tipo de treinamento
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if treinamento not in TIPOS_TREINAMENTO:
        tipos = ', '.join(TIPOS_TREINAMENTO.keys())
        return False, f"Tipo de treinamento inválido. Deve ser um de: {tipos}"
    
    return True, ""

def obter_setup_padrao(treinamento: str) -> Decimal:
    """
    Retorna o valor padrão de setup para o tipo de treinamento.
    
    Args:
        treinamento: String com o tipo de treinamento
    
    Returns:
        Decimal com o valor padrão
    """
    
    if treinamento in TIPOS_TREINAMENTO:
        return TIPOS_TREINAMENTO[treinamento]['setup_padrao']
    
    return Decimal('0.00')

# ============================================================================
# VALIDADORES DE VALORES MONETÁRIOS
# ============================================================================

def validar_valor_monetario(valor: float) -> Tuple[bool, str]:
    """
    Valida se um valor monetário é válido.
    
    Args:
        valor: Valor a validar
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    try:
        valor_decimal = Decimal(str(valor))
        
        if valor_decimal < 0:
            return False, "Valor não pode ser negativo."
        
        if valor_decimal > Decimal('999999.99'):
            return False, "Valor muito alto."
        
        return True, ""
    
    except:
        return False, "Valor inválido."

def formatar_moeda(valor: float) -> str:
    """
    Formata um valor em moeda brasileira.
    
    Args:
        valor: Valor a formatar
    
    Returns:
        String formatada (ex: R$ 1.234,56)
    
    Exemplo:
        >>> formatar_moeda(1234.56)
        "R$ 1.234,56"
    """
    
    try:
        valor_decimal = Decimal(str(valor))
        valor_formatado = f"{valor_decimal:,.2f}"
        valor_formatado = valor_formatado.replace(',', 'X')
        valor_formatado = valor_formatado.replace('.', ',')
        valor_formatado = valor_formatado.replace('X', '.')
        return f"R$ {valor_formatado}"
    
    except:
        return f"R$ {valor:.2f}"

def desformatar_moeda(valor_str: str) -> Decimal:
    """
    Converte uma string formatada em moeda para Decimal.
    
    Args:
        valor_str: String formatada (ex: "R$ 1.234,56")
    
    Returns:
        Decimal com o valor
    
    Exemplo:
        >>> desformatar_moeda("R$ 1.234,56")
        Decimal('1234.56')
    """
    
    valor_limpo = valor_str.replace('R$', '').strip()
    valor_limpo = valor_limpo.replace('.', '')
    valor_limpo = valor_limpo.replace(',', '.')
    
    try:
        return Decimal(valor_limpo)
    except:
        return Decimal('0.00')

# ============================================================================
# VALIDADORES DE DESCONTO
# ============================================================================

def validar_desconto(desconto_percentual: float = None, desconto_valor: float = None) -> Tuple[bool, str]:
    """
    Valida o desconto (percentual ou valor).
    
    Args:
        desconto_percentual: Desconto em percentual (0-100)
        desconto_valor: Desconto em valor (R$)
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if desconto_percentual is not None:
        if desconto_percentual < 0 or desconto_percentual > 100:
            return False, "Desconto percentual deve estar entre 0 e 100%."
        
        if desconto_percentual > 50:
            return False, "Desconto acima de 50% requer aprovação do gerente."
    
    if desconto_valor is not None:
        if desconto_valor < 0:
            return False, "Desconto em valor não pode ser negativo."
    
    return True, ""

def calcular_desconto(valor_total: Decimal, desconto_percentual: float = None, desconto_valor: Decimal = None) -> Decimal:
    """
    Calcula o valor do desconto.
    
    Args:
        valor_total: Valor total da proposta
        desconto_percentual: Desconto em percentual
        desconto_valor: Desconto em valor
    
    Returns:
        Decimal com o valor do desconto
    """
    
    if desconto_percentual is not None:
        return valor_total * Decimal(str(desconto_percentual)) / Decimal('100')
    
    if desconto_valor is not None:
        return Decimal(str(desconto_valor))
    
    return Decimal('0.00')

# ============================================================================
# VALIDADORES DE DATAS
# ============================================================================

def validar_data_inicio_servico(data_str: str) -> Tuple[bool, str]:
    """
    Valida a data de início do serviço.
    
    Args:
        data_str: String com a data (formato: YYYY-MM-DD)
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        
        if data.date() < datetime.utcnow().date():
            return False, "Data de início não pode ser no passado."
        
        return True, ""
    
    except ValueError:
        return False, "Data inválida. Use o formato YYYY-MM-DD."

def calcular_data_validade(dias: int = 30) -> datetime:
    """
    Calcula a data de validade da proposta.
    
    Args:
        dias: Número de dias de validade (padrão: 30)
    
    Returns:
        datetime com a data de validade
    """
    
    return datetime.utcnow() + timedelta(days=dias)

# ============================================================================
# VALIDAÇÕES CRUZADAS
# ============================================================================

def validar_combinacao_plano_usuarios(plano: str, usuarios: int) -> Tuple[bool, str]:
    """
    Valida a combinação de plano e número de usuários.
    
    Args:
        plano: String com o nome do plano
        usuarios: Número de usuários
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    
    if plano not in PLANOS_VALIDOS:
        return False, "Plano inválido."
    
    config = PLANOS_VALIDOS[plano]
    
    if usuarios < config['usuarios_min']:
        return False, f"Plano {plano} requer no mínimo {config['usuarios_min']} usuários."
    
    if usuarios > config['usuarios_max']:
        return False, f"Plano {plano} suporta no máximo {config['usuarios_max']} usuários."
    
    return True, ""

# ============================================================================
# FUNÇÃO PRINCIPAL DE VALIDAÇÃO
# ============================================================================

def validar_proposta_completa(dados: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    Valida todos os dados da proposta.
    
    Args:
        dados: Dicionário com os dados da proposta
    
    Returns:
        Tuple[bool, Dict]: (é_válido, dicionário_de_erros)
    """
    
    erros = {}
    
    # Validar CNPJ
    if 'cnpj' in dados:
        valido, msg = validar_cnpj(dados['cnpj'])
        if not valido:
            erros['cnpj'] = msg
    
    # Validar Email
    if 'email' in dados:
        valido, msg = validar_email(dados['email'])
        if not valido:
            erros['email'] = msg
    
    # Validar Telefone
    if 'telefone' in dados and dados['telefone']:
        valido, msg = validar_telefone(dados['telefone'])
        if not valido:
            erros['telefone'] = msg
    
    # Validar WhatsApp
    if 'whatsapp' in dados and dados['whatsapp']:
        valido, msg = validar_whatsapp(dados['whatsapp'])
        if not valido:
            erros['whatsapp'] = msg
    
    # Validar Plano
    if 'plano' in dados:
        valido, msg = validar_plano(dados['plano'])
        if not valido:
            erros['plano'] = msg
    
    # Validar Usuários
    if 'usuarios' in dados:
        valido, msg = validar_usuarios(dados['usuarios'])
        if not valido:
            erros['usuarios'] = msg
    
    # Validar Combinação Plano + Usuários
    if 'plano' in dados and 'usuarios' in dados:
        valido, msg = validar_combinacao_plano_usuarios(dados['plano'], dados['usuarios'])
        if not valido:
            erros['combinacao'] = msg
    
    # Validar Treinamento
    if 'treinamento_tipo' in dados and dados['treinamento_tipo']:
        valido, msg = validar_treinamento(dados['treinamento_tipo'])
        if not valido:
            erros['treinamento_tipo'] = msg
    
    # Validar Desconto
    if 'desconto_percentual' in dados or 'desconto_valor' in dados:
        valido, msg = validar_desconto(
            dados.get('desconto_percentual'),
            dados.get('desconto_valor')
        )
        if not valido:
            erros['desconto'] = msg
    
    return len(erros) == 0, erros