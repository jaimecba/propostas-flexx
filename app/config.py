from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Banco de Dados
    database_url: str = "postgresql://usuario:flexx123@localhost:5432/flexx_proposta"
    database_echo: bool = False

    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Aplicação
    app_name: str = "Flexx Proposta"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "sua_chave_secreta"

    # URLs
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    redis_url: str = "redis://localhost:6379/0"

    # Notificações
    notificar_vendedor: bool = True
    notificar_gerente: bool = True
    email_gerente: str = "gerente@empresa.com"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()