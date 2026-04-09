# app/auth.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel

# Modelo para credenciais HTTP
class HTTPAuthCredentials(BaseModel):
    scheme: str
    credentials: str

# ============================================================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================================================

# Chave secreta para assinar tokens (MUDE ISSO EM PRODUÇÃO!)
SECRET_KEY = "sua-chave-secreta-super-segura-aqui-mude-em-producao"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de segurança HTTP Bearer
security = HTTPBearer()

# ============================================================================
# FUNÇÕES DE CRIPTOGRAFIA
# ============================================================================

def hash_password(password: str) -> str:
    """Criptografa uma senha"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se uma senha corresponde ao hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# FUNÇÕES DE TOKEN JWT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verifica e decodifica um token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# DEPENDÊNCIA PARA PROTEGER ROTAS
# ============================================================================

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """Extrai e valida o usuário do token JWT"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload


# ============================================================================
# FUNÇÃO DE LOGIN (EXEMPLO)
# ============================================================================

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Autentica um usuário (EXEMPLO SIMPLES)
    Em produção, você buscaria no banco de dados
    """
    # Exemplo: usuário padrão para testes
    if username == "admin" and password == "admin123":
        return {"sub": "admin", "email": "admin@flexx.com"}
    return None