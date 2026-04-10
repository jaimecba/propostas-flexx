"""Script para popular tabelas de preços"""
import sys
import os

# Descobre a pasta raiz do projeto (pasta pai de 'scripts')
pasta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, pasta_raiz)

# Agora importa os módulos da pasta 'app'
from app.database import SessionLocal
from app.models import (
    PrecoFornecedor, 
    Markup, 
    TabelaPrecosServicosAdicionais, 
    TabelaPrecosTreinamentos,
    TabelaPrecosPlanos
)

def seed_precos():
    db = SessionLocal()
    
    try:
        # Limpar dados antigos
        db.query(PrecoFornecedor).delete()
        db.query(Markup).delete()
        db.query(TabelaPrecosServicosAdicionais).delete()
        db.query(TabelaPrecosTreinamentos).delete()
        db.query(TabelaPrecosPlanos).delete()
        
        # --- DADOS: PrecoFornecedor ---
        precos_fornecedor_data = [
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
        
        for plano, inicio, fim, unitario in precos_fornecedor_data:
            preco = PrecoFornecedor(
                plano=plano,
                faixa_inicio=inicio,
                faixa_fim=fim,
                preco_unitario=unitario
            )
            db.add(preco)
        
        # --- DADOS: Markup ---
        markups_data = [
            ('Basic', 290),
            ('Pro', 290),
            ('Ultimate', 290),
        ]
        
        for plano, markup in markups_data:
            m = Markup(plano=plano, markup_percentual=markup)
            db.add(m)

        # --- DADOS: TabelaPrecosPlanos ---
        tabela_precos_planos_data = [
            # Basic
            ('Basic', 0, 10, 99.90),
            ('Basic', 11, 50, 1.93),
            ('Basic', 51, 100, 1.78),
            ('Basic', 101, 200, 1.65),
            ('Basic', 201, 1000, 1.54),
            ('Basic', 1001, 999999, 1.30),
            # Pro
            ('Pro', 0, 10, 119.90),
            ('Pro', 11, 50, 2.47),
            ('Pro', 51, 100, 2.30),
            ('Pro', 101, 200, 2.13),
            ('Pro', 201, 1000, 1.98),
            ('Pro', 1001, 999999, 1.67),
            # Ultimate
            ('Ultimate', 0, 10, 139.90),
            ('Ultimate', 11, 50, 3.44),
            ('Ultimate', 51, 100, 3.18),
            ('Ultimate', 101, 200, 2.93),
            ('Ultimate', 201, 1000, 2.77),
            ('Ultimate', 1001, 999999, 2.31),
        ]

        for plano, inicio, fim, valor_mensal in tabela_precos_planos_data:
            preco_plano = TabelaPrecosPlanos(
                plano=plano,
                faixa_inicio=inicio,
                faixa_fim=fim,
                valor_mensal=valor_mensal
            )
            db.add(preco_plano)

        # --- DADOS: TabelaPrecosServicosAdicionais ---
        servicos_adicionais_data = [
            {"nome_servico": "Licença Facial", "plano": "Basic", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 23.90, "tipo_cobranca": "fixo"},
            {"nome_servico": "Licença Facial", "plano": "Pro", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 23.90, "tipo_cobranca": "fixo"},
            {"nome_servico": "Licença Facial", "plano": "Ultimate", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 23.90, "tipo_cobranca": "fixo"},
            {"nome_servico": "Gestão de Arquivos", "plano": "Basic", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.95, "tipo_cobranca": "faixa"},
            {"nome_servico": "Gestão de Arquivos", "plano": "Pro", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.95, "tipo_cobranca": "faixa"},
            {"nome_servico": "Gestão de Arquivos", "plano": "Ultimate", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.95, "tipo_cobranca": "faixa"},
            {"nome_servico": "Controle de Férias", "plano": "Basic", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.85, "tipo_cobranca": "faixa"},
            {"nome_servico": "Controle de Férias", "plano": "Pro", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.85, "tipo_cobranca": "faixa"},
            {"nome_servico": "Controle de Férias", "plano": "Ultimate", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.85, "tipo_cobranca": "faixa"},
            {"nome_servico": "Mais Requis Cálc Int", "plano": "Basic", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.45, "tipo_cobranca": "faixa"},
            {"nome_servico": "Mais Requis Cálc Int", "plano": "Pro", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.45, "tipo_cobranca": "faixa"},
            {"nome_servico": "Mais Requis Cálc Int", "plano": "Ultimate", "faixa_inicio": 0, "faixa_fim": 999999, "valor_unitario": 0.45, "tipo_cobranca": "faixa"},
        ]

        for item in servicos_adicionais_data:
            servico = TabelaPrecosServicosAdicionais(
                nome_servico=item["nome_servico"],
                plano=item["plano"],
                faixa_inicio=item["faixa_inicio"],
                faixa_fim=item["faixa_fim"],
                valor_unitario=item["valor_unitario"],
                tipo_cobranca=item["tipo_cobranca"]
            )
            db.add(servico)

        # --- DADOS: TabelaPrecosTreinamentos ---
        treinamentos_data = [
            {"tipo_treinamento": "Online", "valor": 0.00},
            {"tipo_treinamento": "Presencial", "valor": 350.00},
            {"tipo_treinamento": "Híbrido", "valor": 250.00},
        ]

        for item in treinamentos_data:
            treinamento = TabelaPrecosTreinamentos(
                tipo_treinamento=item["tipo_treinamento"],
                valor=item["valor"]
            )
            db.add(treinamento)
        
        db.commit()
        print("✅ Dados de preços inseridos com sucesso!")
        print(f"   - {len(precos_fornecedor_data)} preços do fornecedor")
        print(f"   - {len(markups_data)} markups")
        print(f"   - {len(tabela_precos_planos_data)} preços de planos")
        print(f"   - {len(servicos_adicionais_data)} serviços adicionais")
        print(f"   - {len(treinamentos_data)} treinamentos")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inserir dados: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_precos()