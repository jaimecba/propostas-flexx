"""Script para popular tabelas de preços"""
import sys
import os

# Descobre a pasta raiz do projeto (pasta pai de 'scripts')
pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, pasta_raiz)

# Agora importa os módulos da pasta 'app'
from app.database import SessionLocal
from app.models import PrecoFornecedor, Markup

def seed_precos():
    db = SessionLocal()
    
    # Limpar dados antigos (opcional)
    db.query(PrecoFornecedor).delete()
    db.query(Markup).delete()
    
    # Dados do fornecedor
    precos_fornecedor = [
        # BASIC
        ('Basic', 0, 10, 18.91),
        ('Basic', 11, 50, 1.93),
        ('Basic', 51, 100, 1.78),
        ('Basic', 101, 200, 1.65),
        ('Basic', 201, 1000, 1.54),
        ('Basic', 1001, 999999, 1.30),
        # PRO
        ('Pro', 0, 10, 24.72),
        ('Pro', 11, 50, 2.47),
        ('Pro', 51, 100, 2.30),
        ('Pro', 101, 200, 2.13),
        ('Pro', 201, 1000, 1.98),
        ('Pro', 1001, 999999, 1.67),
        # ULTIMATE
        ('Ultimate', 0, 10, 34.13),
        ('Ultimate', 11, 50, 3.44),
        ('Ultimate', 51, 100, 3.18),
        ('Ultimate', 101, 200, 2.93),
        ('Ultimate', 201, 1000, 2.77),
        ('Ultimate', 1001, 999999, 2.31),
    ]
    
    for plano, inicio, fim, unitario in precos_fornecedor:
        preco = PrecoFornecedor(
            plano=plano,
            faixa_inicio=inicio,
            faixa_fim=fim,
            preco_unitario=unitario
        )
        db.add(preco)
    
    # Dados de markup
    markups = [
        ('Basic', 290),
        ('Pro', 290),
        ('Ultimate', 290),
    ]
    
    for plano, markup in markups:
        m = Markup(plano=plano, markup_percentual=markup)
        db.add(m)
    
    db.commit()
    print("✅ Dados de preços inseridos com sucesso!")
    print(f"   - {len(precos_fornecedor)} preços do fornecedor")
    print(f"   - {len(markups)} markups")
    db.close()

if __name__ == "__main__":
    seed_precos()