# auth/dependencies.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.backends import RSAKey, ECKey
import httpx
from functools import lru_cache
from config.settings import settings

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _get_supabase_jwks() -> dict:
    """
    Fetch and cache the Supabase JWKS (public keys) for JWT verification.
    Cached for the lifetime of the process — re-deploy to rotate keys.
    """
    url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def _decode_token(token: str) -> dict:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        jwks = _get_supabase_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")

        matching_key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key_type = k.get("kty")
                if key_type == "RSA":
                    matching_key = RSAKey(k, algorithm=alg)
                elif key_type == "EC":
                    matching_key = ECKey(k, algorithm=alg)
                break

        if matching_key is None:
            raise auth_error

        payload = jwt.decode(
            token,
            matching_key.public_key(),
            algorithms=[alg],
            audience="authenticated",
            options={"verify_exp": True},
        )

        if not payload.get("sub"):
            raise auth_error

        return payload
    except JWTError:
        raise auth_error


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
    return _decode_token(credentials.credentials)


async def get_current_or_guest_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
) -> dict:
    """
    Resolve authenticated user when JWT exists, otherwise allow guest identity when enabled.
    Guest identity is provided via `X-Guest-Id` header.
    """
    if credentials is not None:
        payload = _decode_token(credentials.credentials)
        payload["is_guest"] = False
        return payload

    if not settings.ENABLE_GUEST_MODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    guest_id = (request.headers.get("X-Guest-Id") or "").strip()
    if not guest_id:
        raise HTTPException(status_code=401, detail="Missing X-Guest-Id for guest mode")

    return {
        "sub": guest_id,
        "role": "guest",
        "is_guest": True,
    }
