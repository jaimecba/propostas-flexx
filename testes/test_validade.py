from datetime import datetime, timedelta
from app.models import Proposta, StatusProposta

print("🔍 Testando cálculo de data de validade (10 dias)...")

# Criar proposta com data_validade inicializada
proposta = Proposta(
    hash_id="test123",
    cliente_nome="Teste",
    cliente_email="teste@email.com",
    plano="Basic",
    usuarios=10,
    valor_mensal=100.00,
    status=StatusProposta.PENDENTE,
    data_validade=datetime.utcnow() + timedelta(days=10)
)

# Data de hoje
hoje = datetime.utcnow()
validade = proposta.data_validade

# Calcular diferença
dias_diferenca = (validade - hoje).days

print(f"📅 Data de hoje: {hoje.strftime('%d/%m/%Y')}")
print(f"📅 Data de validade: {validade.strftime('%d/%m/%Y')}")
print(f"📊 Diferença: {dias_diferenca} dias")

# Validar se está entre 9 e 10 dias (permite margem de horas)
if 9 <= dias_diferenca <= 10:
    print("✅ TESTE 3 PASSOU! Data de validade está correta (aproximadamente 10 dias)!")
else:
    print(f"❌ ERRO: Esperava 9-10 dias, mas tem {dias_diferenca}")