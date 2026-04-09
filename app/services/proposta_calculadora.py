from decimal import Decimal
import math


def arredondar_usuarios(usuarios: int) -> int:
    if usuarios <= 0:
        return 10
    return math.ceil(usuarios / 10) * 10


def calcular_desconto_por_percentual(subtotal: Decimal, percentual: Decimal) -> Decimal:
    if subtotal <= 0:
        return Decimal("0.00")
    return (subtotal * percentual) / Decimal("100")


def calcular_percentual_por_desconto(subtotal: Decimal, valor_desconto: Decimal) -> Decimal:
    if subtotal <= 0:
        return Decimal("0.00")
    return (valor_desconto / subtotal) * Decimal("100")


def calcular_total(subtotal: Decimal, desconto_valor: Decimal) -> Decimal:
    total = subtotal - desconto_valor
    if total < 0:
        return Decimal("0.00")
    return total