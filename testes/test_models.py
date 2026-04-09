from datetime import datetime, timedelta
from app.models import Proposta, StatusProposta

print("🔍 Testando modelos de dados...")

# Simular uma proposta (sem salvar no banco ainda)
proposta_teste = Proposta(
    hash_id="abc12345",
    cliente_nome="João Silva",
    cliente_email="joao@empresa.com",
    cliente_telefone="11999999999",
    plano="PRO",
    usuarios=50,
    valor_mensal=500.00,
    setup=1000.00,
    treinamento_tipo="presencial",
    treinamento_valor=2000.00,
    desconto=100.00,
    observacoes="Cliente VIP, dar prioridade",
    status=StatusProposta.PENDENTE,
    data_validade=datetime.utcnow() + timedelta(days=10)  # ← ADICIONE ESTA LINHA
)

print(f"✅ Proposta criada: {proposta_teste.cliente_nome}")
print(f"   Plano: {proposta_teste.plano}")
print(f"   Usuários: {proposta_teste.usuarios}")
print(f"   Desconto: R$ {proposta_teste.desconto}")
print(f"   Observações: {proposta_teste.observacoes}")
print(f"   Data de Validade: {proposta_teste.data_validade.strftime('%d/%m/%Y')}")

# Testar métodos
print(f"\n📊 Testando métodos:")
print(f"   Valor Total: R$ {proposta_teste.valor_total():.2f}")
print(f"   Está expirada? {proposta_teste.is_expirada()}")
print(f"   Total de visualizações: {proposta_teste.total_visualizacoes()}")

print("\n✅ TESTE 2 PASSOU! Modelos estão funcionando!")