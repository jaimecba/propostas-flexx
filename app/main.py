print("\n" + "="*80)
print(">>> ESTE É O ARQUIVO main.py CORRETO - CARREGADO COM SUCESSO <<<")
print("="*80 + "\n", flush=True)

# ============================================================================
# FLEXX PROPOSTA V2 API - MAIN.PY (INTEGRADO COM PRECIFICAÇÃO)
# ============================================================================
# Data: 2026-04-06
# Versão: 2.1.0 (Com suporte a precificação dinâmica)
# ============================================================================

# ============================================================================
# IMPORTS - SEÇÃO ORIGINAL
# ============================================================================
import os
import re
import json
import requests
import hashlib
import logging
import uuid  # 🟢 ADICIONADO: Necessário para gerar o hash_id da proposta
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, Any, List, Dict

import redis.asyncio as aioredis
from dotenv import load_dotenv
from pydantic import BaseModel

from fastapi import FastAPI, Request, Depends, HTTPException, Form, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# 🟢 DESCOMENTADO: Fundamental para a API de preços funcionar no frontend!
from app.routes.preco import router as preco_router
from app.routers import pdf_routes
from app.routes.proposta import router as proposta_router
from app.routes.proposta_pdf import router as proposta_pdf_router
from app.routes.proposta_pdf_melhorado import router as proposta_pdf_router
from app.config import settings

from app.database import get_db  # 🟢 ADICIONADO: Necessário para o Depends(get_db)
from app.email_service import email_service
from app.models import Base, Proposta, Analytics, StatusProposta
from app.models import TabelaPrecosPlanos, TabelaPrecosServicosAdicionais, TabelaPrecosTreinamentos

from app.validators import (
    validar_cnpj,
    validar_email,
    validar_whatsapp,
    PLANOS_VALIDOS,
    TIPOS_TREINAMENTO,
    obter_setup_padrao,
    calcular_data_validade,
    validar_desconto,
    validar_usuarios,
    validar_treinamento,
    validar_combinacao_plano_usuarios,
    calcular_desconto,
    formatar_moeda,
)
from app.services.proposta_calculadora import (
    arredondar_usuarios,
    calcular_desconto_por_percentual,
    calcular_percentual_por_desconto,
    calcular_total,
)
from app.repositories.precos_repository import (
    buscar_valor_plano,
    buscar_valor_servico,
    buscar_valor_treinamento,
)

