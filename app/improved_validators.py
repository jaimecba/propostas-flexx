# app/improved_validators.py

import re
from typing import Tuple

# ============================================================================
# VALIDAÇÃO DE TELEFONE - VERSÃO MELHORADA
# ============================================================================

def limpar_telefone(telefone: str) -> str:
    """Remove todos os caracteres não numéricos"""
    return re.sub(r'\D', '', telefone)


def validar_telefone_flexivel(telefone: str) -> Tuple[bool, str]:
    """
    Valida telefone em múltiplos formatos:
    - (XX) XXXX-XXXX (10 dígitos)
    - (XX) XXXXX-XXXX (11 dígitos)
    - XXXXXXXXXX (10 dígitos)
    - XXXXXXXXXXX (11 dígitos)
    """
    numero_limpo = limpar_telefone(telefone)
    tamanho = len(numero_limpo)

    if not numero_limpo.isdigit():
        return False, "O telefone deve conter apenas dígitos."

    if tamanho == 10:
        return True, "Telefone válido (10 dígitos)."
    elif tamanho == 11:
        if numero_limpo[2] == '9':
            return True, "Telefone válido (11 dígitos - celular)."
        else:
            return False, "Telefone de 11 dígitos inválido (o 9º dígito deve ser '9' para celulares)."
    else:
        return False, f"Telefone inválido. Deve ter 10 ou 11 dígitos, mas possui {tamanho}."


def formatar_telefone(telefone: str) -> str:
    """
    Formata telefone para (XX) XXXX-XXXX ou (XX) XXXXX-XXXX
    """
    numero_limpo = limpar_telefone(telefone)
    tamanho = len(numero_limpo)

    if tamanho == 10:
        return f"({numero_limpo[0:2]}) {numero_limpo[2:6]}-{numero_limpo[6:10]}"
    elif tamanho == 11:
        return f"({numero_limpo[0:2]}) {numero_limpo[2:7]}-{numero_limpo[7:11]}"
    else:
        return numero_limpo


def validar_whatsapp(telefone: str) -> Tuple[bool, str]:
    """
    Valida se é um número de celular válido para WhatsApp
    Deve ter 11 dígitos e o 9º dígito deve ser '9'
    """
    numero_limpo = limpar_telefone(telefone)
    tamanho = len(numero_limpo)

    if tamanho != 11:
        return False, f"Número de WhatsApp inválido. Deve ter 11 dígitos, mas possui {tamanho}."
    
    if numero_limpo[2] != '9':
        return False, "Número de WhatsApp inválido. O 9º dígito (depois do DDD) deve ser '9'."
    
    return True, "Número de WhatsApp válido."


def formatar_whatsapp(telefone: str) -> str:
    """
    Formata para (XX) 9XXXX-XXXX
    """
    valido, _ = validar_whatsapp(telefone)
    if not valido:
        return limpar_telefone(telefone)

    numero_limpo = limpar_telefone(telefone)
    return f"({numero_limpo[0:2]}) {numero_limpo[2:7]}-{numero_limpo[7:11]}"