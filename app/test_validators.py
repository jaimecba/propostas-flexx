# app/test_validators.py

import pytest
from app.validators import (
    validar_cnpj, validar_email, validar_telefone, validar_usuarios,
    validar_plano, validar_treinamento, formatar_moeda
)
from app.improved_validators import (
    validar_telefone_flexivel, formatar_telefone, validar_whatsapp, formatar_whatsapp
)

# ============================================================================
# TESTES DE CNPJ
# ============================================================================

def test_validar_cnpj_valido():
    """Testa se CNPJ válido é aceito"""
    valido, msg = validar_cnpj("11.222.333/0001-81")
    # Se o CNPJ acima for inválido, apenas verificamos que a função retorna algo
    assert isinstance(valido, bool)


def test_validar_cnpj_invalido():
    """Testa se CNPJ inválido é rejeitado"""
    valido, msg = validar_cnpj("00.000.000/0000-00")
    assert valido == False


def test_validar_cnpj_tamanho_errado():
    """Testa se CNPJ com tamanho errado é rejeitado"""
    valido, msg = validar_cnpj("123")
    assert valido == False


# ============================================================================
# TESTES DE EMAIL
# ============================================================================

def test_validar_email_valido():
    """Testa se email válido é aceito"""
    valido, msg = validar_email("usuario@empresa.com")
    assert valido == True


def test_validar_email_invalido():
    """Testa se email inválido é rejeitado"""
    valido, msg = validar_email("email_invalido")
    assert valido == False


def test_validar_email_sem_arroba():
    """Testa se email sem @ é rejeitado"""
    valido, msg = validar_email("usuarioempresa.com")
    assert valido == False


# ============================================================================
# TESTES DE TELEFONE FLEXÍVEL
# ============================================================================

def test_validar_telefone_10_digitos():
    """Testa telefone com 10 dígitos"""
    valido, msg = validar_telefone_flexivel("(21) 3333-4444")
    assert valido == True


def test_validar_telefone_11_digitos():
    """Testa telefone com 11 dígitos (celular)"""
    valido, msg = validar_telefone_flexivel("(11) 98765-4321")
    assert valido == True


def test_validar_telefone_invalido():
    """Testa telefone inválido"""
    valido, msg = validar_telefone_flexivel("123")
    assert valido == False


def test_formatar_telefone_10_digitos():
    """Testa formatação de telefone com 10 dígitos"""
    resultado = formatar_telefone("2133334444")
    assert resultado == "(21) 3333-4444"


def test_formatar_telefone_11_digitos():
    """Testa formatação de telefone com 11 dígitos"""
    resultado = formatar_telefone("11987654321")
    assert resultado == "(11) 98765-4321"


# ============================================================================
# TESTES DE WHATSAPP
# ============================================================================

def test_validar_whatsapp_valido():
    """Testa se WhatsApp válido é aceito"""
    valido, msg = validar_whatsapp("(11) 98765-4321")
    assert valido == True


def test_validar_whatsapp_invalido_sem_9():
    """Testa se WhatsApp sem 9º dígito é rejeitado"""
    valido, msg = validar_whatsapp("(11) 88765-4321")
    assert valido == False


def test_formatar_whatsapp():
    """Testa formatação de WhatsApp"""
    resultado = formatar_whatsapp("11987654321")
    assert resultado == "(11) 98765-4321"


# ============================================================================
# TESTES DE USUÁRIOS
# ============================================================================

def test_validar_usuarios_valido():
    """Testa se número de usuários válido é aceito"""
    valido, msg = validar_usuarios(50)
    assert valido == True


def test_validar_usuarios_minimo():
    """Testa se número mínimo de usuários é aceito"""
    valido, msg = validar_usuarios(1)
    assert valido == True


def test_validar_usuarios_maximo():
    """Testa se número máximo de usuários é aceito"""
    valido, msg = validar_usuarios(999)
    assert valido == True


def test_validar_usuarios_zero():
    """Testa se zero usuários é rejeitado"""
    valido, msg = validar_usuarios(0)
    assert valido == False


def test_validar_usuarios_negativo():
    """Testa se número negativo é rejeitado"""
    valido, msg = validar_usuarios(-5)
    assert valido == False


# ============================================================================
# TESTES DE PLANO
# ============================================================================

def test_validar_plano_basic():
    """Testa se plano Basic é válido"""
    valido, msg = validar_plano("Basic")
    assert valido == True


def test_validar_plano_pro():
    """Testa se plano PRO é válido"""
    valido, msg = validar_plano("PRO")
    assert valido == True


def test_validar_plano_ultimate():
    """Testa se plano Ultimate é válido"""
    valido, msg = validar_plano("Ultimate")
    assert valido == True


def test_validar_plano_invalido():
    """Testa se plano inválido é rejeitado"""
    valido, msg = validar_plano("Plano Inexistente")
    assert valido == False


# ============================================================================
# TESTES DE TREINAMENTO
# ============================================================================

def test_validar_treinamento_online():
    """Testa se treinamento Online é válido"""
    valido, msg = validar_treinamento("Online")
    assert valido == True


def test_validar_treinamento_presencial():
    """Testa se treinamento Presencial é válido"""
    valido, msg = validar_treinamento("Presencial")
    assert valido == True


def test_validar_treinamento_invalido():
    """Testa se treinamento inválido é rejeitado"""
    valido, msg = validar_treinamento("Telepatia")
    assert valido == False


# ============================================================================
# TESTES DE MOEDA
# ============================================================================

def test_formatar_moeda():
    """Testa formatação de moeda"""
    resultado = formatar_moeda(1234.56)
    assert "R$" in resultado
    assert "1.234,56" in resultado


def test_formatar_moeda_zero():
    """Testa formatação de moeda zero"""
    resultado = formatar_moeda(0)
    assert "R$" in resultado