# ============================================================================
# CONFIGURAÇÃO INICIAL - SEÇÃO ORIGINAL
# ============================================================================
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não configurada.")
if not SECRET_KEY:
    logger.warning("SECRET_KEY não configurada. Usando valor temporário apenas para desenvolvimento.")
    SECRET_KEY = "dev-secret-key"

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS - PARSE DATABASE_URL
# ============================================================================
def parse_database_url(url):
    """Parse DATABASE_URL para extrair credenciais"""
    try:
        url_clean = url.replace("postgresql://", "").replace("postgres://", "")
        if "@" in url_clean:
            credentials, host_db = url_clean.split("@")
            user, password = credentials.split(":")
        else:
            user = "postgres"
            password = ""
            host_db = url_clean
        if "/" in host_db:
            host_port, database = host_db.split("/")
        else:
            host_port = host_db
            database = "postgres"
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "5432"
        return {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
    except Exception as e:
        logger.error(f"Erro ao fazer parse de DATABASE_URL: {e}")
        return {
            "host": "localhost",
            "port": "5432",
            "database": "proposal_db",
            "user": "postgres",
            "password": ""
        }

DB_CREDENTIALS = parse_database_url(DATABASE_URL)

def get_db_connection_pricing():
    """Conecta ao PostgreSQL para operações de precificação (psycopg2)."""
    try:
        conn = psycopg2.connect(
            host=DB_CREDENTIALS["host"],
            port=DB_CREDENTIALS["port"],
            database=DB_CREDENTIALS["database"],
            user=DB_CREDENTIALS["user"],
            password=DB_CREDENTIALS["password"]
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar ao BD para precificação: {e}")
        return None

# ============================================================================
# APLICAÇÃO - SEÇÃO ORIGINAL
# ============================================================================
app = FastAPI(
    title="Flexx Proposta V2 API",
    description="API para gerenciamento de propostas comerciais",
    version="2.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(proposta_router)
app.include_router(proposta_pdf_router)
app.include_router(pdf_routes.router)
from app.routes.preco import router as preco_router
app.include_router(preco_router)

# ============================================================================
# BANCO DE DADOS - SEÇÃO ORIGINAL
# ============================================================================
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# REDIS - SEÇÃO ORIGINAL
# ============================================================================
redis_client: Optional[aioredis.Redis] = None

# ============================================================================
# FUNÇÕES AUXILIARES - SEÇÃO ORIGINAL
# ============================================================================
def gerar_hash_id(cnpj: str, email: str) -> str:
    base = f"{cnpj}-{email}-{datetime.utcnow().isoformat()}-{SECRET_KEY}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

def gerar_link_proposta(hash_id: str) -> str:
    return f"{BASE_URL}/proposta/{hash_id}"

def gerar_mensagem_whatsapp(razao_social: str, link_proposta: str) -> str:
    return f"Olá {razao_social}! Sua proposta está pronta: {link_proposta}"

def gerar_link_whatsapp(whatsapp: str, mensagem: str) -> str:
    mensagem_encoded = mensagem.replace(" ", "%20")
    return f"https://wa.me/{whatsapp}?text={mensagem_encoded}"

def converter_para_decimal(valor, padrao: str = "0.00") -> Decimal:
    if not valor or str(valor).strip() == "":
        return Decimal(padrao)
    return Decimal(str(valor).replace(",", ".").strip())

def buscar_plano_valor(plano: str) -> Decimal:
    plano_normalizado = plano.strip()
    if plano_normalizado in PLANOS_VALIDOS:
        return PLANOS_VALIDOS[plano_normalizado]["valor_mensal"]
    for nome, cfg in PLANOS_VALIDOS.items():
        if nome.lower() == plano_normalizado.lower():
            return cfg["valor_mensal"]
    return Decimal("0.00")

def plano_valido_para_usuarios(plano: str, usuarios: int) -> bool:
    for nome, cfg in PLANOS_VALIDOS.items():
        if nome.lower() == plano.lower():
            return cfg["usuarios_min"] <= usuarios <= cfg["usuarios_max"]
    return False

# ============================================================================
# FUNÇÕES DE PRECIFICAÇÃO [NOVO]
# ============================================================================
def arredondar_pessoas(quant_pessoas: int) -> int:
    """Arredonda a quantidade de pessoas para a faixa mais próxima"""
    faixas = [1, 5, 10, 20, 50, 100, 200, 500, 1000]
    for faixa in faixas:
        if quant_pessoas <= faixa:
            return faixa
    return quant_pessoas

def obter_preco_plano_novo(plano: str, quant_pessoas: int) -> dict:
    """Obtém o preço do plano da tabela de precificação"""
    faixa = arredondar_pessoas(quant_pessoas)
    conn = get_db_connection_pricing()
    if not conn:
        return {
            "plano": plano,
            "faixa": faixa,
            "valor": None,
            "sucesso": False,
            "mensagem": "Erro ao conectar ao banco de dados."
        }
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT valor_mensal, faixa_inicio, faixa_fim 
        FROM tabela_precos_planos 
        WHERE LOWER(plano) = LOWER(%s) AND faixa_inicio <= %s 
        ORDER BY faixa_inicio DESC 
        LIMIT 1;
        """
        cur.execute(query, (plano, faixa))
        resultado = cur.fetchone()
        if resultado:
            return {
                "plano": plano,
                "faixa": faixa,
                "faixa_inicio": resultado['faixa_inicio'],
                "faixa_fim": resultado['faixa_fim'],
                "valor": float(resultado['valor_mensal']),
                "sucesso": True,
                "mensagem": "Preço encontrado com sucesso."
            }
        else:
            return {
                "plano": plano,
                "faixa": faixa,
                "valor": None,
                "sucesso": False,
                "mensagem": f"Nenhuma faixa encontrada para o plano '{plano}' e quantidade {quant_pessoas}."
            }
    except psycopg2.Error as e:
        logger.error(f"Erro ao consultar BD para preço: {e}")
        return {
            "plano": plano,
            "faixa": faixa,
            "valor": None,
            "sucesso": False,
            "mensagem": f"Erro ao consultar BD: {str(e)}"
        }
    finally:
        if conn:
            conn.close()

def obter_servicos_adicionais_novo(plano: str, quant_pessoas: int, servicos: List[str], quantidade_licenca_facial: int = 1) -> dict:
    """Obtém os preços dos serviços adicionais"""
    faixa = arredondar_pessoas(quant_pessoas)
    conn = get_db_connection_pricing()
    if not conn:
        return {
            "servicos": [],
            "total": 0,
            "sucesso": False,
            "mensagem": "Erro ao conectar ao banco de dados."
        }
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        servicos_resultado = []
        total = 0
        for servico in servicos:
            servico_norm = servico.lower()
            if servico_norm == 'licenca_facial':
                query = """
                SELECT valor_unitario, tipo_cobranca 
                FROM tabela_precos_servicos_adicionais 
                WHERE LOWER(nome_servico) = LOWER(%s) AND tipo_cobranca = 'fixo' 
                LIMIT 1;
                """
                cur.execute(query, (servico_norm,))
                resultado = cur.fetchone()
                if resultado:
                    valor_unitario = float(resultado['valor_unitario'])
                    valor_total = valor_unitario * quantidade_licenca_facial
                    servicos_resultado.append({
                        "nome": servico,
                        "tipo": "fixo",
                        "valor_unitario": valor_unitario,
                        "quantidade": quantidade_licenca_facial,
                        "valor_total": valor_total
                    })
                    total += valor_total
            else:
                query = """
                SELECT valor_unitario, tipo_cobranca 
                FROM tabela_precos_servicos_adicionais 
                WHERE LOWER(nome_servico) = LOWER(%s) AND tipo_cobranca = 'por_pessoa' 
                LIMIT 1;
                """
                cur.execute(query, (servico_norm,))
                resultado = cur.fetchone()
                if resultado:
                    valor_unitario = float(resultado['valor_unitario'])
                    valor_total = valor_unitario * faixa
                    servicos_resultado.append({
                        "nome": servico,
                        "tipo": resultado['tipo_cobranca'],
                        "valor_unitario": valor_unitario,
                        "quantidade": faixa,
                        "valor_total": valor_total
                    })
                    total += valor_total
        return {
            "servicos": servicos_resultado,
            "total": round(total, 2),
            "sucesso": True,
            "mensagem": "Serviços calculados com sucesso."
        }
    except psycopg2.Error as e:
        logger.error(f"Erro ao consultar BD para serviços: {e}")
        return {
            "servicos": [],
            "total": 0,
            "sucesso": False,
            "mensagem": f"Erro ao consultar BD: {str(e)}"
        }
    finally:
        if conn:
            conn.close()

# ============================================================================
# MODELOS PYDANTIC - PRECIFICAÇÃO [NOVO]
# ============================================================================
class PrecoRequest(BaseModel):
    """Modelo para requisição de preço."""
    plano: str
    quant_pessoas: int

class ServicoRequest(BaseModel):
    """Modelo para requisição de serviços adicionais."""
    plano: str
    quant_pessoas: int
    servicos: List[str]
    quantidade_licenca_facial: Optional[int] = 1

class PrecoResponse(BaseModel):
    """Modelo para resposta de preço."""
    plano: str
    quant_pessoas: int
    faixa_arredondada: int
    valor_mensal: float
    sucesso: bool
    mensagem: str

# ============================================================================
# STARTUP / SHUTDOWN - SEÇÃO ORIGINAL
# ============================================================================
@app.on_event("startup")
async def startup_event():
    global redis_client
    logger.info("Iniciando aplicação Flexx Proposal...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexão com o banco verificada com sucesso.")
    except Exception as e:
        logger.error(f"Falha na conexão com o banco: {e}")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao criar tabelas: {e}")
    try:
        redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        logger.info("Conexão com Redis verificada com sucesso.")
    except Exception as e:
        logger.warning(f"Redis indisponível: {e}")
        redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

# ============================================================================
# FUNÇÃO AUXILIAR - LIMPEZA DE PLACEHOLDERS [NOVO]
# ============================================================================
def limpar_placeholder(valor, nome_campo=None):
    """Remove placeholders do Swagger"""
    if valor is None:
        return None
    if isinstance(valor, list):
        cleaned_list = []
        for item in valor:
            cleaned_item = limpar_placeholder(item, nome_campo)
            if cleaned_item is not None:
                cleaned_list.append(cleaned_item)
        return cleaned_list if cleaned_list else None
    valor_str = str(valor).strip()
    if not valor_str or valor_str == "string" or (nome_campo and valor_str == nome_campo):
        return None
    return valor_str

# ============================================================================
# ROTA PARA BUSCAR CNPJ NA BRASILAPI (ADICIONADA/COMPLETADA)
# ============================================================================
@app.get("/api/cnpj/{cnpj}")
def buscar_cnpj_api(cnpj: str):
    """
    Busca dados do CNPJ na BrasilAPI
    Exemplo: /api/cnpj/04865114000193
    """
    print(f"DEBUG: Buscando CNPJ: {cnpj}")
    
    # Limpar o CNPJ (remover caracteres especiais, manter só números)
    cnpj_limpo = re.sub(r'\D', '', cnpj)
    
    print(f"DEBUG: CNPJ limpo: {cnpj_limpo}")
    
    # Verificar se tem 14 dígitos
    if len(cnpj_limpo) != 14:
        print(f"❌ CNPJ inválido: {len(cnpj_limpo)} dígitos")
        raise HTTPException(status_code=400, detail="CNPJ inválido. Deve conter 14 dígitos.")
    
    # URL da BrasilAPI
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    print(f"DEBUG: Chamando URL: {url}")
    
    try:
        # Fazer a requisição para a BrasilAPI
        response = requests.get(url, timeout=10)
        
        print(f"DEBUG: Status da resposta: {response.status_code}")
        
        # Se a resposta não for 200, significa que não encontrou
        if response.status_code == 404:
            print(f"❌ CNPJ não encontrado na BrasilAPI")
            raise HTTPException(status_code=404, detail="CNPJ não encontrado na Receita Federal.")
        
        # Se houver outro erro
        response.raise_for_status()
        
        # Retornar os dados em JSON
        dados = response.json()
        print(f"✅ Dados encontrados: {dados.get('nome_fantasia', 'N/A')}")
        return dados
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout ao buscar CNPJ")
        raise HTTPException(status_code=500, detail="Timeout ao buscar dados do CNPJ.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados do CNPJ: {str(e)}")

# ============================================================================
# ROTAS - SEÇÃO ORIGINAL (CORRIGIDA: Rota '/' única e com fallback)
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Rota raiz - retorna o formulário de propostas"""
    print("=" * 80)
    print("🔵 ACESSANDO ROTA RAIZ /")
    print("=" * 80)
    
    try:
        # Tentar carregar o arquivo index.html
        index_path = STATIC_DIR / "index.html"
        print(f"📂 Procurando arquivo em: {index_path}")
        print(f"📂 Arquivo existe? {index_path.exists()}")
        
        if index_path.exists():
            print(f"✅ Arquivo encontrado! Carregando...")
            with open(index_path, "r", encoding="utf-8") as f:
                conteudo = f.read()
                print(f"✅ Arquivo carregado com sucesso ({len(conteudo)} bytes)")
                return HTMLResponse(content=conteudo)
        else:
            print(f"⚠️ Arquivo index.html NÃO encontrado em {index_path}")
            print(f"📂 Usando fallback HTML")
    
    except FileNotFoundError as e:
        print(f"❌ ERRO FileNotFoundError: {str(e)}")
        import traceback
        traceback.print_exc()
    
    except Exception as e:
        print(f"❌ ERRO ao carregar index.html: {str(e)}")
        print(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    # 🔴 FALLBACK HTML (retorna se arquivo não existir ou houver erro)
    print("📄 Retornando fallback HTML")
    fallback_html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flexx Proposta</title>
    </head>
    <body>
        <h1>Bem-vindo ao Flexx Proposta V2</h1>
        <p>API para gerenciamento de propostas comerciais.</p>
        <p><a href="/docs">Documentação da API</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=fallback_html)

# ============================================================================
# ROTA PARA CRIAR PROPOSTA (OTIMIZADA COM ORM E CÁLCULOS CORRIGIDOS)
# ============================================================================
@app.post("/criar-proposta")
async def criar_proposta(
    cnpj: str = Form(...),
    razao_social: str = Form(...),
    nome_fantasia: Optional[str] = Form(None),
    email: str = Form(...),
    whatsapp: str = Form(...),
    plano: str = Form(...),
    usuarios: int = Form(...),
    servicos_adicionais: Optional[List[str]] = Form(None),
    qtd_licenca_facial: Optional[int] = Form(1),
    treinamento_tipo: Optional[str] = Form(None),
    treinamentoValor: Optional[str] = Form(None),
    setup: Optional[str] = Form(None),
    desconto: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # ✅ TESTE SIMPLES
    print(f"\n\nSERVICOS ADICIONAIS: {servicos_adicionais}\n\n", flush=True)
    
    # ✅ NOVO - Escrever em arquivo de log
    with open("debug_proposta.log", "a", encoding="utf-8") as f:
        f.write("\n" + "="*80 + "\n")
        f.write("ROTA /criar-proposta CHAMADA\n")
        f.write(f"Servicos Adicionais: {servicos_adicionais}\n")
        f.write(f"Tipo: {type(servicos_adicionais)}\n")
        f.write(f"Quantidade: {len(servicos_adicionais) if servicos_adicionais else 0}\n")
        if servicos_adicionais:
            for i, srv in enumerate(servicos_adicionais):
                f.write(f"   [{i}] {srv}\n")
        f.write("="*80 + "\n")
    
    try:
        # 1. Validar CNPJ e Email
        cnpj_valido, msg_cnpj = validar_cnpj(cnpj)
        if not cnpj_valido: raise HTTPException(status_code=400, detail=f"CNPJ inválido: {msg_cnpj}")
        
        email_valido, msg_email = validar_email(email)
        if not email_valido: raise HTTPException(status_code=400, detail=f"Email inválido: {msg_email}")
        
        # 2. Função auxiliar para converter "R$ 350,00" em Decimal(350.00)
        def parse_brl(valor_str):
            if not valor_str: return Decimal('0.00')
            limpo = str(valor_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
            try: return Decimal(limpo)
            except: return Decimal('0.00')

        val_setup = parse_brl(setup)
        val_treinamento = parse_brl(treinamentoValor)
        val_desconto = parse_brl(desconto)

        # 3. Calcular Faixa Flexx
        faixa_flexx = math.ceil(usuarios / 10) * 10 if usuarios > 0 else 10
        is_consultar_comercial = False
        if usuarios > 5000 or (plano.lower() == 'desktop' and usuarios > 1000):
            faixa_flexx = usuarios # Mantém o original para casos "Consultar Comercial"
            is_consultar_comercial = True

        # 4. Calcular Valor do Plano
        valor_mensal_plano = Decimal('0.00')
        
        if not is_consultar_comercial:
            # 🟢 CORREÇÃO 1: Valores FIXOS para até 10 usuários
            if faixa_flexx <= 10:
                if plano.lower() == 'basic':
                    valor_mensal_plano = Decimal('99.90')
                elif plano.lower() == 'pro':
                    valor_mensal_plano = Decimal('119.90')
                elif plano.lower() == 'ultimate':
                    valor_mensal_plano = Decimal('139.90')
                else:
                    valor_mensal_plano = Decimal('99.90')
            else:
                # Busca no banco
                registro_plano = db.query(TabelaPrecosPlanos).filter(
                    TabelaPrecosPlanos.plano.ilike(plano),
                    TabelaPrecosPlanos.faixa_inicio <= usuarios,
                    TabelaPrecosPlanos.faixa_fim >= usuarios,
                    TabelaPrecosPlanos.ativo == True
                ).first()
                
                if registro_plano:
                    preco_unitario = registro_plano.valor_mensal
                    # 🟢 CORREÇÃO 2: Multiplicar por 3.0 (300%) em vez de 2.9
                    valor_mensal_plano = Decimal(str(round(float(preco_unitario) * faixa_flexx * 3.0, 2)))

        # 5. Calcular Serviços Adicionais (VERSÃO CORRIGIDA - SALVA COMO JSON ESTRUTURADO) ✅ NOVO
        servicos_json = {}
        valor_servicos = Decimal('0.00')
        
        if servicos_adicionais and not is_consultar_comercial:
            servicos_db = db.query(TabelaPrecosServicosAdicionais).filter(
                TabelaPrecosServicosAdicionais.ativo == True
            ).all()
            
            for servico in servicos_adicionais:
                if servico == 'licenca_facial':
                    srv = next((s for s in servicos_db if s.nome_servico == 'licenca_facial'), None)
                    if srv:
                        qtd = qtd_licenca_facial or 1
                        preco_unit = Decimal(str(srv.valor_unitario))  # ✅ ALTERADO
                        valor_total_srv = preco_unit * Decimal(qtd)
                        valor_servicos += valor_total_srv
                        servicos_json['licenca_facial'] = {
                            'quantidade': qtd,
                            'preco_unitario': float(preco_unit),
                            'valor_total': float(valor_total_srv)
                        }
                
                elif servico == 'gestao_arquivos':
                    srv = next((s for s in servicos_db if s.nome_servico == 'gestao_arquivos'), None)
                    if srv:
                        preco_unit = Decimal(str(srv.valor_unitario))  # ✅ ALTERADO
                        valor_total_srv = preco_unit * Decimal(faixa_flexx)
                        valor_servicos += valor_total_srv
                        servicos_json['gestao_arquivos'] = {
                            'quantidade': faixa_flexx,
                            'preco_unitario': float(preco_unit),
                            'valor_total': float(valor_total_srv)
                        }
                
                elif servico == 'controle_ferias':
                    srv = next((s for s in servicos_db if s.nome_servico == 'controle_ferias'), None)
                    if srv:
                        preco_unit = Decimal(str(srv.valor_unitario))  # ✅ ALTERADO
                        valor_total_srv = preco_unit * Decimal(faixa_flexx)
                        valor_servicos += valor_total_srv
                        servicos_json['controle_ferias'] = {
                            'quantidade': faixa_flexx,
                            'preco_unitario': float(preco_unit),
                            'valor_total': float(valor_total_srv)
                        }
                
                elif servico == 'requis_calc_int':
                    srv = next((s for s in servicos_db if s.nome_servico == 'requis_calc_int'), None)
                    if srv:
                        preco_unit = Decimal(str(srv.valor_unitario))  # ✅ ALTERADO
                        valor_total_srv = preco_unit * Decimal(faixa_flexx)
                        valor_servicos += valor_total_srv
                        servicos_json['requis_calc_int'] = {
                            'quantidade': faixa_flexx,
                            'preco_unitario': float(preco_unit),
                            'valor_total': float(valor_total_srv)
                        }
        
        # Converter para JSON string para salvar no banco ✅ NOVO
        servicos_adicionais_json_str = json.dumps(servicos_json) if servicos_json else '{}'

                # DEBUG - Verificar o que foi criado
        print(f"\n\n{'='*80}", flush=True)
        print(f"SERVICOS JSON CRIADO:", flush=True)
        print(f"Tipo: {type(servicos_json)}", flush=True)
        print(f"Conteúdo: {servicos_json}", flush=True)
        print(f"JSON String: {servicos_adicionais_json_str}", flush=True)
        print(f"Valor Total Serviços: {valor_servicos}", flush=True)
        print(f"{'='*80}\n\n", flush=True)

        # 6. Totais Finais
        valor_mensal_total = valor_mensal_plano + valor_servicos
        total_avulsos = val_setup + val_treinamento
        total_geral = max(total_avulsos - val_desconto, Decimal('0.00'))

        # 7. Gerar hash único
        hash_id_gerado = str(uuid.uuid4())[:8]
        data_expiracao = datetime.utcnow() + timedelta(days=15)
        
        # 8. Salvar no Banco
        proposta = Proposta(
            hash_id=hash_id_gerado,
            data_validade=data_expiracao,
            cnpj=cnpj,
            razao_social=razao_social,
            email=email,
            telefone=whatsapp,
            whatsapp=whatsapp,
            plano=plano,
            usuarios=usuarios,
            usuarios_arredondados=faixa_flexx,
            valor_mensal=valor_mensal_total,
            setup_ajustado=val_setup,
            treinamento_tipo=treinamento_tipo or "Online",
            treinamento_valor=val_treinamento,
            servicos_adicionais=servicos_adicionais_json_str,  # ✅ ALTERADO - agora salva JSON
            desconto_valor=val_desconto,
            desconto_percentual=Decimal('0.00'),
            observacoes=observacoes or "",
            subtotal=total_avulsos,
            total=total_geral,
            status="PENDENTE",
            data_criacao=datetime.utcnow()
        )
        
        db.add(proposta)
        db.commit()
        db.refresh(proposta)
        
        print(f"✅ Proposta salva com sucesso! Total Mensal: R$ {valor_mensal_total} | Avulsos: R$ {total_geral}")
        
        return RedirectResponse(
        url=f"{settings.base_url}/proposta/{hash_id_gerado}",
        status_code=303
    )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ ERRO ao criar proposta: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar proposta: {str(e)}")

@app.get("/debug-proposta/{hash_id}")
async def debug_proposta(hash_id: str, db: Session = Depends(get_db)):
    print(f"\n🔴🔴🔴 DEBUG PROPOSTA CHAMADA - HASH: {hash_id}", flush=True)
    
    proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()
    
    if not proposta:
        return {"erro": "Proposta não encontrada"}
    
    print(f"✅ Proposta encontrada: {proposta.razao_social}", flush=True)
    print(f"Servicos Adicionais (RAW): {proposta.servicos_adicionais}", flush=True)
    
    return {
        "hash_id": hash_id,
        "cliente": proposta.razao_social,
        "servicos_adicionais_raw": proposta.servicos_adicionais,
        "tipo": str(type(proposta.servicos_adicionais))
    }

# ============================================================================
# ROTA PARA VISUALIZAR PROPOSTA (ATUALIZADA COM VARIÁVEIS DO TEMPLATE)
# ============================================================================
@app.get("/teste-print")
async def teste_print():
    print("🔴🔴🔴 TESTE DE PRINT FUNCIONANDO! 🔴🔴🔴", flush=True)
    return {"status": "ok"}

@app.get("/teste-simples/{hash_id}")
async def teste_simples(hash_id: str):
    """Rota de teste simples sem template."""
    print(f"\n🟢 TESTE SIMPLES CHAMADA - HASH: {hash_id}", flush=True)
    return {"hash_id": hash_id, "status": "ok"}

@app.get("/teste-proposta-view/{hash_id}")
async def teste_proposta_view(hash_id: str, db: Session = Depends(get_db)):
    """Rota de teste para debugar proposta-view."""
    
    print(f"\n🟡 TESTE PROPOSTA-VIEW CHAMADA - HASH: {hash_id}", flush=True)
    
    try:
        proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()
        print(f"✅ Proposta encontrada: {proposta.razao_social if proposta else 'NÃO ENCONTRADA'}", flush=True)
        
        if not proposta:
            return {"erro": "Proposta não encontrada"}
        
        # Testar JSON parsing
        servicos_adicionais_json = {}
        if proposta.servicos_adicionais:
            servicos_adicionais_json = json.loads(proposta.servicos_adicionais)
            print(f"✅ JSON parseado com sucesso", flush=True)
        
        return {
            "hash_id": hash_id,
            "cliente": proposta.razao_social,
            "servicos_adicionais": servicos_adicionais_json,
            "status": "ok"
        }
    
    except Exception as e:
        print(f"❌ ERRO: {type(e).__name__}: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return {"erro": str(e), "tipo": type(e).__name__}

@app.get("/proposta/{hash_id}", response_class=HTMLResponse)
async def visualizar_proposta(hash_id: str, request: Request, db: Session = Depends(get_db)):
    1/0
    """Rota para visualizar proposta em HTML com serviços adicionais."""
    
    print(f"\n🔵 ROTA VISUALIZAR PROPOSTA CHAMADA - HASH: {hash_id}", flush=True)
    
    try:
        proposta = db.query(Proposta).filter(Proposta.hash_id == hash_id).first()
        if not proposta:
            raise HTTPException(status_code=404, detail="Proposta não encontrada")

        visualizacao = Analytics(
            hash_id=hash_id,
            tipo_evento="visualizacao",
            data_evento=datetime.utcnow(),
        )
        db.add(visualizacao)
        db.commit()

        if proposta.is_expirada() and proposta.status == StatusProposta.PENDENTE.value:
            proposta.status = StatusProposta.EXPIRADA.value
            db.add(proposta)
            db.commit()
            db.refresh(proposta)

        link_proposta = gerar_link_proposta(proposta.hash_id, settings.base_url)
        mensagem_whatsapp = gerar_mensagem_whatsapp(proposta.razao_social, link_proposta)
        link_whatsapp = gerar_link_whatsapp(proposta.whatsapp or "", mensagem_whatsapp)

        # ✅ Converter JSON string para dicionário
        servicos_adicionais_json = {}
        valor_servicos_adicionais = "R$ 0,00"
        
        if proposta.servicos_adicionais:
            try:
                servicos_adicionais_json = json.loads(proposta.servicos_adicionais)
                print(f"✅ JSON parseado: {servicos_adicionais_json}", flush=True)
                
                # Calcular valor total dos serviços
                total_servicos = Decimal("0.00")
                for servico_key, servico_data in servicos_adicionais_json.items():
                    if isinstance(servico_data, dict) and "valor_total" in servico_data:
                        total_servicos += Decimal(str(servico_data["valor_total"]))
                
                valor_servicos_adicionais = formatar_moeda(total_servicos)
                print(f"✅ Valor Total: {valor_servicos_adicionais}", flush=True)
            except Exception as e:
                print(f"❌ Erro ao parsear JSON de serviços: {e}", flush=True)
                servicos_adicionais_json = {}

        context = {
            "request": request,
            "proposta": proposta,
            "hash_id": proposta.hash_id,
            "status": proposta.status,
            "cliente_nome": proposta.razao_social,
            "cliente_email": proposta.email,
            "cliente_telefone": proposta.telefone,
            "whatsapp": proposta.whatsapp,
            "plano": proposta.plano,
            "usuarios": proposta.usuarios,
            "usuarios_arredondados": proposta.usuarios_arredondados,
            "valor_mensal": formatar_moeda(proposta.valor_mensal),
            "setup": formatar_moeda(proposta.setup_ajustado or proposta.setup_padrao or Decimal("0.00")),
            "treinamento_tipo": proposta.treinamento_tipo,
            "treinamento_valor": formatar_moeda(proposta.treinamento_valor or Decimal("0.00")),
            "desconto_valor": formatar_moeda(proposta.desconto_valor or Decimal("0.00")),
            "subtotal": formatar_moeda(proposta.subtotal or Decimal("0.00")),
            "total": formatar_moeda(proposta.total or Decimal("0.00")),
            "observacoes": proposta.observacoes,
            "data_criacao": proposta.data_criacao,
            "data_validade": proposta.data_validade,
            "dias_para_expirar": proposta.dias_para_expirar(),
            "total_visualizacoes": proposta.total_visualizacoes(),
            "link_proposta": link_proposta,
            "mensagem_whatsapp": mensagem_whatsapp,
            "link_whatsapp": link_whatsapp,
            "datetime": datetime,
            "servicos_adicionais_json": servicos_adicionais_json,
            "valor_servicos_adicionais": valor_servicos_adicionais,
            "formatar_moeda": formatar_moeda,
        }

        print(f"✅ Context preparado com sucesso!", flush=True)
        print(f"\n✅ Context keys: {list(context.keys())}", flush=True)
        print(f"✅ formatar_moeda existe? {'formatar_moeda' in context}", flush=True)
        print(f"✅ servicos_adicionais_json: {context.get('servicos_adicionais_json')}", flush=True)
        print(f"✅ valor_servicos_adicionais: {context.get('valor_servicos_adicionais')}", flush=True)
        
        return templates.TemplateResponse("proposta.html", context)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ ERRO NA ROTA VISUALIZAR PROPOSTA:", flush=True)
        print(f"Tipo: {type(e).__name__}", flush=True)
        print(f"Mensagem: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        raise
# ============================================================================
# ENDPOINTS DE PRECIFICAÇÃO [NOVO]
# ============================================================================
@app.get("/api/preco_plano/{plano}/{quant_pessoas}")
def get_preco_plano(plano: str, quant_pessoas: int):
    """
    Endpoint para obter o preço de um plano.
    Exemplo de uso:
    GET /api/preco_plano/Basic/15
    """
    resultado = obter_preco_plano_novo(plano, quant_pessoas)
    resultado["quant_pessoas"] = quant_pessoas
    return resultado

@app.post("/api/calcular_preco")
def calcular_preco(request: PrecoRequest):
    """
    Endpoint POST para calcular preço (alternativa ao GET).
    """
    resultado = obter_preco_plano_novo(request.plano, request.quant_pessoas)
    resultado["quant_pessoas"] = request.quant_pessoas
    return resultado

@app.post("/api/calcular_servicos")
def calcular_servicos(request: ServicoRequest):
    """
    Endpoint para calcular serviços adicionais.
    """
    faixa = arredondar_pessoas(request.quant_pessoas)
    resultado = obter_servicos_adicionais_novo(
        request.plano, 
        request.quant_pessoas, 
        request.servicos, 
        request.quantidade_licenca_facial
    )
    resultado["plano"] = request.plano
    resultado["quant_pessoas"] = request.quant_pessoas
    resultado["faixa_arredondada"] = faixa
    return resultado

@app.post("/api/calcular_proposta_completa")
def calcular_proposta_completa(request: ServicoRequest):
    """
    Endpoint para calcular proposta completa (plano + serviços).
    """
    preco_plano_resultado = obter_preco_plano_novo(request.plano, request.quant_pessoas)
    servicos_resultado = obter_servicos_adicionais_novo(
        request.plano, 
        request.quant_pessoas, 
        request.servicos, 
        request.quantidade_licenca_facial
    )
    faixa = arredondar_pessoas(request.quant_pessoas)
    if preco_plano_resultado["sucesso"] and servicos_resultado["sucesso"]:
        total_proposta = preco_plano_resultado["valor"] + servicos_resultado["total"]
        return {
            "plano": request.plano,
            "quant_pessoas": request.quant_pessoas,
            "faixa_arredondada": faixa,
            "preco_plano": preco_plano_resultado["valor"],
            "servicos": servicos_resultado["servicos"],
            "total_servicos": servicos_resultado["total"],
            "total_proposta": round(total_proposta, 2),
            "sucesso": True,
            "mensagem": "Proposta calculada com sucesso."
        }
    else:
        return {
            "plano": request.plano,
            "quant_pessoas": request.quant_pessoas,
            "faixa_arredondada": faixa,
            "preco_plano": None,
            "servicos": [],
            "total_servicos": 0,
            "total_proposta": None,
            "sucesso": False,
            "mensagem": f"Erro: {preco_plano_resultado.get('mensagem', '')} | {servicos_resultado.get('mensagem', '')}"
        }

# ============================================================================
# HEALTH CHECK [MODIFICADO - ADICIONADO VERIFICAÇÃO DE PRECIFICAÇÃO]
# ============================================================================
@app.get("/health")
async def health_check():
    db_status = "desconectado"
    redis_status = "desconectado"
    pricing_status = "desconectado"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB falhou: {e}")
    try:
        if redis_client:
            await redis_client.ping()
            redis_status = "connected"
    except Exception as e:
        logger.error(f"Health check Redis falhou: {e}")
    try:
        conn = get_db_connection_pricing()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tabela_precos_planos")
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            pricing_status = "connected"
    except Exception as e:
        logger.error(f"Health check Pricing falhou: {e}")
    return {
        "status": "ok",
        "database": db_status,
        "redis": redis_status,
        "pricing": pricing_status
    }

# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)