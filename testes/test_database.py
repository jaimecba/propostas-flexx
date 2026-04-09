# test_database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

from app.models import Base, Proposta, Usuario, Analytics, ConfiguracaoEmail

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("🔍 Testando conexão com PostgreSQL...")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("✅ Conexão com PostgreSQL: OK!")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    exit(1)

print("📊 Criando tabelas no banco...")

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")
except Exception as e:
    print(f"❌ Erro ao criar tabelas: {e}")
    exit(1)

print("\n✅ TESTE 1 PASSOU! Banco de dados está funcionando!")