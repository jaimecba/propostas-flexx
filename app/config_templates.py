# app/config_templates.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Criar um ambiente Jinja2 customizado com cache desabilitado
def get_jinja_environment():
    """Cria um ambiente Jinja2 com configurações otimizadas"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(['html', 'xml']),
        cache_size=0  # ← DESABILITA CACHE
    )
    return env

# Instância global
jinja_env = get_jinja_environment()