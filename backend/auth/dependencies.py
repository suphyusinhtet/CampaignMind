# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.backends import RSAKey
import httpx
from functools import lru_cache
from config.settings import settings

security = HTTPBearer()


@lru_cache(maxsize=1)
def _get_supabase_jwks() -> dict:
    """
    Fetch and cache the Supabase JWKS (public keys) for RS256 JWT verification.
    Cached for the lifetime of the process — re-deploy to rotate keys.
    """
    url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate a Supabase-issued JWT and return the decoded payload.

    The payload contains:
      - sub   : user UUID (auth.users.id)
      - email : user email
      - role  : "authenticated"
      - exp   : expiry timestamp

    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        jwks = _get_supabase_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching key from JWKS
        matching_key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                matching_key = RSAKey(k, algorithm="RS256")
                break

        if matching_key is None:
            raise auth_error

        payload = jwt.decode(
            token,
            matching_key.public_key(),
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )

        if not payload.get("sub"):
            raise auth_error

        return payload

    except JWTError:
        raise auth_error
