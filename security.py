import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Valida o cabeçalho X-API-Key contra a variável de ambiente SOPH_GATEWAY_API_KEY.
    Utiliza secrets.compare_digest para prevenir ataques de tempo (timing attacks).
    """
    expected_key = os.getenv("SOPH_GATEWAY_API_KEY")
    
    # Se o servidor não possuir a chave configurada no ambiente, rejeita por segurança
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A chave de API do servidor não está configurada no ambiente."
        )
        
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente."
        )
        
    return api_key