from decimal import Decimal

from app.services.proposta_calculadora import (
    arredondar_usuarios,
    calcular_desconto_por_percentual,
    calcular_percentual_por_desconto,
    calcular_total,
)
from app.services.precos_repository import (
    buscar_valor_plano,
    buscar_valor_servico,
    buscar_valor_treinamento,
)


def calcular_proposta(
    db,
    plano: str,
    usuarios: int,
    treinamento_tipo: str | None = None,
    setup_padrao: Decimal | None = None,
    setup_ajustado: Decimal | None = None,
    desconto_valor: Decimal | None = None,
    desconto_percentual: Decimal | None = None,
    licenca_facial_quantidade: int = 0,
    servicos_adicionais: list[str] | None = None,
):
    usuarios_arredondados = arredondar_usuarios(usuarios)

    valor_plano = buscar_valor_plano(db, plano, usuarios_arredondados)

    total_adicionais = Decimal("0.00")
    servicos_adicionais = servicos_adicionais or []

    for servico in servicos_adicionais:
        if servico == "Licença Facial":
            valor_unitario = buscar_valor_servico(db, servico, plano, usuarios_arredondados)
            total_adicionais += Decimal(licenca_facial_quantidade) * valor_unitario

        elif servico in ["Gestão de Arquivos", "Controle de Férias", "Mais Requis Cálc Int"]:
            valor_unitario = buscar_valor_servico(db, servico, plano, usuarios_arredondados)
            total_adicionais += Decimal(usuarios_arredondados) * valor_unitario

    valor_treinamento = Decimal("0.00")
    if treinamento_tipo:
        valor_treinamento = buscar_valor_treinamento(db, treinamento_tipo)

    valor_setup = setup_ajustado if setup_ajustado is not None else (setup_padrao or Decimal("0.00"))

    subtotal = valor_plano + total_adicionais + valor_treinamento + valor_setup

    desconto_valor_final = Decimal("0.00")
    desconto_percentual_final = None

    if desconto_valor is not None and desconto_valor > 0:
        desconto_valor_final = desconto_valor
        desconto_percentual_final = calcular_percentual_por_desconto(subtotal, desconto_valor_final)

    elif desconto_percentual is not None and desconto_percentual > 0:
        desconto_percentual_final = desconto_percentual
        desconto_valor_final = calcular_desconto_por_percentual(subtotal, desconto_percentual_final)

    total = calcular_total(subtotal, desconto_valor_final)

    return {
        "usuarios_arredondados": usuarios_arredondados,
        "valor_plano": valor_plano,
        "total_adicionais": total_adicionais,
        "valor_treinamento": valor_treinamento,
        "valor_setup": valor_setup,
        "subtotal": subtotal,
        "desconto_valor": desconto_valor_final,
        "desconto_percentual": desconto_percentual_final,
        "total": total,
    }