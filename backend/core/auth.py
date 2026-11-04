import logging
from functools import lru_cache
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.config import settings
from db.database import get_db

bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def jwks_client(url: str):
    return PyJWKClient(url, timeout=10)


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> str:
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail='Sign in required', headers={'WWW-Authenticate': 'Bearer'})
    if not settings.NEON_AUTH_BASE_URL or not settings.NEON_AUTH_JWKS_URL:
        raise HTTPException(status_code=503, detail='Authentication is not configured')
    parsed = urlsplit(settings.NEON_AUTH_BASE_URL)
    issuer = f'{parsed.scheme}://{parsed.netloc}'
    try:
        key = jwks_client(settings.NEON_AUTH_JWKS_URL).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(credentials.credentials, key.key, algorithms=['EdDSA'], issuer=issuer, leeway=5,
                            options={'require': ['exp', 'iss', 'sub'], 'verify_aud': False})
        if not isinstance(claims['sub'], str) or not claims['sub']:
            raise jwt.InvalidTokenError('Missing user ID')
        user_id = claims['sub']
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(status_code=503, detail='Authentication service unavailable')
    except jwt.PyJWTError as error:
        logging.getLogger(__name__).warning('Neon token verification failed: %s', type(error).__name__)
        raise HTTPException(status_code=401, detail='Invalid or expired sign-in', headers={'WWW-Authenticate': 'Bearer'})
    try:
        exists = db.execute(text('SELECT 1 FROM neon_auth."user" WHERE id = :user_id'), {'user_id': user_id}).scalar()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail='Authentication service unavailable')
    if not exists:
        raise HTTPException(status_code=401, detail='Sign in required', headers={'WWW-Authenticate': 'Bearer'})
    return 'user:' + user_id
